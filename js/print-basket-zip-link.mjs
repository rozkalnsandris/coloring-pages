// UI-independent, visitor-clickable ZIP download links for #206/#199.
// Do not call click() here: visitors must activate the displayed link themselves.
// The caller owns DOM placement and MUST dispose on close/replacement/navigation.
import { MAX_ZIP_INPUT_BYTES } from "./print-zip-store.mjs";

export const BASKET_ZIP_FILENAME = "ausmalwiese-drucksammlung.zip";
export const BOOK_ZIP_FILENAME = "ausmalwiese-malbuch.zip";
export const BOOK_COVER_ZIP_MEMBER = "00-deckblatt.png";

const MAX_ZIP_OVERHEAD = 64 * 1024;
const SAFE_SHEET_FILENAME = /^([0-9]{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.png$/;
const decoder = new TextDecoder();

function checkedFilenames(filenames, { allowCover }) {
  const hasCover = filenames[0] === BOOK_COVER_ZIP_MEMBER;
  if (hasCover && !allowCover) {
    throw new TypeError("Basket ZIP must not contain a book cover member");
  }
  if (hasCover && filenames.length < 2) {
    throw new TypeError("Covered book ZIP requires at least one artwork sheet");
  }

  const offset = hasCover ? 1 : 0;
  for (let i = offset; i < filenames.length; i++) {
    const name = filenames[i];
    const match = typeof name === "string" && name.length <= 128
      ? SAFE_SHEET_FILENAME.exec(name)
      : null;
    const expected = i - offset + 1;
    if (!match || Number(match[1]) !== expected) {
      throw new TypeError("ZIP filenames must have safe sequential sheet names");
    }
  }
  return hasCover;
}

function checkedArchive(zip, { allowCover = false } = {}) {
  const bytes = zip?.bytes;
  const filenames = zip?.filenames;
  if (!(bytes instanceof Uint8Array) || !Array.isArray(filenames) ||
      filenames.length < 1 || filenames.length > 5 ||
      bytes.byteLength < 22 ||
      bytes.byteLength > MAX_ZIP_INPUT_BYTES + MAX_ZIP_OVERHEAD) {
    throw new TypeError("A complete bounded ZIP is required");
  }

  checkedFilenames(filenames, { allowCover });

  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (view.getUint32(0, true) !== 0x04034b50) {
    throw new TypeError("ZIP local header missing");
  }

  const end = bytes.byteLength - 22;
  if (view.getUint32(end, true) !== 0x06054b50 ||
      view.getUint16(end + 4, true) !== 0 ||
      view.getUint16(end + 6, true) !== 0 ||
      view.getUint16(end + 8, true) !== filenames.length ||
      view.getUint16(end + 10, true) !== filenames.length ||
      view.getUint16(end + 20, true) !== 0) {
    throw new TypeError("Incomplete ZIP central directory");
  }

  const size = view.getUint32(end + 12, true);
  const start = view.getUint32(end + 16, true);
  if (start < 30 || size < 46 * filenames.length ||
      start + size !== end || start + size > bytes.byteLength) {
    throw new TypeError("Invalid ZIP central directory size");
  }

  let cursor = start;
  for (const name of filenames) {
    if (cursor + 46 > end ||
        view.getUint32(cursor, true) !== 0x02014b50 ||
        view.getUint16(cursor + 10, true) !== 0) {
      throw new TypeError("Expected uncompressed ZIP entries");
    }
    const nameLength = view.getUint16(cursor + 28, true);
    const extraLength = view.getUint16(cursor + 30, true);
    const commentLength = view.getUint16(cursor + 32, true);
    const next = cursor + 46 + nameLength + extraLength + commentLength;
    const localOffset = view.getUint32(cursor + 42, true);

    if (nameLength !== name.length ||
        next > end ||
        localOffset + 30 > start ||
        view.getUint32(localOffset, true) !== 0x04034b50 ||
        decoder.decode(bytes.subarray(
          cursor + 46,
          cursor + 46 + nameLength,
        )) !== name) {
      throw new TypeError("ZIP entry name or offset mismatch");
    }
    cursor = next;
  }

  if (cursor !== end) {
    throw new TypeError("Unexpected ZIP entries");
  }
  return bytes;
}

function stageZipDownloadLink(
  zip,
  {
    filename,
    allowCover,
    documentRef = globalThis.document,
    urlRef = globalThis.URL,
    BlobCtor = globalThis.Blob,
  },
) {
  const bytes = checkedArchive(zip, { allowCover });
  if (typeof filename !== "string" || !filename ||
      typeof documentRef?.createElement !== "function" ||
      typeof urlRef?.createObjectURL !== "function" ||
      typeof urlRef?.revokeObjectURL !== "function" ||
      typeof BlobCtor !== "function") {
    throw new TypeError("Browser download capabilities unavailable");
  }

  const link = documentRef.createElement("a");
  if (!link || typeof link.removeAttribute !== "function") {
    throw new TypeError("Download link creation failed");
  }

  const blob = new BlobCtor([bytes], { type: "application/zip" });
  if (blob.size !== bytes.byteLength) {
    throw new TypeError("ZIP Blob byte mismatch");
  }

  let objectUrl;
  try {
    objectUrl = urlRef.createObjectURL(blob);
    if (typeof objectUrl !== "string" || !objectUrl.startsWith("blob:")) {
      throw new TypeError("Object URL could not be created");
    }
    link.href = objectUrl;
    link.download = filename;
    link.rel = "noopener";
    link.textContent = "Als ZIP speichern";
  } catch (error) {
    if (typeof objectUrl === "string") {
      try {
        urlRef.revokeObjectURL(objectUrl);
      } catch {
        // Original error wins.
      }
    }
    throw error;
  }

  let disposed = false;
  return {
    link,
    filename,
    dispose() {
      if (disposed) return;
      disposed = true;
      try {
        link.removeAttribute("href");
      } finally {
        urlRef.revokeObjectURL(objectUrl);
      }
    },
  };
}

export function stageBasketZipDownloadLink(zip, options = {}) {
  return stageZipDownloadLink(zip, {
    ...options,
    filename: BASKET_ZIP_FILENAME,
    allowCover: false,
  });
}

export function stageBookZipDownloadLink(zip, options = {}) {
  return stageZipDownloadLink(zip, {
    ...options,
    filename: BOOK_ZIP_FILENAME,
    allowCover: true,
  });
}
