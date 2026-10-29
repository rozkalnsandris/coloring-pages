import test from "node:test";
import assert from "node:assert/strict";
import {
  QA_RECEIPT_FILENAME,
  QA_RECEIPT_SCHEMA,
  auditQaPrivacySurfaces,
  buildQaReceipt,
  captureQaEnvironment,
  createQaAuditedFetch,
  createQaPrivacyCanary,
  prepareQaResourceTimingAudit,
  privacyAuditPass,
  stageQaReceiptDownload,
} from "../tools/print-basket-real-media-qa-receipt.mjs";

function storage(entries = {}) {
  const keys = Object.keys(entries);
  return {
    length: keys.length,
    key(index) { return keys[index] ?? null; },
    getItem(key) { return Object.hasOwn(entries, key) ? String(entries[key]) : null; },
  };
}

test("privacy canary uses synthetic bounded text only", () => {
  const cryptoRef = {
    getRandomValues(words) {
      words[0] = 0x1234abcd;
      words[1] = 0x90abcdef;
      return words;
    },
  };
  assert.deepEqual(createQaPrivacyCanary(cryptoRef), {
    title: "QA Titel 1234ABCD",
    name: "QA Name 90ABCDEF",
  });
});

test("environment capture freezes timestamp/browser facts without location", () => {
  const value = captureQaEnvironment({
    navigatorRef: {
      userAgent: "QA Browser/1",
      language: "de-DE",
      deviceMemory: 4,
      hardwareConcurrency: 8,
    },
    windowRef: {
      innerWidth: 390,
      innerHeight: 844,
      devicePixelRatio: 2,
    },
    intlRef: {
      DateTimeFormat() {
        return { resolvedOptions: () => ({ timeZone: "Europe/Berlin" }) };
      },
    },
    now: () => new Date("2026-10-29T19:00:00.000Z"),
  });
  assert.deepEqual(value, {
    observedAt: "2026-10-29T19:00:00.000Z",
    timeZone: "Europe/Berlin",
    userAgent: "QA Browser/1",
    language: "de-DE",
    viewport: { width: 390, height: 844 },
    devicePixelRatio: 2,
    deviceMemoryGiB: 4,
    hardwareConcurrency: 8,
  });
  assert.equal(JSON.stringify(value).includes("latitude"), false);
  assert.equal(JSON.stringify(value).includes("longitude"), false);
});

test("audited fetch permits only same-origin GET/no-body and records privacy-safe path", async () => {
  const entries = [];
  const calls = [];
  const fetcher = async (input, init) => {
    calls.push({ input, init });
    return { status: 200, redirected: false };
  };
  const audited = createQaAuditedFetch(fetcher, {
    origin: "http://127.0.0.1:8765",
    tokens: ["QA Name SECRET"],
    entries,
  });

  await audited("/catalog.json", { cache: "no-store" });
  assert.equal(calls.length, 1);
  assert.deepEqual(entries, [{
    method: "GET",
    path: "/catalog.json",
    status: 200,
    redirected: false,
  }]);

  await assert.rejects(
    () => audited("https://example.com/catalog.json"),
    /same-origin GET/,
  );
  await assert.rejects(
    () => audited("/catalog.json?name=QA%20Name%20SECRET"),
    /same-origin GET/,
  );
  await assert.rejects(
    () => audited("/catalog.json", { method: "POST", body: "x" }),
    /same-origin GET/,
  );
});

test("privacy audit reports only booleans/counts and detects token in browser surfaces", () => {
  const clear = auditQaPrivacySurfaces(["QA Name SECRET"], {
    locationRef: { href: "http://127.0.0.1:8765/qa/" },
    documentRef: { cookie: "theme=plain" },
    sessionStorageRef: storage({ basket: "[123]" }),
    localStorageRef: storage({ theme: "light" }),
    performanceRef: {
      getEntriesByType(type) {
        assert.equal(type, "resource");
        return [
          { name: "http://127.0.0.1:8765/css/app.css" },
          { name: "http://127.0.0.1:8765/media/123/print.png" },
        ];
      },
    },
    resourceAudit: { startIndex: 1, requestedCapacity: 512 },
  });
  assert.equal(privacyAuditPass(clear), true);
  assert.deepEqual(clear, {
    locationUrlClear: true,
    documentCookieClear: true,
    sessionStorageClear: true,
    localStorageClear: true,
    resourceTimingPrepared: true,
    resourceUrlsClear: true,
    resourceEntryCount: 1,
  });

  const leaked = auditQaPrivacySurfaces(["QA Name SECRET"], {
    locationRef: { href: "http://127.0.0.1:8765/qa/" },
    documentRef: { cookie: "" },
    sessionStorageRef: storage({ accidental: "QA Name SECRET" }),
    localStorageRef: storage(),
    performanceRef: { getEntriesByType: () => [] },
  });
  assert.equal(leaked.sessionStorageClear, false);
  assert.equal(privacyAuditPass(leaked), false);

  const unavailable = auditQaPrivacySurfaces(["QA Name SECRET"], {
    locationRef: { href: "http://127.0.0.1:8765/qa/" },
    documentRef: { get cookie() { throw new Error("blocked"); } },
    sessionStorageRef: null,
    localStorageRef: null,
    performanceRef: null,
  });
  assert.equal(unavailable.documentCookieClear, null);
  assert.equal(unavailable.resourceTimingPrepared, false);
  assert.equal(privacyAuditPass(unavailable), false);
});

test("resource timing audit expands a full default buffer and detects later canary URLs", () => {
  const resources = Array.from({ length: 250 }, (_, index) => ({
    name: "http://127.0.0.1:8765/static/" + index,
  }));
  let requested = null;
  const performanceRef = {
    getEntriesByType(type) {
      assert.equal(type, "resource");
      return resources;
    },
    setResourceTimingBufferSize(value) {
      requested = value;
    },
  };
  const resourceAudit = prepareQaResourceTimingAudit(performanceRef);
  assert.deepEqual(resourceAudit, { startIndex: 250, requestedCapacity: 512 });
  assert.equal(requested, 512);

  resources.push({ name: "http://127.0.0.1:8765/media/QA%20Name%20SECRET.png" });
  const result = auditQaPrivacySurfaces(["QA Name SECRET"], {
    locationRef: { href: "http://127.0.0.1:8765/qa/" },
    documentRef: { cookie: "" },
    sessionStorageRef: storage(),
    localStorageRef: storage(),
    performanceRef,
    resourceAudit,
  });
  assert.equal(result.resourceTimingPrepared, true);
  assert.equal(result.resourceUrlsClear, false);
  assert.equal(privacyAuditPass(result), false);
});

test("resource timing audit fails closed when buffer expansion is unavailable", () => {
  const performanceRef = {
    getEntriesByType() { return []; },
  };
  assert.equal(prepareQaResourceTimingAudit(performanceRef), null);
  const result = auditQaPrivacySurfaces(["QA Name SECRET"], {
    locationRef: { href: "http://127.0.0.1:8765/qa/" },
    documentRef: { cookie: "" },
    sessionStorageRef: storage(),
    localStorageRef: storage(),
    performanceRef,
    resourceAudit: null,
  });
  assert.equal(result.resourceTimingPrepared, false);
  assert.equal(result.resourceUrlsClear, null);
  assert.equal(privacyAuditPass(result), false);
});

test("receipt excludes canary/title/name and stores only public request paths", () => {
  const receipt = buildQaReceipt({
    sourceContext: {
      sourceSha: "a".repeat(40),
      publicOrigin: "https://ausmalwiese.de",
    },
    environment: {
      observedAt: "2026-10-29T19:00:00.000Z",
      timeZone: "Europe/Berlin",
    },
    publicEvidence: {
      status: "STAGING ONLY",
      activityIds: ["1234567"],
      pages: [{ printUrl: "/media/1234567/print.png" }],
    },
    requestAudit: [{
      method: "GET",
      path: "/media/1234567/print.png",
      status: 200,
      redirected: false,
    }],
    privacyAudit: {
      locationUrlClear: true,
      documentCookieClear: true,
      sessionStorageClear: true,
      localStorageClear: true,
      resourceTimingPrepared: true,
      resourceUrlsClear: true,
      resourceEntryCount: 2,
    },
    outcome: {
      mode: "privacy-canary",
      result: "PASS",
      note: "Synthetic privacy canary stayed local.",
    },
  });
  const encoded = JSON.stringify(receipt);
  assert.equal(receipt.schema, QA_RECEIPT_SCHEMA);
  assert.equal(receipt.status, "STAGING ONLY");
  assert.equal(receipt.privacy.pass, true);
  assert.equal(encoded.includes("QA Titel"), false);
  assert.equal(encoded.includes("QA Name"), false);
  assert.equal(encoded.includes("title"), false);
  assert.equal(encoded.includes("name"), false);
  assert.deepEqual(receipt.requests[0], {
    method: "GET",
    path: "/media/1234567/print.png",
    status: 200,
    redirected: false,
  });
});

test("receipt download stages a generic JSON link without automatic click", async () => {
  let revoked = null;
  const attributes = {};
  const link = {
    href: "",
    download: "",
    textContent: "",
    setAttribute(key, value) { attributes[key] = value; },
    removeAttribute(key) { if (key === "href") this.href = ""; },
  };
  const documentRef = {
    createElement(tag) {
      assert.equal(tag, "a");
      return link;
    },
  };
  class BlobCtor {
    constructor(parts, options) {
      this.parts = parts;
      this.options = options;
    }
  }
  const receipt = {
    schema: QA_RECEIPT_SCHEMA,
    status: "STAGING ONLY",
  };
  const staged = stageQaReceiptDownload(receipt, {
    documentRef,
    URLRef: {
      createObjectURL(blob) {
        assert.equal(blob.options.type, "application/json");
        assert.match(blob.parts[0], /STAGING ONLY/);
        return "blob:qa-receipt";
      },
      revokeObjectURL(value) { revoked = value; },
    },
    BlobCtor,
  });
  assert.equal(link.href, "blob:qa-receipt");
  assert.equal(link.download, QA_RECEIPT_FILENAME);
  assert.equal(link.textContent, "QA-Receipt speichern");
  assert.equal(attributes.rel, "nofollow");
  assert.equal(Object.hasOwn(link, "click"), false);
  staged.dispose();
  assert.equal(link.href, "");
  assert.equal(revoked, "blob:qa-receipt");
});
