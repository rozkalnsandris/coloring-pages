import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  stageBasketPrintCanvases, MAX_BASKET_CANVAS_BYTES,
} from "../js/print-basket-print-canvas.mjs";

const portrait = [2480, 3508], landscape = [3508, 2480];

function decodedFor(sizes) {
  const pages = sizes.map((_, i) => ({
    activityId: i < 2 ? "cut-1" : String(i + 1),
    pageIndex: i < 2 ? i + 1 : 1,
    pageCount: i < 2 ? 2 : 1,
    printUrl: "/media/" + (i < 2 ? "cut-1/print-" + (i + 1) : (i + 1) + "/print") + ".png",
  }));
  const plan = { pages, imageUrls: pages.map(p => p.printUrl), sheetCount: pages.length };
  const closed = [];
  const sheets = sizes.map(([width, height], i) => ({
    page: pages[i], width, height,
    orientation: width > height ? "landscape" : "portrait",
    bitmap: {
      width, height,
      close() { closed[i] = (closed[i] || 0) + 1; },
    },
  }));
  let released = false, releaseCalls = 0;
  return {
    plan, sheets, closed,
    get released() { return released; },
    get releaseCalls() { return releaseCalls; },
    release() {
      releaseCalls++;
      if (released) return;
      released = true;
      for (const sheet of sheets) sheet.bitmap.close();
    },
  };
}

function fakeDom({ missingContext = false, draw = () => {}, badStructure = false } = {}) {
  const nodes = [], draws = [], fills = [];
  let bodyMutations = 0, printCalls = 0;
  const createElement = (tag) => {
    const node = {
      tag, children: [], attrs: {}, width: undefined, height: undefined,
      setAttribute(k, v) { this.attrs[k] = v; },
      append(...parts) { this.children.push(...parts); },
    };
    if (tag === "canvas") {
      node.getContext = (kind, options) => {
        assert.equal(kind, "2d");
        assert.equal(options.alpha, false);
        if (missingContext) return null;
        return {
          set fillStyle(value) { assert.equal(value, "#fff"); },
          fillRect(...a) { fills.push({ canvas: node, args: a }); },
          drawImage(...a) {
            draws.push({ canvas: node, args: a });
            draw({ canvas: node, args: a, calls: draws.length });
          },
        };
      };
    }
    if (badStructure && tag === "section") delete node.append;
    nodes.push(node);
    return node;
  };
  const documentRef = {
    createElement,
    body: { append() { bodyMutations++; } },
  };
  return { documentRef, nodes, draws, fills,
    get bodyMutations() { return bodyMutations; },
    get printCalls() { return printCalls; },
  };
}

test("mixed-orientation A4 sheets preserve source order, native pixels, and no browser action", () => {
  const decoded = decodedFor([portrait, landscape, portrait]);
  const dom = fakeDom();
  const staged = stageBasketPrintCanvases(decoded, dom);
  assert.equal(staged.sheets.length, 3);
  assert.deepEqual(staged.sheets.map(x => x.orientation), ["portrait", "landscape", "portrait"]);
  assert.deepEqual(staged.sheets.map(x => x.page.printUrl), decoded.plan.imageUrls);
  assert.ok(Object.isFrozen(staged));
  assert.ok(Object.isFrozen(staged.sheets));
  assert.ok(Object.isFrozen(staged.sheets[0]));
  for (let i = 0; i < staged.sheets.length; i++) {
    const record = staged.sheets[i], canvas = record.element.children[0].children[0];
    const sheet = decoded.sheets[i];
    assert.equal(record.element.tag, "section");
    assert.equal(record.element.className, "print-sheet is-" + sheet.orientation);
    assert.equal(record.element.attrs["aria-label"], "A4-Druckseite " + (i + 1) + " von 3");
    assert.equal(record.element.children[0].className, "print-artwork");
    assert.equal(canvas.tag, "canvas");
    assert.equal(canvas.attrs["aria-hidden"], "true");
    assert.deepEqual([canvas.width, canvas.height], [sheet.width, sheet.height]);
    assert.deepEqual(dom.fills[i].args, [0, 0, sheet.width, sheet.height]);
    assert.deepEqual(dom.draws[i].args, [sheet.bitmap, 0, 0, sheet.width, sheet.height]);
  }
  assert.equal(dom.bodyMutations, 0);
  assert.equal(dom.printCalls, 0);
  assert.equal(decoded.released, true);
  assert.equal(decoded.releaseCalls, 1);
  assert.deepEqual(decoded.closed, [1, 1, 1]);
  assert.equal(staged.disposed, false);
  staged.dispose();
  assert.equal(staged.disposed, true);
  assert.deepEqual(dom.draws.map(x => [x.canvas.width, x.canvas.height]), [[0,0],[0,0],[0,0]]);
  staged.dispose();
  assert.equal(decoded.releaseCalls, 1);
});

test("five sheets stay within memory cap while sixth is rejected before drawing", () => {
  assert.equal(MAX_BASKET_CANVAS_BYTES, 180 * 1024 * 1024);
  const five = decodedFor([portrait, landscape, portrait, landscape, portrait]);
  const dom = fakeDom();
  const staged = stageBasketPrintCanvases(five, dom);
  assert.equal(staged.sheets.length, 5);
  staged.dispose();
  const six = decodedFor([portrait, landscape, portrait, landscape, portrait, landscape]);
  const otherDom = fakeDom();
  assert.throws(() => stageBasketPrintCanvases(six, otherDom), /unreleased A4 decoder output/);
  assert.equal(otherDom.nodes.length, 0);
  assert.deepEqual(six.closed, [1,1,1,1,1,1]);
});

test("stale order, repeated URL, bad raster and wrong bitmap fail before allocation", () => {
  for (const mutate of [
    d => { d.plan.imageUrls[1] = "/media/wrong/print.png"; },
    d => { d.plan.pages[1].printUrl = d.plan.pages[0].printUrl; d.plan.imageUrls[1] = d.plan.imageUrls[0]; },
    d => { d.sheets[1].page = d.plan.pages[0]; },
    d => { d.sheets[0].width = 1000; },
    d => { d.sheets[1].orientation = "portrait"; },
    d => { d.sheets[0].bitmap.width = 3508; },
    d => { d.plan.sheetCount = 0; },
  ]) {
    const d = decodedFor([portrait, landscape]);
    mutate(d);
    const dom = fakeDom();
    assert.throws(() => stageBasketPrintCanvases(d, dom));
    assert.equal(dom.nodes.length, 0);
    assert.equal(d.releaseCalls, 1);
    assert.deepEqual(d.closed, [1,1]);
  }
});

test("unsupported document or canvas context fails closed and releases all bitmaps", () => {
  for (const options of [
    { documentRef: null },
    fakeDom({ missingContext: true }),
    fakeDom({ badStructure: true }),
  ]) {
    const d = decodedFor([portrait, landscape]);
    const dom = options.documentRef === null ? options : options;
    assert.throws(() => stageBasketPrintCanvases(d, dom));
    assert.deepEqual(d.closed, [1,1]);
    const canvases = options.nodes?.filter(x => x.tag === "canvas") || [];
    assert.ok(canvases.every(x => x.width === 0 && x.height === 0));
  }
});

test("draw failure and cancellation clear every allocated canvas without partial success", () => {
  {
    const d = decodedFor([portrait, landscape]);
    const dom = fakeDom({
      draw({ calls }) { if (calls === 2) throw new Error("canvas draw rejected"); },
    });
    assert.throws(() => stageBasketPrintCanvases(d, dom), /draw rejected/);
    assert.deepEqual(d.closed, [1,1]);
    assert.ok(dom.nodes.filter(x => x.tag === "canvas").every(x => x.width === 0 && x.height === 0));
  }
  {
    const controller = new AbortController();
    const d = decodedFor([portrait, landscape]);
    const dom = fakeDom({ draw({ calls }) { if (calls === 1) controller.abort(); } });
    assert.throws(() => stageBasketPrintCanvases(d, {
      documentRef: dom.documentRef, signal: controller.signal,
    }), /aborted/);
    assert.deepEqual(d.closed, [1,1]);
    assert.ok(dom.nodes.filter(x => x.tag === "canvas").every(x => x.width === 0 && x.height === 0));
  }
  {
    const controller = new AbortController();
    controller.abort();
    const d = decodedFor([portrait]);
    const dom = fakeDom();
    assert.throws(() => stageBasketPrintCanvases(d, {
      documentRef: dom.documentRef, signal: controller.signal,
    }), /aborted/);
    assert.equal(dom.nodes.length, 0);
    assert.deepEqual(d.closed, [1]);
  }
});

test("stager has no print, source rewrite, user storage or network side effects", () => {
  const code = readFileSync(new URL("../js/print-basket-print-canvas.mjs", import.meta.url), "utf8")
    .split("\n").filter(line => !line.trimStart().startsWith("//")).join("\n");
  for (const forbidden of [
    "window.print(", ".click()", "document.body", "fetch(", "sessionStorage",
    "localStorage", "toDataURL(", "toBlob(", "createObjectURL", "innerHTML",
  ]) {
    assert.ok(!code.includes(forbidden), forbidden);
  }
});
