import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  BASKET_PRINT_ACTIVE_CLASS,
  BASKET_PRINT_MOUNT_CLASS,
  printStagedDocumentInBasketHost,
} from "../js/print-basket-print-host.mjs";

function stage() {
  let disposed = false;
  let disposeCalls = 0;
  return {
    get disposed() { return disposed; },
    get disposeCalls() { return disposeCalls; },
    dispose() {
      disposeCalls++;
      disposed = true;
    },
  };
}

function browser() {
  const classes = new Set();
  const children = [];
  const body = {
    classList: {
      add(value) { classes.add(value); },
      remove(value) { classes.delete(value); },
      contains(value) { return classes.has(value); },
    },
    append(node) {
      children.push(node);
      node.isConnected = true;
      node.parentNode = body;
      node.parentElement = body;
    },
  };
  const documentRef = {
    body,
    createElement(tag) {
      assert.equal(tag, "section");
      return {
        className: "",
        dataset: {},
        attributes: {},
        children: [],
        isConnected: false,
        parentNode: null,
        parentElement: null,
        get childElementCount() { return this.children.length; },
        setAttribute(key, value) { this.attributes[key] = value; },
        remove() {
          const index = children.indexOf(this);
          if (index >= 0) children.splice(index, 1);
          this.isConnected = false;
          this.parentNode = null;
          this.parentElement = null;
        },
      };
    },
  };
  return { documentRef, body, children, classes };
}

test("host exposes only the isolated mount while delegated blocking print runs", () => {
  const doc = stage();
  const ui = browser();
  let lifecycleCalls = 0;
  const result = printStagedDocumentInBasketHost(doc, {
    documentRef: ui.documentRef,
    print() {},
    lifecycle(staged, { mount, print, signal }) {
      lifecycleCalls++;
      assert.strictEqual(staged, doc);
      assert.equal(signal, undefined);
      assert.equal(ui.body.classList.contains(BASKET_PRINT_ACTIVE_CLASS), true);
      assert.equal(ui.children.length, 1);
      assert.strictEqual(ui.children[0], mount);
      assert.equal(mount.className, BASKET_PRINT_MOUNT_CLASS);
      assert.equal(mount.dataset.basketPrintMount, "");
      assert.equal(mount.attributes["aria-hidden"], "true");
      assert.equal(mount.isConnected, true);
      print();
      staged.dispose();
      return Object.freeze({ sheetCount: 2, orientations: Object.freeze(["portrait", "landscape"]) });
    },
  });

  assert.equal(lifecycleCalls, 1);
  assert.deepEqual(result, { sheetCount: 2, orientations: ["portrait", "landscape"] });
  assert.equal(ui.body.classList.contains(BASKET_PRINT_ACTIVE_CLASS), false);
  assert.equal(ui.children.length, 0);
  assert.equal(doc.disposed, true);
  assert.equal(doc.disposeCalls, 1);
});

test("host setup failure disposes a staged document before lifecycle ownership", () => {
  const doc = stage();
  const ui = browser();
  ui.documentRef.createElement = () => ({});
  let lifecycleCalls = 0;
  assert.throws(
    () => printStagedDocumentInBasketHost(doc, {
      documentRef: ui.documentRef,
      print() {},
      lifecycle() { lifecycleCalls++; },
    }),
    /mount unavailable/,
  );
  assert.equal(lifecycleCalls, 0);
  assert.equal(doc.disposed, true);
  assert.equal(doc.disposeCalls, 1);
  assert.equal(ui.body.classList.contains(BASKET_PRINT_ACTIVE_CLASS), false);
});

test("abort before host activation disposes stage without appending or printing", () => {
  const doc = stage();
  const ui = browser();
  let prints = 0;
  assert.throws(
    () => printStagedDocumentInBasketHost(doc, {
      documentRef: ui.documentRef,
      signal: AbortSignal.abort(),
      print() { prints++; },
    }),
    /aborted/,
  );
  assert.equal(prints, 0);
  assert.equal(ui.children.length, 0);
  assert.equal(doc.disposeCalls, 1);
});

test("delegated lifecycle failure still removes body class and mount without double-dispose", () => {
  const doc = stage();
  const ui = browser();
  assert.throws(
    () => printStagedDocumentInBasketHost(doc, {
      documentRef: ui.documentRef,
      print() {},
      lifecycle(staged) {
        staged.dispose();
        throw new Error("print dialog failed");
      },
    }),
    /print dialog failed/,
  );
  assert.equal(ui.body.classList.contains(BASKET_PRINT_ACTIVE_CLASS), false);
  assert.equal(ui.children.length, 0);
  assert.equal(doc.disposeCalls, 1);
});

test("host module has no network, storage, timer, popup or afterprint dependency", () => {
  const code = readFileSync(
    new URL("../js/print-basket-print-host.mjs", import.meta.url),
    "utf8",
  ).split("\n").filter(line => !line.trimStart().startsWith("//")).join("\n");
  for (const forbidden of [
    "fetch(", "sessionStorage", "localStorage", "sendBeacon(", "analytics",
    "window.open(", "setTimeout(", ".click()", "afterprint",
    "beforeprint", "createObjectURL",
  ]) {
    assert.equal(code.includes(forbidden), false, forbidden);
  }
});


test("print-basket CSS isolates only the staged mount during active print media", () => {
  const css = readFileSync(
    new URL("../css/print-basket.css", import.meta.url),
    "utf8",
  );
  for (const required of [
    ".basket-print-mount { display: none; }",
    "@media print",
    "body.basket-print-active > *:not([data-basket-print-mount])",
    "display: none !important;",
    "body.basket-print-active > [data-basket-print-mount]",
    "display: block !important;",
  ]) {
    assert.equal(css.includes(required), true, required);
  }
  assert.equal(css.includes("page-orientation:"), false);
});
