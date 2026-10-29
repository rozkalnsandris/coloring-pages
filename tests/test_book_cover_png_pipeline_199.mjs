import test from "node:test";
import assert from "node:assert/strict";
import { runBookCoverPngPipeline } from "../js/book-cover-png-pipeline.mjs";

function renderedRecord(log) {
  let disposed = false;
  return {
    canvas: {},
    get disposed() {
      return disposed;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      log.push("dispose");
    },
  };
}

test("returns only verified PNG bytes in render-extract-encode-verify order and wipes RGB", async () => {
  const log = [];
  const rendered = renderedRecord(log);
  const rgb = Uint8Array.from([10, 20, 30, 40, 50, 60]);
  const png = Uint8Array.from([137, 80, 78, 71]);

  const result = await runBookCoverPngPipeline(
    { title: "Mein Ausmalbuch", name: "Mia" },
    { strokeWidthPx: 20, lineGapPx: 120 },
    {
      documentRef: { marker: "doc" },
      fonts: { marker: "fonts" },
      services: {
        async render(cover, options, env) {
          log.push(["render", cover, options, env.documentRef, env.fonts]);
          return rendered;
        },
        extract(value) {
          log.push(["extract", value === rendered]);
          value.dispose();
          return rgb;
        },
        async encode(value) {
          log.push(["encode", value === rgb, Array.from(value)]);
          return png;
        },
        async verify(encoded, source) {
          log.push(["verify", encoded === png, source === rgb, Array.from(source)]);
          return { ok: true };
        },
      },
    },
  );

  assert.equal(result, png);
  assert.deepEqual(
    log.map(entry => Array.isArray(entry) ? entry[0] : entry),
    ["render", "extract", "dispose", "encode", "verify"],
  );
  assert.deepEqual(Array.from(rgb), [0, 0, 0, 0, 0, 0]);
  assert.equal(rendered.disposed, true);
  assert.equal(JSON.stringify(result).includes("Mia"), false);
});

test("extract failure defensively disposes a renderer left undisposed", async () => {
  const log = [];
  const rendered = renderedRecord(log);

  await assert.rejects(
    runBookCoverPngPipeline(
      { title: "x", name: "" },
      { strokeWidthPx: 1, lineGapPx: 1 },
      {
        services: {
          async render() {
            log.push("render");
            return rendered;
          },
          extract() {
            log.push("extract");
            throw new Error("extract failed");
          },
          async encode() {
            throw new Error("must not encode");
          },
          async verify() {
            throw new Error("must not verify");
          },
        },
      },
    ),
    /extract failed/,
  );

  assert.equal(rendered.disposed, true);
  assert.deepEqual(log, ["render", "extract", "dispose"]);
});

test("encode failure wipes extracted RGB and does not verify", async () => {
  const log = [];
  const rendered = renderedRecord(log);
  const rgb = Uint8Array.from([1, 2, 3]);
  let verified = false;

  await assert.rejects(
    runBookCoverPngPipeline(
      { title: "x", name: "" },
      { strokeWidthPx: 1, lineGapPx: 1 },
      {
        services: {
          async render() {
            return rendered;
          },
          extract(value) {
            value.dispose();
            return rgb;
          },
          async encode() {
            throw new Error("encode failed");
          },
          async verify() {
            verified = true;
            return { ok: true };
          },
        },
      },
    ),
    /encode failed/,
  );

  assert.equal(verified, false);
  assert.deepEqual(Array.from(rgb), [0, 0, 0]);
});

test("verification false or throw never returns unverified PNG and wipes RGB", async () => {
  for (const verify of [
    async () => ({ ok: false }),
    async () => { throw new Error("verify failed"); },
  ]) {
    const log = [];
    const rendered = renderedRecord(log);
    const rgb = Uint8Array.from([9, 8, 7]);
    const png = Uint8Array.from([1, 2, 3, 4]);

    await assert.rejects(
      runBookCoverPngPipeline(
        { title: "x", name: "" },
        { strokeWidthPx: 1, lineGapPx: 1 },
        {
          services: {
            async render() {
              return rendered;
            },
            extract(value) {
              value.dispose();
              return rgb;
            },
            async encode() {
              return png;
            },
            verify,
          },
        },
      ),
      /verification failed|verify failed/,
    );

    assert.deepEqual(Array.from(rgb), [0, 0, 0]);
  }
});

test("invalid encoded bytes fail before verification and wipe RGB", async () => {
  const log = [];
  const rendered = renderedRecord(log);
  const rgb = Uint8Array.from([5, 4, 3]);
  let verified = false;

  await assert.rejects(
    runBookCoverPngPipeline(
      { title: "x", name: "" },
      { strokeWidthPx: 1, lineGapPx: 1 },
      {
        services: {
          async render() {
            return rendered;
          },
          extract(value) {
            value.dispose();
            return rgb;
          },
          async encode() {
            return new Uint8Array();
          },
          async verify() {
            verified = true;
            return { ok: true };
          },
        },
      },
    ),
    /PNG bytes required/,
  );

  assert.equal(verified, false);
  assert.deepEqual(Array.from(rgb), [0, 0, 0]);
});

test("abort after render disposes renderer and stops before extraction", async () => {
  const log = [];
  const rendered = renderedRecord(log);
  const controller = new AbortController();
  let extracted = false;

  await assert.rejects(
    runBookCoverPngPipeline(
      { title: "x", name: "" },
      { strokeWidthPx: 1, lineGapPx: 1 },
      {
        signal: controller.signal,
        services: {
          async render() {
            controller.abort();
            return rendered;
          },
          extract() {
            extracted = true;
            return Uint8Array.from([1]);
          },
          async encode() {
            return Uint8Array.from([1]);
          },
          async verify() {
            return { ok: true };
          },
        },
      },
    ),
    /pipeline aborted/,
  );

  assert.equal(extracted, false);
  assert.equal(rendered.disposed, true);
});

test("missing pipeline services fail closed before rendering", async () => {
  await assert.rejects(
    runBookCoverPngPipeline(
      { title: "", name: "" },
      { strokeWidthPx: 0, lineGapPx: 0 },
      { services: {} },
    ),
    TypeError,
  );
});
