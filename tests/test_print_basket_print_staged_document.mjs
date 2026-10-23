import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stagePreparedBasketPrintDocument } from "../js/print-basket-print-staged-document.mjs";

function crc32(bytes) {
  let value = -1;
  for (const byte of bytes) {
    value ^= byte;
    for (let i = 0; i < 8; i++) {
      value = (value >>> 1) ^ ((value & 1) ? 0xedb88320 : 0);
    }
  }
  return (value ^ -1) >>> 0;
}
function chunk(type, data) {
  const output = Buffer.alloc(12 + data.length);
  output.writeUInt32BE(data.length, 0);
  output.write(type, 4, 4, "ascii");
  Buffer.from(data).copy(output, 8);
  output.writeUInt32BE(crc32(output.subarray(4, output.length - 4)), output.length - 4);
  return output;
}
// Structural PNG sentinel, not a true raster: tests inject a mock ImageBitmap
// decoder. The actual browser decoder must validate the compressed payload.
function pngA4(width, height) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr), chunk("IDAT", Buffer.from([1])),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}
const P = [2480, 3508], L = [3508, 2480];
const pBytes = pngA4(...P), lBytes = pngA4(...L);

function preparedFor(sizes) {
  const pages = sizes.map((_, i) => Object.freeze({
    activityId: i < 2 ? "activity-1" : "activity-" + i,
    pageIndex: i < 2 ? i + 1 : 1,
    pageCount: i < 2 ? 2 : 1,
    printUrl: "/media/" + (i < 2 ? "activity-1/print-" + (i + 1) : "activity-" + i + "/print") + ".png",
  }));
  const plan = Object.freeze({
    pages: Object.freeze(pages),
    imageUrls: Object.freeze(pages.map(p => p.printUrl)),
    sheetCount: sizes.length,
  });
  const sheets = sizes.map(([width, height], i) => Object.freeze({
    page: pages[i], width, height,
    orientation: width > height ? "landscape" : "portrait",
    bytes: Buffer.from(width > height ? lBytes : pBytes),
  }));
  return Object.freeze({ plan, sheets: Object.freeze(sheets) });
}

function fakeDom({ rejectCanvasAt = 0, rejectFooterAt = 0 } = {}) {
  const nodes = [], drawn = [];
  let canvasCount = 0, footerCount = 0;
  function createElement(tag) {
    const node = {
      tag, className: "", children: [], parent: null, attrs: {}, textContent: "",
      setAttribute(key, value) { this.attrs[key] = value; },
      append(...items) {
        for (const child of items) {
          this.children.push(child);
          child.parent = this;
        }
        if (tag === "section" && items.some(x => x.tag === "footer")) {
          footerCount++;
          if (footerCount === rejectFooterAt) throw new Error("footer rejected");
        }
      },
      remove() {
        if (!this.parent) return;
        const siblings = this.parent.children;
        const index = siblings.indexOf(this);
        if (index >= 0) siblings.splice(index, 1);
        this.parent = null;
      },
    };
    if (tag === "canvas") {
      canvasCount++;
      const which = canvasCount;
      node.getContext = () => {
        if (which === rejectCanvasAt) return null;
        return {
          set fillStyle(value) { assert.equal(value, "#fff"); },
          fillRect() {},
          drawImage(bitmap, x, y, width, height) {
            assert.equal(x, 0); assert.equal(y, 0);
            assert.deepEqual([width, height], [bitmap.width, bitmap.height]);
            drawn.push(node);
          },
        };
      };
    }
    nodes.push(node);
    return node;
  }
  return { documentRef: { createElement }, nodes, drawn };
}

function decoderFor(sizes, { corruptAt = 0, controller } = {}) {
  let calls = 0;
  const closed = [];
  return {
    closed,
    get calls() { return calls; },
    decode: async blob => {
      assert.equal(blob.type, "image/png");
      assert.ok(blob.size > 57);
      const index = calls++;
      const [width, height] = sizes[index];
      if (controller && index === 0) controller.abort();
      return {
        width: corruptAt === index + 1 ? 1 : width, height,
        close() { closed[index] = (closed[index] || 0) + 1; },
      };
    },
  };
}

test("detached mixed-orientation A4 text-branded sheets preserve order and source bytes", async () => {
  const sizes = [P, L, P];
  const prepared = preparedFor(sizes);
  const snapshots = prepared.sheets.map(x => Buffer.from(x.bytes));
  const dom = fakeDom(), decoder = decoderFor(sizes);
  const result = await stagePreparedBasketPrintDocument(prepared, {
    documentRef: dom.documentRef, decode: decoder.decode,
  });
  assert.strictEqual(result.plan, prepared.plan);
  assert.deepEqual(result.sheets.map(x => x.page), prepared.plan.pages);
  assert.deepEqual(result.sheets.map(x => x.orientation), ["portrait", "landscape", "portrait"]);
  assert.equal(dom.drawn.length, 3);
  assert.deepEqual(decoder.closed, [1, 1, 1]);
  for (let i = 0; i < 3; i++) {
    const section = result.sheets[i].element;
    assert.equal(section.className, "print-sheet is-" + result.sheets[i].orientation + " has-text-footer");
    assert.equal(section.children[0].className, "print-artwork");
    const canvas = section.children[0].children[0];
    assert.deepEqual([canvas.width, canvas.height], sizes[i]);
    assert.equal(section.children[1].className, "print-branding text-only");
    assert.equal(section.children[1].children.length, 2);
    assert.equal(section.children[1].attrs["aria-label"], "Ausmalwiese – Malspaß zum Ausdrucken");
    assert.deepEqual(Buffer.from(prepared.sheets[i].bytes), snapshots[i]);
  }
  assert.equal(result.disposed, false);
  result.dispose();
  result.dispose();
  assert.equal(result.disposed, true);
  assert.ok(dom.drawn.every(canvas => canvas.width === 0 && canvas.height === 0));
  assert.deepEqual(decoder.closed, [1, 1, 1]);
  assert.ok(result.sheets.every(x => x.element.children.length === 1));
});

test("five-page memory ceiling is inherited; sixth rejects without decoding or allocating", async () => {
  const five = [P, L, P, L, P];
  const dom = fakeDom(), decoder = decoderFor(five);
  const result = await stagePreparedBasketPrintDocument(preparedFor(five), {
    decode: decoder.decode, documentRef: dom.documentRef,
  });
  assert.equal(result.sheets.length, 5);
  result.dispose();
  const otherDom = fakeDom(), otherDecoder = decoderFor([...five, L]);
  await assert.rejects(stagePreparedBasketPrintDocument(preparedFor([...five, L]), {
    decode: otherDecoder.decode, documentRef: otherDom.documentRef,
  }), /preflight/);
  assert.equal(otherDecoder.calls, 0);
  assert.equal(otherDom.nodes.length, 0);
});

test("canvas context error releases decoded bitmaps and clears all allocated canvases", async () => {
  const sizes = [P, L], dom = fakeDom({ rejectCanvasAt: 2 }), decoder = decoderFor(sizes);
  await assert.rejects(stagePreparedBasketPrintDocument(preparedFor(sizes), {
    decode: decoder.decode, documentRef: dom.documentRef,
  }), /context unavailable/);
  assert.deepEqual(decoder.closed, [1, 1]);
  assert.ok(dom.nodes.filter(x => x.tag === "canvas").every(x => x.width === 0 && x.height === 0));
});

test("footer mutation failure clears canvases, removes partial footers and restores classes", async () => {
  const sizes = [P, L], dom = fakeDom({ rejectFooterAt: 2 }), decoder = decoderFor(sizes);
  await assert.rejects(stagePreparedBasketPrintDocument(preparedFor(sizes), {
    decode: decoder.decode, documentRef: dom.documentRef,
  }), /footer rejected/);
  assert.deepEqual(decoder.closed, [1, 1]);
  assert.ok(dom.nodes.filter(x => x.tag === "canvas").every(x => x.width === 0 && x.height === 0));
  assert.ok(dom.nodes.filter(x => x.tag === "section").every(x =>
    x.children.length === 1 && !x.className.includes("has-text-footer")));
});

test("aborted decode and wrong ImageBitmap size cannot return staged success", async () => {
  const sizes = [P, L];
  {
    const controller = new AbortController(), dom = fakeDom();
    const decoder = decoderFor(sizes, { controller });
    await assert.rejects(stagePreparedBasketPrintDocument(preparedFor(sizes), {
      decode: decoder.decode, documentRef: dom.documentRef, signal: controller.signal,
    }), /aborted/);
    assert.deepEqual(decoder.closed, [1]);
    assert.equal(dom.nodes.length, 0);
  }
  {
    const dom = fakeDom(), decoder = decoderFor(sizes, { corruptAt: 2 });
    await assert.rejects(stagePreparedBasketPrintDocument(preparedFor(sizes), {
      decode: decoder.decode, documentRef: dom.documentRef,
    }), /dimensions/);
    assert.deepEqual(decoder.closed, [1, 1]);
    assert.equal(dom.nodes.length, 0);
  }
});

test("orchestration has no network, print, permanent selection, QR or source-reencoding path", () => {
  const code = readFileSync(new URL("../js/print-basket-print-staged-document.mjs", import.meta.url), "utf8")
    .split("\n").filter(line => !line.trimStart().startsWith("//")).join("\n");
  for (const forbidden of [
    "window.print(", "fetch(", "sessionStorage", "localStorage", "document.body",
    "innerHTML", "createObjectURL", "toBlob(", "toDataURL(", ".click()",
  ]) assert.ok(!code.includes(forbidden), forbidden);
});
