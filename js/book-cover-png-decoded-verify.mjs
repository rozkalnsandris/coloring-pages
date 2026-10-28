// #199 independent verification of the emitted portrait A4 RGB PNG bytes.
// This restricted gate accepts only unfiltered (filter 0), noninterlaced RGB8
// scanlines produced by the reviewed cover encoder. It does not render glyphs,
// print, export ZIPs or prove browser/device quality.
import { BOOK_COVER_A4_CONTRACT, validateBookCoverPngStructure } from "./book-cover-a4-contract.mjs";
import { parseBookCoverPngStructure } from "./book-cover-png-parser.mjs";
import { validateBookCoverRgbSafeFrame } from "./book-cover-rgb-safe-frame.mjs";

const { width: WIDTH, height: HEIGHT, safeFramePx: MARGIN } = BOOK_COVER_A4_CONTRACT;
const ROW_BYTES = WIDTH * 3;
const MAX_COMPRESSED_BYTES = 32 * 1024 * 1024;

function u32(bytes, offset) {
  return (
    bytes[offset] * 0x1000000 +
    (bytes[offset + 1] << 16) +
    (bytes[offset + 2] << 8) +
    bytes[offset + 3]
  ) >>> 0;
}

// Check actual PNG IDAT output, not merely the caller's original RGB buffer.
// The inflater is streamed with an exact A4 row bound, so a zlib bomb cannot
// allocate unbounded decoded bytes in this function.
export async function verifyBookCoverPngDecodedRgb(png, rgb) {
  if (!(png instanceof Uint8Array) || !(rgb instanceof Uint8Array) ||
      rgb.length !== WIDTH * HEIGHT * 3) {
    throw new TypeError("PNG bytes and complete A4 RGB8 raster required");
  }
  if (!validateBookCoverRgbSafeFrame(rgb).ok) {
    throw new RangeError("Source RGB cover safe frame is not exact white");
  }
  const summary = parseBookCoverPngStructure(png);
  if (!validateBookCoverPngStructure(summary).ok || summary.interlaceMethod !== 0 ||
      summary.hasPlte) {
    throw new Error("Nonconforming RGB A4 cover PNG structure");
  }
  if (typeof ReadableStream !== "function" || typeof DecompressionStream !== "function") {
    throw new Error("Native PNG decompression is unavailable");
  }

  const idats = [];
  let idatBytes = 0;
  for (let offset = 8; offset < png.length;) {
    const length = u32(png, offset);
    const type = String.fromCharCode(...png.subarray(offset + 4, offset + 8));
    if (type === "IDAT") {
      idatBytes += length;
      if (idatBytes > MAX_COMPRESSED_BYTES) {
        throw new RangeError("Compressed cover PNG exceeds fixed limit");
      }
      idats.push(png.subarray(offset + 8, offset + 8 + length));
    }
    offset += 12 + length;
  }
  if (idatBytes === 0) throw new Error("Cover PNG IDAT is empty");

  const input = new ReadableStream({
    start(controller) {
      for (const bytes of idats) controller.enqueue(bytes);
      controller.close();
    },
  });
  const reader = input.pipeThrough(new DecompressionStream("deflate")).getReader();
  const row = new Uint8Array(ROW_BYTES + 1);
  let rowIndex = 0;
  let filled = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      let start = 0;
      while (start < value.length) {
        if (rowIndex >= HEIGHT) throw new RangeError("Decoded PNG exceeds A4 raster");
        const count = Math.min(row.length - filled, value.length - start);
        row.set(value.subarray(start, start + count), filled);
        start += count;
        filled += count;
        if (filled === row.length) {
          if (row[0] !== 0) throw new Error("Unexpected PNG scanline filter");
          const expected = rowIndex * ROW_BYTES;
          const fullMarginRow = rowIndex < MARGIN || rowIndex >= HEIGHT - MARGIN;
          for (let x = 0; x < WIDTH; x++) {
            const margin = fullMarginRow || x < MARGIN || x >= WIDTH - MARGIN;
            for (let channel = 0; channel < 3; channel++) {
              const pos = x * 3 + channel;
              const decoded = row[pos + 1];
              if (margin && decoded !== 255) {
                throw new Error("Decoded PNG safe frame is not exact white");
              }
              if (decoded !== rgb[expected + pos]) {
                throw new Error("Decoded PNG differs from cover RGB input");
              }
            }
          }
          rowIndex++;
          filled = 0;
        }
      }
    }
  } catch (error) {
    try { await reader.cancel(); } catch { /* keep the original error */ }
    throw error;
  } finally {
    reader.releaseLock();
  }
  if (rowIndex !== HEIGHT || filled !== 0) {
    throw new Error("Decoded PNG is shorter than the exact A4 raster");
  }
  return Object.freeze({ ok: true, rowsVerified: HEIGHT, rgbBytesVerified: rgb.length });
}
