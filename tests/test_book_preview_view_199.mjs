import test from "node:test";
import assert from "node:assert/strict";
import { buildBookPreviewPlan } from "../js/book-preview-plan.mjs";
import {
  createBookPreviewCursor,
  setBookPreviewSheet,
} from "../js/book-preview-navigation.mjs";
import { buildBookPreviewView } from "../js/book-preview-view.mjs";

const one = (id) => ({ id, title: "Malvorlage", print: `/media/${id}/print.png` });
const cover = (changes = {}) => ({
  enabled: false,
  title: "Mein Ausmalbuch",
  name: "",
  ...changes,
});

test("active cover view keeps literal personal text only in cover content", () => {
  const plan = buildBookPreviewPlan(
    ["1"],
    [one("1")],
    cover({ enabled: true, title: "Mein Äpfelbuch", name: "Léa" }),
  );
  const view = buildBookPreviewView(plan, createBookPreviewCursor(plan));
  assert.deepEqual(view.content, {
    kind: "cover",
    title: "Mein Äpfelbuch",
    name: "Léa",
  });
  assert.equal(Object.hasOwn(view.content, "printUrl"), false);
  assert.equal(view.selectionText, "2 von 5 Druckseiten (1 Deckblatt + 1 Ausmalseiten)");
  assert.equal(view.pageText, "Seite 1 von 2");
});

test("artwork view exposes only canonical preview-plan page identity", () => {
  const plan = buildBookPreviewPlan(
    ["2", "1"],
    [one("1"), one("2")],
    cover(),
  );
  const view = buildBookPreviewView(plan, createBookPreviewCursor(plan));
  assert.deepEqual(view.content, {
    kind: "artwork",
    activityId: "2",
    pageIndex: 1,
    pageCount: 1,
    printUrl: "/media/2/print.png",
  });
  assert.equal(Object.hasOwn(view.content, "title"), false);
  assert.equal(Object.hasOwn(view.content, "name"), false);
});

test("navigation controls and page text come from current cursor", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2", "3"],
    [one("1"), one("2"), one("3")],
    cover(),
  );
  const view = buildBookPreviewView(plan, setBookPreviewSheet(plan, 2));
  assert.equal(view.pageText, "Seite 2 von 3");
  assert.deepEqual(view.previous, { label: "Zurück", disabled: false });
  assert.deepEqual(view.next, { label: "Weiter", disabled: false });
  assert.equal(view.content.printUrl, "/media/2/print.png");
});

test("disabled cover cannot leak dormant title or name into the view", () => {
  const plan = buildBookPreviewPlan(
    ["1"],
    [one("1")],
    cover({ title: "Privater Titel", name: "Mia" }),
  );
  const view = buildBookPreviewView(plan, createBookPreviewCursor(plan));
  const serialized = JSON.stringify(view);
  assert.equal(serialized.includes("Privater Titel"), false);
  assert.equal(serialized.includes("Mia"), false);
  assert.equal(view.content.kind, "artwork");
});

test("cursor item payload is ignored; active content is read from the plan", () => {
  const plan = buildBookPreviewPlan(["1"], [one("1")], cover());
  const cursor = {
    ...createBookPreviewCursor(plan),
    item: { kind: "cover", title: "Injected", name: "Injected" },
  };
  const view = buildBookPreviewView(plan, cursor);
  assert.equal(view.content.kind, "artwork");
  assert.equal(JSON.stringify(view).includes("Injected"), false);
});

test("view and all nested presentation objects are frozen snapshots", () => {
  const plan = buildBookPreviewPlan(["1"], [one("1")], cover());
  const view = buildBookPreviewView(plan, createBookPreviewCursor(plan));
  assert.equal(Object.isFrozen(view), true);
  assert.equal(Object.isFrozen(view.previous), true);
  assert.equal(Object.isFrozen(view.next), true);
  assert.equal(Object.isFrozen(view.content), true);
});

test("stale cursor and mismatched active item fail closed", () => {
  const plan = buildBookPreviewPlan(
    ["1", "2"],
    [one("1"), one("2")],
    cover(),
  );
  const first = createBookPreviewCursor(plan);
  assert.throws(
    () => buildBookPreviewView(plan, { ...first, sheetCount: 3 }),
    TypeError,
  );
  const badPlan = {
    ...plan,
    items: [
      { ...plan.items[0], sheetNumber: 2 },
      plan.items[1],
    ],
  };
  assert.throws(() => buildBookPreviewView(badPlan, first), TypeError);
});

test("malformed cover or artwork content cannot become render input", () => {
  const covered = buildBookPreviewPlan(
    ["1"],
    [one("1")],
    cover({ enabled: true }),
  );
  const coverCursor = createBookPreviewCursor(covered);
  assert.throws(
    () => buildBookPreviewView(
      { ...covered, items: [{ ...covered.items[0], title: 7 }, covered.items[1]] },
      coverCursor,
    ),
    TypeError,
  );

  const plain = buildBookPreviewPlan(["1"], [one("1")], cover());
  const plainCursor = createBookPreviewCursor(plain);
  assert.throws(
    () => buildBookPreviewView(
      { ...plain, items: [{ ...plain.items[0], printUrl: null }] },
      plainCursor,
    ),
    TypeError,
  );
});
