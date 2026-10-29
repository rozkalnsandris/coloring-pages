// #199 source-only orchestration for one freshly validated "Mein Malbuch" output.
// Modes are either a staged visitor-clickable ZIP link or a detached print
// document. This module does not attach DOM, click, call window.print(), mutate
// storage, persist cover text, record analytics, publish, or activate UI.
import { readStoredBasketIds } from "./print-basket-storage.mjs";
import { prepareBookOutputBundle } from "./book-output-bundle.mjs";
import { stageBookPrintDocument } from "./book-print-document.mjs";
import { stageBookZipDownloadLink } from "./print-basket-zip-link.mjs";

const MODES = new Set(["zip", "print"]);

function checkedOrigin(origin) {
  if (typeof origin !== "string") {
    throw new TypeError("Explicit site origin required");
  }
  const url = new URL(origin);
  if (!["https:", "http:"].includes(url.protocol) ||
      url.username || url.password ||
      url.origin !== origin ||
      url.pathname !== "/" ||
      url.search || url.hash) {
    throw new TypeError("Canonical site origin required");
  }
  return url.origin;
}

function checkedMode(mode) {
  if (!MODES.has(mode)) {
    throw new TypeError("Book output mode must be zip or print");
  }
  return mode;
}

function checkedCoverState(state) {
  if (!state || typeof state !== "object" || Array.isArray(state) ||
      typeof state.enabled !== "boolean" ||
      typeof state.title !== "string" ||
      typeof state.name !== "string") {
    throw new TypeError("Valid in-memory book cover state required");
  }
  return Object.freeze({
    enabled: state.enabled,
    title: state.title,
    name: state.name,
  });
}

function checkedServices(services) {
  if (!services || typeof services !== "object" ||
      typeof services.prepareBundle !== "function" ||
      typeof services.stagePrint !== "function" ||
      typeof services.stageZip !== "function") {
    throw new TypeError("Complete book output session services required");
  }
  return services;
}

function sameIds(left, right) {
  return Array.isArray(left) && Array.isArray(right) &&
    left.length === right.length &&
    left.every((value, index) =>
      typeof value === "string" && value === right[index]);
}

function samePages(left, right) {
  return Array.isArray(left) && Array.isArray(right) &&
    left.length === right.length &&
    left.every((page, index) => {
      const other = right[index];
      return page && other &&
        page.activityId === other.activityId &&
        page.pageIndex === other.pageIndex &&
        page.pageCount === other.pageCount &&
        page.printUrl === other.printUrl;
    });
}

function snapshotStillMatches(previousBasket, ids, plan) {
  return previousBasket &&
    sameIds(previousBasket.ids, ids) &&
    Array.isArray(previousBasket.droppedIds) &&
    previousBasket.droppedIds.length === 0 &&
    previousBasket.sheetCount === plan?.artworkSheetCount &&
    samePages(previousBasket.pages, plan?.artworkPages);
}

function throwIfAborted(signal) {
  if (signal?.aborted) {
    throw new Error("Book output session aborted");
  }
}

function checkedResource(mode, resource, sheetCount) {
  if (!resource || typeof resource.dispose !== "function") {
    throw new TypeError("Disposable book output resource required");
  }
  if (mode === "zip") {
    if (!resource.link || typeof resource.filename !== "string" ||
        resource.filename !== "ausmalwiese-malbuch.zip") {
      throw new TypeError("Book ZIP link resource invalid");
    }
  } else if (!resource.plan ||
      resource.plan.sheetCount !== sheetCount ||
      !Array.isArray(resource.sheets) ||
      resource.sheets.length !== sheetCount) {
    throw new TypeError("Book print document resource invalid");
  }
  return resource;
}

export async function runCurrentBookOutputSession(
  previousBasket,
  coverState,
  {
    mode,
    origin,
    readIds,
    fetcher,
    signal,
    documentRef,
    fonts,
    coverRenderOptions,
    decode,
    blobFactory,
    urlRef,
    BlobCtor,
    services,
  } = {},
) {
  const outputMode = checkedMode(mode);
  const site = checkedOrigin(origin);
  const cover = checkedCoverState(coverState);
  const ops = checkedServices(services);

  if (typeof readIds !== "function" || typeof fetcher !== "function") {
    throw new TypeError("Browser selection and fetch capabilities required");
  }

  throwIfAborted(signal);
  const initialIds = readIds();
  if (!initialIds.length || !sameIds(initialIds, previousBasket?.ids)) {
    throw new Error("Drucksammlung changed; review selection before output");
  }

  let bundle = null;
  let resource = null;
  try {
    const catalogUrl = site + "/catalog.json";
    const response = await fetcher(catalogUrl, {
      cache: "no-store",
      credentials: "omit",
      mode: "same-origin",
      redirect: "error",
      signal,
    });
    throwIfAborted(signal);

    if (!response || response.status !== 200 ||
        response.redirected ||
        response.url !== catalogUrl ||
        typeof response.json !== "function") {
      throw new Error("Fresh public catalogue unavailable");
    }

    const freshCatalog = await response.json();
    throwIfAborted(signal);
    if (!Array.isArray(freshCatalog)) {
      throw new TypeError("Fresh catalogue array required");
    }

    bundle = await ops.prepareBundle(
      initialIds,
      freshCatalog,
      previousBasket,
      cover,
      {
        origin: site,
        fetcher,
        signal,
        documentRef,
        fonts,
        coverRenderOptions,
      },
    );
    throwIfAborted(signal);

    if (!bundle || bundle.disposed ||
        typeof bundle.dispose !== "function" ||
        !bundle.plan ||
        !snapshotStillMatches(previousBasket, initialIds, bundle.plan) ||
        !sameIds(readIds(), initialIds)) {
      throw new Error("Book selection changed during output preparation");
    }

    const sheetCount = bundle.plan.sheetCount;
    const coverEnabled = bundle.plan.coverEnabled;

    if (outputMode === "zip") {
      resource = ops.stageZip(bundle.zip, {
        documentRef,
        urlRef,
        BlobCtor,
      });
    } else {
      resource = await ops.stagePrint(bundle, {
        decode,
        blobFactory,
        documentRef,
        signal,
      });
    }
    throwIfAborted(signal);

    checkedResource(outputMode, resource, sheetCount);

    if (!snapshotStillMatches(previousBasket, initialIds, bundle.plan) ||
        !sameIds(readIds(), initialIds)) {
      throw new Error("Book selection changed during output staging");
    }

    // ZIP Blob and staged print canvases now own their independent output
    // resources. Wipe personalized cover PNG and transient archive bytes.
    bundle.dispose();
    bundle = null;

    return Object.freeze({
      mode: outputMode,
      coverEnabled,
      sheetCount,
      resource,
    });
  } catch (error) {
    try {
      resource?.dispose?.();
    } catch {
      // Original error wins.
    }
    try {
      bundle?.dispose?.();
    } catch {
      // Original error wins.
    }
    throw error;
  }
}

export function prepareCurrentBookOutputSession(
  previousBasket,
  coverState,
  options = {},
) {
  return runCurrentBookOutputSession(
    previousBasket,
    coverState,
    {
      ...options,
      origin: options.origin ?? globalThis.location?.origin,
      readIds: options.readIds ?? readStoredBasketIds,
      fetcher: options.fetcher ?? globalThis.fetch,
      services: {
        prepareBundle: prepareBookOutputBundle,
        stagePrint: stageBookPrintDocument,
        stageZip: stageBookZipDownloadLink,
      },
    },
  );
}
