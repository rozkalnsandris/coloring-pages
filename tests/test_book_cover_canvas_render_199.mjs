import test from "node:test";
import assert from "node:assert/strict";
import { BOOK_COVER_A4_CONTRACT } from "../js/book-cover-a4-contract.mjs";
import {
  BOOK_COVER_FONT_SPEC,
  BOOK_COVER_REQUIRED_GLYPHS,
} from "../js/book-cover-font-preflight.mjs";
import { renderBookCoverCanvas } from "../js/book-cover-canvas-render.mjs";

function metricFor(value) {
  if (value === "Mein Ausmalbuch") {
    return {
      width: 1000,
      actualBoundingBoxLeft: 490,
      actualBoundingBoxRight: 510,
      actualBoundingBoxAscent: 200,
      actualBoundingBoxDescent: 40,
    };
  }
  return {
    width: 400,
    actualBoundingBoxLeft: 190,
    actualBoundingBoxRight: 210,
    actualBoundingBoxAscent: 160,
    actualBoundingBoxDescent: 30,
  };
}

function fontSet(log, overrides = {}) {
  return {
    async load(spec, probe) {
      log.push(["font-load", spec, probe]);
      if (overrides.load) return overrides.load(spec, probe);
      return [{}];
    },
    check(spec, probe) {
      log.push(["font-check", spec, probe]);
      return overrides.check ? overrides.check(spec, probe) : true;
    },
  };
}

function fakeDocument(log, { strokeThrows = false } = {}) {
  const canvas = {
    width: -1,
    height: -1,
    attributes: {},
    setAttribute(name, value) {
      this.attributes[name] = value;
    },
    getContext(kind, options) {
      log.push(["getContext", kind, options]);
      return {
        font: "old-font",
        textAlign: "left",
        textBaseline: "top",
        fillStyle: "",
        strokeStyle: "",
        lineWidth: 0,
        lineJoin: "",
        measureText(value) {
          log.push(["measure", value]);
          return metricFor(value);
        },
        fillRect(x, y, width, height) {
          log.push(["fillRect", this.fillStyle, x, y, width, height]);
        },
        strokeText(value, x, y) {
          log.push(["strokeText", value, x, y, this.strokeStyle, this.lineWidth, this.lineJoin]);
          if (strokeThrows) throw new Error("draw failed");
        },
        fillText(value, x, y) {
          log.push(["fillText", value, x, y, this.fillStyle]);
        },
      };
    },
  };
  return {
    canvas,
    documentRef: {
      fonts: null,
      createElement(name) {
        assert.equal(name, "canvas");
        log.push(["createElement", name]);
        return canvas;
      },
    },
  };
}

test("renders detached exact-A4 white canvas with outlined local text in order", async () => {
  const log = [];
  const { canvas, documentRef } = fakeDocument(log);
  const fonts = fontSet(log);
  const result = await renderBookCoverCanvas(
    { title: "Mein Ausmalbuch", name: "Mia" },
    { strokeWidthPx: 20, lineGapPx: 120 },
    { documentRef, fonts },
  );

  assert.equal(canvas.width, BOOK_COVER_A4_CONTRACT.width);
  assert.equal(canvas.height, BOOK_COVER_A4_CONTRACT.height);
  assert.equal(canvas.attributes["aria-hidden"], "true");
  assert.equal(result.canvas, canvas);
  assert.equal(result.layout.lineCount, 2);
  assert.equal(result.disposed, false);
  assert.equal(JSON.stringify(result.layout).includes("Mein Ausmalbuch"), false);
  assert.equal(JSON.stringify(result.layout).includes("Mia"), false);

  assert.deepEqual(log[0], ["font-load", BOOK_COVER_FONT_SPEC, BOOK_COVER_REQUIRED_GLYPHS]);
  assert.deepEqual(log[1], ["font-check", BOOK_COVER_FONT_SPEC, BOOK_COVER_REQUIRED_GLYPHS]);

  const white = log.find(entry => entry[0] === "fillRect");
  assert.deepEqual(white, [
    "fillRect",
    "#fff",
    0,
    0,
    BOOK_COVER_A4_CONTRACT.width,
    BOOK_COVER_A4_CONTRACT.height,
  ]);

  const draw = log.filter(entry => entry[0] === "strokeText" || entry[0] === "fillText");
  assert.deepEqual(draw.map(entry => [entry[0], entry[1]]), [
    ["strokeText", "Mein Ausmalbuch"],
    ["fillText", "Mein Ausmalbuch"],
    ["strokeText", "Mia"],
    ["fillText", "Mia"],
  ]);
  assert.equal(draw[0][4], "#000");
  assert.equal(draw[0][5], 20);
  assert.equal(draw[0][6], "round");
  assert.equal(draw[1][4], "#fff");

  result.dispose();
  assert.equal(result.disposed, true);
  assert.equal(canvas.width, 0);
  assert.equal(canvas.height, 0);
  result.dispose();
});

test("empty cover still creates only an opaque white A4 sheet", async () => {
  const log = [];
  const { documentRef } = fakeDocument(log);
  const result = await renderBookCoverCanvas(
    { title: "", name: "" },
    { strokeWidthPx: 18, lineGapPx: 80 },
    { documentRef, fonts: fontSet(log) },
  );

  assert.equal(result.layout.lineCount, 0);
  assert.equal(log.filter(entry => entry[0] === "strokeText").length, 0);
  assert.equal(log.filter(entry => entry[0] === "fillText").length, 0);
  assert.equal(log.filter(entry => entry[0] === "fillRect").length, 1);
});

test("font gate fails before canvas allocation", async () => {
  const log = [];
  const { documentRef } = fakeDocument(log);
  await assert.rejects(
    renderBookCoverCanvas(
      { title: "Mein Ausmalbuch", name: "" },
      { strokeWidthPx: 20, lineGapPx: 100 },
      { documentRef, fonts: fontSet(log, { check: () => false }) },
    ),
    /font is not ready/,
  );
  assert.equal(log.some(entry => entry[0] === "createElement"), false);
});

test("draw failure clears the partially allocated giant canvas", async () => {
  const log = [];
  const { canvas, documentRef } = fakeDocument(log, { strokeThrows: true });
  await assert.rejects(
    renderBookCoverCanvas(
      { title: "Mein Ausmalbuch", name: "" },
      { strokeWidthPx: 20, lineGapPx: 100 },
      { documentRef, fonts: fontSet(log) },
    ),
    /draw failed/,
  );
  assert.equal(canvas.width, 0);
  assert.equal(canvas.height, 0);
});

test("aborted render fails closed without drawing text", async () => {
  const log = [];
  const { documentRef } = fakeDocument(log);
  const controller = new AbortController();
  const fonts = fontSet(log, {
    load() {
      controller.abort();
      return [{}];
    },
  });

  await assert.rejects(
    renderBookCoverCanvas(
      { title: "Mein Ausmalbuch", name: "Mia" },
      { strokeWidthPx: 20, lineGapPx: 100 },
      { documentRef, fonts, signal: controller.signal },
    ),
    /rendering aborted/,
  );
  assert.equal(log.some(entry => entry[0] === "createElement"), false);
});

test("invalid cover/options/document fail before rendering", async () => {
  const log = [];
  const { documentRef } = fakeDocument(log);
  const fonts = fontSet(log);

  await assert.rejects(
    renderBookCoverCanvas(null, { strokeWidthPx: 20, lineGapPx: 100 }, { documentRef, fonts }),
    TypeError,
  );
  await assert.rejects(
    renderBookCoverCanvas(
      { title: "x", name: "" },
      { strokeWidthPx: -1, lineGapPx: 100 },
      { documentRef, fonts },
    ),
    TypeError,
  );
  await assert.rejects(
    renderBookCoverCanvas(
      { title: "x", name: "" },
      { strokeWidthPx: 20, lineGapPx: 100 },
      { documentRef: null, fonts },
    ),
    TypeError,
  );
});
