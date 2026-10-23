import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { reconcileBasket } from "../js/print-basket-selection.mjs";
import { buildBasketPrintPlan } from "../js/print-basket-print-plan.mjs";

const one = (id) => ({ id, title: "Ausmalbild", print: `/media/${id}/print.png` });
const activity = (id, count = 2) => ({
  id, title: "Ausschneiden und kleben",
  pages: Array.from({ length: count }, (_, i) => ({
    print: `/media/${id}/print-${i + 1}.png`,
  })),
});
const snapshot = (ids, catalog) => reconcileBasket(ids, catalog);
const plan = (ids, catalog) => buildBasketPrintPlan(ids, catalog, snapshot(ids, catalog));

test("ordered cross-category activities preserve atomic nested page order", () => {
  const catalog = [one("0000001"), activity("cut-2"), one("0000003")];
  const state = snapshot(["cut-2", "0000003", "0000001"], catalog);
  const result = buildBasketPrintPlan(state.ids, catalog, state);
  assert.equal(result.sheetCount, 4);
  assert.equal(result.activityCount, 3);
  assert.deepEqual(result.imageUrls, [
    "/media/cut-2/print-1.png", "/media/cut-2/print-2.png",
    "/media/0000003/print.png", "/media/0000001/print.png",
  ]);
  assert.deepEqual(result.pages.map((p) => p.pageIndex), [1, 2, 1, 1]);
  assert.deepEqual(result.pages.map((p) => p.pageCount), [2, 2, 1, 1]);
});

test("exactly five sheets accepted, sixth and partial activity rejected", () => {
  const catalog = [activity("cut-1", 2), one("2"), one("3"), one("4"), one("5")];
  assert.equal(plan(["cut-1", "2", "3", "4"], catalog).sheetCount, 5);
  const over = snapshot(["cut-1", "2", "3", "4", "5"], catalog);
  assert.deepEqual(over.droppedIds, ["5"]);
  assert.throws(() => buildBasketPrintPlan(over.ids, catalog, over), /snapshot/);
});

test("legacy relative print paths are canonicalized under site root", () => {
  const catalog = [{ id: "0000030", title: "Alte Vorlage", print: "media/0000030/print.png" }];
  const result = plan(["0000030"], catalog);
  assert.deepEqual(result.imageUrls, ["/media/0000030/print.png"]);
});

test("empty selection, malformed snapshot and catalogue failure fail closed", () => {
  const catalog = [one("1")];
  for (const state of [null, {}, { ids: ["1"], pages: [], droppedIds: [], sheetCount: 1 }]) {
    assert.throws(() => buildBasketPrintPlan(["1"], catalog, state));
  }
  assert.throws(() => buildBasketPrintPlan([], catalog, snapshot([], catalog)));
  assert.throws(() => buildBasketPrintPlan(["1"], null, snapshot(["1"], catalog)));
});

test("a changed session ID, reorder or stale on-screen activity is rejected", () => {
  const catalog = [activity("cut-1"), one("2"), one("3")];
  const previous = snapshot(["cut-1", "2", "3"], catalog);
  assert.throws(() => buildBasketPrintPlan(["2", "cut-1", "3"], catalog, previous));
  assert.throws(() => buildBasketPrintPlan(["cut-1", "2"], catalog, previous));
  const next = [one("3"), activity("cut-1"), one("2")];
  assert.deepEqual(buildBasketPrintPlan(previous.ids, next, previous).imageUrls,
    previous.pages.map((page) => page.printUrl));
});

test("changed public PNG URL, missing item and changed multi-page contents reject", () => {
  const catalog = [activity("cut-1"), one("2")];
  const previous = snapshot(["cut-1", "2"], catalog);
  assert.throws(() => buildBasketPrintPlan(previous.ids, [activity("cut-1")], previous));
  assert.throws(() => buildBasketPrintPlan(previous.ids, [
    { id: "cut-1", title: "Neue Seiten", pages: [
      { print: "/media/cut-1/print-1.png" },
      { print: "/media/cut-1/print-3.png" },
    ] }, one("2")], previous));
  assert.throws(() => buildBasketPrintPlan(previous.ids, [
    activity("cut-1", 3), one("2")], previous));
  assert.throws(() => buildBasketPrintPlan(previous.ids, [
    activity("cut-1"), { ...one("2"), print: "/media/2/preview.webp" }], previous));
});

test("duplicate catalogue IDs and aliases never become print plan URLs", () => {
  const duplicate = [one("1"), { ...one("1"), title: "Double" }];
  assert.throws(() => buildBasketPrintPlan(["1"], duplicate, snapshot(["1"], [one("1")])));
  const malicious = [{ id: "1", title: "External", print: "https://example.com/x.png" }];
  assert.throws(() => buildBasketPrintPlan(["1"], malicious, snapshot(["1"], [one("1")])));
});

test("tampered previous snapshot, including page count and dropped IDs, rejects", () => {
  const catalog = [activity("cut-1"), one("2")];
  const state = snapshot(["cut-1", "2"], catalog);
  assert.throws(() => buildBasketPrintPlan(state.ids, catalog, {
    ...state, pages: [state.pages[1], state.pages[0], state.pages[2]],
  }));
  assert.throws(() => buildBasketPrintPlan(state.ids, catalog, {
    ...state, sheetCount: 2,
  }));
  assert.throws(() => buildBasketPrintPlan(state.ids, catalog, {
    ...state, droppedIds: ["withdrawn"],
  }));
});

test("returned immutable plan does not modify prior state or catalogue", () => {
  const catalog = [activity("cut-1"), one("2")];
  const state = snapshot(["2", "cut-1"], catalog);
  const before = JSON.stringify({ catalog, state });
  const result = buildBasketPrintPlan(state.ids, catalog, state);
  assert.ok(Object.isFrozen(result));
  assert.ok(Object.isFrozen(result.pages));
  assert.ok(Object.isFrozen(result.pages[0]));
  assert.ok(Object.isFrozen(result.imageUrls));
  assert.throws(() => { result.pages[0].printUrl = "/media/evil/print.png"; }, TypeError);
  assert.equal(JSON.stringify({ catalog, state }), before);
});

test("module stays source-only; never activates printing or downloads", () => {
  const source = readFileSync(new URL("../js/print-basket-print-plan.mjs", import.meta.url), "utf8");
  for (const forbidden of [
    "window.print", "document.", "sessionStorage", "fetch(", "createObjectURL",
    "preview.webp", "originals/", "window.open(", ".click()",
  ]) assert.ok(!source.includes(forbidden), forbidden);
});
