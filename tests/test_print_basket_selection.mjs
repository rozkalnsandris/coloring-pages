import test from "node:test";
import assert from "node:assert/strict";
import {
  MAX_BASKET_SHEETS, reconcileBasket, addBasketActivity,
  removeBasketActivity, moveBasketActivity, clearBasket, expandBasketForExport,
} from "../js/print-basket-selection.mjs";

const one = (id) => ({ id, title: "Malvorlage", print: `/media/${id}/print.png` });
const multi = (id, count = 2) => ({
  id, title: "Ausschneiden und kleben",
  print: `/media/${id}/print-1.png`,
  pages: Array.from({ length: count }, (_, i) => ({
    print: `/media/${id}/print-${i + 1}.png`,
  })),
});

test("published single-page IDs preserve order, leading zeros and count", () => {
  const entries = [one("0000001"), one("xyz-1"), one("0000002")];
  const state = reconcileBasket(["0000002", "0000001"], entries);
  assert.equal(MAX_BASKET_SHEETS, 5);
  assert.deepEqual(state.ids, ["0000002", "0000001"]);
  assert.equal(state.sheetCount, 2);
  assert.deepEqual(state.pages.map((p) => p.printUrl), [
    "/media/0000002/print.png", "/media/0000001/print.png",
  ]);
});

test("add is idempotent, does not change caller inputs", () => {
  const source = Object.freeze(["0000001"]);
  const entries = [one("0000001"), one("0000002")];
  const again = addBasketActivity(source, "0000001", entries);
  const next = addBasketActivity(source, "0000002", entries);
  assert.equal(again.reason, "already-selected");
  assert.deepEqual(again.ids, ["0000001"]);
  assert.deepEqual(next.ids, ["0000001", "0000002"]);
  assert.deepEqual(source, ["0000001"]);
});

test("a sixth physical sheet is rejected without evicting anything", () => {
  const items = Array.from({ length: 6 }, (_, i) => one(String(i + 1)));
  const ids = ["1", "2", "3", "4", "5"];
  const state = addBasketActivity(ids, "6", items);
  assert.equal(state.ok, false);
  assert.equal(state.reason, "limit");
  assert.equal(state.sheetCount, 5);
  assert.deepEqual(state.ids, ids);
});

test("multi-page activity consumes all sheets atomically and preserves page order", () => {
  const entries = [multi("cut-1"), one("2"), one("3"), one("4"), one("5")];
  const full = addBasketActivity(["cut-1", "2", "3"], "4", entries);
  assert.equal(full.ok, true);
  assert.equal(full.sheetCount, 5);
  assert.deepEqual(full.pages.filter((p) => p.activityId === "cut-1").map((p) => p.pageIndex), [1, 2]);
  const over = addBasketActivity(full.ids, "5", entries);
  assert.equal(over.reason, "limit");
  assert.equal(over.sheetCount, 5);
  assert.deepEqual(over.ids, full.ids);
});

test("restore discards over-limit activity, never takes only its first sheet", () => {
  const catalog = [one("1"), one("2"), one("3"), one("4"), multi("cut-1")];
  const current = reconcileBasket(["1", "2", "3", "4", "cut-1"], catalog);
  assert.deepEqual(current.ids, ["1", "2", "3", "4"]);
  assert.deepEqual(current.droppedIds, ["cut-1"]);
  assert.equal(current.sheetCount, 4);
  assert.throws(() => expandBasketForExport(["1", "2", "3", "4", "cut-1"], catalog));
});

test("reorder swaps whole activities and keeps nested page ordering", () => {
  const catalog = [multi("cut-1"), one("2"), one("3")];
  const next = moveBasketActivity(["cut-1", "2", "3"], "cut-1", 1, catalog);
  assert.deepEqual(next.ids, ["2", "cut-1", "3"]);
  assert.deepEqual(next.pages.map((p) => p.printUrl), [
    "/media/2/print.png", "/media/cut-1/print-1.png",
    "/media/cut-1/print-2.png", "/media/3/print.png",
  ]);
  assert.deepEqual(moveBasketActivity(next.ids, "cut-1", -1, catalog).ids, ["cut-1", "2", "3"]);
  assert.deepEqual(moveBasketActivity(next.ids, "3", 1, catalog).ids, next.ids);
  assert.throws(() => moveBasketActivity(next.ids, "2", 0, catalog), RangeError);
});

test("removal and clear retain no stale sheets", () => {
  const catalog = [multi("cut-1"), one("2")];
  const current = removeBasketActivity(["cut-1", "2"], "cut-1", catalog);
  assert.deepEqual(current.ids, ["2"]);
  assert.equal(current.sheetCount, 1);
  assert.deepEqual(clearBasket(), { ids: [], pages: [], sheetCount: 0, droppedIds: [] });
});

test("missing IDs and duplicated selection IDs are reconciled without inventing content", () => {
  const state = reconcileBasket(["1", "1", "gone", null, "2"], [one("1"), one("2")]);
  assert.deepEqual(state.ids, ["1", "2"]);
  assert.deepEqual(state.droppedIds, ["1", "gone", null]);
  assert.equal(state.sheetCount, 2);
  assert.throws(() => expandBasketForExport(["1", "gone"], [one("1")]));
  assert.equal(addBasketActivity(["1"], "gone", [one("1")]).reason, "unavailable");
});

test("duplicate catalogue IDs are ambiguous, even with a malformed duplicate", () => {
  const catalog = [one("1"), { id: "1", title: "Andere Malvorlage" }];
  assert.deepEqual(reconcileBasket(["1"], catalog).ids, []);
  assert.equal(addBasketActivity([], "1", catalog).ok, false);
});

test("accept only canonical public print PNGs, not previews or external/unsafe URLs", () => {
  const wrong = [
    "https://example.com/media/1/print.png",
    "//example.com/media/1/print.png",
    "/media/1/preview.webp",
    "/media/1/thumb.webp",
    "/media/2/print.png",
    "/media/1/../2/print.png",
    "/media/1/print.png?foo=bar",
    "/media/1/print.png#x",
    "/media/1/%70rint.png",
    "/media/1/print.jpg",
    "/originals/1/source.png",
  ];
  for (const print of wrong) {
    assert.deepEqual(reconcileBasket(["1"], [{ id: "1", title: "x", print }]).ids, [], print);
  }
  const ok = one("1");
  ok.print = "media/1/print-1.png";
  assert.equal(reconcileBasket(["1"], [ok]).sheetCount, 1);
});

test("malformed or partial pages arrays fail as a unit rather than top-level fallback", () => {
  const broken = [
    { ...multi("cut-1"), pages: [] },
    { ...multi("cut-1"), pages: [{ print: "/media/cut-1/print-1.png" }, {}] },
    { ...multi("cut-1"), pages: [{ print: "/media/cut-1/print-1.png" }, { print: "/media/2/print-2.png" }] },
    { ...multi("cut-1"), pages: [{ print: "/media/cut-1/print-1.png" }, { print: "/media/cut-1/print-1.png" }] },
    multi("cut-1", 13),
  ];
  for (const item of broken) {
    assert.deepEqual(reconcileBasket(["cut-1"], [item]).ids, []);
  }
});

test("failed catalogue load cannot silently clear a selection", () => {
  assert.throws(() => reconcileBasket(["1"], null), TypeError);
  assert.throws(() => reconcileBasket(null, [one("1")]), TypeError);
  assert.throws(() => addBasketActivity(["1"], "2", undefined), TypeError);
  assert.throws(() => expandBasketForExport([], [one("1")]));
});

test("the export expansion returns ordered URLs without mutating anything", () => {
  const catalog = [one("1"), multi("cut-1")];
  const input = Object.freeze(["cut-1", "1"]);
  const pages = expandBasketForExport(input, catalog);
  assert.equal(pages.length, 3);
  assert.deepEqual(pages.map((p) => p.activityId), ["cut-1", "cut-1", "1"]);
  assert.deepEqual(input, ["cut-1", "1"]);
});

test("relative print URLs normalize to site root without reordering pages", () => {
  const catalog = [
    { id: "legacy-42", title: "Einzelseite", print: "media/legacy-42/print.png" },
    {
      id: "cut-1", title: "Zweiteilig",
      pages: [
        { print: "media/cut-1/print-1.png" },
        { print: "/media/cut-1/print-2.png" },
      ],
    },
  ];
  const selection = reconcileBasket(["cut-1", "legacy-42"], catalog);
  assert.equal(selection.sheetCount, 3);
  assert.deepEqual(selection.pages.map((page) => page.printUrl), [
    "/media/cut-1/print-1.png",
    "/media/cut-1/print-2.png",
    "/media/legacy-42/print.png",
  ]);
  // The catalogue itself stays immutable and suitable for other clients.
  assert.equal(catalog[0].print, "media/legacy-42/print.png");
  assert.equal(catalog[1].pages[0].print, "media/cut-1/print-1.png");
});

test("same print PNG with slash and without slash rejects whole multi-page item", () => {
  const aliased = multi("cut-1");
  aliased.pages[0].print = "media/cut-1/print-1.png";
  aliased.pages[1].print = "/media/cut-1/print-1.png";
  assert.deepEqual(reconcileBasket(["cut-1"], [aliased]).ids, []);
  assert.equal(addBasketActivity([], "cut-1", [aliased]).reason, "unavailable");
  assert.throws(() => expandBasketForExport(["cut-1"], [aliased]));
});
