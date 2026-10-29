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
function planControls(
  { basketSheetCount, coverEnabled, busy = false },
  release = { coveredZip: false, combinedPrint: false },
) {
  const hasSelection = basketSheetCount > 0;
  return {
    zipEnabled: hasSelection && !busy && (!coverEnabled || release.coveredZip),
    printEnabled: hasSelection && !busy && release.combinedPrint,
    zipStatus: coverEnabled && !release.coveredZip
      ? "ZIP mit Deckblatt ist noch nicht verfügbar."
      : "",
    printStatus: release.combinedPrint
      ? ""
      : "Alles drucken ist noch nicht verfügbar.",
  };
}

function sample(ids = [], { release = { coveredZip: false, combinedPrint: false } } = {}) {
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
  const bookCover = { enabled: false, title: "Mein Ausmalbuch", name: "" };
  let prints = 0;
  const dialog = vm.runInNewContext(
    source.slice(start, end) + "\nconst dialog = createDialog(); renderDialog(); dialog;",
    { document, panelButton, basket, catalogById: new Map([[entry.id, entry]]),
      bookCover,
      bookSheetCount: () => basket.sheetCount + (bookCover.enabled ? 1 : 0),
      planBookOutputControls: state => planControls(state, release),
      BOOK_OUTPUT_RELEASE: release,
      BOOK_COVER_BROWSER_RENDER_OPTIONS: { strokeWidthPx: 20, lineGapPx: 120 },
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

test("production UI keeps direct print API absent and combined print behind release gate", () => {
  const liveCode = source.split("\n").filter(line =>
    !line.trimStart().startsWith("//")).join("\n");
  assert.equal(liveCode.includes("window.print"), false);
  assert.equal(liveCode.includes("printStagedBasketDocumentOnce("), false);
  assert.equal(liveCode.includes('from "./print-basket-print-host.mjs"'), true);
  assert.equal(liveCode.includes("printStagedDocumentInBasketHost(staged"), true);
  assert.equal(liveCode.includes("!BOOK_OUTPUT_RELEASE.combinedPrint"), true);
});


const printStart = source.indexOf("function resetPrint() {");
const printEnd = source.indexOf("\nfunction resetZip() {", printStart);
if (printStart < 0 || printEnd <= printStart) throw new Error("Print UI source unavailable");

function printScenario({ released = false, sessionFails = false, dialogOpen = true } = {}) {
  const id = "0000001";
  const action = { disabled: false };
  const note = { textContent: "" };
  const controls = {
    "[data-basket-print]": action,
    "#basket-print-unavailable": note,
  };
  const dialog = {
    open: dialogOpen,
    querySelector: selector => controls[selector] || null,
  };
  let sessions = 0, hosts = 0, disposals = 0, zipResets = 0;
  const staged = {
    disposed: false,
    dispose() {
      if (!this.disposed) disposals++;
      this.disposed = true;
    },
  };
  const context = {
    dialog,
    basket: {
      ids: [id],
      pages: [{ activityId: id, pageIndex: 1, pageCount: 1, printUrl: "/media/0000001/print.png" }],
      sheetCount: 1,
      droppedIds: [],
    },
    bookCover: { enabled: false, title: "Mein Ausmalbuch", name: "" },
    window: { location: { origin: "https://ausmalwiese.de" } },
    document: {},
    planBookOutputControls: state => planControls(state, {
      coveredZip: false,
      combinedPrint: released,
    }),
    BOOK_OUTPUT_RELEASE: {
      coveredZip: false,
      combinedPrint: released,
    },
    BOOK_COVER_BROWSER_RENDER_OPTIONS: { strokeWidthPx: 20, lineGapPx: 120 },
    prepareCurrentBookOutputSession: async () => {
      sessions++;
      if (sessionFails) throw new Error("session failed");
      return { resource: staged };
    },
    printStagedDocumentInBasketHost: resource => {
      hosts++;
      assert.strictEqual(resource, staged);
      staged.dispose();
      return { sheetCount: 1, orientations: ["portrait"] };
    },
    resetZip() { zipResets++; },
    AbortController,
    zipBusy: false,
    printController: null,
    printBusy: false,
    printEpoch: 0,
  };

  vm.runInNewContext(
    source.slice(printStart, printEnd) + "\nthis.runPrint = preparePrint;",
    context,
  );

  return {
    run: () => context.runPrint(),
    action,
    note,
    staged,
    get sessions() { return sessions; },
    get hosts() { return hosts; },
    get disposals() { return disposals; },
    get zipResets() { return zipResets; },
  };
}

test("production combined-print gate cannot start session, host or print resource", async () => {
  const value = printScenario({ released: false });
  await value.run();
  assert.equal(value.sessions, 0);
  assert.equal(value.hosts, 0);
  assert.equal(value.disposals, 0);
  assert.equal(value.zipResets, 0);
});

test("hypothetical reviewed combined-print release uses fresh session then isolated host once", async () => {
  const value = printScenario({ released: true });
  await value.run();
  assert.equal(value.sessions, 1);
  assert.equal(value.hosts, 1);
  assert.equal(value.disposals, 1);
  assert.equal(value.zipResets, 1);
  assert.equal(value.action.disabled, false);
  assert.match(value.note.textContent, /Druckdialog geschlossen/);
  assert.equal(value.staged.disposed, true);
});

test("print preparation failure never reaches host and restores the released action", async () => {
  const value = printScenario({ released: true, sessionFails: true });
  await value.run();
  assert.equal(value.sessions, 1);
  assert.equal(value.hosts, 0);
  assert.equal(value.disposals, 0);
  assert.equal(value.action.disabled, false);
  assert.match(value.note.textContent, /konnte nicht vorbereitet/);
});

test("closed dialog cannot start combined print even under hypothetical release", async () => {
  const value = printScenario({ released: true, dialogOpen: false });
  await value.run();
  assert.equal(value.sessions, 0);
  assert.equal(value.hosts, 0);
  assert.equal(value.zipResets, 0);
});


const zipStart = source.indexOf("function resetZip() {");
const zipEnd = source.indexOf("\nfunction createDialog() {", zipStart);
if (zipStart < 0 || zipEnd <= zipStart) throw new Error("ZIP UI source unavailable");

function zipScenario({
  driftDuringFetch = false,
  failInsert = false,
  coverEnabled = false,
  coveredZipReleased = false,
} = {}) {
  const id = "0000001";
  const page = { activityId: id, pageIndex: 1, printUrl: "/media/0000001/print.png" };
  let stored = [id], allocations = 0, disposals = 0, bookSessions = 0;
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
    bookCover: { enabled: coverEnabled, title: "Mein Ausmalbuch", name: "Mia" },
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
    prepareCurrentBookOutputSession: async () => {
      bookSessions++;
      allocations++;
      return {
        resource: {
          link: { className: "", remove() {} },
          dispose() { disposals++; },
        },
      };
    },
    planBookOutputControls: state => planControls(state, {
      coveredZip: coveredZipReleased,
      combinedPrint: false,
    }),
    BOOK_OUTPUT_RELEASE: {
      coveredZip: coveredZipReleased,
      combinedPrint: false,
    },
    BOOK_COVER_BROWSER_RENDER_OPTIONS: { strokeWidthPx: 20, lineGapPx: 120 },
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
    get bookSessions() { return bookSessions; },
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


test("covered ZIP remains disabled in production gate and cannot start a book session", async () => {
  const caseZip = zipScenario({ coverEnabled: true, coveredZipReleased: false });
  assert.equal(caseZip.prepare.disabled, false, "fixture starts neutral before reset/render");
  await caseZip.run();
  assert.equal(caseZip.bookSessions, 0);
  assert.equal(caseZip.allocations, 0);
  assert.equal(caseZip.slot.children.length, 0);
});

test("hypothetical covered-ZIP release uses the fresh book session and not coverless exporter", async () => {
  const caseZip = zipScenario({ coverEnabled: true, coveredZipReleased: true });
  await caseZip.run();
  assert.equal(caseZip.bookSessions, 1);
  assert.equal(caseZip.allocations, 1);
  assert.equal(caseZip.disposals, 0);
  assert.equal(caseZip.slot.children.length, 1);
  assert.match(caseZip.message.textContent, /ZIP bereit/);
  assert.equal(caseZip.cancel.disabled, true);
  assert.equal(caseZip.prepare.disabled, false);
});
