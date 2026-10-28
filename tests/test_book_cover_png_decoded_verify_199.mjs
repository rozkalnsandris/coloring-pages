import test from "node:test";
import assert from "node:assert/strict";
import { deflateSync, inflateSync } from "node:zlib";
import { encodeBookCoverRgbPng } from "../js/book-cover-rgb-png-encoder.mjs";
import { verifyBookCoverPngDecodedRgb } from "../js/book-cover-png-decoded-verify.mjs";
import { BOOK_COVER_A4_CONTRACT } from "../js/book-cover-a4-contract.mjs";

const { width: WIDTH, height: HEIGHT, safeFramePx: MARGIN } = BOOK_COVER_A4_CONTRACT;
const ROW_BYTES = WIDTH * 3;
const rgb = new Uint8Array(ROW_BYTES * HEIGHT).fill(255);

function u32(bytes, pos) {
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(pos);
}
function writeU32(bytes, pos, value) {
  new DataView(bytes.buffer).setUint32(pos, value);
}
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const value of bytes) {
    crc ^= value;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}
function chunk(type, payload) {
  const bytes = new Uint8Array(payload.length + 12);
  writeU32(bytes, 0, payload.length);
  bytes.set([...type].map(c => c.charCodeAt(0)), 4);
  bytes.set(payload, 8);
  writeU32(bytes, bytes.length - 4, crc32(bytes.subarray(4, bytes.length - 4)));
  return bytes;
}
function replaceIdat(png, payload) {
  const pieces = [png.subarray(0, 8)];
  let pos = 8;
  for (; pos < png.length;) {
    const size = u32(png, pos);
    const name = String.fromCharCode(...png.subarray(pos + 4, pos + 8));
    pieces.push(name === "IDAT" ? chunk(name, payload) : png.subarray(pos, pos + size + 12));
    pos += size + 12;
  }
  const result = new Uint8Array(pieces.reduce((sum, item) => sum + item.length, 0));
  let offset = 0;
  for (const part of pieces) { result.set(part, offset); offset += part.length; }
  return result;
}
function idatData(png) {
  let pos = 8;
  const pieces = [];
  while (pos < png.length) {
    const length = u32(png, pos);
    const name = String.fromCharCode(...png.subarray(pos + 4, pos + 8));
    if (name === "IDAT") pieces.push(png.subarray(pos + 8, pos + 8 + length));
    pos += 12 + length;
  }
  return Buffer.concat(pieces);
}

test("decode and verify actual cover encoder PNG against full original RGB bytes", async () => {
  const pos = (MARGIN * WIDTH + MARGIN) * 3;
  rgb[pos] = 31;
  try {
    const png = await encodeBookCoverRgbPng(rgb);
    assert.deepEqual(await verifyBookCoverPngDecodedRgb(png, rgb), {
      ok: true, rowsVerified: HEIGHT, rgbBytesVerified: rgb.length,
    });
    rgb[pos] = 32;
    await assert.rejects(verifyBookCoverPngDecodedRgb(png, rgb), /differs/);
  } finally { rgb[pos] = 255; }
});

test("re-CRCed IDAT tampering is rejected by actual decoded white frame and filter gate", async () => {
  const png = await encodeBookCoverRgbPng(rgb);
  const raw = new Uint8Array(inflateSync(idatData(png)));
  raw[1] = 254; // top-left white margin; source RGB remains exact white
  await assert.rejects(
    verifyBookCoverPngDecodedRgb(replaceIdat(png, deflateSync(raw, { level: 1 })), rgb),
    /Decoded PNG safe frame/,
  );
  raw[1] = 255;
  raw[0] = 1; // generated encoder guarantees filter 0 only
  await assert.rejects(
    verifyBookCoverPngDecodedRgb(replaceIdat(png, deflateSync(raw, { level: 1 })), rgb),
    /scanline filter/,
  );
});

test("short, excess or invalid compressed content cannot masquerade as complete A4 PNG", async () => {
  const png = await encodeBookCoverRgbPng(rgb);
  await assert.rejects(
    verifyBookCoverPngDecodedRgb(replaceIdat(png, deflateSync(Uint8Array.of(0))), rgb),
    /shorter than/,
  );
  const raw = inflateSync(idatData(png));
  const extra = Buffer.concat([raw, Buffer.from([0])]);
  await assert.rejects(
    verifyBookCoverPngDecodedRgb(replaceIdat(png, deflateSync(extra, { level: 1 })), rgb),
    /exceeds A4/,
  );
  await assert.rejects(
    verifyBookCoverPngDecodedRgb(replaceIdat(png, Uint8Array.of(1, 2, 3)), rgb),
  );
});

test("unsupported native inflater, invalid input and malformed PNG all fail closed", async () => {
  await assert.rejects(verifyBookCoverPngDecodedRgb(null, rgb), TypeError);
  await assert.rejects(verifyBookCoverPngDecodedRgb(new Uint8Array(), rgb), /too short/);
  await assert.rejects(verifyBookCoverPngDecodedRgb(new Uint8Array(), rgb.subarray(0, -1)), TypeError);
  const png = await encodeBookCoverRgbPng(rgb);
  const saved = globalThis.DecompressionStream;
  try {
    globalThis.DecompressionStream = undefined;
    await assert.rejects(verifyBookCoverPngDecodedRgb(png, rgb), /unavailable/);
  } finally { globalThis.DecompressionStream = saved; }
});
