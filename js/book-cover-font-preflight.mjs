// #199 browser-native font readiness gate for the optional A4 book cover.
// Uses only the already committed local Baloo 2 family. This module does not
// render user text, fetch fonts itself, persist names, encode PNGs, print, or
// prove physical glyph legibility. Visual/font-fallback QA remains separate.
export const BOOK_COVER_FONT_FAMILY = "Baloo 2";
export const BOOK_COVER_FONT_SPEC = '700 240px "Baloo 2"';
export const BOOK_COVER_REQUIRED_GLYPHS = "AaÄäÖöÜüß";

function checkedFontSet(fonts) {
  if (!fonts || typeof fonts.load !== "function" || typeof fonts.check !== "function") {
    throw new TypeError("FontFaceSet-like load/check interface required");
  }
  return fonts;
}

function checkedContext(context) {
  if (!context || typeof context.measureText !== "function") {
    throw new TypeError("Canvas text-measure interface required");
  }
  return context;
}

// Load/check only a fixed non-personal glyph probe. Never pass a visitor's
// title/name into this readiness function, logs, URLs, storage, or analytics.
export async function preflightBookCoverFont(fonts) {
  const set = checkedFontSet(fonts);
  let loaded;
  try {
    loaded = await set.load(BOOK_COVER_FONT_SPEC, BOOK_COVER_REQUIRED_GLYPHS);
  } catch {
    throw new Error("Book cover font load failed");
  }

  let faces;
  try {
    faces = Array.from(loaded);
  } catch {
    throw new Error("Book cover font load result is invalid");
  }
  if (faces.length < 1) {
    throw new Error("Book cover font face is unavailable");
  }
  if (!set.check(BOOK_COVER_FONT_SPEC, BOOK_COVER_REQUIRED_GLYPHS)) {
    throw new Error("Book cover font is not ready for required German glyphs");
  }

  return Object.freeze({
    ok: true,
    family: BOOK_COVER_FONT_FAMILY,
    spec: BOOK_COVER_FONT_SPEC,
    requiredGlyphs: BOOK_COVER_REQUIRED_GLYPHS,
    loadedFaceCount: faces.length,
  });
}

// This is a mechanical metrics gate only. Non-zero browser text metrics do not
// prove the selected face did not visually fall back, nor that letter interiors
// are large enough for children. Those remain explicit browser/physical QA.
export function measureBookCoverRequiredGlyphs(context) {
  const canvas = checkedContext(context);
  const measurements = [];
  for (const glyph of BOOK_COVER_REQUIRED_GLYPHS) {
    const metrics = canvas.measureText(glyph);
    const values = {
      width: metrics?.width,
      left: metrics?.actualBoundingBoxLeft,
      right: metrics?.actualBoundingBoxRight,
      ascent: metrics?.actualBoundingBoxAscent,
      descent: metrics?.actualBoundingBoxDescent,
    };
    if (Object.values(values).some(value => !Number.isFinite(value)) ||
        values.width <= 0 || values.left + values.right <= 0 ||
        values.ascent + values.descent <= 0) {
      throw new Error("Required book cover glyph has unusable text metrics");
    }
    measurements.push(Object.freeze({ glyph, ...values }));
  }
  return Object.freeze(measurements);
}
