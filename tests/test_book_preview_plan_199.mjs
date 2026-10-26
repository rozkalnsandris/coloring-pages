import test from "node:test";
import assert from "node:assert/strict";
import { buildBookPreviewPlan } from "../js/book-preview-plan.mjs";

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

test("coverless preview preserves canonical #206 artwork order", () => {
  const catalog = [one("1"), one("2")];
  const plan = buildBookPreviewPlan(["2", "1"], catalog, cover());
  assert.equal(plan.coverEnabled, false);
  assert.equal(plan.activityCount, 2);
  assert.equal(plan.artworkSheetCount, 2);
  assert.equal(plan.sheetCount, 2);
  assert.deepEqual(plan.items.map((item) => item.printUrl), [
    "/media/2/print.png",
    "/media/1/print.png",
  ]);
  assert.deepEqual(plan.items.map((item) => item.sheetNumber), [1, 2]);
});

test("enabled cover is exactly first and consumes one of five sheets", () => {
  const catalog = [one("1"), one("2"), one("3")];
  const plan = buildBookPreviewPlan(
    ["1", "2", "3"],
    catalog,
    cover({ enabled: true, title: "Mein Äpfelbuch", name: "Léa" }),
  );
  assert.equal(plan.sheetCount, 4);
  assert.deepEqual(plan.items[0], {
    kind: "cover",
    sheetNumber: 1,
    sheetCount: 4,
    title: "Mein Äpfelbuch",
    name: "Léa",
  });
  assert.deepEqual(plan.items.slice(1).map((item) => item.sheetNumber), [2, 3, 4]);
});

test("disabled cover does not expose dormant title or name in preview output", () => {
  const plan = buildBookPreviewPlan(
    ["1"],
    [one("1")],
    cover({ title: "Privater Titel", name: "Mia" }),
  );
  assert.equal(JSON.stringify(plan).includes("Privater Titel"), false);
  assert.equal(JSON.stringify(plan).includes("Mia"), false);
  assert.equal(plan.items[0].kind, "artwork");
});

test("multi-page activity stays atomic and internally ordered after cover", () => {
  const catalog = [multi("cut-1"), one("2")];
  const plan = buildBookPreviewPlan(
    ["cut-1", "2"],
    catalog,
    cover({ enabled: true }),
  );
  assert.deepEqual(plan.items.map((item) => item.kind), [
    "cover", "artwork", "artwork", "artwork",
  ]);
  assert.deepEqual(
    plan.items.filter((item) => item.kind === "artwork").map((item) => [
      item.activityId, item.pageIndex, item.pageCount, item.printUrl,
    ]),
    [
      ["cut-1", 1, 2, "/media/cut-1/print-1.png"],
      ["cut-1", 2, 2, "/media/cut-1/print-2.png"],
      ["2", 1, 1, "/media/2/print.png"],
    ],
  );
});

test("full five-artwork-sheet selection rejects an added cover", () => {
  const catalog = [multi("cut-1"), one("1"), one("2"), one("3")];
  assert.throws(
    () => buildBookPreviewPlan(
      ["cut-1", "1", "2", "3"],
      catalog,
      cover({ enabled: true }),
    ),
    RangeError,
  );
});

test("empty, stale, duplicated or malformed selections fail closed", () => {
  assert.throws(() => buildBookPreviewPlan([], [], cover()));
  assert.throws(() => buildBookPreviewPlan(["gone"], [one("1")], cover()));
  assert.throws(() => buildBookPreviewPlan(["1", "1"], [one("1")], cover()));
  assert.throws(() => buildBookPreviewPlan(["1"], [one("1"), one("1")], cover()));
});

test("preview result and every item are frozen snapshots", () => {
  const plan = buildBookPreviewPlan(
    ["1"],
    [one("1")],
    cover({ enabled: true }),
  );
  assert.equal(Object.isFrozen(plan), true);
  assert.equal(Object.isFrozen(plan.items), true);
  assert.equal(plan.items.every(Object.isFrozen), true);
});

test("invalid cover state types cannot invent preview state", () => {
  for (const state of [
    null,
    [],
    {},
    { enabled: "true", title: "x", name: "" },
    { enabled: false, title: 7, name: "" },
    { enabled: false, title: "x", name: null },
  ]) {
    assert.throws(() => buildBookPreviewPlan(["1"], [one("1")], state), TypeError);
  }
});
