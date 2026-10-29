import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  buildStagingBasket,
  parseActivityIds,
  parseCanonicalA4PngHeader,
  publicEvidence,
} from "../tools/print-basket-real-media-qa.mjs";

const catalog = [
  {
    id: "1234567",
    title: "Portrait",
    print: "/media/1234567/print.png",
  },
  {
    id: "cut-1",
    title: "Cut",
    pages: [
      { print: "/media/cut-1/print-1.png" },
      { print: "/media/cut-1/print-2.png" },
    ],
  },
];

function pngHeader(width, height, bitDepth = 8, colorType = 2) {
  const bytes = new Uint8Array(29);
  bytes.set([137, 80, 78, 71, 13, 10, 26, 10], 0);
  new DataView(bytes.buffer).setUint32(8, 13, false);
  bytes.set([73, 72, 68, 82], 12);
  const view = new DataView(bytes.buffer);
  view.setUint32(16, width, false);
  view.setUint32(20, height, false);
  bytes[24] = bitDepth;
  bytes[25] = colorType;
  return bytes;
}

test("QA harness parses only distinct bounded activity IDs", () => {
  assert.deepEqual(parseActivityIds("1234567, cut-1"), ["1234567", "cut-1"]);
  for (const value of ["", "bad/id", "1234567 1234567", "a b c d e f"]) {
    assert.throws(() => parseActivityIds(value));
  }
});

test("QA staging basket reuses canonical fresh catalogue semantics", () => {
  const value = buildStagingBasket(["cut-1", "1234567"], catalog);
  assert.deepEqual(value.ids, ["cut-1", "1234567"]);
  assert.equal(value.sheetCount, 3);
  assert.deepEqual(
    value.pages.map(page => page.printUrl),
    [
      "/media/cut-1/print-1.png",
      "/media/cut-1/print-2.png",
      "/media/1234567/print.png",
    ],
  );
  assert.throws(() => buildStagingBasket(["missing"], catalog));
});

test("QA PNG header evidence accepts only canonical RGB8 A4 orientations", () => {
  assert.deepEqual(parseCanonicalA4PngHeader(pngHeader(2480, 3508)), {
    width: 2480, height: 3508, bitDepth: 8, colorType: 2, orientation: "portrait",
  });
  assert.deepEqual(parseCanonicalA4PngHeader(pngHeader(3508, 2480)), {
    width: 3508, height: 2480, bitDepth: 8, colorType: 2, orientation: "landscape",
  });
  assert.throws(() => parseCanonicalA4PngHeader(pngHeader(100, 100)));
  assert.throws(() => parseCanonicalA4PngHeader(pngHeader(2480, 3508, 8, 6)));
});

test("public evidence deliberately excludes cover title and name", () => {
  const basket = buildStagingBasket(["1234567"], catalog);
  const media = [{
    activityId: "1234567",
    pageIndex: 1,
    pageCount: 1,
    printUrl: "/media/1234567/print.png",
    httpStatus: 200,
    mime: "image/png",
    bytes: 123,
    sha256: "a".repeat(64),
    width: 2480,
    height: 3508,
    orientation: "portrait",
  }];
  const evidence = publicEvidence(basket, {
    mode: "validate",
    coverEnabled: true,
    publicMedia: media,
  });
  const encoded = JSON.stringify(evidence);
  assert.equal(evidence.status, "STAGING ONLY");
  assert.equal(evidence.totalSheetCount, 2);
  assert.equal(encoded.includes("title"), false);
  assert.equal(encoded.includes("name"), false);
  assert.deepEqual(evidence.activityIds, ["1234567"]);
  assert.deepEqual(evidence.publicMedia, media);
});

test("browser QA harness has no release mutation, persistence, analytics or automatic click", () => {
  const source = readFileSync(
    new URL("../tools/print-basket-real-media-qa.mjs", import.meta.url),
    "utf8",
  );
  for (const forbidden of [
    "BOOK_OUTPUT_RELEASE",
    "URLSearchParams",
    "sendBeacon(",
    "analytics",
    "console.",
    ".click(",
    "location.search",
    "location.hash",
    ".setItem(",
    ".removeItem(",
    ".clear(",
  ]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
  assert.equal(source.includes('import { reconcileBasket } from "../js/print-basket-selection.mjs"'), true);
  assert.equal(source.includes("printStagedDocumentInBasketHost"), true);
  assert.equal(source.includes("prepareCurrentBookOutputSession"), true);
  assert.equal(source.includes("collectPublicMediaEvidence"), true);
  assert.equal(source.includes('from "./receipt.mjs"'), true);
  assert.equal(source.includes("createQaAuditedFetch"), true);
  assert.equal(source.includes("runPrivacyCanary"), true);
  assert.equal(source.includes("globalThis.sessionStorage"), true);
  assert.equal(source.includes("globalThis.localStorage"), true);
});
