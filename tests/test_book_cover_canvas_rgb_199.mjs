import test from "node:test";
import assert from "node:assert/strict";
import { BOOK_COVER_A4_CONTRACT } from "../js/book-cover-a4-contract.mjs";
import { extractBookCoverRgb } from "../js/book-cover-canvas-rgb.mjs";

const WIDTH = BOOK_COVER_A4_CONTRACT.width;
const HEIGHT = BOOK_COVER_A4_CONTRACT.height;

function opaqueWhiteRow() {
  const data = new Uint8ClampedArray(WIDTH * 4);
  data.fill(255);
  return data;
}

function renderedFor(getImageData) {
  let disposed = false;
  const calls = [];
  const canvas = {
    width: WIDTH,
    height: HEIGHT,
    getContext(kind, options) {
      calls.push(["getContext", kind, options]);
      return { getImageData };
    },
  };
  const rendered = {
    canvas,
    get disposed() {
      return disposed;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      canvas.width = 0;
      canvas.height = 0;
      calls.push(["dispose"]);
    },
  };
  return { rendered, calls, canvas };
}

test("extracts exact A4 opaque RGB row-by-row, preserves interior pixels and disposes canvas", () => {
  const white = opaqueWhiteRow();
  const interior = opaqueWhiteRow();
  const x = BOOK_COVER_A4_CONTRACT.safeFramePx;
  const y = Math.floor(HEIGHT / 2);
  const rgbaOffset = x * 4;
  interior[rgbaOffset] = 12;
  interior[rgbaOffset + 1] = 34;
  interior[rgbaOffset + 2] = 56;

  let rowCalls = 0;
  const { rendered, calls, canvas } = renderedFor((left, top, width, height) => {
    assert.equal(left, 0);
    assert.equal(width, WIDTH);
    assert.equal(height, 1);
    rowCalls++;
    return { data: top === y ? interior : white };
  });

  const rgb = extractBookCoverRgb(rendered);

  assert.equal(rgb instanceof Uint8Array, true);
  assert.equal(rgb.length, WIDTH * HEIGHT * 3);
  assert.equal(rowCalls, HEIGHT);
  const target = (y * WIDTH + x) * 3;
  assert.deepEqual(Array.from(rgb.subarray(target, target + 3)), [12, 34, 56]);
  assert.deepEqual(Array.from(rgb.subarray(0, 3)), [255, 255, 255]);
  assert.deepEqual(
    calls[0],
    ["getContext", "2d", { alpha: false, willReadFrequently: true }],
  );
  assert.equal(rendered.disposed, true);
  assert.equal(canvas.width, 0);
  assert.equal(canvas.height, 0);
  assert.deepEqual(calls.at(-1), ["dispose"]);
});

test("non-opaque canvas fails closed and still disposes immediately", () => {
  const row = opaqueWhiteRow();
  row[3] = 254;
  let rowCalls = 0;
  const { rendered, canvas } = renderedFor(() => {
    rowCalls++;
    return { data: row };
  });

  assert.throws(
    () => extractBookCoverRgb(rendered),
    /fully opaque/,
  );
  assert.equal(rowCalls, 1);
  assert.equal(rendered.disposed, true);
  assert.equal(canvas.width, 0);
});

test("invalid scanline and pixel-read failure fail closed with cleanup", () => {
  const short = new Uint8ClampedArray(WIDTH * 4 - 1);
  const a = renderedFor(() => ({ data: short }));
  assert.throws(
    () => extractBookCoverRgb(a.rendered),
    /scanline/,
  );
  assert.equal(a.rendered.disposed, true);

  const b = renderedFor(() => {
    throw new Error("security");
  });
  assert.throws(
    () => extractBookCoverRgb(b.rendered),
    /pixel read failed/,
  );
  assert.equal(b.rendered.disposed, true);
});

test("aborted extraction performs no pixel read and disposes the render", () => {
  const controller = new AbortController();
  controller.abort();
  let reads = 0;
  const { rendered, calls } = renderedFor(() => {
    reads++;
    return { data: opaqueWhiteRow() };
  });

  assert.throws(
    () => extractBookCoverRgb(rendered, { signal: controller.signal }),
    /extraction aborted/,
  );
  assert.equal(reads, 0);
  assert.equal(calls.some(entry => entry[0] === "getContext"), false);
  assert.equal(rendered.disposed, true);
});

test("invalid or already disposed render is rejected before allocation/read", () => {
  assert.throws(() => extractBookCoverRgb(null), TypeError);

  const { rendered } = renderedFor(() => ({ data: opaqueWhiteRow() }));
  rendered.dispose();
  assert.throws(() => extractBookCoverRgb(rendered), /undisposed/);

  const wrong = renderedFor(() => ({ data: opaqueWhiteRow() }));
  wrong.canvas.width = WIDTH - 1;
  assert.throws(() => extractBookCoverRgb(wrong.rendered), /undisposed/);
});
