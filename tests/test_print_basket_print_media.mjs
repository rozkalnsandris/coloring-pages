import test from "node:test";
import assert from "node:assert/strict";
import { deflateSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { reconcileBasket } from "../js/print-basket-selection.mjs";
import { prepareBasketPrintMedia } from "../js/print-basket-print-media.mjs";
import { decodeBasketPrintMedia } from "../js/print-basket-print-decode.mjs";

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

test("all ordered A4 pages decode sequentially and release exactly once", async () => {
  const catalog = [multi("cut-1"), one("2")], ids = ["cut-1","2"];
  const selected = snap(ids, catalog);
  const files = [portrait, landscape, portrait];
  const { fetcher } = mockFetch(selected.pages.map(p=>p.printUrl), files);
  const media = await prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher });
  let calls = 0, active = 0, peak = 0;
  const closures = [];
  const dimensions = [[2480,3508],[3508,2480],[2480,3508]];
  const decode = async (blob) => {
    const index = calls++;
    assert.equal(blob.type, "image/png");
    assert.equal(blob.size, files[index].byteLength);
    active++;
    peak = Math.max(active, peak);
    await Promise.resolve();
    active--;
    return {
      width: dimensions[index][0], height: dimensions[index][1],
      close() { closures[index] = (closures[index] || 0) + 1; },
    };
  };
  const result = await decodeBasketPrintMedia(media, { decode });
  assert.equal(result.released, false);
  assert.equal(calls, 3);
  assert.equal(peak, 1);
  assert.deepEqual(result.sheets.map(s => s.orientation), ["portrait","landscape","portrait"]);
  assert.deepEqual(result.sheets.map(s => s.page.printUrl), selected.pages.map(p => p.printUrl));
  assert.ok(Object.isFrozen(result));
  assert.ok(Object.isFrozen(result.sheets));
  assert.ok(Object.isFrozen(result.sheets[0]));
  result.release();
  assert.equal(result.released, true);
  result.release();
  assert.deepEqual(closures, [1,1,1]);
});

test("second decoder failure closes all earlier A4 bitmaps without partial result", async () => {
  const catalog = [one("1"), one("2")], ids = ["1","2"];
  const selected = snap(ids, catalog);
  const { fetcher } = mockFetch(selected.pages.map(p=>p.printUrl), [portrait, landscape]);
  const media = await prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher });
  let calls = 0, closed = 0;
  const decode = async () => {
    if (++calls === 2) throw new Error("Decoder refused second sheet");
    return { width: 2480, height: 3508, close() { closed++; } };
  };
  await assert.rejects(decodeBasketPrintMedia(media, { decode }), /second sheet/);
  assert.equal(calls, 2);
  assert.equal(closed, 1);
});

test("wrong decoded orientation closes all bitmaps and never returns a success set", async () => {
  const catalog = [one("1"), one("2")], ids = ["1","2"];
  const selected = snap(ids, catalog);
  const { fetcher } = mockFetch(selected.pages.map(p=>p.printUrl), [portrait, landscape]);
  const media = await prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher });
  let closed = 0, calls = 0;
  await assert.rejects(decodeBasketPrintMedia(media, { decode: async () => {
    calls++;
    return { width: 2480, height: 3508, close() { closed++; } };
  } }), /dimensions/);
  assert.equal(calls, 2);
  assert.equal(closed, 2);
});

test("abort during awaiting decode closes the late image and previously decoded images", async () => {
  const catalog = [one("1"), one("2")], ids = ["1","2"];
  const selected = snap(ids, catalog);
  const { fetcher } = mockFetch(selected.pages.map(p=>p.printUrl), [portrait, landscape]);
  const media = await prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher });
  const controller = new AbortController();
  let calls = 0, closed = 0;
  const decode = async () => {
    calls++;
    if (calls === 2) controller.abort();
    return { width: calls === 1 ? 2480 : 3508, height: calls === 1 ? 3508 : 2480,
      close() { closed++; } };
  };
  await assert.rejects(
    decodeBasketPrintMedia(media, { decode, signal: controller.signal }), /aborted/i);
  assert.equal(calls, 2);
  assert.equal(closed, 2);
});

test("invalid preflight metadata, CRC and input decoder fail before decoding", async () => {
  const catalog = [one("1")], ids = ["1"], selected = snap(ids, catalog);
  const { fetcher } = mockFetch(selected.pages.map(p=>p.printUrl), [portrait]);
  const media = await prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher });
  let calls = 0;
  const decode = async () => { calls++; throw new Error("Unexpected decoder"); };
  await assert.rejects(decodeBasketPrintMedia({ ...media, sheets: [] }, { decode }));
  await assert.rejects(decodeBasketPrintMedia({ ...media, sheets: [
    { ...media.sheets[0], width: 3508 },
  ] }, { decode }));
  await assert.rejects(decodeBasketPrintMedia({ ...media, sheets: [
    { ...media.sheets[0], orientation: "landscape" },
  ] }, { decode }));
  const bad = Buffer.from(portrait);
  bad[bad.length - 6] ^= 1;
  await assert.rejects(decodeBasketPrintMedia({ ...media, sheets: [
    { ...media.sheets[0], bytes: bad },
  ] }, { decode }), /PNG/);
  await assert.rejects(decodeBasketPrintMedia(media, { decode: null }), /decoder/);
  assert.equal(calls, 0);
});

test("bad decoder return and mismatched Blob must fail closed", async () => {
  const catalog = [one("1")], ids = ["1"], selected = snap(ids, catalog);
  const { fetcher } = mockFetch(selected.pages.map(p=>p.printUrl), [portrait]);
  const media = await prepareBasketPrintMedia(ids, catalog, selected, { origin: SITE, fetcher });
  await assert.rejects(decodeBasketPrintMedia(media, {
    decode: async () => ({ width: 2480, height: 3508 }),
  }), /released/);
  let decodeCalls = 0;
  await assert.rejects(decodeBasketPrintMedia(media, {
    blobFactory: () => new Blob([], { type: "image/png" }),
    decode: async () => { decodeCalls++; },
  }), /preserve PNG bytes/);
  assert.equal(decodeCalls, 0);
});

test("decoder helper has no browser printing, download, tracking or storage side effects", () => {
  const source = readFileSync(new URL("../js/print-basket-print-decode.mjs", import.meta.url), "utf8");
  const code = source.split("\\n").filter(line => !line.trimStart().startsWith("//")).join("\\n");
  for (const forbidden of ["document.", "sessionStorage", "localStorage", "window.print(",
    "window.open(", "createObjectURL", "innerHTML", "fetch(", ".click()"]) {
    assert.ok(!code.includes(forbidden), forbidden);
  }
});
