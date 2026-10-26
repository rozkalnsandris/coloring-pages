import test from "node:test";
import assert from "node:assert/strict";
import { planBookSheetCapacity } from "../js/book-cover-capacity.mjs";

const single = (id) => ({
  id, title: "Blume", print: `/media/${id}/print.png`,
});
const double = (id) => ({
  id, title: "Cut & Paste", pages: [
    { print: `/media/${id}/print-1.png` },
    { print: `/media/${id}/print-2.png` },
  ],
});

test("coverless empty book counts zero without inventing any print assets", () => {
  const result = planBookSheetCapacity([], []);
  assert.deepEqual(result, {
    activityCount: 0, artworkSheetCount: 0, coverSheetCount: 0,
    totalSheetCount: 0, remainingSheetSlots: 5, maxSheetCount: 5,
  });
  assert.equal(Object.isFrozen(result), true);
});

test("one optional cover occupies exactly one of five physical A4 sheets", () => {
  const catalog = [single("0000001"), single("0000002"), single("0000003"), single("0000004")];
  const ids = Object.freeze(["0000001", "0000002", "0000003", "0000004"]);
  const covered = planBookSheetCapacity(ids, catalog, { coverEnabled: true });
  assert.deepEqual(covered, {
    activityCount: 4, artworkSheetCount: 4, coverSheetCount: 1,
    totalSheetCount: 5, remainingSheetSlots: 0, maxSheetCount: 5,
  });
  assert.deepEqual(ids, ["0000001", "0000002", "0000003", "0000004"]);
  assert.deepEqual(planBookSheetCapacity(ids, catalog).totalSheetCount, 4);
});

test("whole two-page Cut & Paste activity counts two in the same ordered selection", () => {
  const catalog = [double("cut-1"), single("1"), single("2")];
  const plan = planBookSheetCapacity(["cut-1", "1", "2"], catalog, { coverEnabled: true });
  assert.equal(plan.activityCount, 3);
  assert.equal(plan.artworkSheetCount, 4);
  assert.equal(plan.coverSheetCount, 1);
  assert.equal(plan.totalSheetCount, 5);
  assert.equal(plan.remainingSheetSlots, 0);
});

test("fifth artwork sheet remains valid uncovered but cannot acquire a cover", () => {
  const catalog = [double("cut-1"), single("1"), single("2"), single("3")];
  const ids = Object.freeze(["cut-1", "1", "2", "3"]);
  const uncovered = planBookSheetCapacity(ids, catalog);
  assert.equal(uncovered.totalSheetCount, 5);
  assert.throws(
    () => planBookSheetCapacity(ids, catalog, { coverEnabled: true }),
    RangeError,
  );
  assert.deepEqual(ids, ["cut-1", "1", "2", "3"], "rejection must not evict an activity");
  assert.equal(planBookSheetCapacity(ids, catalog).totalSheetCount, 5);
});

test("a cover cannot become an otherwise empty printable book", () => {
  assert.throws(() => planBookSheetCapacity([], [], { coverEnabled: true }), RangeError);
  assert.throws(() => planBookSheetCapacity([], [], { coverEnabled: "true" }), TypeError);
  assert.throws(() => planBookSheetCapacity([], [], { coverEnabled: 1 }), TypeError);
});

test("withdrawn, repeated and over-limit activity IDs reject without truncating pages", () => {
  const catalog = [double("cut-1"), single("1"), single("2"), single("3"), single("4")];
  for (const ids of [
    ["cut-1", "gone"],
    ["1", "1"],
    ["cut-1", "1", "2", "3", "4"],
  ]) {
    assert.throws(() => planBookSheetCapacity(ids, catalog));
  }
  assert.throws(() => planBookSheetCapacity(["1"], [single("1"), single("1")]));
});

test("malformed public PNG/catalogue data is never treated as a valid book page", () => {
  const broken = {
    ...double("cut-1"),
    pages: [{ print: "/media/cut-1/print-1.png" }, { print: "/media/cut-1/preview.webp" }],
  };
  assert.throws(() => planBookSheetCapacity(["cut-1"], [broken]));
  assert.throws(() => planBookSheetCapacity(["1"], null), TypeError);
  assert.throws(() => planBookSheetCapacity(null, [single("1")]), TypeError);
});
