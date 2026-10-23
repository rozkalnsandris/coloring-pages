import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { reconcileBasket } from "../js/print-basket-selection.mjs";
import { stageCurrentBasketPrintSession } from "../js/print-basket-print-session.mjs";

const SITE = "https://ausmalwiese.de";
const catalog = [
  { id: "cut-1", title: "Basteln", pages: [
    { print: "/media/cut-1/print-1.png" },
    { print: "/media/cut-1/print-2.png" },
  ] },
  { id: "7", title: "Blume", print: "/media/7/print.png" },
];
function crc32(bytes) {
  let crc = -1;
  for (const byte of bytes) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) {
      crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
    }
  }
  return (crc ^ -1) >>> 0;
}
function chunk(type, bytes) {
  const out = Buffer.alloc(12 + bytes.length);
  out.writeUInt32BE(bytes.length, 0);
  out.write(type, 4, 4, "ascii");
  Buffer.from(bytes).copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, out.length - 4)), out.length - 4);
  return out;
}
// Structurally complete CRC-checked PNG sentinel; not a decodable raster.
// The injected decoder simulates image processing without committing binaries.
function a4Bytes(width, height) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr), chunk("IDAT", Buffer.from([1])),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}
const PORTRAIT = a4Bytes(2480, 3508);
const LANDSCAPE = a4Bytes(3508, 2480);

function fakeDocument() {
  const all = [];
  function createElement(tag) {
    const node = {
      tag, className: "", children: [], parent: null, attrs: {}, textContent: "",
      setAttribute(k, v) { this.attrs[k] = v; },
      append(...children) {
        for (const child of children) { this.children.push(child); child.parent = this; }
      },
      remove() {
        if (!this.parent) return;
        const array = this.parent.children;
        const index = array.indexOf(this);
        if (index >= 0) array.splice(index, 1);
        this.parent = null;
      },
    };
    if (tag === "canvas") {
      node.getContext = () => ({
        set fillStyle(value) { assert.equal(value, "#fff"); },
        fillRect() {},
        drawImage(bitmap, x, y, width, height) {
          assert.equal(x, 0); assert.equal(y, 0);
          assert.deepEqual([width, height], [bitmap.width, bitmap.height]);
        },
      });
    }
    all.push(node);
    return node;
  }
  return { documentRef: { createElement }, all };
}

function fixture(ids = ["cut-1", "7"], opts = {}) {
  let saved = [...ids];
  const basket = reconcileBasket(ids, catalog);
  const urls = basket.pages.map(p => SITE + p.printUrl);
  const files = basket.pages.map((p, i) => i === 1 ? LANDSCAPE : PORTRAIT);
  let calls = [], closed = [];
  let decoded = 0;
  const dom = fakeDocument();
  const response = (url, data, overrides = {}) => ({
    status: overrides.status ?? 200,
    redirected: overrides.redirected ?? false,
    url: overrides.url ?? url,
    headers: new Headers({
      "content-type": overrides.mime ?? "image/png",
      "content-length": String(data.length),
    }),
    body: new ReadableStream({
      start(c) { c.enqueue(data); c.close(); },
    }),
  });
  const fetcher = async (url, init) => {
    calls.push({ url, init });
    if (url === SITE + "/catalog.json") {
      if (opts.catalogReject) throw new Error("catalog request rejected");
      return {
        status: opts.catalogStatus ?? 200, redirected: Boolean(opts.catalogRedirect),
        url: opts.catalogWrongUrl ? SITE + "/other.json" : url,
        async json() {
          if (opts.abortOnCatalog) opts.abortOnCatalog();
          return opts.freshCatalog ?? catalog;
        },
      };
    }
    const index = urls.indexOf(url);
    if (index < 0) throw new Error("unexpected URL " + url);
    if (opts.failPngAt === index + 1) return response(url, files[index], { status: 404 });
    return response(url, files[index]);
  };
  const decode = async blob => {
    assert.equal(blob.type, "image/png");
    assert.ok(blob.size > 57);
    const index = decoded++;
    const width = index === 1 ? 3508 : 2480;
    const height = index === 1 ? 2480 : 3508;
    if (opts.onDecode) opts.onDecode(index, api);
    if (opts.failDecodeAt === index + 1) throw new Error("decoder failed");
    return { width, height, close() { closed[index] = (closed[index] || 0) + 1; } };
  };
  const api = {
    basket, dom, fetcher, decode,
    get calls() { return calls; },
    get closed() { return closed; },
    get decoded() { return decoded; },
    get saved() { return saved; },
    setSaved(value) { saved = [...value]; },
    readIds: () => [...saved],
    options(extra = {}) {
      return {
        origin: SITE, fetcher, decode, documentRef: dom.documentRef,
        readIds: api.readIds, ...extra,
      };
    },
  };
  return api;
}

test("fresh catalogue and native public PNGs stage three ordered mixed A4 sheets, detached and reusable", async () => {
  const f = fixture();
  const staged = await stageCurrentBasketPrintSession(f.basket, f.options());
  assert.deepEqual(f.calls.map(c => c.url), [
    SITE + "/catalog.json",
    SITE + "/media/cut-1/print-1.png",
    SITE + "/media/cut-1/print-2.png",
    SITE + "/media/7/print.png",
  ]);
  assert.ok(f.calls.every(c => c.init.redirect === "error" &&
    c.init.credentials === "omit" && c.init.cache === "no-store" &&
    c.init.mode === "same-origin"));
  assert.deepEqual(staged.sheets.map(x => x.orientation),
    ["portrait", "landscape", "portrait"]);
  assert.deepEqual(staged.sheets.map(x => x.page.printUrl),
    f.basket.pages.map(x => x.printUrl));
  assert.ok(staged.sheets.every(x => x.element.className.includes("has-text-footer")));
  assert.deepEqual(f.closed, [1, 1, 1]);
  assert.equal(staged.disposed, false);
  staged.dispose();
  staged.dispose();
  assert.equal(staged.disposed, true);
  assert.ok(f.dom.all.filter(x => x.tag === "canvas")
    .every(x => x.width === 0 && x.height === 0));
});

test("stale tab selection blocks all I/O and markup allocations", async () => {
  const f = fixture();
  f.setSaved(["7", "cut-1"]);
  await assert.rejects(stageCurrentBasketPrintSession(f.basket, f.options()),
    /changed/);
  assert.equal(f.calls.length, 0);
  assert.equal(f.dom.all.length, 0);
});

test("withdrawn catalogue entry fails before any PNG requests or canvases", async () => {
  const f = fixture(undefined, { freshCatalog: [catalog[0]] });
  await assert.rejects(stageCurrentBasketPrintSession(f.basket, f.options()));
  assert.deepEqual(f.calls.map(c => c.url), [SITE + "/catalog.json"]);
  assert.equal(f.dom.all.length, 0);
});

test("catalogue redirect/wrong URL/unavailable response cannot be used", async () => {
  for (const input of [
    { catalogStatus: 404 }, { catalogRedirect: true }, { catalogWrongUrl: true },
  ]) {
    const f = fixture(undefined, input);
    await assert.rejects(stageCurrentBasketPrintSession(f.basket, f.options()),
      /catalogue unavailable/);
    assert.equal(f.calls.length, 1);
    assert.equal(f.dom.all.length, 0);
  }
});

test("missing last public PNG cannot return a partial document", async () => {
  const f = fixture(undefined, { failPngAt: 3 });
  await assert.rejects(stageCurrentBasketPrintSession(f.basket, f.options()));
  assert.equal(f.calls.length, 4);
  assert.equal(f.decoded, 0);
  assert.equal(f.dom.all.length, 0);
});

test("selection changed during decode disposes entire native canvas collection", async () => {
  const f = fixture(undefined, { onDecode(index, api) {
    if (index === 0) api.setSaved(["7"]);
  } });
  await assert.rejects(stageCurrentBasketPrintSession(f.basket, f.options()),
    /selection changed/);
  assert.deepEqual(f.closed, [1, 1, 1]);
  assert.ok(f.dom.all.filter(x => x.tag === "canvas")
    .every(x => x.width === 0 && x.height === 0));
});

test("changed visible snapshot during async media work rejects instead of silently accepting", async () => {
  const f = fixture(undefined, { onDecode(index, api) {
    if (index === 0) api.basket.pages[1].printUrl = "/media/cut-1/print-updated.png";
  } });
  await assert.rejects(stageCurrentBasketPrintSession(f.basket, f.options()),
    /selection changed/);
  assert.deepEqual(f.closed, [1, 1, 1]);
  assert.ok(f.dom.all.filter(x => x.tag === "canvas")
    .every(x => x.width === 0 && x.height === 0));
});

test("cancellation and failed decoder produce no print-ready result", async () => {
  const controller = new AbortController();
  const f = fixture(undefined, { abortOnCatalog: () => controller.abort() });
  await assert.rejects(stageCurrentBasketPrintSession(f.basket,
    f.options({ signal: controller.signal })), /aborted/);
  assert.equal(f.calls.length, 1);
  assert.equal(f.dom.all.length, 0);

  const bad = fixture(undefined, { failDecodeAt: 2 });
  await assert.rejects(stageCurrentBasketPrintSession(bad.basket, bad.options()),
    /decoder failed/);
  assert.deepEqual(bad.closed, [1]);
  assert.equal(bad.dom.all.length, 0);
});

test("the session orchestrator does not enable UI, call print, track visitors or rewrite PNGs", () => {
  const code = readFileSync(new URL("../js/print-basket-print-session.mjs", import.meta.url), "utf8")
    .split("\n").filter(line => !line.trimStart().startsWith("//")).join("\n");
  for (const forbidden of [
    "window.print(", "document.body", ".showModal(", ".click()", "innerHTML",
    "sessionStorage.", "localStorage", "toBlob(", "toDataURL(", "createObjectURL",
    "sendBeacon(", "analytics",
  ]) assert.ok(!code.includes(forbidden), forbidden);
});
