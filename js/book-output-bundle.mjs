// #199 source-only preparation of a cover-aware book output bundle.
// Uses the shared #206 public-PNG fetcher and ZIP STORE writer. The optional
// personalized cover stays in memory and is never sent to fetch/network APIs.
// This module does not create Blob URLs, attach DOM, download, print, persist,
// log, publish, or enable any visitor-facing control.
import { buildBookExportPlan } from "./book-export-plan.mjs";
import { buildBookCoverPng } from "./book-cover-png-pipeline.mjs";
import { fetchBasketPrintPngBytes } from "./print-basket-zip-fetch.mjs";
import {
  BOOK_COVER_ZIP_FILENAME,
  buildBookPrintPngZip,
  buildPrintPngZip,
} from "./print-zip-store.mjs";

function checkedServices(services) {
  if (!services || typeof services !== "object" ||
      typeof services.buildCoverPng !== "function" ||
      typeof services.fetchArtwork !== "function" ||
      typeof services.buildArtworkZip !== "function" ||
      typeof services.buildBookZip !== "function") {
    throw new TypeError("Complete book output services required");
  }
  return services;
}

function throwIfAborted(signal) {
  if (signal?.aborted) throw new Error("Book output preparation aborted");
}

function wipe(bytes) {
  try {
    if (bytes instanceof Uint8Array) bytes.fill(0);
  } catch {
    // Best effort cleanup only.
  }
}

export async function runBookOutputBundle(
  savedIds,
  freshCatalog,
  previousBasket,
  coverState,
  {
    origin,
    fetcher,
    signal,
    documentRef,
    fonts,
    coverRenderOptions,
    services,
  } = {},
) {
  const ops = checkedServices(services);
  const plan = buildBookExportPlan(
    savedIds,
    freshCatalog,
    previousBasket,
    coverState,
  );
  throwIfAborted(signal);

  let coverPng = null;
  let zip = null;
  try {
    if (plan.coverEnabled) {
      if (!coverRenderOptions || typeof coverRenderOptions !== "object" ||
          Array.isArray(coverRenderOptions)) {
        throw new TypeError("Explicit cover rendering options required");
      }
      // Personal text is passed only to the local cover renderer. It is never
      // included in filenames, network options, catalogue IDs or the plan.
      coverPng = await ops.buildCoverPng(
        { title: coverState.title, name: coverState.name },
        coverRenderOptions,
        { documentRef, fonts, signal },
      );
      throwIfAborted(signal);
      if (!(coverPng instanceof Uint8Array) || coverPng.byteLength === 0) {
        throw new TypeError("Verified cover PNG bytes required");
      }
    }

    // Network work receives only trusted catalogue-derived artwork pages.
    const downloads = await ops.fetchArtwork(plan.artworkPages, {
      origin,
      fetcher,
      signal,
    });
    throwIfAborted(signal);
    if (!Array.isArray(downloads) ||
        downloads.length !== plan.artworkSheetCount) {
      throw new Error("Incomplete book artwork download set");
    }

    zip = plan.coverEnabled
      ? ops.buildBookZip(plan.artworkPages, downloads, coverPng)
      : ops.buildArtworkZip(plan.artworkPages, downloads);

    throwIfAborted(signal);
    if (!zip || !(zip.bytes instanceof Uint8Array) ||
        !Array.isArray(zip.filenames) ||
        zip.filenames.length !== plan.sheetCount) {
      throw new TypeError("Complete book ZIP result required");
    }
    if (plan.coverEnabled && zip.filenames[0] !== BOOK_COVER_ZIP_FILENAME) {
      throw new Error("Book cover ZIP filename contract mismatch");
    }

    let disposed = false;
    return Object.freeze({
      plan,
      coverPng,
      artworkDownloads: Object.freeze(downloads.slice()),
      zip,
      get disposed() {
        return disposed;
      },
      dispose() {
        if (disposed) return;
        disposed = true;
        wipe(coverPng);
        wipe(zip.bytes);
      },
    });
  } catch (error) {
    wipe(coverPng);
    wipe(zip?.bytes);
    throw error;
  }
}

export function prepareBookOutputBundle(
  savedIds,
  freshCatalog,
  previousBasket,
  coverState,
  options = {},
) {
  return runBookOutputBundle(
    savedIds,
    freshCatalog,
    previousBasket,
    coverState,
    {
      ...options,
      services: {
        buildCoverPng: buildBookCoverPng,
        fetchArtwork: fetchBasketPrintPngBytes,
        buildArtworkZip: buildPrintPngZip,
        buildBookZip: buildBookPrintPngZip,
      },
    },
  );
}
