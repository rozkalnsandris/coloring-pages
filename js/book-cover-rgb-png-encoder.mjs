// #199 independent browser-native encoder for an already rendered A4 RGB cover.
// No DOM/canvas, font, ZIP, network, storage or print operations are performed.
import { BOOK_COVER_A4_CONTRACT } from "./book-cover-a4-contract.mjs";
import { validateBookCoverRgbSafeFrame } from "./book-cover-rgb-safe-frame.mjs";

const { width: WIDTH, height: HEIGHT, physPixelsPerMetre: PPM } = BOOK_COVER_A4_CONTRACT;
const ROW_BYTES = WIDTH * 3;
const PNG_SIGNATURE = Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10]);
const MAX_COMPRESSED_BYTES = 32 * 1024 * 1024;
const CRC_TABLE = Uint32Array.from({ length: 256 }, (_, value) => {
  let crc = value;
  for (let bit = 0; bit < 8; bit++) {
    crc = (crc & 1) ? (0xedb88320 ^ (crc >>> 1)) : (crc >>> 1);
  }
  return crc >>> 0;
});

function putU32(bytes, offset, value) {
  bytes[offset] = (value >>> 24) & 255;
  bytes[offset + 1] = (value >>> 16) & 255;
  bytes[offset + 2] = (value >>> 8) & 255;
  bytes[offset + 3] = value & 255;
}

function pngChunk(type, data) {
  const bytes = new Uint8Array(data.length + 12);
  putU32(bytes, 0, data.length);
  for (let index = 0; index < 4; index++) bytes[4 + index] = type.charCodeAt(index);
  bytes.set(data, 8);
  let crc = 0xffffffff;
  for (let index = 4; index < bytes.length - 4; index++) {
    crc = CRC_TABLE[(crc ^ bytes[index]) & 255] ^ (crc >>> 8);
  }
  putU32(bytes, bytes.length - 4, (crc ^ 0xffffffff) >>> 0);
  return bytes;
}

// Feed one unfiltered scanline at a time; do not allocate another 26 MiB raster.
// A future browser/phone-memory gate must still measure peak memory usage.
export async function encodeBookCoverRgbPng(rgb) {
  if (!(rgb instanceof Uint8Array) || rgb.length !== WIDTH * HEIGHT * 3) {
    throw new TypeError("Complete A4 RGB8 raster required");
  }
  if (!validateBookCoverRgbSafeFrame(rgb).ok) {
    throw new RangeError("A4 cover requires an exact-white 177 px frame");
  }
  if (typeof CompressionStream !== "function" ||
      typeof ReadableStream !== "function" || typeof Response !== "function") {
    throw new Error("Native PNG compression is not supported");
  }

  let y = 0;
  const rows = new ReadableStream({
    pull(controller) {
      if (y === HEIGHT) {
        controller.close();
        return;
      }
      const row = new Uint8Array(ROW_BYTES + 1); // filter type 0
      row.set(rgb.subarray(y * ROW_BYTES, (y + 1) * ROW_BYTES), 1);
      y++;
      controller.enqueue(row);
    },
  });
  let compressed;
  try {
    compressed = new Uint8Array(await new Response(
      rows.pipeThrough(new CompressionStream("deflate")),
    ).arrayBuffer());
  } catch {
    throw new Error("Cover PNG compression failed");
  }
  if (!compressed.length || compressed.length > MAX_COMPRESSED_BYTES) {
    throw new RangeError("Compressed A4 cover exceeds bounded PNG size");
  }

  const ihdr = new Uint8Array(13);
  putU32(ihdr, 0, WIDTH);
  putU32(ihdr, 4, HEIGHT);
  ihdr[8] = 8; // 8-bit RGB, no alpha, no interlace
  ihdr[9] = 2;
  const phys = new Uint8Array(9);
  putU32(phys, 0, PPM);
  putU32(phys, 4, PPM);
  phys[8] = 1; // metre

  const chunks = [
    PNG_SIGNATURE,
    pngChunk("IHDR", ihdr),
    pngChunk("pHYs", phys),
    pngChunk("IDAT", compressed),
    pngChunk("IEND", new Uint8Array()),
  ];
  const output = new Uint8Array(chunks.reduce((sum, chunk) => sum + chunk.length, 0));
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.length;
  }
  return output;
}
