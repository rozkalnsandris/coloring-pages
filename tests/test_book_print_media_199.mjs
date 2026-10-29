import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  LOCAL_BOOK_COVER_PRINT_URL,
  prepareBookPrintMediaFromBundle,
} from "../js/book-print-media.mjs";

function crc32(bytes) {
  let value = -1;
  for (const byte of bytes) {
    value ^= byte;
    for (let i = 0; i < 8; i++) {
      value = (value >>> 1) ^ ((value & 1) ? 0xedb88320 : 0);
    }
  }
  return (value ^ -1) >>> 0;
}
function chunk(type, data) {
  const output = Buffer.alloc(12 + data.length);
  output.writeUInt32BE(data.length, 0);
  output.write(type, 4, 4, "ascii");
  Buffer.from(data).copy(output, 8);
  output.writeUInt32BE(crc32(output.subarray(4, output.length - 4)), output.length - 4);
  return output;
}
function png(width = 2480, height = 3508, { phys = false } = {}) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  const chunks = [
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
  ];
  if (phys) {
    const body = Buffer.alloc(9);
    body.writeUInt32BE(11811, 0);
    body.writeUInt32BE(11811, 4);
    body[8] = 1;
    chunks.push(chunk("pHYs", body));
  }
  chunks.push(chunk("IDAT", Buffer.from([1])));
  chunks.push(chunk("IEND", Buffer.alloc(0)));
  return Buffer.concat(chunks);
}

const page = (id, index = 1, count = 1, landscape = false) => Object.freeze({
  activityId: id,
  pageIndex: index,
  pageCount: count,
  printUrl: "/media/" + id + "/" + (count === 1 ? "print" : "print-" + index) + ".png",
  landscape,
});

function bundle({ cover = true } = {}) {
  const artworkPages = Object.freeze([
    page("cut-1", 1, 2),
    page("cut-1", 2, 2, true),
  ]);
  const total = artworkPages.length + (cover ? 1 : 0);
  const sheets = [];
  if (cover) {
    sheets.push(Object.freeze({
      kind: "cover",
      sheetNumber: 1,
      sheetCount: total,
      orientation: "portrait",
    }));
  }
  artworkPages.forEach((value, index) => sheets.push(Object.freeze({
    kind: "artwork",
    sheetNumber: index + 1 + (cover ? 1 : 0),
    sheetCount: total,
    activityId: value.activityId,
    pageIndex: value.pageIndex,
    pageCount: value.pageCount,
    printUrl: value.printUrl,
  })));

  const portrait = png();
  const landscape = png(3508, 2480);
  const downloads = Object.freeze([
    { url: artworkPages[0].printUrl, bytes: portrait },
    { url: artworkPages[1].printUrl, bytes: landscape },
  ]);
  let disposed = false;
  return {
    plan: Object.freeze({
      coverEnabled: cover,
      artworkSheetCount: artworkPages.length,
      sheetCount: total,
      artworkPages,
      sheets: Object.freeze(sheets),
    }),
    coverPng: cover ? png(2480, 3508, { phys: true }) : null,
    artworkDownloads: downloads,
    zip: { bytes: new Uint8Array([1]), filenames: [] },
    get disposed() { return disposed; },
    dispose() { disposed = true; },
  };
}

test("cover becomes first local portrait sheet and artwork keeps exact order/bytes", () => {
  const value = bundle({ cover: true });
  const result = prepareBookPrintMediaFromBundle(value);

  assert.equal(result.plan.coverEnabled, true);
  assert.equal(result.plan.sheetCount, 3);
  assert.equal(result.plan.pages[0].kind, "cover");
  assert.equal(result.plan.pages[0].printUrl, LOCAL_BOOK_COVER_PRINT_URL);
  assert.deepEqual(result.plan.imageUrls, [
    LOCAL_BOOK_COVER_PRINT_URL,
    "/media/cut-1/print-1.png",
    "/media/cut-1/print-2.png",
  ]);
  assert.deepEqual(result.sheets.map(sheet => sheet.orientation), [
    "portrait", "portrait", "landscape",
  ]);
  assert.equal(result.sheets[0].bytes, value.coverPng);
  assert.equal(result.sheets[1].bytes, value.artworkDownloads[0].bytes);
  assert.equal(result.sheets[2].bytes, value.artworkDownloads[1].bytes);
  assert.equal(JSON.stringify(result).includes("Mein Ausmalbuch"), false);
  assert.equal(JSON.stringify(result).includes("Mia"), false);
});

test("coverless bundle reuses artwork bytes without inventing a local cover sheet", () => {
  const value = bundle({ cover: false });
  const result = prepareBookPrintMediaFromBundle(value);
  assert.equal(result.plan.coverEnabled, false);
  assert.equal(result.plan.sheetCount, 2);
  assert.deepEqual(result.plan.imageUrls, [
    "/media/cut-1/print-1.png",
    "/media/cut-1/print-2.png",
  ]);
  assert.equal(result.sheets[0].bytes, value.artworkDownloads[0].bytes);
  assert.equal(result.sheets[1].bytes, value.artworkDownloads[1].bytes);
});

test("disposed, malformed, changed and nonconforming cover bundles fail closed", () => {
  {
    const value = bundle();
    value.dispose();
    assert.throws(() => prepareBookPrintMediaFromBundle(value), /undisposed/);
  }
  {
    const value = bundle();
    value.plan = { ...value.plan, sheetCount: 4 };
    assert.throws(() => prepareBookPrintMediaFromBundle(value), /sheet count/);
  }
  {
    const value = bundle();
    value.coverPng = png();
    assert.throws(() => prepareBookPrintMediaFromBundle(value), /exact A4 RGB 300 DPI/);
  }
  {
    const value = bundle();
    value.coverPng = png(3508, 2480, { phys: true });
    assert.throws(() => prepareBookPrintMediaFromBundle(value), /exact A4 RGB 300 DPI|portrait A4/);
  }
  {
    const value = bundle();
    value.artworkDownloads = [
      { ...value.artworkDownloads[0], url: "/media/other/print.png" },
      value.artworkDownloads[1],
    ];
    assert.throws(() => prepareBookPrintMediaFromBundle(value), /artwork media/);
  }
});

test("adapter remains source-only and has no personal-data/network/print sink", () => {
  const source = readFileSync(
    new URL("../js/book-print-media.mjs", import.meta.url),
    "utf8",
  );
  const code = source.split("\n")
    .filter(line => !line.trimStart().startsWith("//"))
    .join("\n");
  for (const forbidden of [
    "fetch(", "sessionStorage", "localStorage", "window.print",
    "document.", "console.", "sendBeacon(", "createObjectURL",
    "toBlob(", "toDataURL(",
  ]) {
    assert.equal(code.includes(forbidden), false, forbidden);
  }
});
