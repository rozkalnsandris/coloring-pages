import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stageBookPrintDocument } from "../js/book-print-document.mjs";
import { printStagedBasketDocumentOnce } from "../js/print-basket-print-lifecycle.mjs";

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
function png(width = 2480, height = 3508, { phys = false } = {}) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  const chunks = [
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
  ];
  if (phys) {
    const body = Buffer.alloc(9);
    body.writeUInt32BE(11811, 0);
    body.writeUInt32BE(11811, 4);
    body[8] = 1;
    chunks.push(chunk("pHYs", body));
  }
  chunks.push(chunk("IDAT", Buffer.from([1])));
  chunks.push(chunk("IEND", Buffer.alloc(0)));
  return Buffer.concat(chunks);
}

function makeBundle() {
  const artworkPages = Object.freeze([
    Object.freeze({
      activityId: "1", pageIndex: 1, pageCount: 1,
      printUrl: "/media/1/print.png",
    }),
    Object.freeze({
      activityId: "cut-2", pageIndex: 1, pageCount: 1,
      printUrl: "/media/cut-2/print.png",
    }),
  ]);
  const sheets = Object.freeze([
    Object.freeze({
      kind: "cover", sheetNumber: 1, sheetCount: 3, orientation: "portrait",
    }),
    Object.freeze({
      kind: "artwork", sheetNumber: 2, sheetCount: 3,
      ...artworkPages[0],
    }),
    Object.freeze({
      kind: "artwork", sheetNumber: 3, sheetCount: 3,
      ...artworkPages[1],
    }),
  ]);
  let disposed = false;
  return {
    plan: Object.freeze({
      coverEnabled: true,
      artworkSheetCount: 2,
      sheetCount: 3,
      artworkPages,
      sheets,
    }),
    coverPng: png(2480, 3508, { phys: true }),
    artworkDownloads: Object.freeze([
      { url: artworkPages[0].printUrl, bytes: png() },
      { url: artworkPages[1].printUrl, bytes: png(3508, 2480) },
    ]),
    zip: { bytes: new Uint8Array([1]), filenames: [] },
    get disposed() { return disposed; },
    dispose() { disposed = true; },
  };
}

function fakeDom() {
  const nodes = [];
  function createElement(tag) {
    const node = {
      tag,
      className: "",
      children: [],
      parent: null,
      parentNode: null,
      parentElement: null,
      isConnected: false,
      attrs: {},
      textContent: "",
      setAttribute(key, value) { this.attrs[key] = value; },
      append(...items) {
        for (const item of items) {
          this.children.push(item);
          item.parent = this;
        }
      },
      remove() {
        if (!this.parent) return;
        const index = this.parent.children.indexOf(this);
        if (index >= 0) this.parent.children.splice(index, 1);
        this.parent = null;
      },
    };
    if (tag === "canvas") {
      node.getContext = () => ({
        set fillStyle(value) { assert.equal(value, "#fff"); },
        fillRect() {},
        drawImage(bitmap, x, y, width, height) {
          assert.equal(x, 0);
          assert.equal(y, 0);
          assert.deepEqual([width, height], [bitmap.width, bitmap.height]);
        },
      });
    }
    nodes.push(node);
    return node;
  }
  return { documentRef: { createElement }, nodes };
}

function decoder() {
  const sizes = [
    [2480, 3508],
    [2480, 3508],
    [3508, 2480],
  ];
  let calls = 0;
  const closed = [];
  return {
    closed,
    async decode(blob) {
      assert.equal(blob.type, "image/png");
      const index = calls++;
      const [width, height] = sizes[index];
      return {
        width,
        height,
        close() { closed[index] = (closed[index] || 0) + 1; },
      };
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

test("covered book stages through shared decode/canvas/footer path in exact sheet order", async () => {
  const value = makeBundle();
  const dom = fakeDom();
  const images = decoder();
  const staged = await stageBookPrintDocument(value, {
    documentRef: dom.documentRef,
    decode: images.decode,
    blobFactory: bytes => ({ type: "image/png", size: bytes.byteLength }),
  });

  assert.equal(staged.plan.sheetCount, 3);
  assert.deepEqual(staged.plan.imageUrls, [
    "local:book-cover",
    "/media/1/print.png",
    "/media/cut-2/print.png",
  ]);
  assert.deepEqual(staged.sheets.map(sheet => sheet.orientation), [
    "portrait", "portrait", "landscape",
  ]);
  assert.deepEqual(staged.sheets.map(sheet => sheet.element.className), [
    "print-sheet is-portrait has-text-footer",
    "print-sheet is-portrait has-text-footer",
    "print-sheet is-landscape has-text-footer",
  ]);
  assert.deepEqual(images.closed, [1, 1, 1]);
  assert.equal(value.disposed, false, "staging does not consume ZIP/cover bundle ownership");
  assert.equal(staged.disposed, false);

  staged.dispose();
  assert.equal(staged.disposed, true);
  assert.ok(dom.nodes.filter(node => node.tag === "canvas")
    .every(canvas => canvas.width === 0 && canvas.height === 0));
});

test("shared lifecycle accepts the covered staged document, prints once, and releases canvases", async () => {
  const dom = fakeDom();
  const images = decoder();
  const staged = await stageBookPrintDocument(makeBundle(), {
    documentRef: dom.documentRef,
    decode: images.decode,
    blobFactory: bytes => ({ type: "image/png", size: bytes.byteLength }),
  });
  const host = mount();
  let prints = 0;
  const result = printStagedBasketDocumentOnce(staged, {
    mount: host,
    print() {
      prints++;
      assert.equal(host.childElementCount, 3);
      assert.equal(host.children[0].className, "print-sheet is-portrait has-text-footer");
    },
  });

  assert.equal(prints, 1);
  assert.deepEqual(result.orientations, ["portrait", "portrait", "landscape"]);
  assert.equal(host.childElementCount, 0);
  assert.equal(staged.disposed, true);
  assert.ok(dom.nodes.filter(node => node.tag === "canvas")
    .every(canvas => canvas.width === 0 && canvas.height === 0));
});

test("abort before staging creates no detached DOM", async () => {
  const dom = fakeDom();
  await assert.rejects(
    stageBookPrintDocument(makeBundle(), {
      documentRef: dom.documentRef,
      signal: AbortSignal.abort(),
      decode: decoder().decode,
    }),
    /aborted/,
  );
  assert.equal(dom.nodes.length, 0);
});

test("book print document module never activates UI, storage, network or print", () => {
  const source = readFileSync(
    new URL("../js/book-print-document.mjs", import.meta.url),
    "utf8",
  );
  const code = source.split("\n")
    .filter(line => !line.trimStart().startsWith("//"))
    .join("\n");
  for (const forbidden of [
    "window.print(", "fetch(", "sessionStorage", "localStorage",
    "document.body", ".showModal(", ".click()", "sendBeacon(",
    "analytics", "createObjectURL",
  ]) {
    assert.equal(code.includes(forbidden), false, forbidden);
  }
});
