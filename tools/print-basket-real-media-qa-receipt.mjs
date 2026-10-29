// Local-only #199 QA receipt/privacy helpers.
// Receipts contain public media metadata and environment facts only. Cover
// title/name and privacy-canary tokens are inputs to checks, never receipt data.
export const QA_RECEIPT_SCHEMA = "ausmalwiese.book-real-media-qa-receipt.v1";
export const QA_RECEIPT_FILENAME = "ausmalwiese-qa-evidence.json";

function finiteOrNull(value) {
  return Number.isFinite(value) ? value : null;
}

function safeText(value) {
  return typeof value === "string" ? value : "";
}

function tokenVariants(tokens) {
  if (!Array.isArray(tokens)) throw new TypeError("privacy tokens must be an array");
  const variants = [];
  for (const token of tokens) {
    if (typeof token !== "string" || !token) continue;
    variants.push(token, encodeURIComponent(token), token.toLowerCase(), encodeURIComponent(token).toLowerCase());
  }
  return Object.freeze([...new Set(variants)]);
}

function containsToken(value, variants) {
  if (typeof value !== "string" || !value) return false;
  const lower = value.toLowerCase();
  return variants.some(token => value.includes(token) || lower.includes(token.toLowerCase()));
}

function checkedOrigin(origin) {
  const value = new URL(origin);
  if (!["http:", "https:"].includes(value.protocol) ||
      value.username || value.password ||
      value.origin !== origin ||
      value.pathname !== "/" ||
      value.search || value.hash) {
    throw new TypeError("exact QA origin required");
  }
  return value.origin;
}

function storageClear(storage, variants) {
  if (!storage) return null;
  try {
    for (let index = 0; index < storage.length; index++) {
      const key = storage.key(index);
      const value = key === null ? null : storage.getItem(key);
      if (containsToken(key, variants) || containsToken(value, variants)) return false;
    }
    return true;
  } catch {
    return null;
  }
}

export function createQaPrivacyCanary(cryptoRef = globalThis.crypto) {
  if (!cryptoRef || typeof cryptoRef.getRandomValues !== "function") {
    throw new TypeError("crypto.getRandomValues required");
  }
  const words = new Uint32Array(2);
  cryptoRef.getRandomValues(words);
  const left = words[0].toString(16).padStart(8, "0").slice(0, 8).toUpperCase();
  const right = words[1].toString(16).padStart(8, "0").slice(0, 8).toUpperCase();
  return Object.freeze({
    title: "QA Titel " + left,
    name: "QA Name " + right,
  });
}

export function captureQaEnvironment({
  navigatorRef = globalThis.navigator,
  windowRef = globalThis.window,
  intlRef = globalThis.Intl,
  now = () => new Date(),
} = {}) {
  const observed = now();
  if (!(observed instanceof Date) || !Number.isFinite(observed.getTime())) {
    throw new TypeError("valid QA clock required");
  }
  let timeZone = null;
  try {
    timeZone = intlRef?.DateTimeFormat?.().resolvedOptions?.().timeZone || null;
  } catch {
    timeZone = null;
  }

  return Object.freeze({
    observedAt: observed.toISOString(),
    timeZone,
    userAgent: safeText(navigatorRef?.userAgent) || null,
    language: safeText(navigatorRef?.language) || null,
    viewport: Object.freeze({
      width: Number.isInteger(windowRef?.innerWidth) ? windowRef.innerWidth : null,
      height: Number.isInteger(windowRef?.innerHeight) ? windowRef.innerHeight : null,
    }),
    devicePixelRatio: finiteOrNull(windowRef?.devicePixelRatio),
    deviceMemoryGiB: finiteOrNull(navigatorRef?.deviceMemory),
    hardwareConcurrency: Number.isInteger(navigatorRef?.hardwareConcurrency)
      ? navigatorRef.hardwareConcurrency
      : null,
  });
}

function requestInputUrl(input) {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  if (input && typeof input.url === "string") return input.url;
  throw new TypeError("audited fetch URL required");
}

export function createQaAuditedFetch(
  fetcher,
  {
    origin,
    tokens = [],
    entries = [],
  } = {},
) {
  if (typeof fetcher !== "function" || !Array.isArray(entries)) {
    throw new TypeError("fetcher and mutable audit entry list required");
  }
  const site = checkedOrigin(origin);
  const variants = tokenVariants(tokens);

  return async function auditedFetch(input, init = undefined) {
    const raw = requestInputUrl(input);
    const url = new URL(raw, site + "/");
    const method = String(init?.method || input?.method || "GET").toUpperCase();
    if (url.origin !== site || url.search || url.hash ||
        method !== "GET" || init?.body !== undefined && init?.body !== null) {
      throw new Error("QA fetch escaped same-origin GET/no-body contract");
    }
    if (containsToken(url.href, variants)) {
      throw new Error("QA privacy token reached request URL");
    }

    const response = await fetcher(input, init);
    entries.push(Object.freeze({
      method,
      path: url.pathname,
      status: Number.isInteger(response?.status) ? response.status : null,
      redirected: response?.redirected === true,
    }));
    return response;
  };
}

export function auditQaPrivacySurfaces(
  tokens,
  {
    locationRef = globalThis.location,
    documentRef = globalThis.document,
    sessionStorageRef = globalThis.sessionStorage,
    localStorageRef = globalThis.localStorage,
    performanceRef = globalThis.performance,
    resourceStartIndex = 0,
  } = {},
) {
  const variants = tokenVariants(tokens);
  let resourceUrlsClear = null;
  let resourceEntryCount = null;
  try {
    const resources = performanceRef?.getEntriesByType?.("resource");
    if (Array.isArray(resources)) {
      const recent = resources.slice(
        Number.isInteger(resourceStartIndex) && resourceStartIndex >= 0
          ? resourceStartIndex
          : 0,
      );
      resourceEntryCount = recent.length;
      resourceUrlsClear = recent.every(entry => !containsToken(entry?.name, variants));
    }
  } catch {
    resourceUrlsClear = null;
    resourceEntryCount = null;
  }

  let cookieClear = null;
  try {
    cookieClear = !containsToken(documentRef?.cookie || "", variants);
  } catch {
    cookieClear = null;
  }

  return Object.freeze({
    locationUrlClear: !containsToken(locationRef?.href || "", variants),
    documentCookieClear: cookieClear,
    sessionStorageClear: storageClear(sessionStorageRef, variants),
    localStorageClear: storageClear(localStorageRef, variants),
    resourceUrlsClear,
    resourceEntryCount,
  });
}

export function privacyAuditPass(audit) {
  if (!audit || typeof audit !== "object") return false;
  return [
    "locationUrlClear",
    "documentCookieClear",
    "sessionStorageClear",
    "localStorageClear",
    "resourceUrlsClear",
  ].every(key => audit[key] === true);
}

export function buildQaReceipt({
  sourceContext,
  environment,
  publicEvidence,
  requestAudit = [],
  privacyAudit = null,
  outcome,
} = {}) {
  if (!sourceContext || typeof sourceContext !== "object" ||
      typeof sourceContext.sourceSha !== "string" ||
      !/^[a-f0-9]{40}$/.test(sourceContext.sourceSha) ||
      typeof sourceContext.publicOrigin !== "string" ||
      !environment || typeof environment !== "object" ||
      !publicEvidence || typeof publicEvidence !== "object" ||
      !Array.isArray(requestAudit) ||
      !outcome || typeof outcome !== "object") {
    throw new TypeError("complete QA receipt inputs required");
  }

  const receipt = {
    schema: QA_RECEIPT_SCHEMA,
    status: "STAGING ONLY",
    source: {
      sha: sourceContext.sourceSha,
      publicOrigin: sourceContext.publicOrigin,
    },
    environment,
    evidence: publicEvidence,
    requests: requestAudit.map(item => ({
      method: item.method,
      path: item.path,
      status: item.status,
      redirected: item.redirected,
    })),
    privacy: privacyAudit
      ? {
          pass: privacyAuditPass(privacyAudit),
          locationUrlClear: privacyAudit.locationUrlClear,
          documentCookieClear: privacyAudit.documentCookieClear,
          sessionStorageClear: privacyAudit.sessionStorageClear,
          localStorageClear: privacyAudit.localStorageClear,
          resourceUrlsClear: privacyAudit.resourceUrlsClear,
          resourceEntryCount: privacyAudit.resourceEntryCount,
        }
      : null,
    outcome: {
      mode: safeText(outcome.mode),
      result: safeText(outcome.result),
      note: safeText(outcome.note),
    },
  };

  return Object.freeze(receipt);
}

export function stageQaReceiptDownload(
  receipt,
  {
    documentRef = globalThis.document,
    URLRef = globalThis.URL,
    BlobCtor = globalThis.Blob,
  } = {},
) {
  if (!receipt || receipt.schema !== QA_RECEIPT_SCHEMA ||
      !documentRef || typeof documentRef.createElement !== "function" ||
      !URLRef || typeof URLRef.createObjectURL !== "function" ||
      typeof URLRef.revokeObjectURL !== "function" ||
      typeof BlobCtor !== "function") {
    throw new TypeError("valid QA receipt download environment required");
  }

  const blob = new BlobCtor(
    [JSON.stringify(receipt, null, 2) + "\n"],
    { type: "application/json" },
  );
  const href = URLRef.createObjectURL(blob);
  const link = documentRef.createElement("a");
  link.href = href;
  link.download = QA_RECEIPT_FILENAME;
  link.textContent = "QA-Receipt speichern";
  link.setAttribute("rel", "nofollow");

  let disposed = false;
  return Object.freeze({
    link,
    dispose() {
      if (disposed) return;
      disposed = true;
      try { link.removeAttribute("href"); } catch {}
      try { URLRef.revokeObjectURL(href); } catch {}
    },
  });
}
