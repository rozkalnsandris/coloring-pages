// #199 pure decoded-RGB pixel gate for the optional portrait A4 cover.
// Input is a *complete, already decoded*, row-major RGB 8-bit raster.
// This does not decode PNG IDAT, validate font/glyph layout, render/encode
// a cover, stage ZIP files, or authorize visitor printing.
import { BOOK_COVER_A4_CONTRACT } from "./book-cover-a4-contract.mjs";

const { width: WIDTH, height: HEIGHT, safeFramePx: MARGIN } = BOOK_COVER_A4_CONTRACT;
const RGB_LENGTH = WIDTH * HEIGHT * 3;
const INVALID_FRAME = Object.freeze({
  ok: false,
  errors: Object.freeze(["A4 cover safe frame must be exact white RGB"]),
});
const VALID_FRAME = Object.freeze({ ok: true, errors: Object.freeze([]) });

// Do not accept RGBA or an arbitrary width/height: this lane intentionally
// proves only the full-size 2480x3508 RGB outer 177-pixel margin.
export function validateBookCoverRgbSafeFrame(rgb) {
  if (!(rgb instanceof Uint8Array) || rgb.length !== RGB_LENGTH) {
    throw new TypeError("Complete 2480x3508 RGB8 raster required");
  }

  for (let y = 0; y < HEIGHT; y++) {
    const row = y * WIDTH * 3;
    const fullRow = y < MARGIN || y >= HEIGHT - MARGIN;
    for (let x = 0; x < WIDTH; x++) {
      if (!fullRow && x >= MARGIN && x < WIDTH - MARGIN) {
        x = WIDTH - MARGIN - 1; // skip interior; scan only the two side bands
        continue;
      }
      const offset = row + x * 3;
      if (rgb[offset] !== 255 || rgb[offset + 1] !== 255 || rgb[offset + 2] !== 255) {
        return INVALID_FRAME;
      }
    }
  }
  return VALID_FRAME;
}
