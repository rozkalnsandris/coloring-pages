import test from "node:test";
import assert from "node:assert/strict";
import { reconcileBasket } from "../js/print-basket-selection.mjs";
import { runBookOutputBundle } from "../js/book-output-bundle.mjs";

const one = id => ({
  id,
  title: "Malvorlage",
  print: "/media/" + id + "/print.png",
});
const previous = (ids, catalog) => reconcileBasket(ids, catalog);

function baseServices(overrides = {}) {
  return {
    async buildCoverPng() {
      return Uint8Array.from([9, 8, 7]);
    },
    async fetchArtwork(pages) {
      return pages.map(page => ({
        url: page.printUrl,
        bytes: Uint8Array.from([1, 2, 3]),
      }));
    },
    buildArtworkZip(pages) {
      return {
        bytes: Uint8Array.from([4, 5]),
        filenames: pages.map((page, i) =>
          String(i + 1).padStart(2, "0") + "-" + page.activityId + ".png"),
      };
    },
    buildBookZip(pages, downloads, coverPng) {
      return {
        bytes: Uint8Array.from([6, 7, 8]),
        filenames: [
          "00-deckblatt.png",
          ...pages.map((page, i) =>
            String(i + 1).padStart(2, "0") + "-" + page.activityId + ".png"),
        ],
      };
    },
    ...overrides,
  };
}

test("covered bundle sends personal text only to local cover renderer and returns generic ZIP name", async () => {
  const catalog = [one("1"), one("2")];
  const ids = ["2", "1"];
  const basket = previous(ids, catalog);
  const coverState = {
    enabled: true,
    title: "Mein Ausmalbuch",
    name: "Mia",
  };
  const calls = [];
  const coverBytes = Uint8Array.from([9, 8, 7]);
  const zipBytes = Uint8Array.from([6, 7, 8]);

  const result = await runBookOutputBundle(
    ids,
    catalog,
    basket,
    coverState,
    {
      origin: "https://ausmalwiese.de",
      coverRenderOptions: { strokeWidthPx: 20, lineGapPx: 100 },
      services: baseServices({
        async buildCoverPng(value, renderOptions) {
          calls.push(["cover", value, renderOptions]);
          return coverBytes;
        },
        async fetchArtwork(pages, options) {
          calls.push(["fetch", pages, options]);
          assert.equal(JSON.stringify(pages).includes("Mia"), false);
          assert.equal(JSON.stringify(options).includes("Mia"), false);
          assert.equal(JSON.stringify(options).includes("Mein Ausmalbuch"), false);
          return pages.map(page => ({
            url: page.printUrl,
            bytes: Uint8Array.from([1]),
          }));
        },
        buildBookZip(pages, downloads, png) {
          calls.push(["zip", png === coverBytes, pages.length, downloads.length]);
          return {
            bytes: zipBytes,
            filenames: ["00-deckblatt.png", "01-2.png", "02-1.png"],
          };
        },
      }),
    },
  );

  assert.deepEqual(calls.map(call => call[0]), ["cover", "fetch", "zip"]);
  assert.deepEqual(calls[0][1], {
    title: "Mein Ausmalbuch",
    name: "Mia",
  });
  assert.equal(result.plan.sheetCount, 3);
  assert.equal(JSON.stringify(result.plan).includes("Mia"), false);
  assert.deepEqual(result.zip.filenames, [
    "00-deckblatt.png", "01-2.png", "02-1.png",
  ]);
  assert.equal(result.coverPng, coverBytes);

  result.dispose();
  assert.equal(result.disposed, true);
  assert.deepEqual(Array.from(coverBytes), [0, 0, 0]);
  assert.deepEqual(Array.from(zipBytes), [0, 0, 0]);
  result.dispose();
});

test("coverless bundle never invokes local cover renderer", async () => {
  const catalog = [one("1")];
  const ids = ["1"];
  let coverCalls = 0;
  let bookZipCalls = 0;
  const result = await runBookOutputBundle(
    ids,
    catalog,
    previous(ids, catalog),
    { enabled: false, title: "Secret", name: "Mia" },
    {
      origin: "https://ausmalwiese.de",
      services: baseServices({
        async buildCoverPng() {
          coverCalls++;
          return Uint8Array.from([1]);
        },
        buildBookZip() {
          bookZipCalls++;
          throw new Error("must not build covered ZIP");
        },
      }),
    },
  );
  assert.equal(coverCalls, 0);
  assert.equal(bookZipCalls, 0);
  assert.equal(result.coverPng, null);
  assert.deepEqual(result.zip.filenames, ["01-1.png"]);
});

test("failure after cover generation wipes personalized cover bytes", async () => {
  const catalog = [one("1")];
  const ids = ["1"];
  const sensitive = Uint8Array.from([5, 6, 7]);

  await assert.rejects(
    runBookOutputBundle(
      ids,
      catalog,
      previous(ids, catalog),
      { enabled: true, title: "T", name: "N" },
      {
        origin: "https://ausmalwiese.de",
        coverRenderOptions: { strokeWidthPx: 1, lineGapPx: 1 },
        services: baseServices({
          async buildCoverPng() {
            return sensitive;
          },
          async fetchArtwork() {
            throw new Error("network failed");
          },
        }),
      },
    ),
    /network failed/,
  );
  assert.deepEqual(Array.from(sensitive), [0, 0, 0]);
});

test("abort after cover generation stops before artwork fetch and wipes cover", async () => {
  const catalog = [one("1")];
  const ids = ["1"];
  const controller = new AbortController();
  const sensitive = Uint8Array.from([9, 9, 9]);
  let fetched = false;

  await assert.rejects(
    runBookOutputBundle(
      ids,
      catalog,
      previous(ids, catalog),
      { enabled: true, title: "T", name: "N" },
      {
        origin: "https://ausmalwiese.de",
        signal: controller.signal,
        coverRenderOptions: { strokeWidthPx: 1, lineGapPx: 1 },
        services: baseServices({
          async buildCoverPng() {
            controller.abort();
            return sensitive;
          },
          async fetchArtwork() {
            fetched = true;
            return [];
          },
        }),
      },
    ),
    /preparation aborted/,
  );
  assert.equal(fetched, false);
  assert.deepEqual(Array.from(sensitive), [0, 0, 0]);
});

test("five artwork sheets plus cover reject before any output service runs", async () => {
  const catalog = ["1", "2", "3", "4", "5"].map(one);
  const ids = ["1", "2", "3", "4", "5"];
  let calls = 0;
  const services = baseServices({
    async buildCoverPng() { calls++; return Uint8Array.from([1]); },
    async fetchArtwork() { calls++; return []; },
    buildBookZip() { calls++; return { bytes: new Uint8Array([1]), filenames: [] }; },
  });

  await assert.rejects(
    runBookOutputBundle(
      ids,
      catalog,
      previous(ids, catalog),
      { enabled: true, title: "T", name: "N" },
      {
        origin: "https://ausmalwiese.de",
        coverRenderOptions: { strokeWidthPx: 1, lineGapPx: 1 },
        services,
      },
    ),
    /exceed five physical A4 sheets/,
  );
  assert.equal(calls, 0);
});
