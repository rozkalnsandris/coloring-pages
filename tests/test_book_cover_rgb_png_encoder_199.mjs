import test from "node:test";
import assert from "node:assert/strict";
import { inflateSync } from "node:zlib";
import { encodeBookCoverRgbPng } from "../js/book-cover-rgb-png-encoder.mjs";
import {
  BOOK_COVER_A4_CONTRACT,
  validateBookCoverPngStructure,
} from "../js/book-cover-a4-contract.mjs";
import { parseBookCoverPngStructure } from "../js/book-cover-png-parser.mjs";

const { width: WIDTH, height: HEIGHT, safeFramePx: SAFE } = BOOK_COVER_A4_CONTRACT;
const ROW_BYTES = WIDTH * 3;
const rgb = new Uint8Array(ROW_BYTES * HEIGHT).fill(255);

function at(x, y, channel = 0) {
  return (y * WIDTH + x) * 3 + channel;
}

function readU32(bytes, offset) {
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(offset);
}

function idatBytes(png) {
  const pieces = [];
  let pos = 8;
  while (pos < png.length) {
    const length = readU32(png, pos);
    const name = String.fromCharCode(...png.subarray(pos + 4, pos + 8));
    if (name === "IDAT") pieces.push(png.subarray(pos + 8, pos + 8 + length));
    pos += 12 + length;
  }
  return Buffer.concat(pieces);
}

test("RGB encoder yields valid A4 PNG, pHYs and exact independent zlib roundtrip", async () => {
  const points = [
    [SAFE, SAFE, 0, 0],
    [SAFE + 7, SAFE + 5, 1, 91],
    [WIDTH - SAFE - 1, HEIGHT - SAFE - 1, 2, 33],
  ];
  for (const [x, y, channel, value] of points) rgb[at(x, y, channel)] = value;
  try {
    const png = await encodeBookCoverRgbPng(rgb);
    assert.deepEqual(Array.from(png.subarray(0, 8)), [137, 80, 78, 71, 13, 10, 26, 10]);
    const summary = parseBookCoverPngStructure(png);
    assert.equal(validateBookCoverPngStructure(summary).ok, true);
    assert.equal(summary.hasPlte, false);
    assert.equal(summary.interlaceMethod, 0);
    assert.equal(summary.chunkCount, 4);
    const data = inflateSync(idatBytes(png));
    assert.equal(data.length, (ROW_BYTES + 1) * HEIGHT);
    for (let y = 0; y < HEIGHT; y++) {
      assert.equal(data[y * (ROW_BYTES + 1)], 0, "row " + y + " filter");
      assert.equal(Buffer.compare(
        data.subarray(y * (ROW_BYTES + 1) + 1, (y + 1) * (ROW_BYTES + 1)),
        rgb.subarray(y * ROW_BYTES, (y + 1) * ROW_BYTES),
      ), 0, "row " + y + " roundtrip");
    }
    assert.equal(rgb[at(SAFE + 7, SAFE + 5, 1)], 91);
  } finally {
    for (const [x, y, channel] of points) rgb[at(x, y, channel)] = 255;
  }
});

test("wrong type, missing bytes, RGBA or nonwhite safe frame is rejected", async () => {
  await assert.rejects(encodeBookCoverRgbPng(null), TypeError);
  await assert.rejects(encodeBookCoverRgbPng(rgb.subarray(0, -1)), TypeError);
  await assert.rejects(encodeBookCoverRgbPng(new Uint8Array(WIDTH * HEIGHT * 4)), TypeError);
  const offset = at(0, SAFE, 2);
  rgb[offset] = 254;
  try {
    await assert.rejects(encodeBookCoverRgbPng(rgb), /exact-white/);
  } finally {
    rgb[offset] = 255;
  }
});

test("unavailable browser-native compression fails closed", async () => {
  const saved = globalThis.CompressionStream;
  try {
    globalThis.CompressionStream = undefined;
    await assert.rejects(encodeBookCoverRgbPng(rgb), /not supported/);
  } finally {
    globalThis.CompressionStream = saved;
  }
});
