// #199 pure A4 text-fit/layout planner for the optional book cover.
// Measures only in the caller's already-loaded Canvas context and returns
// geometry. It does not draw text, persist/return visitor text, encode PNGs,
// access storage/network, print, or prove visual glyph quality.
import { getBookCoverSafeRect } from "./book-cover-a4-contract.mjs";
import { BOOK_COVER_FONT_SPEC } from "./book-cover-font-preflight.mjs";

function checkedContext(context) {
  if (!context || typeof context.measureText !== "function") {
    throw new TypeError("Canvas text-measure interface required");
  }
  return context;
}

function checkedText(value, field) {
  if (typeof value !== "string") throw new TypeError(field + " must be a string");
  if (/[\r\n]/u.test(value)) throw new RangeError(field + " must fit on one line");
  return value;
}

function checkedPx(value, field) {
  if (!Number.isFinite(value) || value < 0) {
    throw new TypeError(field + " must be a finite non-negative pixel value");
  }
  return value;
}

function measureLine(context, kind, value, strokeWidthPx) {
  const metrics = context.measureText(value);
  const values = {
    width: metrics?.width,
    left: metrics?.actualBoundingBoxLeft,
    right: metrics?.actualBoundingBoxRight,
    ascent: metrics?.actualBoundingBoxAscent,
    descent: metrics?.actualBoundingBoxDescent,
  };
  if (Object.values(values).some(item => !Number.isFinite(item)) ||
      values.width <= 0 || values.left + values.right <= 0 ||
      values.ascent + values.descent <= 0) {
    throw new Error("Book cover " + kind + " has unusable text metrics");
  }
  const halfStroke = strokeWidthPx / 2;
  return {
    kind,
    left: values.left,
    right: values.right,
    ascent: values.ascent,
    descent: values.descent,
    outerWidth: values.left + values.right + strokeWidthPx,
    outerHeight: values.ascent + values.descent + strokeWidthPx,
    halfStroke,
  };
}

export function planBookCoverTextLayout(context, cover, options) {
  const canvas = checkedContext(context);
  if (!cover || typeof cover !== "object" || Array.isArray(cover)) {
    throw new TypeError("Cover text object required");
  }
  if (!options || typeof options !== "object" || Array.isArray(options)) {
    throw new TypeError("Cover layout options required");
  }

  const title = checkedText(cover.title, "title");
  const name = checkedText(cover.name, "name");
  const stroke = checkedPx(options.strokeWidthPx, "strokeWidthPx");
  const gap = checkedPx(options.lineGapPx, "lineGapPx");
  const safe = getBookCoverSafeRect();

  const previous = {
    font: canvas.font,
    textAlign: canvas.textAlign,
    textBaseline: canvas.textBaseline,
  };
  const measured = [];
  try {
    canvas.font = BOOK_COVER_FONT_SPEC;
    canvas.textAlign = "center";
    canvas.textBaseline = "alphabetic";
    if (title.length) measured.push(measureLine(canvas, "title", title, stroke));
    if (name.length) measured.push(measureLine(canvas, "name", name, stroke));
  } finally {
    if ("font" in canvas) canvas.font = previous.font;
    if ("textAlign" in canvas) canvas.textAlign = previous.textAlign;
    if ("textBaseline" in canvas) canvas.textBaseline = previous.textBaseline;
  }

  if (!measured.length) {
    return Object.freeze({
      ok: true,
      fontSpec: BOOK_COVER_FONT_SPEC,
      strokeWidthPx: stroke,
      lineGapPx: gap,
      lineCount: 0,
      lines: Object.freeze([]),
    });
  }

  for (const line of measured) {
    if (line.outerWidth > safe.width || line.outerHeight > safe.height) {
      throw new RangeError("Book cover " + line.kind + " does not fit the A4 safe area");
    }
  }

  const totalHeight = measured.reduce((sum, line) => sum + line.outerHeight, 0) +
    gap * (measured.length - 1);
  if (totalHeight > safe.height) {
    throw new RangeError("Book cover text block does not fit the A4 safe area");
  }

  const safeCenterX = safe.x + safe.width / 2;
  let outerTop = safe.y + (safe.height - totalHeight) / 2;
  const lines = measured.map(line => {
    const x = safeCenterX + (line.left - line.right) / 2;
    const baselineY = outerTop + line.halfStroke + line.ascent;
    const bounds = Object.freeze({
      left: x - line.left - line.halfStroke,
      top: baselineY - line.ascent - line.halfStroke,
      right: x + line.right + line.halfStroke,
      bottom: baselineY + line.descent + line.halfStroke,
    });
    if (bounds.left < safe.x || bounds.top < safe.y ||
        bounds.right > safe.right || bounds.bottom > safe.bottom) {
      throw new RangeError("Book cover " + line.kind + " exceeds the A4 safe area");
    }
    outerTop += line.outerHeight + gap;
    return Object.freeze({
      kind: line.kind,
      x,
      baselineY,
      bounds,
    });
  });

  return Object.freeze({
    ok: true,
    fontSpec: BOOK_COVER_FONT_SPEC,
    strokeWidthPx: stroke,
    lineGapPx: gap,
    lineCount: lines.length,
    lines: Object.freeze(lines),
  });
}
