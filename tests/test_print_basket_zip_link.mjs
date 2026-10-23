import test from "node:test";
import assert from "node:assert/strict";
import { deflateSync } from "node:zlib";
import { buildPrintPngZip } from "../js/print-zip-store.mjs";
import {
  BASKET_ZIP_FILENAME, stageBasketZipDownloadLink,
} from "../js/print-basket-zip-link.mjs";

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
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  const rowSize = width * 3 + 1;
  const raw = Buffer.alloc(rowSize * height, 255);
  for (let i = 0; i < height; i++) raw[i * rowSize] = 0;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 1 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

const page = (id, pageIndex = 1, pageCount = 1) => ({
  activityId: id,
  pageIndex,
  pageCount,
  printUrl: "/media/" + id + "/" + (pageCount === 1 ? "print" : "print-" + pageIndex) + ".png",
});
const pages = [page("0000001"), page("cut-2", 1, 2), page("cut-2", 2, 2)];
const images = [png(), png(3508, 2480), png()];
const zip = buildPrintPngZip(pages, pages.map((p, i) => ({ url: p.printUrl, bytes: images[i] })));

function fakeBrowser(overrides = {}) {
  const created = [], revoked = [], nodes = [];
  let clicks = 0, insertions = 0;
  const documentRef = {
    createElement(tag) {
      assert.equal(tag, "a");
      const link = {
        attrs: {},
        set href(value) { this.attrs.href = value; },
        get href() { return this.attrs.href; },
        removeAttribute(key) { delete this.attrs[key]; },
        click() { clicks += 1; },
        appendChild() { insertions += 1; },
      };
      nodes.push(link);
      return link;
    },
    ...overrides.documentRef,
  };
  const urlRef = {
    createObjectURL(blob) {
      const url = "blob:https://ausmalwiese.de/test-" + (created.length + 1);
      created.push({ url, blob });
      return url;
    },
    revokeObjectURL(url) { revoked.push(url); },
    ...overrides.urlRef,
  };
  return {
    documentRef, urlRef, nodes, created, revoked,
    get clicks() { return clicks; },
    get insertions() { return insertions; },
  };
}

test("stages a genuine 3-sheet ZIP as user-clickable link, without auto-click/DOM append", async () => {
  const browser = fakeBrowser();
  const staged = stageBasketZipDownloadLink(zip, browser);
  assert.equal(staged.filename, BASKET_ZIP_FILENAME);
  assert.equal(staged.link.download, "ausmalwiese-drucksammlung.zip");
  assert.equal(staged.link.textContent, "Als ZIP speichern");
  assert.equal(staged.link.rel, "noopener");
  assert.equal(staged.link.href, browser.created[0].url);
  assert.equal(browser.clicks, 0, "visitor must click the displayed link");
  assert.equal(browser.insertions, 0, "caller owns DOM placement");
  assert.equal(browser.created.length, 1);
  assert.equal(browser.created[0].blob.type, "application/zip");
  const materialized = Buffer.from(await browser.created[0].blob.arrayBuffer());
  assert.deepEqual(materialized, Buffer.from(zip.bytes), "no PNG/ZIP transformation");
  assert.equal(browser.revoked.length, 0, "link must stay valid until caller disposes");

  staged.dispose();
  assert.equal(staged.link.href, undefined);
  assert.deepEqual(browser.revoked, [browser.created[0].url]);
  staged.dispose();
  assert.equal(browser.revoked.length, 1, "dispose is idempotent");
});

test("checks 1-5 true numbered filenames and rejects unsafe or mismatched metadata before Blob URL", () => {
  const invalid = [
    null, {}, { bytes: new Uint8Array(), filenames: [] },
    { ...zip, filenames: [] },
    { ...zip, filenames: ["01-0000001.png", "../2.png", "03-cut-2.png"] },
    { ...zip, filenames: ["01-0000001.png", "03-cut-2.png", "03-cut-2.png"] },
    { ...zip, filenames: ["01-0000001.png", "02-cut-2.png"] },
    { ...zip, filenames: Array.from({ length: 6 }, (_, i) => "0" + (i + 1) + "-id.png") },
    { ...zip, filenames: ["01-0000001.png", "02-cut-2.png", "03-cut-2.png", "04-evil.png"] },
    { ...zip, filenames: ["01-0000001.png", "02-cut-2.png", "03-cut-2.png?".repeat(100)] },
  ];
  for (const candidate of invalid) {
    const browser = fakeBrowser();
    assert.throws(() => stageBasketZipDownloadLink(candidate, browser));
    assert.equal(browser.created.length, 0);
    assert.equal(browser.nodes.length, 0);
  }
});

test("corrupted central-directory, missing local header and trailing data reject before allocation", () => {
  const mutations = [];
  const local = Buffer.from(zip.bytes); local[0] = 0; mutations.push(local);
  const eocd = Buffer.from(zip.bytes); eocd[eocd.length - 22] = 0; mutations.push(eocd);
  const extra = Buffer.concat([Buffer.from(zip.bytes), Buffer.from("junk")]); mutations.push(extra);
  const wrongCount = Buffer.from(zip.bytes); wrongCount.writeUInt16LE(4, wrongCount.length - 12); mutations.push(wrongCount);
  const wrongCentral = Buffer.from(zip.bytes);
  const centralStart = wrongCentral.readUInt32LE(wrongCentral.length - 6);
  wrongCentral[centralStart] = 0; mutations.push(wrongCentral);
  for (const bytes of mutations) {
    const browser = fakeBrowser();
    assert.throws(() => stageBasketZipDownloadLink({ ...zip, bytes }, browser));
    assert.equal(browser.created.length, 0);
  }
});

test("missing capabilities fail before creating any object URL", () => {
  const browser = fakeBrowser();
  assert.throws(() => stageBasketZipDownloadLink(zip, {
    ...browser, urlRef: { createObjectURL() { throw Error("unexpected"); } },
  }), TypeError);
  assert.equal(browser.created.length, 0);
  assert.throws(() => stageBasketZipDownloadLink(zip, {
    ...browser, BlobCtor: null,
  }), TypeError);
  assert.equal(browser.created.length, 0);
});

test("URL creation and link assignment errors cannot leave an active object URL", () => {
  {
    const browser = fakeBrowser({ urlRef: { createObjectURL: () => "invalid-scheme" } });
    assert.throws(() => stageBasketZipDownloadLink(zip, browser), TypeError);
    assert.deepEqual(browser.revoked, ["invalid-scheme"]);
  }
  {
    const browser = fakeBrowser({
      documentRef: {
        createElement() {
          return {
            set href(_) { throw new Error("DOM rejected link"); },
            removeAttribute() {},
          };
        },
      },
    });
    assert.throws(() => stageBasketZipDownloadLink(zip, browser), /DOM rejected link/);
    assert.deepEqual(browser.revoked, [browser.created[0].url]);
  }
});

test("byteOffset ZIP view retains exactly its logical bytes in the download Blob", async () => {
  const padded = Buffer.concat([Buffer.alloc(6), Buffer.from(zip.bytes), Buffer.alloc(4)]);
  const view = padded.subarray(6, 6 + zip.bytes.length);
  const browser = fakeBrowser();
  const staged = stageBasketZipDownloadLink({ ...zip, bytes: view }, browser);
  assert.deepEqual(Buffer.from(await browser.created[0].blob.arrayBuffer()), Buffer.from(zip.bytes));
  staged.dispose();
});
