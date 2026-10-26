import test from "node:test";
import assert from "node:assert/strict";
import {
  DEFAULT_BOOK_COVER_TITLE, createBookCoverState,
  updateBookCoverText, setBookCoverEnabled,
} from "../js/book-cover-state.mjs";

const one = (id) => ({ id, title: "Malvorlage", print: `/media/${id}/print.png` });
const two = (id) => ({
  id, title: "Cut & Paste",
  pages: [
    { print: `/media/${id}/print-1.png` },
    { print: `/media/${id}/print-2.png` },
  ],
});

test("default cover draft is disabled, local-only data and frozen", () => {
  const state = createBookCoverState();
  assert.equal(DEFAULT_BOOK_COVER_TITLE, "Mein Ausmalbuch");
  assert.deepEqual(state, { enabled: false, title: "Mein Ausmalbuch", name: "" });
  assert.equal(Object.isFrozen(state), true);
});

test("text updates preserve German and literal text without toggling cover", () => {
  const initial = createBookCoverState();
  const changed = updateBookCoverText(initial, {
    title: "Äpfel, Öl & Grüße <3",
    name: "Lina Marie",
  });
  assert.deepEqual(changed, {
    enabled: false,
    title: "Äpfel, Öl & Grüße <3",
    name: "Lina Marie",
  });
  assert.equal(Object.isFrozen(changed), true);
  assert.deepEqual(initial, { enabled: false, title: "Mein Ausmalbuch", name: "" });
  assert.strictEqual(updateBookCoverText(changed, {}), changed, "no-op is idempotent");
});

test("text model accepts empty/long strings but rejects non-text values", () => {
  const state = createBookCoverState();
  const longTitle = "B".repeat(400);
  const changed = updateBookCoverText(state, { title: "", name: longTitle });
  assert.equal(changed.title, "");
  assert.equal(changed.name, longTitle);
  for (const changes of [
    { title: null }, { title: 7 }, { name: undefined }, { name: {} },
  ]) {
    assert.throws(() => updateBookCoverText(state, changes), TypeError);
  }
  assert.throws(() => updateBookCoverText(state, null), TypeError);
  assert.throws(() => updateBookCoverText(state, []), TypeError);
});

test("cover enables only when one of five A4 sheet slots remains", () => {
  const catalog = [one("1"), one("2"), two("cut-1")];
  const state = updateBookCoverText(createBookCoverState(), {
    title: "Mein Herbstbuch", name: "Mia",
  });
  const enabled = setBookCoverEnabled(state, true, ["cut-1", "1", "2"], catalog);
  assert.deepEqual(enabled, {
    enabled: true, title: "Mein Herbstbuch", name: "Mia",
  });
  assert.equal(Object.isFrozen(enabled), true);
  assert.strictEqual(
    setBookCoverEnabled(enabled, true, ["cut-1", "1", "2"], catalog),
    enabled,
    "same enabled state is idempotent after fresh capacity validation",
  );
});

test("full five-sheet basket rejects cover without changing prior draft", () => {
  const catalog = [two("cut-1"), one("1"), one("2"), one("3")];
  const ids = ["cut-1", "1", "2", "3"];
  const state = updateBookCoverText(createBookCoverState(), { name: "Noah" });
  assert.throws(() => setBookCoverEnabled(state, true, ids, catalog), RangeError);
  assert.deepEqual(state, { enabled: false, title: "Mein Ausmalbuch", name: "Noah" });
});

test("enabled cover can be disabled while retaining draft text", () => {
  const catalog = [one("1")];
  const draft = updateBookCoverText(createBookCoverState(), {
    title: "Mein Tierbuch", name: "Léa",
  });
  const enabled = setBookCoverEnabled(draft, true, ["1"], catalog);
  const disabled = setBookCoverEnabled(enabled, false, ["1"], catalog);
  assert.deepEqual(disabled, {
    enabled: false, title: "Mein Tierbuch", name: "Léa",
  });
});

test("cover toggle fails closed on stale catalogue and invalid state/flag", () => {
  const state = createBookCoverState();
  assert.throws(() => setBookCoverEnabled(state, true, ["gone"], [one("1")]));
  assert.throws(() => setBookCoverEnabled(state, true, ["1"], [one("1"), one("1")]));
  assert.throws(() => setBookCoverEnabled(state, "true", ["1"], [one("1")]), TypeError);
  assert.throws(() => setBookCoverEnabled({}, false, [], []), TypeError);
});
