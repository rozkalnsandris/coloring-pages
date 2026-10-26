// #199 pure in-memory cover draft state for "Mein Malbuch erstellen".
// Deliberately no DOM, storage, network, rendering, ZIP, or print side effects.
import { planBookSheetCapacity } from "./book-cover-capacity.mjs";

export const DEFAULT_BOOK_COVER_TITLE = "Mein Ausmalbuch";

function checkedState(state) {
  if (!state || typeof state !== "object" ||
      typeof state.enabled !== "boolean" ||
      typeof state.title !== "string" ||
      typeof state.name !== "string") {
    throw new TypeError("Valid in-memory book cover state required");
  }
  return state;
}

export function createBookCoverState() {
  return Object.freeze({
    enabled: false,
    title: DEFAULT_BOOK_COVER_TITLE,
    name: "",
  });
}

// Keep user-entered text exactly as text. A later renderer must use text-safe
// APIs (never HTML parsing) and separately prove layout/overflow/A4 quality.
export function updateBookCoverText(state, changes = {}) {
  const current = checkedState(state);
  if (!changes || typeof changes !== "object" || Array.isArray(changes)) {
    throw new TypeError("Cover text changes must be an object");
  }
  const title = Object.hasOwn(changes, "title") ? changes.title : current.title;
  const name = Object.hasOwn(changes, "name") ? changes.name : current.name;
  if (typeof title !== "string" || typeof name !== "string") {
    throw new TypeError("Cover title and name must be strings");
  }
  if (title === current.title && name === current.name) return current;
  return Object.freeze({ enabled: current.enabled, title, name });
}

// Enabling the cover is allowed only when the current fresh published
// selection still fits the shared five-physical-sheet contract. This helper
// does not mutate the basket and does not persist the draft.
export function setBookCoverEnabled(state, enabled, savedIds, freshCatalog) {
  const current = checkedState(state);
  if (typeof enabled !== "boolean") {
    throw new TypeError("Cover enabled flag must be a boolean");
  }
  planBookSheetCapacity(savedIds, freshCatalog, { coverEnabled: enabled });
  if (enabled === current.enabled) return current;
  return Object.freeze({
    enabled,
    title: current.title,
    name: current.name,
  });
}
