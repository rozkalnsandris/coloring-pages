import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stageBasketPrintTextFooters } from "../js/print-basket-print-footer.mjs";

function fakeDocument({ failAttachAt = 0, abortOnAttach } = {}) {
  let attachments = 0;
  function createElement(tag) {
    return {
      tag, className: "", children: [], parent: null, attrs: {}, textContent: "",
      setAttribute(key, value) { this.attrs[key] = value; },
      append(...children) {
        for (const child of children) {
          this.children.push(child);
          child.parent = this;
        }
        if (tag === "section") {
          attachments++;
          if (abortOnAttach) abortOnAttach(attachments);
          if (failAttachAt === attachments) throw new Error("section attach failed");
        }
      },
      remove() {
        if (!this.parent) return;
        const siblings = this.parent.children;
        siblings.splice(siblings.indexOf(this), 1);
        this.parent = null;
      },
    };
  }
  return {
    documentRef: { createElement }, createElement,
    get attachments() { return attachments; },
  };
}

function makeStaged(doc, orientations = ["portrait", "landscape", "portrait"]) {
  const pages = orientations.map((orientation, i) => ({
    printUrl: "/media/" + (i + 1) + "/print.png",
    orientation,
  }));
  const sheets = orientations.map((orientation, i) => {
    const element = doc.createElement("section");
    element.className = "print-sheet is-" + orientation;
    const artwork = doc.createElement("div");
    artwork.className = "print-artwork";
    element.children.push(artwork);
    artwork.parent = element;
    return { element, page: pages[i], orientation };
  });
  let disposed = false, calls = 0;
  return {
    plan: { pages, sheetCount: pages.length }, sheets,
    get disposed() { return disposed; },
    get disposeCalls() { return calls; },
    dispose() { calls++; disposed = true; },
  };
}

function descendants(root, tag) {
  const all = [];
  const visit = node => {
    if (node.tag === tag) all.push(node);
    for (const child of node.children) visit(child);
  };
  visit(root);
  return all;
}

test("three mixed-orientation detached sheets receive matching CSS text branding", () => {
  const dom = fakeDocument();
  const stage = makeStaged(dom);
  const originalArtworks = stage.sheets.map(s => s.element.children[0]);
  const result = stageBasketPrintTextFooters(stage, { documentRef: dom.documentRef });
  assert.strictEqual(result.plan, stage.plan);
  assert.strictEqual(result.sheets, stage.sheets);
  assert.deepEqual(result.sheets.map(s => s.orientation), ["portrait", "landscape", "portrait"]);
  assert.equal(dom.attachments, 3);
  for (let i = 0; i < 3; i++) {
    const section = stage.sheets[i].element;
    assert.strictEqual(section.children[0], originalArtworks[i]);
    assert.equal(section.className, "print-sheet is-" + stage.sheets[i].orientation + " has-text-footer");
    const footer = section.children[1];
    assert.equal(footer.className, "print-branding text-only");
    assert.equal(footer.attrs["aria-label"], "Ausmalwiese – Malspaß zum Ausdrucken");
    assert.equal(descendants(footer, "i").length, 5);
    assert.equal(descendants(footer, "b").map(x => x.textContent).join(""), "wiese");
    assert.deepEqual(descendants(footer, "strong").map(x => x.textContent), ["auf ausmalwiese.de"]);
    assert.equal(descendants(footer, "img").length, 0);
  }
  assert.equal(stage.disposed, false);
  result.dispose();
  assert.equal(result.disposed, true);
  assert.equal(stage.disposeCalls, 1);
  for (const sheet of stage.sheets) {
    assert.equal(sheet.element.children.length, 1);
    assert.equal(sheet.element.className, "print-sheet is-" + sheet.orientation);
  }
  result.dispose();
  assert.equal(stage.disposeCalls, 1);
});

test("changed order, invalid orientation and attached DOM release without drawing", () => {
  for (const mutate of [
    stage => { stage.sheets[1].page = stage.plan.pages[0]; },
    stage => { stage.sheets[0].orientation = "sideways"; },
    stage => { stage.sheets[0].element.className += " has-text-footer"; },
    stage => { stage.sheets[1].element.isConnected = true; },
    stage => { stage.plan.sheetCount = 6; },
  ]) {
    const dom = fakeDocument();
    const stage = makeStaged(dom);
    mutate(stage);
    assert.throws(() => stageBasketPrintTextFooters(stage, { documentRef: dom.documentRef }));
    assert.equal(dom.attachments, 0);
    assert.equal(stage.disposeCalls, 1);
    assert.ok(stage.sheets.every(s => s.element.children.length === 1));
  }
});

test("failed attachment removes all branding and releases stage once", () => {
  const dom = fakeDocument({ failAttachAt: 2 });
  const stage = makeStaged(dom);
  assert.throws(() => stageBasketPrintTextFooters(stage, { documentRef: dom.documentRef }), /attach failed/);
  assert.equal(dom.attachments, 2);
  assert.equal(stage.disposeCalls, 1);
  assert.ok(stage.sheets.every(s => s.element.children.length === 1));
  assert.ok(stage.sheets.every(s => s.element.className === "print-sheet is-" + s.orientation));
});

test("abort during attachment rolls back all footer nodes", () => {
  const controller = new AbortController();
  const dom = fakeDocument({ abortOnAttach(i) { if (i === 1) controller.abort(); } });
  const stage = makeStaged(dom);
  assert.throws(
    () => stageBasketPrintTextFooters(stage, { documentRef: dom.documentRef, signal: controller.signal }),
    /aborted/,
  );
  assert.equal(dom.attachments, 1);
  assert.equal(stage.disposeCalls, 1);
  assert.ok(stage.sheets.every(s => s.element.children.length === 1));
});

test("missing document and initially aborted signal fail closed", () => {
  for (const options of [{ documentRef: null }, { signal: AbortSignal.abort() }]) {
    const dom = fakeDocument(), stage = makeStaged(dom);
    assert.throws(() => stageBasketPrintTextFooters(stage, options));
    assert.equal(dom.attachments, 0);
    assert.equal(stage.disposeCalls, 1);
  }
});

test("footer staging cannot print, fetch, encode, navigate or track", () => {
  const source = readFileSync(new URL("../js/print-basket-print-footer.mjs", import.meta.url), "utf8")
    .split("\n").filter(line => !line.trimStart().startsWith("//")).join("\n");
  for (const forbidden of [
    "window.print(", "fetch(", "sessionStorage", "localStorage", "innerHTML",
    "createObjectURL", "toBlob(", "toDataURL(", ".click()", "print-brand-qr",
  ]) {
    assert.ok(!source.includes(forbidden), forbidden);
  }
});
