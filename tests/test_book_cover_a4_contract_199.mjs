import test from "node:test";
import assert from "node:assert/strict";
import {
  BOOK_COVER_A4_CONTRACT,
  getBookCoverSafeRect,
  validateBookCoverPngStructure,
} from "../js/book-cover-a4-contract.mjs";

const validSummary = () => ({
  width: 2480,
  height: 3508,
  bitDepth: 8,
  colorType: 2,
  physX: 11811,
  physY: 11811,
  physUnit: 1,
  physChunkCount: 1,
});

test("portrait A4 contract matches reviewed #199 dimensions and 15 mm frame", () => {
  assert.deepEqual(BOOK_COVER_A4_CONTRACT, {
    width: 2480,
    height: 3508,
    safeFramePx: 177,
    bitDepth: 8,
    colorType: 2,
    physPixelsPerMetre: 11811,
    physUnit: 1,
    physChunkCount: 1,
  });
  assert.equal(Object.isFrozen(BOOK_COVER_A4_CONTRACT), true);
  assert.deepEqual(getBookCoverSafeRect(), {
    x: 177,
    y: 177,
    width: 2126,
    height: 3154,
    right: 2303,
    bottom: 3331,
  });
  assert.equal(Object.isFrozen(getBookCoverSafeRect()), true);
});

test("independently parsed RGB 8-bit A4 + one 300-DPI pHYs summary passes", () => {
  const result = validateBookCoverPngStructure(validSummary());
  assert.deepEqual(result, { ok: true, errors: [] });
  assert.equal(Object.isFrozen(result), true);
  assert.equal(Object.isFrozen(result.errors), true);
});

test("RGBA output cannot be mistaken for the required no-alpha RGB PNG", () => {
  const summary = validSummary();
  summary.colorType = 6;
  const result = validateBookCoverPngStructure(summary);
  assert.equal(result.ok, false);
  assert.deepEqual(result.errors, ["colorType: expected 2"]);
});

test("wrong raster dimensions and bit depth fail independently", () => {
  const summary = validSummary();
  summary.width = 3508;
  summary.height = 2480;
  summary.bitDepth = 16;
  const result = validateBookCoverPngStructure(summary);
  assert.equal(result.ok, false);
  assert.deepEqual(result.errors, [
    "width: expected 2480",
    "height: expected 3508",
    "bitDepth: expected 8",
  ]);
});

test("96-DPI-style pHYs metadata is rejected", () => {
  const summary = validSummary();
  summary.physX = 3780;
  summary.physY = 3780;
  const result = validateBookCoverPngStructure(summary);
  assert.equal(result.ok, false);
  assert.deepEqual(result.errors, [
    "physX: expected 11811",
    "physY: expected 11811",
  ]);
});

test("missing, duplicate or unitless pHYs evidence fails closed", () => {
  for (const changes of [
    { physChunkCount: 0 },
    { physChunkCount: 2 },
    { physUnit: 0 },
  ]) {
    const result = validateBookCoverPngStructure({ ...validSummary(), ...changes });
    assert.equal(result.ok, false);
  }
});

test("invalid summary objects throw instead of inventing export evidence", () => {
  for (const value of [null, undefined, [], "png", 7]) {
    assert.throws(() => validateBookCoverPngStructure(value), TypeError);
  }
});
