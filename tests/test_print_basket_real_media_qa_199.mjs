import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  buildStagingBasket,
  parseActivityIds,
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

test("QA harness parses only distinct bounded activity IDs", () => {
  assert.deepEqual(parseActivityIds("1234567, cut-1"), ["1234567", "cut-1"]);
  for (const value of [
    "",
    "bad/id",
    "1234567 1234567",
    "a b c d e f",
  ]) {
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

test("public evidence deliberately excludes cover title and name", () => {
  const basket = buildStagingBasket(["1234567"], catalog);
  const evidence = publicEvidence(basket, {
    mode: "print",
    coverEnabled: true,
  });
  const encoded = JSON.stringify(evidence);
  assert.equal(evidence.status, "STAGING ONLY");
  assert.equal(evidence.totalSheetCount, 2);
  assert.equal(encoded.includes("title"), false);
  assert.equal(encoded.includes("name"), false);
  assert.deepEqual(evidence.activityIds, ["1234567"]);
  assert.deepEqual(evidence.pages[0], {
    activityId: "1234567",
    pageIndex: 1,
    pageCount: 1,
    printUrl: "/media/1234567/print.png",
  });
});

test("browser QA harness has no release mutation, persistence, analytics or automatic click", () => {
  const source = readFileSync(
    new URL("../tools/print-basket-real-media-qa.mjs", import.meta.url),
    "utf8",
  );
  for (const forbidden of [
    "BOOK_OUTPUT_RELEASE",
    "sessionStorage",
    "localStorage",
    "URLSearchParams",
    "sendBeacon(",
    "analytics",
    "console.",
    ".click(",
    "location.search",
    "location.hash",
  ]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
  assert.equal(source.includes('mode,\\n        origin: location.origin'), true);
  assert.equal(source.includes("printStagedDocumentInBasketHost"), true);
  assert.equal(source.includes("prepareCurrentBookOutputSession"), true);
});
