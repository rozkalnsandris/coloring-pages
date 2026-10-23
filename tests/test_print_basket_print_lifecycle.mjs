import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { printStagedBasketDocumentOnce } from "../js/print-basket-print-lifecycle.mjs";

function makeElement(className) {
  return { className, isConnected: false, parentNode: null, parentElement: null };
}

function staged(orientations = ["portrait", "landscape", "portrait"]) {
  const pages = orientations.map((orientation, index) => Object.freeze({
    activityId: "activity-" + index,
    pageIndex: 1,
    pageCount: 1,
    printUrl: "/media/" + index + "/print.png",
  }));
  const sheets = orientations.map((orientation, index) => ({
    page: pages[index],
    orientation,
    element: makeElement("print-sheet is-" + orientation + " has-text-footer"),
  }));
  let disposed = false, disposeCalls = 0;
  return {
    plan: { pages, sheetCount: sheets.length },
    sheets,
    get disposed() { return disposed; },
    get disposeCalls() { return disposeCalls; },
    dispose() {
      disposeCalls++;
      if (disposed) return;
      disposed = true;
    },
  };
}

function mount() {
  return {
    isConnected: true,
    children: [],
    get childElementCount() { return this.children.length; },
    replaceChildren(...items) {
      for (const old of this.children) {
        old.isConnected = false;
        old.parentNode = null;
        old.parentElement = null;
      }
      this.children = items;
      for (const item of items) {
        item.isConnected = true;
        item.parentNode = this;
        item.parentElement = this;
      }
    },
  };
}

test("one lifecycle call mounts ordered sheets, prints once, then releases everything", () => {
  const doc = staged(), host = mount();
  let calls = 0;
  const result = printStagedBasketDocumentOnce(doc, {
    mount: host,
    print() {
      calls++;
      assert.equal(host.childElementCount, 3);
      assert.equal(doc.disposed, false);
      assert.deepEqual(host.children.map(x => x.className), [
        "print-sheet is-portrait has-text-footer",
        "print-sheet is-landscape has-text-footer",
        "print-sheet is-portrait has-text-footer",
      ]);
    },
  });
  assert.equal(calls, 1);
  assert.deepEqual(result, { sheetCount: 3, orientations: ["portrait", "landscape", "portrait"] });
  assert.equal(Object.isFrozen(result), true);
  assert.equal(Object.isFrozen(result.orientations), true);
  assert.equal(host.childElementCount, 0);
  assert.equal(doc.disposed, true);
  assert.equal(doc.disposeCalls, 1);
});

test("print failure still empties the mount and disposes the native stage once", () => {
  const doc = staged(["portrait"]), host = mount();
  assert.throws(() => printStagedBasketDocumentOnce(doc, {
    mount: host, print() { throw new Error("dialog unavailable"); },
  }), /dialog unavailable/);
  assert.equal(host.childElementCount, 0);
  assert.equal(doc.disposed, true);
  assert.equal(doc.disposeCalls, 1);
});

test("abort before the dialog prevents print and releases a valid stage", () => {
  const doc = staged(["portrait", "landscape"]), host = mount();
  let calls = 0;
  assert.throws(() => printStagedBasketDocumentOnce(doc, {
    mount: host, print() { calls++; }, signal: AbortSignal.abort(),
  }), /aborted/);
  assert.equal(calls, 0);
  assert.equal(host.childElementCount, 0);
  assert.equal(doc.disposeCalls, 1);
});

test("bad mount or missing print capability fails closed after stage ownership", () => {
  for (const options of [
    { mount: { isConnected: false, childElementCount: 0, replaceChildren() {} }, print() {} },
    { mount: mount(), print: null },
  ]) {
    const doc = staged(["portrait"]);
    assert.throws(() => printStagedBasketDocumentOnce(doc, options));
    assert.equal(doc.disposeCalls, 1);
  }
});

test("invalid connected repeated or reordered sheets never invoke print", () => {
  const mutators = [
    d => { d.plan.sheetCount = 0; },
    d => { d.sheets[0].element.isConnected = true; },
    d => { d.sheets[1].element = d.sheets[0].element; },
    d => { d.sheets[1].page = d.plan.pages[0]; },
    d => { d.sheets[0].orientation = "sideways"; },
    d => { d.sheets[0].element.className = "print-sheet"; },
    d => { d.plan.pages[1] = { ...d.plan.pages[1], printUrl: d.plan.pages[0].printUrl }; },
  ];
  for (const mutate of mutators) {
    const doc = staged(["portrait", "landscape"]);
    mutate(doc);
    let calls = 0;
    assert.throws(() => printStagedBasketDocumentOnce(doc, {
      mount: mount(), print() { calls++; },
    }));
    assert.equal(calls, 0);
  }
});

test("a disposed document cannot be printed twice", () => {
  const doc = staged(["portrait"]);
  printStagedBasketDocumentOnce(doc, { mount: mount(), print() {} });
  assert.throws(() => printStagedBasketDocumentOnce(doc, {
    mount: mount(), print() { throw new Error("must not run"); },
  }), /undisposed/);
  assert.equal(doc.disposeCalls, 1);
});

test("lifecycle helper has no network storage navigation timer or analytics path", () => {
  const code = readFileSync(
    new URL("../js/print-basket-print-lifecycle.mjs", import.meta.url), "utf8",
  ).split("\n").filter(line => !line.trimStart().startsWith("//")).join("\n");
  for (const forbidden of [
    "fetch(", "sessionStorage", "localStorage", "sendBeacon(", "analytics",
    "window.open(", "createObjectURL", "toBlob(", "toDataURL(", ".click()",
    "setTimeout(", "afterprint",
  ]) assert.equal(code.includes(forbidden), false, forbidden);
});
