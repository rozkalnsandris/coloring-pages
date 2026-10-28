import test from "node:test";
import assert from "node:assert/strict";
import { validateBookCoverRgbSafeFrame } from "../js/book-cover-rgb-safe-frame.mjs";
import { BOOK_COVER_A4_CONTRACT } from "../js/book-cover-a4-contract.mjs";

const { width, height, safeFramePx: margin } = BOOK_COVER_A4_CONTRACT;
const rgb = new Uint8Array(width * height * 3).fill(255);
const at = (x, y, channel = 0) => ((y * width + x) * 3) + channel;

function withPixelChanged(x, y, channel, value, fn) {
  const index = at(x, y, channel);
  const previous = rgb[index];
  rgb[index] = value;
  try { fn(); } finally { rgb[index] = previous; }
}

test("full A4 white safe frame is accepted; valid result is immutable", () => {
  const result = validateBookCoverRgbSafeFrame(rgb);
  assert.deepEqual(result, { ok: true, errors: [] });
  assert.equal(Object.isFrozen(result), true);
  assert.equal(Object.isFrozen(result.errors), true);
});

test("nonwhite artwork inside the 177-pixel inset is permitted", () => {
  for (const [x, y] of [[margin, margin], [width - margin - 1, height - margin - 1]]) {
    withPixelChanged(x, y, 2, 0, () => {
      assert.equal(validateBookCoverRgbSafeFrame(rgb).ok, true);
    });
  }
});

test("one dirty channel in any of four exact-white bands fails closed", () => {
  const locations = [
    [margin, margin - 1],
    [margin, height - margin],
    [margin - 1, Math.floor(height / 2)],
    [width - margin, Math.floor(height / 2)],
    [0, 0],
    [width - 1, height - 1],
  ];
  for (const [x, y] of locations) {
    withPixelChanged(x, y, 1, 254, () => {
      const result = validateBookCoverRgbSafeFrame(rgb);
      assert.deepEqual(result, {
        ok: false,
        errors: ["A4 cover safe frame must be exact white RGB"],
      });
      assert.equal(Object.isFrozen(result.errors), true);
    });
  }
});

test("wrong byte length and RGBA input are not mistaken for a valid RGB raster", () => {
  assert.throws(() => validateBookCoverRgbSafeFrame(null), TypeError);
  assert.throws(() => validateBookCoverRgbSafeFrame({ pixels: rgb }), TypeError);
  assert.throws(() => validateBookCoverRgbSafeFrame(rgb.subarray(0, -1)), TypeError);
  assert.throws(() => validateBookCoverRgbSafeFrame(new Uint8Array(width * height * 4)), TypeError);
});

test("input bytes remain untouched, and pixels outside the inset are checked", () => {
  const before = rgb.slice(0, 16);
  assert.equal(validateBookCoverRgbSafeFrame(rgb).ok, true);
  assert.deepEqual(rgb.slice(0, 16), before);
  withPixelChanged(width - 1, height - margin, 0, 0, () => {
    assert.equal(validateBookCoverRgbSafeFrame(rgb).ok, false);
  });
});

test("this pixel gate does not claim any PNG decompression, glyph or print QA", () => {
  // White decoded pixels alone are not evidence of a valid compressed PNG.
  // Keep ZIP-with-cover and Alles drucken gated in the visitor-facing UI.
  assert.equal(validateBookCoverRgbSafeFrame(rgb).ok, true);
});
