import test from "node:test";
import assert from "node:assert/strict";
import { deflateSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { reconcileBasket } from "../js/print-basket-selection.mjs";
import { prepareBasketPrintMedia } from "../js/print-basket-print-media.mjs";

const SITE = "https://ausmalwiese.de";
const one = (id) => ({ id, title: "Malvorlage", print: `/media/${id}/print.png` });
const multi = (id) => ({ id, title: "Zwei Seiten", pages: [
  { print: `/media/${id}/print-1.png` },
  { print: `/media/${id}/print-2.png` },
] });
const snap = (ids, catalog) => reconcileBasket(ids, catalog);

function crc32(bytes) {
  let crc = -1;
  for (const byte of bytes) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ -1) >>> 0;
}
function chunk(type, bytes) {
  const result = Buffer.alloc(12 + bytes.length);
  result.writeUInt32BE(bytes.length, 0);
  result.write(type, 4, 4, "ascii");
  Buffer.from(bytes).copy(result, 8);
  result.writeUInt32BE(crc32(result.subarray(4, result.length - 4)), result.length - 4);
  return result;
}
function syntheticA4(width = 2480, height = 3508) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2;
  // Complete white RGB A4 raster; no committed image binaries.
  const raw = Buffer.alloc((width * 3 + 1) * height, 255);
  for (let row = 0; row < height; row++) raw[row * (width * 3 + 1)] = 0;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 1 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}
const portrait = syntheticA4();
const landscape = syntheticA4(3508, 2480);

function response(url, bytes, { status = 200, mime = "image/png", redirected = false, declaredLength } = {}) {
  return {
    status, redirected, url,
    headers: new Headers({
      "content-type": mime,
      "content-length": String(declaredLength ?? bytes.length),
    }),
    body: new ReadableStream({
      start(controller) {
        controller.enqueue(bytes);
        controller.close();
      },
    }),
  };
}
function mockFetch(pages, bytes) {
  const requests = [];
  return {
    requests,
    fetcher: async (url, opts) => {
      requests.push({ url, opts });
      const index = pages.indexOf(url.slice(SITE.length));
      if (index < 0) throw Error("unrecognized URL");
      return response(url, bytes[index]);
    },
  };
}

test("ordered portrait/landscape media retain exact A4 public PNG bytes and page order", async () => {
  const catalog = [one("42"), multi("cut-2")];
  const ids = ["cut-2", "42"], selected = snap(ids, catalog);
  const paths = selected.pages.map(p => p.printUrl);
  const files = [portrait, landscape, portrait];
  const { fetcher, requests } = mockFetch(paths, files);
  const result = await prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher });
  assert.deepEqual(result.sheets.map(s => s.page.printUrl), paths);
  assert.deepEqual(result.sheets.map(s => s.orientation), ["portrait", "landscape", "portrait"]);
  assert.deepEqual(result.sheets.map(s => [s.width, s.height]), [[2480,3508],[3508,2480],[2480,3508]]);
  result.sheets.forEach((sheet, i) => assert.deepEqual(Buffer.from(sheet.bytes), files[i]));
  assert.equal(requests.length, 3);
  assert.deepEqual(requests.map(r => r.url), paths.map(p => SITE + p));
  assert.ok(requests.every(r => r.opts.redirect === "error" && r.opts.credentials === "omit" &&
    r.opts.cache === "no-store" && r.opts.mode === "same-origin"));
  assert.ok(Object.isFrozen(result));
  assert.ok(Object.isFrozen(result.sheets));
  assert.ok(Object.isFrozen(result.plan.pages[0]));
});

test("catalogue withdrawal, replaced PNG URL and reordered session IDs block all fetches", async () => {
  const catalog = [one("1"), one("2")];
  const state = snap(["1","2"], catalog);
  let calls = 0;
  const fetcher = async () => { calls++; throw Error("unexpected request"); };
  const options = { origin: SITE, fetcher };
  await assert.rejects(prepareBasketPrintMedia(["2","1"], catalog, state, options));
  await assert.rejects(prepareBasketPrintMedia(state.ids, [one("1")], state, options));
  await assert.rejects(prepareBasketPrintMedia(state.ids, [
    one("1"), { ...one("2"), print: "/media/2/print-updated.png" },
  ], state, options));
  assert.equal(calls, 0);
});

test("malformed second PNG prevents any successful media result", async () => {
  const catalog = [one("1"), one("2")];
  const state = snap(["1", "2"], catalog);
  const corrupted = Buffer.from(landscape);
  corrupted[corrupted.length - 7] ^= 0x02;
  const { fetcher, requests } = mockFetch(state.pages.map(p=>p.printUrl), [portrait, corrupted]);
  await assert.rejects(
    prepareBasketPrintMedia(state.ids, catalog, state, { origin: SITE, fetcher }),
    /PNG/,
  );
  assert.equal(requests.length, 2);
});

test("HTTP, MIME and declared-size failures propagate without print-ready success", async () => {
  const catalog = [one("1")], ids = ["1"], selected = snap(ids, catalog);
  const url = SITE + selected.pages[0].printUrl;
  for (const overrides of [
    { status: 404 }, { mime: "image/jpeg" }, { redirected: true },
    { declaredLength: portrait.length - 1 },
  ]) {
    const fetcher = async () => response(url, portrait, overrides);
    await assert.rejects(prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher }));
  }
});

test("cancellation during a multi-page load rejects without partial result", async () => {
  const catalog = [one("1"), one("2")], ids = ["1","2"], state = snap(ids, catalog);
  const controller = new AbortController();
  const paths = state.pages.map(p=>p.printUrl);
  const calls = [];
  const fetcher = async (url) => {
    calls.push(url);
    if (calls.length === 2) controller.abort();
    const index = paths.indexOf(url.slice(SITE.length));
    return response(url, index===0 ? portrait : landscape);
  };
  await assert.rejects(
    prepareBasketPrintMedia(ids, catalog, state, {
      origin: SITE, fetcher, signal: controller.signal,
    }), /aborted/i,
  );
  assert.equal(calls.length, 2);
});

test("print media preflight never starts rendering, printing, downloads or telemetry", () => {
  const source = readFileSync(new URL("../js/print-basket-print-media.mjs", import.meta.url), "utf8");
  const code = source.split("\n").filter(line => !line.trimStart().startsWith("//")).join("\n");
  for(const forbidden of ["window.", "document.", "sessionStorage", "createObjectURL",
    "window.print", ".click()", "innerHTML", "fetch("]) {
    assert.ok(!code.includes(forbidden), forbidden);
  }
});
