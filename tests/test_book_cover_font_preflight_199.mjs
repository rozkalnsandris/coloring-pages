import test from "node:test";
import assert from "node:assert/strict";
import {
  BOOK_COVER_FONT_FAMILY,
  BOOK_COVER_FONT_SPEC,
  BOOK_COVER_REQUIRED_GLYPHS,
  preflightBookCoverFont,
  measureBookCoverRequiredGlyphs,
} from "../js/book-cover-font-preflight.mjs";

test("font preflight uses only the fixed local German glyph probe and freezes evidence", async () => {
  const calls = [];
  const fonts = {
    async load(spec, text) {
      calls.push(["load", spec, text]);
      return [{ family: "Baloo 2" }];
    },
    check(spec, text) {
      calls.push(["check", spec, text]);
      return true;
    },
  };
  const result = await preflightBookCoverFont(fonts);
  assert.deepEqual(result, {
    ok: true,
    family: "Baloo 2",
    spec: '700 240px "Baloo 2"',
    requiredGlyphs: "AaÄäÖöÜüß",
    loadedFaceCount: 1,
  });
  assert.equal(Object.isFrozen(result), true);
  assert.deepEqual(calls, [
    ["load", BOOK_COVER_FONT_SPEC, BOOK_COVER_REQUIRED_GLYPHS],
    ["check", BOOK_COVER_FONT_SPEC, BOOK_COVER_REQUIRED_GLYPHS],
  ]);
  assert.equal(BOOK_COVER_FONT_FAMILY, "Baloo 2");
});

test("font load rejection, empty match and failed readiness check all fail closed", async () => {
  await assert.rejects(
    preflightBookCoverFont({ load: async () => { throw new Error("offline"); }, check: () => true }),
    /load failed/,
  );
  await assert.rejects(
    preflightBookCoverFont({ load: async () => [], check: () => true }),
    /unavailable/,
  );
  await assert.rejects(
    preflightBookCoverFont({ load: async () => [{}], check: () => false }),
    /not ready/,
  );
  await assert.rejects(
    preflightBookCoverFont({ load: async () => null, check: () => true }),
    /load result is invalid/,
  );
  await assert.rejects(preflightBookCoverFont(null), TypeError);
});

test("required German glyph metrics are measured individually and frozen", () => {
  const seen = [];
  const context = {
    measureText(glyph) {
      seen.push(glyph);
      const code = glyph.codePointAt(0);
      return {
        width: 100 + (code % 13),
        actualBoundingBoxLeft: 4,
        actualBoundingBoxRight: 96,
        actualBoundingBoxAscent: 150,
        actualBoundingBoxDescent: 24,
      };
    },
  };
  const result = measureBookCoverRequiredGlyphs(context);
  assert.deepEqual(seen, Array.from(BOOK_COVER_REQUIRED_GLYPHS));
  assert.equal(result.length, Array.from(BOOK_COVER_REQUIRED_GLYPHS).length);
  assert.equal(Object.isFrozen(result), true);
  assert.equal(result.every(Object.isFrozen), true);
  assert.deepEqual(result.map(item => item.glyph), Array.from(BOOK_COVER_REQUIRED_GLYPHS));
});

test("missing or unusable browser metrics fail closed instead of claiming glyph quality", () => {
  assert.throws(() => measureBookCoverRequiredGlyphs(null), TypeError);
  const cases = [
    { width: 0, actualBoundingBoxLeft: 1, actualBoundingBoxRight: 1, actualBoundingBoxAscent: 2, actualBoundingBoxDescent: 1 },
    { width: 10, actualBoundingBoxLeft: 0, actualBoundingBoxRight: 0, actualBoundingBoxAscent: 2, actualBoundingBoxDescent: 1 },
    { width: 10, actualBoundingBoxLeft: 1, actualBoundingBoxRight: 1, actualBoundingBoxAscent: 0, actualBoundingBoxDescent: 0 },
    { width: 10, actualBoundingBoxLeft: 1, actualBoundingBoxRight: 1, actualBoundingBoxAscent: Number.NaN, actualBoundingBoxDescent: 1 },
  ];
  for (const metrics of cases) {
    assert.throws(
      () => measureBookCoverRequiredGlyphs({ measureText: () => metrics }),
      /unusable text metrics/,
    );
  }
});
