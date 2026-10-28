// #199 bounded Canvas -> RGB8 extraction for the optional A4 book cover.
// Reads one scanline at a time to avoid a second full-size RGBA ImageData
// allocation. The rendered canvas is always disposed after extraction.
// No PNG encoding, ZIP, DOM attachment, download, storage, network or print.
import { BOOK_COVER_A4_CONTRACT } from "./book-cover-a4-contract.mjs";
import { validateBookCoverRgbSafeFrame } from "./book-cover-rgb-safe-frame.mjs";

const WIDTH = BOOK_COVER_A4_CONTRACT.width;
const HEIGHT = BOOK_COVER_A4_CONTRACT.height;
const RGB_LENGTH = WIDTH * HEIGHT * 3;
const RGBA_ROW_LENGTH = WIDTH * 4;

function checkedRendered(rendered) {
  if (!rendered || typeof rendered !== "object" ||
      rendered.disposed === true ||
      typeof rendered.dispose !== "function" ||
      !rendered.canvas ||
      rendered.canvas.width !== WIDTH ||
      rendered.canvas.height !== HEIGHT ||
      typeof rendered.canvas.getContext !== "function") {
    throw new TypeError("Complete undisposed A4 cover render required");
  }
  return rendered;
}

function checkedRowData(row) {
  const data = row?.data;
  if (!(data instanceof Uint8ClampedArray) || data.length !== RGBA_ROW_LENGTH) {
    throw new TypeError("Exact A4 RGBA canvas scanline required");
  }
  return data;
}

export function extractBookCoverRgb(
  rendered,
  { signal } = {},
) {
  const value = checkedRendered(rendered);
  const rgb = new Uint8Array(RGB_LENGTH);

  try {
    if (signal?.aborted) throw new Error("Book cover RGB extraction aborted");

    const context = value.canvas.getContext("2d", {
      alpha: false,
      willReadFrequently: true,
    });
    if (!context || typeof context.getImageData !== "function") {
      throw new TypeError("Readable A4 cover canvas context required");
    }

    let target = 0;
    for (let y = 0; y < HEIGHT; y++) {
      if (signal?.aborted) throw new Error("Book cover RGB extraction aborted");

      let row;
      try {
        row = context.getImageData(0, y, WIDTH, 1);
      } catch {
        throw new Error("Book cover canvas pixel read failed");
      }
      const rgba = checkedRowData(row);

      for (let source = 0; source < RGBA_ROW_LENGTH; source += 4) {
        if (rgba[source + 3] !== 255) {
          throw new RangeError("Book cover canvas must be fully opaque");
        }
        rgb[target++] = rgba[source];
        rgb[target++] = rgba[source + 1];
        rgb[target++] = rgba[source + 2];
      }
    }

    if (target !== RGB_LENGTH) {
      throw new Error("Incomplete A4 RGB extraction");
    }
    if (signal?.aborted) throw new Error("Book cover RGB extraction aborted");
    if (!validateBookCoverRgbSafeFrame(rgb).ok) {
      throw new RangeError("A4 cover requires an exact-white 177 px frame");
    }

    return rgb;
  } finally {
    value.dispose();
  }
}
