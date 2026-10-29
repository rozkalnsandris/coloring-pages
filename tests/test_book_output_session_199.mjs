import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runCurrentBookOutputSession } from "../js/book-output-session.mjs";

const SITE = "https://ausmalwiese.de";
const page = Object.freeze({
  activityId: "0000001",
  pageIndex: 1,
  pageCount: 1,
  printUrl: "/media/0000001/print.png",
});
const catalog = Object.freeze([Object.freeze({
  id: "0000001",
  title: "Blume",
  print: page.printUrl,
})]);

function basket() {
  return {
    ids: ["0000001"],
    pages: [{ ...page }],
    sheetCount: 1,
    droppedIds: [],
  };
}

function bundle({ coverEnabled = true } = {}) {
  let disposed = false;
  let disposeCalls = 0;
  const value = {
    plan: Object.freeze({
      coverEnabled,
      artworkSheetCount: 1,
      sheetCount: coverEnabled ? 2 : 1,
      artworkPages: Object.freeze([page]),
    }),
    coverPng: coverEnabled ? new Uint8Array([9, 8, 7]) : null,
    artworkDownloads: Object.freeze([
      Object.freeze({ url: page.printUrl, bytes: new Uint8Array([1, 2, 3]) }),
    ]),
    zip: {
      bytes: new Uint8Array([4, 5, 6]),
      filenames: coverEnabled
        ? ["00-deckblatt.png", "01-0000001.png"]
        : ["01-0000001.png"],
    },
    get disposed() { return disposed; },
    get disposeCalls() { return disposeCalls; },
    dispose() {
      disposeCalls++;
      disposed = true;
    },
  };
  return value;
}

function zipResource() {
  let disposed = false;
  return {
    link: {},
    filename: "ausmalwiese-malbuch.zip",
    get disposed() { return disposed; },
    dispose() { disposed = true; },
  };
}

function printResource(sheetCount) {
  let disposed = false;
  return {
    plan: { sheetCount },
    sheets: Array.from({ length: sheetCount }, () => ({})),
    get disposed() { return disposed; },
    dispose() { disposed = true; },
  };
}

function catalogFetcher({ onJson } = {}) {
  const calls = [];
  const fetcher = async (url, init) => {
    calls.push({ url, init });
    return {
      status: 200,
      redirected: false,
      url,
      async json() {
        onJson?.();
        return catalog;
      },
    };
  };
  return { fetcher, calls };
}

function servicesFor(value, overrides = {}) {
  return {
    async prepareBundle() { return value; },
    async stagePrint(current) { return printResource(current.plan.sheetCount); },
    stageZip() { return zipResource(); },
    ...overrides,
  };
}

test("stable covered ZIP session uses fresh catalogue, snapshots personal text, then wipes bundle", async () => {
  const previous = basket();
  const coverState = {
    enabled: true,
    title: "Mein Tierbuch",
    name: "Mia",
  };
  const stored = ["0000001"];
  const network = catalogFetcher({
    onJson() {
      coverState.title = "Mutated later";
      coverState.name = "Changed later";
    },
  });
  const value = bundle();
  const calls = [];
  const resource = zipResource();

  const result = await runCurrentBookOutputSession(
    previous,
    coverState,
    {
      mode: "zip",
      origin: SITE,
      readIds: () => [...stored],
      fetcher: network.fetcher,
      services: servicesFor(value, {
        async prepareBundle(ids, freshCatalog, prior, cover, options) {
          calls.push({ ids, freshCatalog, prior, cover, options });
          assert.deepEqual(cover, {
            enabled: true,
            title: "Mein Tierbuch",
            name: "Mia",
          });
          assert.equal(Object.isFrozen(cover), true);
          assert.equal(options.origin, SITE);
          assert.strictEqual(options.fetcher, network.fetcher);
          return value;
        },
        stageZip(zip) {
          assert.strictEqual(zip, value.zip);
          return resource;
        },
      }),
    },
  );

  assert.equal(network.calls.length, 1);
  assert.equal(network.calls[0].url, SITE + "/catalog.json");
  assert.deepEqual(network.calls[0].init, {
    cache: "no-store",
    credentials: "omit",
    mode: "same-origin",
    redirect: "error",
    signal: undefined,
  });
  assert.equal(JSON.stringify(network.calls).includes("Mein Tierbuch"), false);
  assert.equal(JSON.stringify(network.calls).includes("Mia"), false);
  assert.equal(calls.length, 1);
  assert.equal(value.disposed, true);
  assert.equal(value.disposeCalls, 1);
  assert.equal(resource.disposed, false);
  assert.deepEqual(
    { mode: result.mode, coverEnabled: result.coverEnabled, sheetCount: result.sheetCount },
    { mode: "zip", coverEnabled: true, sheetCount: 2 },
  );
  assert.strictEqual(result.resource, resource);
  assert.equal(JSON.stringify(result).includes("Mein Tierbuch"), false);
  assert.equal(JSON.stringify(result).includes("Mia"), false);
});

test("stable print session stages detached shared print resource and releases bundle bytes", async () => {
  const previous = basket();
  const network = catalogFetcher();
  const value = bundle();
  const resource = printResource(2);
  let staged = 0;

  const result = await runCurrentBookOutputSession(
    previous,
    { enabled: true, title: "T", name: "N" },
    {
      mode: "print",
      origin: SITE,
      readIds: () => ["0000001"],
      fetcher: network.fetcher,
      decode: async () => {},
      services: servicesFor(value, {
        async stagePrint(current, options) {
          staged++;
          assert.strictEqual(current, value);
          assert.equal(options.signal, undefined);
          return resource;
        },
      }),
    },
  );

  assert.equal(staged, 1);
  assert.equal(result.mode, "print");
  assert.strictEqual(result.resource, resource);
  assert.equal(value.disposed, true);
  assert.equal(resource.disposed, false);
});

test("selection drift after bundle preparation blocks staging and disposes sensitive bundle", async () => {
  const previous = basket();
  const network = catalogFetcher();
  const value = bundle();
  let stored = ["0000001"];
  let staged = 0;

  await assert.rejects(
    runCurrentBookOutputSession(
      previous,
      { enabled: true, title: "T", name: "N" },
      {
        mode: "zip",
        origin: SITE,
        readIds: () => [...stored],
        fetcher: network.fetcher,
        services: servicesFor(value, {
          async prepareBundle() {
            stored = ["0000002"];
            return value;
          },
          stageZip() {
            staged++;
            return zipResource();
          },
        }),
      },
    ),
    /selection changed during output preparation/,
  );

  assert.equal(staged, 0);
  assert.equal(value.disposed, true);
  assert.equal(value.disposeCalls, 1);
});

test("selection drift during print staging disposes both staged canvases and bundle", async () => {
  const previous = basket();
  const network = catalogFetcher();
  const value = bundle();
  let stored = ["0000001"];
  const resource = printResource(2);

  await assert.rejects(
    runCurrentBookOutputSession(
      previous,
      { enabled: true, title: "T", name: "N" },
      {
        mode: "print",
        origin: SITE,
        readIds: () => [...stored],
        fetcher: network.fetcher,
        services: servicesFor(value, {
          async stagePrint() {
            stored = ["0000002"];
            return resource;
          },
        }),
      },
    ),
    /selection changed during output staging/,
  );

  assert.equal(resource.disposed, true);
  assert.equal(value.disposed, true);
  assert.equal(value.disposeCalls, 1);
});

test("abort after catalogue read prevents bundle preparation", async () => {
  const previous = basket();
  const controller = new AbortController();
  const network = catalogFetcher({
    onJson() { controller.abort(); },
  });
  let prepared = 0;

  await assert.rejects(
    runCurrentBookOutputSession(
      previous,
      { enabled: false, title: "Dormant", name: "Mia" },
      {
        mode: "zip",
        origin: SITE,
        signal: controller.signal,
        readIds: () => ["0000001"],
        fetcher: network.fetcher,
        services: servicesFor(bundle({ coverEnabled: false }), {
          async prepareBundle() {
            prepared++;
            throw new Error("must not run");
          },
        }),
      },
    ),
    /aborted/,
  );

  assert.equal(prepared, 0);
});

test("invalid mode, stale initial snapshot and redirected catalogue fail before output staging", async () => {
  const previous = basket();
  const network = catalogFetcher();
  const value = bundle();

  await assert.rejects(
    runCurrentBookOutputSession(previous, {
      enabled: false, title: "", name: "",
    }, {
      mode: "pdf",
      origin: SITE,
      readIds: () => ["0000001"],
      fetcher: network.fetcher,
      services: servicesFor(value),
    }),
    /zip or print/,
  );

  await assert.rejects(
    runCurrentBookOutputSession(previous, {
      enabled: false, title: "", name: "",
    }, {
      mode: "zip",
      origin: SITE,
      readIds: () => ["other"],
      fetcher: network.fetcher,
      services: servicesFor(value),
    }),
    /Drucksammlung changed/,
  );

  let prepared = 0;
  await assert.rejects(
    runCurrentBookOutputSession(previous, {
      enabled: false, title: "", name: "",
    }, {
      mode: "zip",
      origin: SITE,
      readIds: () => ["0000001"],
      fetcher: async url => ({
        status: 200,
        redirected: true,
        url,
        async json() { return catalog; },
      }),
      services: servicesFor(value, {
        async prepareBundle() {
          prepared++;
          return value;
        },
      }),
    }),
    /catalogue unavailable/,
  );
  assert.equal(prepared, 0);
});

test("session orchestrator has no automatic download, print, storage write or analytics sink", () => {
  const source = readFileSync(
    new URL("../js/book-output-session.mjs", import.meta.url),
    "utf8",
  );
  const code = source.split("\n")
    .filter(line => !line.trimStart().startsWith("//"))
    .join("\n");
  for (const forbidden of [
    ".click(",
    "window.print(",
    "sessionStorage.setItem",
    "localStorage",
    "sendBeacon(",
    "analytics",
    "document.body",
    "innerHTML",
  ]) {
    assert.equal(code.includes(forbidden), false, forbidden);
  }
});
