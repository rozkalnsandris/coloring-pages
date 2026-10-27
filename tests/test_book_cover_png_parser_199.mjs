import test from "node:test";
import assert from "node:assert/strict";
import { parseBookCoverPngStructure } from "../js/book-cover-png-parser.mjs";
import { validateBookCoverPngStructure } from "../js/book-cover-a4-contract.mjs";

const signature = Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10]);

function u32(value) {
  return Uint8Array.from([
    (value >>> 24) & 255,
    (value >>> 16) & 255,
    (value >>> 8) & 255,
    value & 255,
  ]);
}

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function concat(...parts) {
  const length = parts.reduce((sum, part) => sum + part.length, 0);
  const result = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) {
    result.set(part, offset);
    offset += part.length;
  }
  return result;
}

function chunk(type, data = new Uint8Array()) {
  const typeBytes = Uint8Array.from([...type].map((char) => char.charCodeAt(0)));
  const body = concat(typeBytes, data);
  return concat(u32(data.length), body, u32(crc32(body)));
}

function ihdr({
  width = 2480,
  height = 3508,
  bitDepth = 8,
  colorType = 2,
  compression = 0,
  filter = 0,
  interlace = 0,
} = {}) {
  return chunk("IHDR", concat(
    u32(width), u32(height),
    Uint8Array.from([bitDepth, colorType, compression, filter, interlace]),
  ));
}

function phys({ x = 11811, y = 11811, unit = 1 } = {}) {
  return chunk("pHYs", concat(u32(x), u32(y), Uint8Array.from([unit])));
}

function png(...chunks) {
  return concat(signature, ...chunks);
}

const structuralCover = () => png(
  ihdr(),
  phys(),
  chunk("IDAT", Uint8Array.from([1, 2, 3, 4])),
  chunk("IEND"),
);

test("independent byte parser feeds the reviewed A4 structure validator", () => {
  const bytes = structuralCover();
  const summary = parseBookCoverPngStructure(bytes);
  assert.deepEqual(summary, {
    width: 2480,
    height: 3508,
    bitDepth: 8,
    colorType: 2,
    compressionMethod: 0,
    filterMethod: 0,
    interlaceMethod: 0,
    physX: 11811,
    physY: 11811,
    physUnit: 1,
    physChunkCount: 1,
    idatChunkCount: 1,
    chunkCount: 4,
    hasPlte: false,
  });
  assert.equal(Object.isFrozen(summary), true);
  assert.deepEqual(validateBookCoverPngStructure(summary), { ok: true, errors: [] });
});

test("ArrayBuffer and typed-array views are accepted without mutating source bytes", () => {
  const bytes = structuralCover();
  const before = Uint8Array.from(bytes);
  const fromBuffer = parseBookCoverPngStructure(bytes.buffer.slice(0));
  const view = new DataView(bytes.buffer, 0, bytes.byteLength);
  const fromView = parseBookCoverPngStructure(view);
  assert.equal(fromBuffer.width, 2480);
  assert.equal(fromView.height, 3508);
  assert.deepEqual(bytes, before);
  assert.throws(() => parseBookCoverPngStructure("png"), TypeError);
});

test("signature, CRC and truncation failures are rejected before producing evidence", () => {
  const badSignature = structuralCover();
  badSignature[0] = 0;
  assert.throws(() => parseBookCoverPngStructure(badSignature), /signature/);

  const badCrc = structuralCover();
  badCrc[badCrc.length - 1] ^= 1;
  assert.throws(() => parseBookCoverPngStructure(badCrc), /CRC mismatch/);

  const truncated = structuralCover().slice(0, -3);
  assert.throws(() => parseBookCoverPngStructure(truncated), /Truncated/);
});

test("IHDR values and critical chunk order fail closed", () => {
  assert.throws(
    () => parseBookCoverPngStructure(png(phys(), ihdr(), chunk("IDAT"), chunk("IEND"))),
    /IHDR must be the first/,
  );
  assert.throws(
    () => parseBookCoverPngStructure(png(
      ihdr({ colorType: 2, bitDepth: 4 }), chunk("IDAT"), chunk("IEND"),
    )),
    /bit depth\/color type/,
  );
  assert.throws(
    () => parseBookCoverPngStructure(png(
      ihdr(), chunk("ABCD"), chunk("IDAT"), chunk("IEND"),
    )),
    /Unsupported critical/,
  );
});

test("pHYs is unique and must precede consecutive IDAT chunks", () => {
  assert.throws(
    () => parseBookCoverPngStructure(png(
      ihdr(), phys(), phys(), chunk("IDAT"), chunk("IEND"),
    )),
    /pHYs must not appear more than once/,
  );
  assert.throws(
    () => parseBookCoverPngStructure(png(
      ihdr(), chunk("IDAT"), phys(), chunk("IEND"),
    )),
    /pHYs must appear before IDAT/,
  );
  assert.throws(
    () => parseBookCoverPngStructure(png(
      ihdr(), chunk("IDAT"), chunk("tEXt"), chunk("IDAT"), chunk("IEND"),
    )),
    /IDAT chunks must be consecutive/,
  );
});

test("IEND must terminate a PNG with at least one IDAT and no trailing bytes", () => {
  assert.throws(
    () => parseBookCoverPngStructure(png(ihdr(), phys(), chunk("IEND"))),
    /IDAT before IEND/,
  );

  const trailing = concat(structuralCover(), Uint8Array.from([0]));
  assert.throws(() => parseBookCoverPngStructure(trailing), /Trailing bytes after IEND/);
});

test("missing pHYs remains structural evidence that the A4 contract rejects", () => {
  const summary = parseBookCoverPngStructure(png(
    ihdr(), chunk("IDAT", Uint8Array.from([9])), chunk("IEND"),
  ));
  assert.equal(summary.physChunkCount, 0);
  const result = validateBookCoverPngStructure(summary);
  assert.equal(result.ok, false);
  assert.deepEqual(result.errors, [
    "physX: expected 11811",
    "physY: expected 11811",
    "physUnit: expected 1",
    "physChunkCount: expected 1",
  ]);
});

test("parser intentionally does not claim IDAT decompression or pixel-safe-frame validation", () => {
  // Arbitrary IDAT bytes can pass this structure-only lane. A later independent
  // decoder/pixel validator must still prove zlib decoding, exact white 177 px
  // bands and decoded pixel equality before covered ZIP can be enabled.
  const summary = parseBookCoverPngStructure(structuralCover());
  assert.equal(summary.idatChunkCount, 1);
  assert.equal(validateBookCoverPngStructure(summary).ok, true);
});
