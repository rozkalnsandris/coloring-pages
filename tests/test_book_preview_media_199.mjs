import test from "node:test";
import assert from "node:assert/strict";
import { buildBookPreviewPlan } from "../js/book-preview-plan.mjs";
import {
  createBookPreviewCursor,
  setBookPreviewSheet,
} from "../js/book-preview-navigation.mjs";
import { buildBookPreviewDisplay } from "../js/book-preview-media.mjs";

const single = (id) => ({
  id,
  title: "Malvorlage",
  thumb: `media/${id}/thumb.webp`,
  preview: `media/${id}/preview.webp`,
  print: `media/${id}/print.png`,
});
const multi = (id) => ({
  id,
  title: "Bastelvorlage",
  thumb: `media/${id}/thumb.webp`,
  pages: [
    {
      preview: `media/${id}/preview-1.webp`,
      print: `media/${id}/print-1.png`,
    },
    {
      preview: `media/${id}/preview-2.webp`,
      print: `media/${id}/print-2.png`,
    },
  ],
});
const cover = (changes = {}) => ({
  enabled: false,
  title: "Mein Ausmalbuch",
  name: "",
  ...changes,
});

test("single-page artwork resolves watermarked preview rather than print master", () => {
  const catalog = [single("0000001")];
  const plan = buildBookPreviewPlan(["0000001"], catalog, cover());
  const display = buildBookPreviewDisplay(
    plan,
    createBookPreviewCursor(plan),
    catalog,
  );
  assert.deepEqual(display.content, {
    kind: "artwork",
    activityId: "0000001",
    pageIndex: 1,
    pageCount: 1,
    previewUrl: "/media/0000001/preview.webp",
  });
  assert.equal(Object.hasOwn(display.content, "printUrl"), false);
});

test("multipage preview follows selected internal page index", () => {
  const catalog = [multi("cut-1")];
  const plan = buildBookPreviewPlan(["cut-1"], catalog, cover());
  const display = buildBookPreviewDisplay(
    plan,
    setBookPreviewSheet(plan, 2),
    catalog,
  );
  assert.equal(display.content.previewUrl, "/media/cut-1/preview-2.webp");
  assert.equal(display.content.pageIndex, 2);
  assert.equal(display.content.pageCount, 2);
});

test("covered first sheet needs no catalogue preview media", () => {
  const catalog = [single("0000001"), single("0000002")];
  const plan = buildBookPreviewPlan(
    ["0000001", "0000002"],
    catalog,
    cover({ enabled: true, title: "Mein Tierbuch", name: "Mia" }),
  );
  const display = buildBookPreviewDisplay(
    plan,
    createBookPreviewCursor(plan),
    catalog,
  );
  assert.deepEqual(display.content, {
    kind: "cover",
    title: "Mein Tierbuch",
    name: "Mia",
  });
  assert.equal(JSON.stringify(display).includes("preview.webp"), false);
});

test("catalogue reorder does not affect preview identity", () => {
  const first = single("0000001");
  const second = single("0000002");
  const plan = buildBookPreviewPlan(
    ["0000002", "0000001"],
    [first, second],
    cover(),
  );
  const display = buildBookPreviewDisplay(
    plan,
    createBookPreviewCursor(plan),
    [second, first],
  );
  assert.equal(display.content.activityId, "0000002");
  assert.equal(display.content.previewUrl, "/media/0000002/preview.webp");
});

test("duplicate catalogue IDs fail closed", () => {
  const entry = single("0000001");
  const plan = buildBookPreviewPlan(["0000001"], [entry], cover());
  assert.throws(
    () => buildBookPreviewDisplay(
      plan,
      createBookPreviewCursor(plan),
      [entry, { ...entry }],
    ),
    /missing or ambiguous/,
  );
});

test("preview must remain scoped to the selected activity", () => {
  const catalog = [single("0000001")];
  const plan = buildBookPreviewPlan(["0000001"], catalog, cover());
  const drifted = [{
    ...catalog[0],
    preview: "media/0000002/preview.webp",
  }];
  assert.throws(
    () => buildBookPreviewDisplay(plan, createBookPreviewCursor(plan), drifted),
    /single-page preview media is invalid/,
  );
});

test("print drift blocks pairing a stale plan with a fresh preview", () => {
  const catalog = [single("0000001")];
  const plan = buildBookPreviewPlan(["0000001"], catalog, cover());
  const drifted = [{
    ...catalog[0],
    print: "media/0000001/print-repaired.png",
  }];
  assert.throws(
    () => buildBookPreviewDisplay(plan, createBookPreviewCursor(plan), drifted),
    /no longer matches/,
  );
});

test("multipage preview numbering and completeness are enforced atomically", () => {
  const catalog = [multi("cut-1")];
  const plan = buildBookPreviewPlan(["cut-1"], catalog, cover());
  const wrongNumber = [{
    ...catalog[0],
    pages: [
      catalog[0].pages[0],
      { ...catalog[0].pages[1], preview: "media/cut-1/preview-3.webp" },
    ],
  }];
  assert.throws(
    () => buildBookPreviewDisplay(plan, setBookPreviewSheet(plan, 2), wrongNumber),
    /multipage preview media is invalid/,
  );
  const missingPage = [{ ...catalog[0], pages: [catalog[0].pages[0]] }];
  assert.throws(
    () => buildBookPreviewDisplay(plan, createBookPreviewCursor(plan), missingPage),
    /page count changed/,
  );
});

test("display snapshot and content remain frozen", () => {
  const catalog = [single("0000001")];
  const plan = buildBookPreviewPlan(["0000001"], catalog, cover());
  const display = buildBookPreviewDisplay(
    plan,
    createBookPreviewCursor(plan),
    catalog,
  );
  assert.equal(Object.isFrozen(display), true);
  assert.equal(Object.isFrozen(display.content), true);
  assert.equal(Object.isFrozen(display.previous), true);
  assert.equal(Object.isFrozen(display.next), true);
});
