import test from "node:test";
import assert from "node:assert/strict";
import { buildBookPreviewPlan } from "../js/book-preview-plan.mjs";
import {
  createBookPreviewCursor,
  setBookPreviewSheet,
} from "../js/book-preview-navigation.mjs";
import { buildBookPreviewLabels } from "../js/book-preview-labels.mjs";

const one = (id) => ({ id, title: "Malvorlage", print: `/media/${id}/print.png` });
const cover = (changes = {}) => ({
  enabled: false,
  title: "Mein Ausmalbuch",
  name: "",
  ...changes,
});

test("coverless selection uses Druckseiten rather than Motive", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2", "3"],
    [one("1"), one("2"), one("3")],
    cover(),
  );
  const labels = buildBookPreviewLabels(plan, createBookPreviewCursor(plan));
  assert.equal(labels.selectionText, "3 von 5 Druckseiten");
  assert.equal(labels.selectionText.includes("Motive"), false);
});

test("covered selection reports Deckblatt plus Ausmalseiten explicitly", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2", "3"],
    [one("1"), one("2"), one("3")],
    cover({ enabled: true }),
  );
  const labels = buildBookPreviewLabels(plan, createBookPreviewCursor(plan));
  assert.equal(
    labels.selectionText,
    "4 von 5 Druckseiten (1 Deckblatt + 3 Ausmalseiten)",
  );
});

test("first sheet exposes Seite X von Y and disables Zurück only", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2"],
    [one("1"), one("2")],
    cover({ enabled: true }),
  );
  const labels = buildBookPreviewLabels(plan, createBookPreviewCursor(plan));
  assert.deepEqual(labels, {
    selectionText: "3 von 5 Druckseiten (1 Deckblatt + 2 Ausmalseiten)",
    pageText: "Seite 1 von 3",
    previousLabel: "Zurück",
    nextLabel: "Weiter",
    previousDisabled: true,
    nextDisabled: false,
  });
});

test("middle sheet keeps both navigation actions available", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2", "3"],
    [one("1"), one("2"), one("3")],
    cover(),
  );
  const labels = buildBookPreviewLabels(plan, setBookPreviewSheet(plan, 2));
  assert.equal(labels.pageText, "Seite 2 von 3");
  assert.equal(labels.previousDisabled, false);
  assert.equal(labels.nextDisabled, false);
});

test("last sheet disables Weiter only", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2"],
    [one("1"), one("2")],
    cover(),
  );
  const labels = buildBookPreviewLabels(plan, setBookPreviewSheet(plan, 2));
  assert.equal(labels.pageText, "Seite 2 von 2");
  assert.equal(labels.previousDisabled, false);
  assert.equal(labels.nextDisabled, true);
});

test("personal cover title and name never appear in label output", () => {
  const plan = buildBookPreviewPlan(
    ["1"],
    [one("1")],
    cover({ enabled: true, title: "Privates Buch", name: "Mia" }),
  );
  const labels = buildBookPreviewLabels(plan, createBookPreviewCursor(plan));
  const serialized = JSON.stringify(labels);
  assert.equal(serialized.includes("Privates Buch"), false);
  assert.equal(serialized.includes("Mia"), false);
});

test("labels are a frozen presentation snapshot", () => {
  const plan = buildBookPreviewPlan(["1"], [one("1")], cover());
  const labels = buildBookPreviewLabels(plan, createBookPreviewCursor(plan));
  assert.equal(Object.isFrozen(labels), true);
});

test("stale or internally inconsistent plan/cursor state fails closed", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2"],
    [one("1"), one("2")],
    cover(),
  );
  const cursor = createBookPreviewCursor(plan);

  assert.throws(
    () => buildBookPreviewLabels(
      { ...plan, sheetCount: 3 },
      cursor,
    ),
    TypeError,
  );
  assert.throws(
    () => buildBookPreviewLabels(
      plan,
      { ...cursor, hasNext: false },
    ),
    TypeError,
  );
  assert.throws(
    () => buildBookPreviewLabels(plan, null),
    TypeError,
  );
});
