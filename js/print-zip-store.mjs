// Offline ZIP STORE exporter for already-validated, ordered public A4 PNG sheets.
// No fetch, browser download, storage, third-party library or image transcoding.
import { validateBookCoverPngStructure } from "./book-cover-a4-contract.mjs";
import { parseBookCoverPngStructure } from "./book-cover-png-parser.mjs";
const MAX_SHEETS = 5;
export const MAX_ZIP_INPUT_BYTES = 64 * 1024 * 1024; // conservative pre-device-QA memory guard
const PNG_SIGNATURE = Uint8Array.of(137, 80, 78, 71, 13, 10, 26, 10);
const SAFE_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const SAFE_PUBLIC_PRINT = /^\/media\/([a-z0-9]+(?:-[a-z0-9]+)*)\/print(?:-[a-z0-9]+|\.[a-f0-9]{64})?\.png$/;
const encoder = new TextEncoder();
const CRC_TABLE = Uint32Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let i = 0; i < 8; i++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
  return c >>> 0;
});

function u32(view, offset) { return view.getUint32(offset, false); }
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = CRC_TABLE[(crc ^ byte) & 255] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

export function assertCanonicalA4Png(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.byteLength < 57) throw new TypeError("Valid PNG bytes required");
  for (let i = 0; i < PNG_SIGNATURE.length; i++) {
    if (bytes[i] !== PNG_SIGNATURE[i]) throw new TypeError("Invalid PNG signature");
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let cursor = 8, first = true, hasData = false, finished = false;
  while (cursor < bytes.length) {
    if (bytes.length - cursor < 12) throw new TypeError("Truncated PNG chunk");
    const size = u32(view, cursor);
    if (size > bytes.length - cursor - 12) throw new TypeError("Invalid PNG chunk length");
    const type = String.fromCharCode(...bytes.subarray(cursor + 4, cursor + 8));
    const dataPos = cursor + 8;
    const crcPos = dataPos + size;
    const declaredCrc = u32(view, crcPos);
    const computedCrc = crc32(bytes.subarray(cursor + 4, crcPos));
    if (computedCrc !== declaredCrc) throw new TypeError("Invalid PNG chunk CRC");
    if (first) {
      if (type !== "IHDR" || size !== 13) throw new TypeError("Missing PNG IHDR");
      const width = u32(view, dataPos), height = u32(view, dataPos + 4);
      if (!((width === 2480 && height === 3508) || (width === 3508 && height === 2480))) {
        throw new TypeError("PNG does not have canonical A4 dimensions");
      }
      if (bytes[dataPos + 8] !== 8 || bytes[dataPos + 9] !== 2 ||
          bytes[dataPos + 10] !== 0 || bytes[dataPos + 11] !== 0 || bytes[dataPos + 12] !== 0) {
        throw new TypeError("PNG must use 8-bit non-interlaced RGB");
      }
      first = false;
    } else if (type === "IHDR") {
      throw new TypeError("Duplicate PNG IHDR");
    }
    if (type === "IDAT" && size > 0) hasData = true;
    cursor = crcPos + 4;
    if (type === "IEND") {
      if (size !== 0 || !hasData || cursor !== bytes.length) throw new TypeError("Incomplete PNG image");
      finished = true;
      break;
    }
  }
  if (!finished) throw new TypeError("Missing PNG IEND");
}

// orderedPages must come from expandBasketForExport(fresh catalogue);
// downloads are fetched by the caller in exactly that order, with their URLs.
// Returns bytes only; callers own URL.createObjectURL lifecycle and user-click gates.
function validatedArtworkFiles(
  orderedPages,
  downloads,
  { maxSheets = MAX_SHEETS, initialBytes = 0 } = {},
) {
  if (!Array.isArray(orderedPages) || !Array.isArray(downloads) ||
      !orderedPages.length || orderedPages.length > maxSheets ||
      orderedPages.length !== downloads.length ||
      !Number.isSafeInteger(initialBytes) || initialBytes < 0 ||
      initialBytes > MAX_ZIP_INPUT_BYTES) {
    throw new RangeError("ZIP requires a bounded matching A4 artwork set");
  }

  const files = [];
  const seenUrls = new Set();
  const seenPages = new Set();
  let totalInput = initialBytes;

  for (let i = 0; i < orderedPages.length; i++) {
    const page = orderedPages[i], download = downloads[i];
    if (!page || !SAFE_ID.test(page.activityId) ||
        !Number.isInteger(page.pageIndex) || page.pageIndex < 1 ||
        !Number.isInteger(page.pageCount) || page.pageCount < page.pageIndex ||
        page.pageCount > 12 ||
        typeof page.printUrl !== "string" || !SAFE_PUBLIC_PRINT.test(page.printUrl) ||
        SAFE_PUBLIC_PRINT.exec(page.printUrl)[1] !== page.activityId ||
        !download || download.url !== page.printUrl ||
        !(download.bytes instanceof Uint8Array) ||
        seenUrls.has(page.printUrl) ||
        seenPages.has(page.activityId + ":" + page.pageIndex)) {
      throw new TypeError("Untrusted or mismatched ZIP page");
    }

    const data = download.bytes;
    totalInput += data.byteLength;
    if (totalInput > MAX_ZIP_INPUT_BYTES) {
      throw new RangeError("ZIP memory guard exceeded");
    }
    assertCanonicalA4Png(data);
    seenUrls.add(page.printUrl);
    seenPages.add(page.activityId + ":" + page.pageIndex);

    const filename = String(i + 1).padStart(2, "0") + "-" + page.activityId + ".png";
    files.push({
      data,
      name: encoder.encode(filename),
      crc: crc32(data),
      filename,
    });
  }
  return files;
}

function buildStoreArchive(files) {
  if (!Array.isArray(files) || files.length < 1 || files.length > MAX_SHEETS) {
    throw new RangeError("ZIP STORE requires 1-5 files");
  }
  const filenames = files.map(file => file.filename);
  if (new Set(filenames).size !== filenames.length) {
    throw new TypeError("ZIP filenames must be unique");
  }

  const size = 22 + files.reduce(
    (n, f) => n + 76 + f.name.length * 2 + f.data.length,
    0,
  );
  if (size > 0xffffffff) throw new RangeError("ZIP64 is unsupported");

  const result = new Uint8Array(size);
  const view = new DataView(result.buffer);
  const set16 = (offset, value) => view.setUint16(offset, value, true);
  const set32 = (offset, value) => view.setUint32(offset, value, true);
  const offsets = [];
  let pos = 0;

  for (const file of files) {
    offsets.push(pos);
    set32(pos, 0x04034b50);
    set16(pos + 4, 20);
    set16(pos + 6, 0);
    set16(pos + 8, 0); // no flags, STORE (no PNG recompression)
    set16(pos + 10, 0);
    set16(pos + 12, 33); // deterministic DOS 1980-01-01
    set32(pos + 14, file.crc);
    set32(pos + 18, file.data.length);
    set32(pos + 22, file.data.length);
    set16(pos + 26, file.name.length);
    set16(pos + 28, 0);
    pos += 30;
    result.set(file.name, pos);
    pos += file.name.length;
    result.set(file.data, pos);
    pos += file.data.length;
  }

  const centralStart = pos;
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    set32(pos, 0x02014b50);
    set16(pos + 4, 20);
    set16(pos + 6, 20);
    set16(pos + 8, 0);
    set16(pos + 10, 0);
    set16(pos + 12, 0);
    set16(pos + 14, 33);
    set32(pos + 16, file.crc);
    set32(pos + 20, file.data.length);
    set32(pos + 24, file.data.length);
    set16(pos + 28, file.name.length);
    set16(pos + 30, 0);
    set16(pos + 32, 0);
    set16(pos + 34, 0);
    set16(pos + 36, 0);
    set32(pos + 38, 0);
    set32(pos + 42, offsets[i]);
    pos += 46;
    result.set(file.name, pos);
    pos += file.name.length;
  }

  const centralSize = pos - centralStart;
  set32(pos, 0x06054b50);
  set16(pos + 4, 0);
  set16(pos + 6, 0);
  set16(pos + 8, files.length);
  set16(pos + 10, files.length);
  set32(pos + 12, centralSize);
  set32(pos + 16, centralStart);
  set16(pos + 20, 0);
  if (pos + 22 !== result.length) throw new Error("ZIP layout mismatch");

  return Object.freeze({
    bytes: result,
    filenames: Object.freeze(filenames),
  });
}

export function buildPrintPngZip(orderedPages, downloads) {
  return buildStoreArchive(validatedArtworkFiles(orderedPages, downloads));
}

export const BOOK_COVER_ZIP_FILENAME = "00-deckblatt.png";

// Covered book ZIPs reuse the same STORE writer. The cover is always first,
// never contains title/name in its filename, and consumes one of five sheets.
export function buildBookPrintPngZip(orderedPages, downloads, coverPng) {
  if (!(coverPng instanceof Uint8Array) || coverPng.byteLength === 0) {
    throw new TypeError("Verified book cover PNG bytes required");
  }
  assertCanonicalA4Png(coverPng);
  const summary = parseBookCoverPngStructure(coverPng);
  if (!validateBookCoverPngStructure(summary).ok) {
    throw new TypeError("Book cover PNG does not satisfy the exact A4 RGB 300 DPI contract");
  }
  if (coverPng.byteLength > MAX_ZIP_INPUT_BYTES) {
    throw new RangeError("ZIP memory guard exceeded");
  }

  const artworkFiles = validatedArtworkFiles(orderedPages, downloads, {
    maxSheets: MAX_SHEETS - 1,
    initialBytes: coverPng.byteLength,
  });
  const coverName = encoder.encode(BOOK_COVER_ZIP_FILENAME);
  const coverFile = {
    data: coverPng,
    name: coverName,
    crc: crc32(coverPng),
    filename: BOOK_COVER_ZIP_FILENAME,
  };
  return buildStoreArchive([coverFile, ...artworkFiles]);
}
