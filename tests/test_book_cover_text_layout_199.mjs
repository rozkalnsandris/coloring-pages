import test from "node:test";
import assert from "node:assert/strict";
import { getBookCoverSafeRect } from "../js/book-cover-a4-contract.mjs";
import { BOOK_COVER_FONT_SPEC } from "../js/book-cover-font-preflight.mjs";
import { planBookCoverTextLayout } from "../js/book-cover-text-layout.mjs";

function contextFor(map) {
  return {
    font: "old-font",
    textAlign: "left",
    textBaseline: "top",
    measureText(value) {
      const metrics = map[value];
      if (!metrics) throw new Error("unexpected text");
      return metrics;
    },
  };
}

const metric = (left, right, ascent, descent) => ({
  width: left + right,
  actualBoundingBoxLeft: left,
  actualBoundingBoxRight: right,
  actualBoundingBoxAscent: ascent,
  actualBoundingBoxDescent: descent,
});

test("plans title and optional name inside the exact A4 safe rect without returning text", () => {
  const context = contextFor({
    "Mein Ausmalbuch": metric(490, 510, 200, 40),
    "Mia": metric(190, 210, 160, 30),
  });
  const result = planBookCoverTextLayout(
    context,
    { title: "Mein Ausmalbuch", name: "Mia" },
    { strokeWidthPx: 20, lineGapPx: 120 },
  );

  assert.equal(result.ok, true);
  assert.equal(result.fontSpec, BOOK_COVER_FONT_SPEC);
  assert.equal(result.lineCount, 2);
  assert.deepEqual(result.lines.map(line => line.kind), ["title", "name"]);
  assert.equal(Object.isFrozen(result), true);
  assert.equal(Object.isFrozen(result.lines), true);
  assert.equal(result.lines.every(Object.isFrozen), true);
  assert.equal(JSON.stringify(result).includes("Mein Ausmalbuch"), false);
  assert.equal(JSON.stringify(result).includes("Mia"), false);

  const safe = getBookCoverSafeRect();
  for (const line of result.lines) {
    assert.ok(line.bounds.left >= safe.x);
    assert.ok(line.bounds.top >= safe.y);
    assert.ok(line.bounds.right <= safe.right);
    assert.ok(line.bounds.bottom <= safe.bottom);
  }

  assert.equal(context.font, "old-font");
  assert.equal(context.textAlign, "left");
  assert.equal(context.textBaseline, "top");
});

test("empty title and name create a frozen zero-line plan without measuring", () => {
  let measured = false;
  const context = {
    font: "old",
    textAlign: "start",
    textBaseline: "middle",
    measureText() {
      measured = true;
      throw new Error("must not measure empty text");
    },
  };
  const result = planBookCoverTextLayout(
    context,
    { title: "", name: "" },
    { strokeWidthPx: 16, lineGapPx: 80 },
  );
  assert.equal(measured, false);
  assert.deepEqual(result.lines, []);
  assert.equal(result.lineCount, 0);
  assert.equal(Object.isFrozen(result.lines), true);
});

test("over-wide, over-high and combined text blocks fail closed", () => {
  const wide = contextFor({ Wide: metric(1200, 1200, 100, 20) });
  assert.throws(
    () => planBookCoverTextLayout(
      wide, { title: "Wide", name: "" }, { strokeWidthPx: 20, lineGapPx: 0 },
    ),
    /does not fit/,
  );

  const high = contextFor({ High: metric(100, 100, 1800, 1600) });
  assert.throws(
    () => planBookCoverTextLayout(
      high, { title: "High", name: "" }, { strokeWidthPx: 10, lineGapPx: 0 },
    ),
    /does not fit/,
  );

  const block = contextFor({
    A: metric(100, 100, 1400, 100),
    B: metric(100, 100, 1400, 100),
  });
  assert.throws(
    () => planBookCoverTextLayout(
      block, { title: "A", name: "B" }, { strokeWidthPx: 10, lineGapPx: 200 },
    ),
    /text block does not fit/,
  );
});

test("newline, invalid input/options and unusable metrics fail closed and restore canvas state", () => {
  const context = contextFor({ Bad: {
    width: Number.NaN,
    actualBoundingBoxLeft: 1,
    actualBoundingBoxRight: 1,
    actualBoundingBoxAscent: 2,
    actualBoundingBoxDescent: 1,
  } });

  assert.throws(
    () => planBookCoverTextLayout(
      context, { title: "line\nbreak", name: "" }, { strokeWidthPx: 10, lineGapPx: 20 },
    ),
    /one line/,
  );
  assert.throws(
    () => planBookCoverTextLayout(
      context, { title: "Bad", name: "" }, { strokeWidthPx: 10, lineGapPx: 20 },
    ),
    /unusable text metrics/,
  );
  assert.equal(context.font, "old-font");
  assert.equal(context.textAlign, "left");
  assert.equal(context.textBaseline, "top");

  assert.throws(() => planBookCoverTextLayout(null, { title: "", name: "" }, {
    strokeWidthPx: 0, lineGapPx: 0,
  }), TypeError);
  assert.throws(() => planBookCoverTextLayout(context, null, {
    strokeWidthPx: 0, lineGapPx: 0,
  }), TypeError);
  assert.throws(() => planBookCoverTextLayout(context, { title: 7, name: "" }, {
    strokeWidthPx: 0, lineGapPx: 0,
  }), TypeError);
  assert.throws(() => planBookCoverTextLayout(context, { title: "", name: "" }, {
    strokeWidthPx: -1, lineGapPx: 0,
  }), TypeError);
  assert.throws(() => planBookCoverTextLayout(context, { title: "", name: "" }, {
    strokeWidthPx: 0, lineGapPx: Number.NaN,
  }), TypeError);
});
