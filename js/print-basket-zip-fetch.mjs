// Source-only ordered full-quality PNG retrieval for basket ZIP (#206).
// No DOM, storage, download trigger, telemetry or third-party dependency.
// Caller MUST first derive pages with expandBasketForExport from a fresh catalogue.
import { assertCanonicalA4Png, buildPrintPngZip, MAX_ZIP_INPUT_BYTES } from "./print-zip-store.mjs";

const MAX_SHEETS = 5;
const PATH = /^\/media\/([a-z0-9]+(?:-[a-z0-9]+)*)\/print(?:-[a-z0-9]+|\.[a-f0-9]{64})?\.png$/;
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function checkedPages(pages) {
  if (!Array.isArray(pages) || pages.length < 1 || pages.length > MAX_SHEETS) {
    throw new RangeError("Exactly 1-5 ordered print pages required");
  }
  const seen = new Set();
  for (const page of pages) {
    const match = typeof page?.printUrl === "string" ? PATH.exec(page.printUrl) : null;
    if (!match || !ID.test(page.activityId) || match[1] !== page.activityId ||
        !Number.isInteger(page.pageIndex) || page.pageIndex < 1 ||
        !Number.isInteger(page.pageCount) || page.pageCount < page.pageIndex ||
        page.pageCount > 12 || seen.has(page.printUrl)) {
      throw new TypeError("Untrusted or duplicate public print page");
    }
    seen.add(page.printUrl);
  }
}

function checkedOrigin(origin) {
  if (typeof origin !== "string") throw new TypeError("An explicit site origin is required");
  const url = new URL(origin);
  if (!["https:", "http:"].includes(url.protocol) || !url.hostname ||
      url.username || url.password || url.pathname !== "/" || url.search || url.hash ||
      url.origin !== origin.replace(/\/$/, "")) {
    throw new TypeError("A canonical site origin is required");
  }
  return url.origin;
}

function checkedSize(raw, remaining) {
  if (raw === null) return null;
  if (!/^(0|[1-9][0-9]*)$/.test(raw)) throw new TypeError("Invalid PNG Content-Length");
  const size = Number(raw);
  if (!Number.isSafeInteger(size) || size > remaining) throw new RangeError("PNG exceeds ZIP memory budget");
  return size;
}

async function readBoundedStream(response, remaining, declared, signal) {
  if (!response.body || typeof response.body.getReader !== "function") {
    throw new TypeError("Streaming PNG response required");
  }
  const reader = response.body.getReader();
  let finished = false, count = 0;
  const chunks = [];
  try {
    for (;;) {
      if (signal?.aborted) throw new Error("PNG request aborted");
      const next = await reader.read();
      if (next.done) { finished = true; break; }
      if (!(next.value instanceof Uint8Array) || next.value.byteLength === 0) {
        throw new TypeError("Invalid PNG stream chunk");
      }
      count += next.value.byteLength;
      if (!Number.isSafeInteger(count) || count > remaining || (declared !== null && count > declared)) {
        throw new RangeError("PNG exceeds declared/bounded size");
      }
      chunks.push(next.value);
    }
    if (signal?.aborted) throw new Error("PNG request aborted");
    if (!count || (declared !== null && count !== declared)) {
      throw new TypeError("Empty or incomplete PNG response");
    }
    const bytes = new Uint8Array(count);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    return bytes;
  } finally {
    if (!finished) {
      try { await reader.cancel(); } catch { /* cancellation is best effort after failure */ }
    }
    reader.releaseLock();
  }
}

// Shared sequential, bounded transport. No file is returned on HTTP, MIME, size,
// redirect, stream or cancellation failure. The raw helper is private to keep
// validation mandatory for every public caller.
async function fetchRawPrintPngs(pages, { origin, fetcher = globalThis.fetch, signal } = {}) {
  checkedPages(pages); // Reject unsafe URLs before any network request.
  const site = checkedOrigin(origin);
  if (typeof fetcher !== "function") throw new TypeError("Fetch capability unavailable");
  if (signal?.aborted) throw new Error("PNG request aborted");

  const downloads = [];
  let total = 0;
  for (const page of pages) {
    if (signal?.aborted) throw new Error("PNG request aborted");
    const expectedUrl = site + page.printUrl;
    const response = await fetcher(expectedUrl, {
      credentials: "omit", mode: "same-origin", redirect: "error",
      cache: "no-store", signal,
    });
    if (!response || response.status !== 200 || response.redirected ||
        response.url !== expectedUrl || typeof response.headers?.get !== "function") {
      throw new Error("Public PNG request failed or redirected");
    }
    const mime = response.headers.get("content-type");
    if (typeof mime !== "string" || mime.split(";", 1)[0].trim().toLowerCase() !== "image/png") {
      throw new TypeError("Public file is not PNG");
    }
    const remaining = MAX_ZIP_INPUT_BYTES - total;
    const declared = checkedSize(response.headers.get("content-length"), remaining);
    const bytes = await readBoundedStream(response, remaining, declared, signal);
    total += bytes.byteLength;
    downloads.push({ url: page.printUrl, bytes });
  }
  return downloads;
}

// Structural PNG validation uses the existing ZIP validator: A4 dimensions,
// 8-bit RGB, chunk boundaries and CRC. Successful structural validation is NOT
// an image decode or authority to print: a reviewed renderer must decode all
// images and verify pagination before enabling visitor-initiated printing.
export async function fetchBasketPrintPngBytes(pages, options = {}) {
  const downloads = await fetchRawPrintPngs(pages, options);
  for (const item of downloads) assertCanonicalA4Png(item.bytes);
  return downloads;
}

// Preserve the existing ZIP path and full byte checks inside buildPrintPngZip.
export async function prepareBasketPngZip(pages, options = {}) {
  const downloads = await fetchRawPrintPngs(pages, options);
  return buildPrintPngZip(pages, downloads);
}

