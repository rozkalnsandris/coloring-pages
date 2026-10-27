// #199 pure A4 cover geometry and PNG-structure contract.
// This module does not render, encode, download, store, print, or inspect pixels.
// Pixel-safe-frame and visual/glyph acceptance remain separate evidence gates.

export const BOOK_COVER_A4_CONTRACT = Object.freeze({
  width: 2480,
  height: 3508,
  safeFramePx: 177,
  bitDepth: 8,
  colorType: 2,
  physPixelsPerMetre: 11811,
  physUnit: 1,
  physChunkCount: 1,
});

export function getBookCoverSafeRect() {
  const { width, height, safeFramePx } = BOOK_COVER_A4_CONTRACT;
  return Object.freeze({
    x: safeFramePx,
    y: safeFramePx,
    width: width - (2 * safeFramePx),
    height: height - (2 * safeFramePx),
    right: width - safeFramePx,
    bottom: height - safeFramePx,
  });
}

function checkedSummary(summary) {
  if (!summary || typeof summary !== "object" || Array.isArray(summary)) {
    throw new TypeError("Parsed PNG structure summary required");
  }
  return summary;
}

// Validate only independently parsed PNG header/chunk metadata. A PASS here
// does not prove exact-white 177 px edge pixels, glyph fit, font loading,
// decoded pixel equality, browser memory safety, or physical print quality.
export function validateBookCoverPngStructure(summary) {
  const value = checkedSummary(summary);
  const expected = BOOK_COVER_A4_CONTRACT;
  const errors = [];

  const checks = [
    ["width", expected.width],
    ["height", expected.height],
    ["bitDepth", expected.bitDepth],
    ["colorType", expected.colorType],
    ["physX", expected.physPixelsPerMetre],
    ["physY", expected.physPixelsPerMetre],
    ["physUnit", expected.physUnit],
    ["physChunkCount", expected.physChunkCount],
  ];

  for (const [field, wanted] of checks) {
    if (value[field] !== wanted) {
      errors.push(`${field}: expected ${wanted}`);
    }
  }

  return Object.freeze({
    ok: errors.length === 0,
    errors: Object.freeze(errors),
  });
}
