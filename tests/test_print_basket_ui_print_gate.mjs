import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const source = readFileSync(new URL("../js/print-basket-ui.mjs", import.meta.url), "utf8");
const start = source.indexOf("function createDialog() {");
const end = source.indexOf("\nfunction setUnavailable(", start);
if (start < 0 || end <= start) throw new Error("Basket dialog source unavailable");

function node(tag) {
  return {
    tag, id: "", dataset: {}, attributes: {}, children: [], events: new Map(),
    disabled: false, hidden: false, textContent: "",
    setAttribute(key, value) { this.attributes[key] = value; },
    append(...items) { this.children.push(...items); },
    replaceChildren(...items) { this.children = items; },
    addEventListener(key, listener) { this.events.set(key, listener); },
    querySelector(selector) {
      const match = selector.startsWith("[data-") && selector.endsWith("]") ? [null, selector.slice(6, -1)] : null;
      if (!match) throw new Error("Unknown selector " + selector);
      const key = match[1].replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      const visit = element => {
        if (Object.hasOwn(element.dataset, key)) return element;
        for (const child of element.children) {
          const found = visit(child);
          if (found) return found;
        }
        return null;
      };
      return visit(this);
    },
  };
}
function sample(ids = []) {
  const appended = [];
  const document = {
    createElement: node,
    createDocumentFragment: () => node("fragment"),
    body: { append(item) { appended.push(item); } },
  };
  const entry = { id: "0000001", title: "Blume", thumb: "" };
  const basket = {
    ids, sheetCount: ids.length, droppedIds: [],
    pages: ids.length ? [{ activityId: "0000001", printUrl: "/media/0000001/print.png" }] : [],
  };
  function panelButton(text, action, id = "") {
    const button = node("button");
    button.type = "button";
    button.textContent = text;
    button.dataset.basketAction = action;
    if (id) button.dataset.basketId = id;
    return button;
  }
  let prints = 0;
  const dialog = vm.runInNewContext(
    source.slice(start, end) + "\nconst dialog = createDialog(); renderDialog(); dialog;",
    { document, panelButton, basket, catalogById: new Map([[entry.id, entry]]),
      bookCover: { enabled: false, title: "Mein Ausmalbuch", name: "" },
      window: { print() { prints++; } }, zipBusy: false },
  );
  assert.equal(appended.length, 1);
  assert.strictEqual(appended[0], dialog);
  return { dialog, get prints() { return prints; } };
}

test("empty basket exposes an accessible disabled Alles drucken option", () => {
  const { dialog } = sample();
  const print = dialog.querySelector("[data-basket-print]");
  const zip = dialog.querySelector("[data-basket-zip-prepare]");
  const note = dialog.children.find(child => child.id === "basket-print-unavailable");
  assert.equal(print.tag, "button");
  assert.equal(print.type, "button");
  assert.equal(print.textContent, "Alles drucken");
  assert.equal(print.dataset.basketAction, "print");
  assert.equal(print.disabled, true);
  assert.equal(print.attributes["aria-describedby"], "basket-print-unavailable");
  assert.equal(zip.disabled, true);
  assert.ok(note);
  assert.match(note.textContent, /noch nicht verfügbar/);
});

test("selection enables ZIP but never enables or triggers print before QA", () => {
  const state = sample(["0000001"]);
  const print = state.dialog.querySelector("[data-basket-print]");
  const zip = state.dialog.querySelector("[data-basket-zip-prepare]");
  assert.equal(zip.disabled, false);
  assert.equal(print.disabled, true);
  state.dialog.events.get("click")({ target: { closest: () => print } });
  assert.equal(state.prints, 0);
});

test("the basket UI has no print trigger or print-session wiring", () => {
  const liveCode = source.split("\n").filter(line =>
    !line.trimStart().startsWith("//")).join("\n");
  assert.equal(liveCode.includes("window.print("), false);
  assert.equal(liveCode.includes("stageCurrentBasketPrintSession("), false);
});


const zipStart = source.indexOf("function resetZip() {");
const zipEnd = source.indexOf("\nfunction createDialog() {", zipStart);
if (zipStart < 0 || zipEnd <= zipStart) throw new Error("ZIP UI source unavailable");

function zipScenario({ driftDuringFetch = false, failInsert = false } = {}) {
  const id = "0000001";
  const page = { activityId: id, pageIndex: 1, printUrl: "/media/0000001/print.png" };
  let stored = [id], allocations = 0, disposals = 0;
  const prepare = { disabled: false };
  const cancel = { disabled: true };
  const message = { textContent: "" };
  const slot = {
    children: [],
    replaceChildren(...nodes) {
      if (failInsert && nodes.length) throw new Error("DOM insertion failed");
      this.children = nodes;
    },
  };
  const controls = {
    "[data-basket-zip-prepare]": prepare,
    "[data-basket-zip-cancel]": cancel,
    "[data-basket-zip-status]": message,
    "[data-basket-zip-link]": slot,
  };
  const dialog = { open: true, querySelector: selector => controls[selector] || null };
  const context = {
    dialog, basket: { ids: [id], pages: [page], sheetCount: 1 },
    bookCover: { enabled: false, title: "Mein Ausmalbuch", name: "" },
    window: { location: { origin: "https://ausmalwiese.de" } },
    readStoredBasketIds: () => [...stored],
    fetch: async () => ({ ok: true, redirected: false, json: async () => [] }),
    expandBasketForExport: () => [page],
    prepareBasketPngZip: async () => {
      if (driftDuringFetch) stored = ["0000002"];
      return { bytes: new Uint8Array([1]) };
    },
    stageBasketZipDownloadLink: () => {
      allocations++;
      return {
        link: { className: "", remove() {} },
        dispose() { disposals++; },
      };
    },
    AbortController,
    zipEpoch: 0, zipController: null, zipBusy: false, stagedZip: null,
  };
  vm.runInNewContext(
    source.slice(zipStart, zipEnd) + "\nthis.runZip = prepareZip;",
    context,
  );
  return {
    run: () => context.runZip(), message, slot, prepare, cancel,
    get allocations() { return allocations; },
    get disposals() { return disposals; },
  };
}

test("ZIP link appears for a stable completed selection", async () => {
  const caseZip = zipScenario();
  await caseZip.run();
  assert.equal(caseZip.allocations, 1);
  assert.equal(caseZip.disposals, 0);
  assert.equal(caseZip.slot.children.length, 1);
  assert.match(caseZip.message.textContent, /ZIP bereit/);
  assert.equal(caseZip.cancel.disabled, true);
  assert.equal(caseZip.prepare.disabled, false);
});

test("ZIP link is withheld if tab selection changes while PNGs load", async () => {
  const caseZip = zipScenario({ driftDuringFetch: true });
  await caseZip.run();
  assert.equal(caseZip.allocations, 0);
  assert.equal(caseZip.disposals, 0);
  assert.equal(caseZip.slot.children.length, 0);
  assert.match(caseZip.message.textContent, /konnte nicht vorbereitet/);
});

test("ZIP Blob URL is disposed if final DOM attachment fails", async () => {
  const caseZip = zipScenario({ failInsert: true });
  await caseZip.run();
  assert.equal(caseZip.allocations, 1);
  assert.equal(caseZip.disposals, 1);
  assert.equal(caseZip.slot.children.length, 0);
  assert.match(caseZip.message.textContent, /konnte nicht vorbereitet/);
});
