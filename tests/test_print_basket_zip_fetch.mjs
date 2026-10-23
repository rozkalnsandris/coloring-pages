import test from "node:test";
import assert from "node:assert/strict";
import { deflateSync } from "node:zlib";
import { prepareBasketPngZip } from "../js/print-basket-zip-fetch.mjs";

function crc32(bytes) {
  let crc = -1;
  for (const byte of bytes) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ -1) >>> 0;
}
function chunk(type, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(type, 4, 4, "ascii");
  Buffer.from(data).copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, out.length - 4)), out.length - 4);
  return out;
}
function png(width = 2480, height = 3508) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2;
  const raw = Buffer.alloc((width * 3 + 1) * height, 255);
  for (let i = 0; i < height; i++) raw[i * (width * 3 + 1)] = 0;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 1 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

const SITE = "https://ausmalwiese.de";
const sheet = (id, index = 1, count = 1) => ({
  activityId: id, pageIndex: index, pageCount: count,
  printUrl: "/media/" + id + "/" + (count === 1 ? "print" : "print-" + index) + ".png",
});
function fakeResponse(url, bytes, options = {}) {
  const chunks = options.chunks || [bytes];
  return {
    status: options.status ?? 200,
    redirected: options.redirected ?? false,
    url: options.responseUrl ?? url,
    headers: new Headers({
      "content-type": options.mime ?? "image/png",
      ...(options.noLength ? {} : { "content-length": String(options.length ?? bytes.length) }),
    }),
    body: options.body ?? new ReadableStream({
      start(controller) {
        for (const part of chunks) controller.enqueue(part);
        controller.close();
      },
    }),
  };
}
function fakeFetch(pages, buffers, calls, customize = (_, url, bytes) => fakeResponse(url, bytes)) {
  return async (url, options) => {
    calls.push({ url, options });
    const i = calls.length - 1;
    return customize(i, url, buffers[i]);
  };
}
function zipLocalEntries(zip) {
  const view = new DataView(zip.bytes.buffer, zip.bytes.byteOffset, zip.bytes.byteLength);
  const entries = [];
  let p = 0;
  while (view.getUint32(p, true) === 0x04034b50) {
    const length = view.getUint32(p + 18, true);
    const filenameLength = view.getUint16(p + 26, true);
    const start = p + 30;
    const name = Buffer.from(zip.bytes.subarray(start, start + filenameLength)).toString("ascii");
    const data = zip.bytes.subarray(start + filenameLength, start + filenameLength + length);
    entries.push({ name, data });
    p = start + filenameLength + length;
  }
  return entries;
}

test("sequential full-size portrait/landscape fetch and ZIP keep exact bytes and order", async () => {
  const pages = [sheet("0000001"), sheet("cut-2", 1, 2), sheet("cut-2", 2, 2)];
  const images = [png(), png(3508, 2480), png()];
  const calls = [];
  const fetcher = fakeFetch(pages, images, calls, (_, url, bytes) =>
    fakeResponse(url, bytes, { chunks: [bytes.subarray(0, 100), bytes.subarray(100)] })
  );
  const zip = await prepareBasketPngZip(pages, { origin: SITE, fetcher });
  assert.deepEqual(zip.filenames, ["01-0000001.png", "02-cut-2.png", "03-cut-2.png"]);
  assert.deepEqual(zipLocalEntries(zip).map(f => f.name), zip.filenames);
  zipLocalEntries(zip).forEach((f, i) => assert.deepEqual(Buffer.from(f.data), images[i]));
  assert.deepEqual(calls.map(c => c.url), pages.map(p => SITE + p.printUrl));
  assert.ok(calls.every(c => c.options.credentials === "omit" && c.options.mode === "same-origin" &&
    c.options.redirect === "error" && c.options.cache === "no-store"));
});

test("unsafe pages, empty selection and origin reject without network activity", async () => {
  const ok = sheet("1"), bytes = png(), calls = [];
  const fetcher = fakeFetch([ok], [bytes], calls);
  const sets = [
    [], Array(6).fill(ok), [ok, ok], [{ ...ok, printUrl: "/media/2/print.png" }],
    [{ ...ok, printUrl: "//evil.test/media/1/print.png" }],
    [{ ...ok, printUrl: "/media/1/print.png?x=1" }],
    [{ ...ok, pageIndex: 0 }],
  ];
  for (const pages of sets) await assert.rejects(prepareBasketPngZip(pages, { origin: SITE, fetcher }));
  for (const origin of ["https://evil.test/extra", "javascript:foo", "https://user:secret@host.test",
    "https://ausmalwiese.de?x=1"]) {
    await assert.rejects(prepareBasketPngZip([ok], { origin, fetcher }));
  }
  assert.equal(calls.length, 0);
});

test("404, HTML, redirected or mismatched response fail without any partial ZIP", async () => {
  const p = sheet("1"), image = png();
  for (const customize of [
    (_, url, bytes) => fakeResponse(url, bytes, { status: 404 }),
    (_, url, bytes) => fakeResponse(url, bytes, { mime: "text/html" }),
    (_, url, bytes) => fakeResponse(url, bytes, { redirected: true }),
    (_, url, bytes) => fakeResponse(url, bytes, { responseUrl: "https://other.test/media/1/print.png" }),
    (_, url, bytes) => fakeResponse(url, bytes, { responseUrl: url + "?tracking=1" }),
  ]) {
    const calls = [];
    await assert.rejects(prepareBasketPngZip([p], { origin: SITE,
      fetcher: fakeFetch([p], [image], calls, customize) }));
    assert.equal(calls.length, 1);
  }
});

test("second missing image stops immediately before a third request", async () => {
  const pages = [sheet("1"), sheet("2"), sheet("3")], image = png(), calls = [];
  const fetcher = fakeFetch(pages, [image, image, image], calls,
    (index, url, bytes) => fakeResponse(url, bytes, { status: index === 1 ? 404 : 200 }));
  await assert.rejects(prepareBasketPngZip(pages, { origin: SITE, fetcher }));
  assert.equal(calls.length, 2);
});

test("missing and wrong size headers, oversized declared length and truncated stream reject", async () => {
  const p = sheet("1"), image = png();
  for (const options of [
    { length: image.length + 1 },
    { length: image.length - 1 },
    { length: 64 * 1024 * 1024 + 1 },
    { chunks: [image.subarray(0, image.length - 2)], length: image.length },
  ]) {
    await assert.rejects(prepareBasketPngZip([p], { origin: SITE,
      fetcher: (url) => Promise.resolve(fakeResponse(url, image, options)) }));
  }
  const noLength = await prepareBasketPngZip([p], { origin: SITE,
    fetcher: (url) => Promise.resolve(fakeResponse(url, image, { noLength: true })) });
  assert.deepEqual(Buffer.from(zipLocalEntries(noLength)[0].data), image);
});

test("empty or malformed streams and invalid A4 bytes never yield ZIP", async () => {
  const p = sheet("1"), good = png(), bad = Buffer.from(good);
  bad[20] ^= 1;
  for (const data of [Buffer.alloc(0), bad, Buffer.from("no-png")]) {
    await assert.rejects(prepareBasketPngZip([p], { origin: SITE,
      fetcher: (url) => Promise.resolve(fakeResponse(url, data)) }));
  }
  const malformed = fakeResponse(SITE + p.printUrl, good, {
    body: new ReadableStream({ start(controller) { controller.enqueue("not binary"); controller.close(); } }),
  });
  await assert.rejects(prepareBasketPngZip([p], { origin: SITE,
    fetcher: async () => malformed }));
});

test("aborted signal stops before fetch and aborts after first completed file", async () => {
  const controller = new AbortController();
  const p1 = sheet("1"), p2 = sheet("2"), image = png();
  controller.abort();
  let calls = 0;
  await assert.rejects(prepareBasketPngZip([p1], { origin: SITE,
    signal: controller.signal, fetcher: async () => { calls++; throw Error("should not fetch"); } }));
  assert.equal(calls, 0);

  const controller2 = new AbortController();
  await assert.rejects(prepareBasketPngZip([p1, p2], { origin: SITE,
    signal: controller2.signal,
    fetcher: async (url) => {
      calls++;
      controller2.abort();
      return fakeResponse(url, image);
    },
  }));
  assert.equal(calls, 1);
});

test("early stream failure prevents unsafe ZIP and other fetches", async () => {
  const pages = [sheet("1"), sheet("2")], bytes = png();
  let calls = 0;
  const fail = new ReadableStream({
    start(controller) {
      controller.enqueue(bytes.subarray(0, 64));
      controller.error(new Error("network lost"));
    },
  });
  await assert.rejects(prepareBasketPngZip(pages, { origin: SITE,
    fetcher: async (url) => {
      calls++;
      return fakeResponse(url, bytes, { body: fail });
    },
  }));
  assert.equal(calls, 1);
});
