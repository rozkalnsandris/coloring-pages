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
      const match = /^\\[data-([a-z-]+)\\]$/.exec(selector);
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
      window: { print() { prints++; } } },
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
