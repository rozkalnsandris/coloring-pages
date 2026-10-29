import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildBookExportPlan } from "../js/book-export-plan.mjs";
import { reconcileBasket } from "../js/print-basket-selection.mjs";

const one = id => ({
  id,
  title: "Malvorlage",
  print: "/media/" + id + "/print.png",
});
const multi = id => ({
  id,
  title: "Ausschneiden",
  pages: [
    { print: "/media/" + id + "/print-1.png" },
    { print: "/media/" + id + "/print-2.png" },
  ],
});
const cover = (enabled, title = "Mein Ausmalbuch", name = "Mia") => ({
  enabled,
  title,
  name,
});

test("cover is sheet one and atomic artwork order follows the fresh basket", () => {
  const catalog = [one("1"), multi("cut-2"), one("3")];
  const ids = ["cut-2", "3"];
  const previous = reconcileBasket(ids, catalog);
  const result = buildBookExportPlan(ids, catalog, previous, cover(true));

  assert.equal(result.coverEnabled, true);
  assert.equal(result.activityCount, 2);
  assert.equal(result.artworkSheetCount, 3);
  assert.equal(result.sheetCount, 4);
  assert.deepEqual(result.sheets.map(item => item.kind), [
    "cover", "artwork", "artwork", "artwork",
  ]);
  assert.deepEqual(
    result.sheets.filter(item => item.kind === "artwork")
      .map(item => [item.activityId, item.pageIndex]),
    [["cut-2", 1], ["cut-2", 2], ["3", 1]],
  );
  assert.deepEqual(result.sheets.map(item => item.sheetNumber), [1, 2, 3, 4]);
  assert.equal(JSON.stringify(result).includes("Mein Ausmalbuch"), false);
  assert.equal(JSON.stringify(result).includes("Mia"), false);
});

test("coverless plan stays identical to artwork sheet count", () => {
  const catalog = [one("1"), one("2")];
  const ids = ["2", "1"];
  const previous = reconcileBasket(ids, catalog);
  const result = buildBookExportPlan(ids, catalog, previous, cover(false));
  assert.equal(result.coverEnabled, false);
  assert.equal(result.sheetCount, 2);
  assert.deepEqual(result.sheets.map(item => item.activityId), ["2", "1"]);
  assert.deepEqual(result.sheets.map(item => item.sheetNumber), [1, 2]);
});

test("cover consumes one of five physical sheets and never drops artwork", () => {
  const catalog = ["1", "2", "3", "4", "5"].map(one);
  const four = ["1", "2", "3", "4"];
  assert.equal(
    buildBookExportPlan(four, catalog, reconcileBasket(four, catalog), cover(true)).sheetCount,
    5,
  );
  const five = ["1", "2", "3", "4", "5"];
  assert.throws(
    () => buildBookExportPlan(five, catalog, reconcileBasket(five, catalog), cover(true)),
    /exceed five physical A4 sheets/,
  );
});

test("stale snapshot and invalid cover state fail closed", () => {
  const catalog = [one("1"), one("2")];
  const previous = reconcileBasket(["1", "2"], catalog);
  assert.throws(
    () => buildBookExportPlan(["2", "1"], catalog, previous, cover(true)),
    /snapshot/,
  );
  assert.throws(
    () => buildBookExportPlan(["1", "2"], catalog, previous, {
      enabled: true, title: "x",
    }),
    TypeError,
  );
});

test("plan module stays pure and contains no personal-data sinks", () => {
  const source = readFileSync(
    new URL("../js/book-export-plan.mjs", import.meta.url),
    "utf8",
  );
  const code = source.split("\n")
    .filter(line => !line.trimStart().startsWith("//"))
    .join("\n");
  for (const forbidden of [
    "fetch(", "sessionStorage", "localStorage", "createObjectURL",
    "window.print", "console.", "location.", "FormData",
  ]) {
    assert.equal(code.includes(forbidden), false, forbidden);
  }
});
