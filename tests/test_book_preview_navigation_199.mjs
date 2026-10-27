import test from "node:test";
import assert from "node:assert/strict";
import { buildBookPreviewPlan } from "../js/book-preview-plan.mjs";
import {
  createBookPreviewCursor,
  setBookPreviewSheet,
  moveBookPreviewCursor,
} from "../js/book-preview-navigation.mjs";

const one = (id) => ({ id, title: "Malvorlage", print: `/media/${id}/print.png` });
const multi = (id) => ({
  id, title: "Ausschneiden und kleben",
  pages: [
    { print: `/media/${id}/print-1.png` },
    { print: `/media/${id}/print-2.png` },
  ],
});
const cover = (changes = {}) => ({
  enabled: false,
  title: "Mein Ausmalbuch",
  name: "",
  ...changes,
});

test("covered preview starts on the cover with only Weiter available", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2"],
    [one("1"), one("2")],
    cover({ enabled: true, title: "Mein Tierbuch", name: "Mia" }),
  );
  const cursor = createBookPreviewCursor(plan);
  assert.equal(cursor.sheetNumber, 1);
  assert.equal(cursor.sheetCount, 3);
  assert.equal(cursor.hasPrevious, false);
  assert.equal(cursor.hasNext, true);
  assert.deepEqual(cursor.item, {
    kind: "cover", sheetNumber: 1, sheetCount: 3,
    title: "Mein Tierbuch", name: "Mia",
  });
});

test("coverless preview starts on the first canonical artwork sheet", () => {
  const plan = buildBookPreviewPlan(
    ["2", "1"],
    [one("1"), one("2")],
    cover(),
  );
  const cursor = createBookPreviewCursor(plan);
  assert.equal(cursor.item.kind, "artwork");
  assert.equal(cursor.item.printUrl, "/media/2/print.png");
  assert.equal(cursor.sheetNumber, 1);
  assert.equal(cursor.sheetCount, 2);
});

test("Weiter and Zurück traverse multipage activity order without skipping", () => {
  const plan = buildBookPreviewPlan(
    ["cut-1", "2"],
    [multi("cut-1"), one("2")],
    cover({ enabled: true }),
  );
  const first = createBookPreviewCursor(plan);
  const second = moveBookPreviewCursor(plan, first, 1);
  const third = moveBookPreviewCursor(plan, second, 1);
  const fourth = moveBookPreviewCursor(plan, third, 1);

  assert.equal(first.item.kind, "cover");
  assert.deepEqual(
    [second.item.printUrl, third.item.printUrl, fourth.item.printUrl],
    [
      "/media/cut-1/print-1.png",
      "/media/cut-1/print-2.png",
      "/media/2/print.png",
    ],
  );
  assert.deepEqual([second.item.pageIndex, third.item.pageIndex], [1, 2]);

  const back = moveBookPreviewCursor(plan, fourth, -1);
  assert.equal(back.sheetNumber, 3);
  assert.equal(back.item.printUrl, "/media/cut-1/print-2.png");
});

test("navigation clamps at first and last sheet instead of wrapping", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2"],
    [one("1"), one("2")],
    cover(),
  );
  const first = createBookPreviewCursor(plan);
  const stillFirst = moveBookPreviewCursor(plan, first, -1);
  assert.equal(stillFirst.sheetNumber, 1);
  assert.equal(stillFirst.hasPrevious, false);

  const last = setBookPreviewSheet(plan, 2);
  const stillLast = moveBookPreviewCursor(plan, last, 1);
  assert.equal(stillLast.sheetNumber, 2);
  assert.equal(stillLast.hasNext, false);
});

test("direct sheet selection exposes consistent button bounds", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2", "3"],
    [one("1"), one("2"), one("3")],
    cover(),
  );
  const middle = setBookPreviewSheet(plan, 2);
  assert.deepEqual(
    {
      sheetNumber: middle.sheetNumber,
      sheetCount: middle.sheetCount,
      hasPrevious: middle.hasPrevious,
      hasNext: middle.hasNext,
    },
    { sheetNumber: 2, sheetCount: 3, hasPrevious: true, hasNext: true },
  );
});

test("cursor snapshots and active items are frozen", () => {
  const plan = buildBookPreviewPlan(["1"], [one("1")], cover());
  const cursor = createBookPreviewCursor(plan);
  assert.equal(Object.isFrozen(cursor), true);
  assert.equal(Object.isFrozen(cursor.item), true);
});

test("stale cursor from another sheet count fails closed", () => {
  const two = buildBookPreviewPlan(
    ["1", "2"],
    [one("1"), one("2")],
    cover(),
  );
  const three = buildBookPreviewPlan(
    ["1", "2", "3"],
    [one("1"), one("2"), one("3")],
    cover(),
  );
  const cursor = createBookPreviewCursor(two);
  assert.throws(() => moveBookPreviewCursor(three, cursor, 1), TypeError);
});

test("invalid plan, sheet and direction inputs cannot invent navigation state", () => {
  assert.throws(() => createBookPreviewCursor(null), TypeError);
  assert.throws(() => createBookPreviewCursor({ sheetCount: 1, items: [] }), TypeError);

  const plan = buildBookPreviewPlan(["1"], [one("1")], cover());
  for (const sheet of [0, 2, 1.5, "1"]) {
    assert.throws(() => setBookPreviewSheet(plan, sheet), RangeError);
  }
  const cursor = createBookPreviewCursor(plan);
  for (const direction of [0, 2, -2, "1"]) {
    assert.throws(() => moveBookPreviewCursor(plan, cursor, direction), RangeError);
  }
});
