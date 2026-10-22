import { reconcileBasket } from "./print-basket-selection.mjs";

export const BASKET_STORAGE_KEY = "ausmalwiese-print-basket-v1";
const MAX_STORED_ACTIVITIES = 5;
const ACTIVITY_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function sessionStore() {
  const storage = globalThis.sessionStorage;
  if (
    !storage ||
    typeof storage.getItem !== "function" ||
    typeof storage.setItem !== "function" ||
    typeof storage.removeItem !== "function"
  ) {
    throw new TypeError("sessionStorage unavailable");
  }
  return storage;
}

function validateIds(ids) {
  if (!Array.isArray(ids)) throw new TypeError("Basket storage must contain an ID array");
  if (ids.length > MAX_STORED_ACTIVITIES) throw new RangeError("Stored basket exceeds activity limit");

  const seen = new Set();
  for (const id of ids) {
    if (typeof id !== "string" || !ACTIVITY_ID.test(id)) {
      throw new TypeError("Stored basket contains an invalid catalogue ID");
    }
    if (seen.has(id)) throw new TypeError("Stored basket contains duplicate catalogue IDs");
    seen.add(id);
  }
  return [...ids];
}

export function readStoredBasketIds() {
  const raw = sessionStore().getItem(BASKET_STORAGE_KEY);
  if (raw === null) return [];

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new TypeError("Stored basket JSON is invalid");
  }
  return validateIds(parsed);
}

export function writeStoredBasketIds(ids) {
  const valid = validateIds(ids);
  const storage = sessionStore();
  if (!valid.length) storage.removeItem(BASKET_STORAGE_KEY);
  else storage.setItem(BASKET_STORAGE_KEY, JSON.stringify(valid));
  return valid;
}

export function clearStoredBasketIds() {
  sessionStore().removeItem(BASKET_STORAGE_KEY);
}

export function restoreStoredBasket(catalog) {
  const savedIds = readStoredBasketIds();
  const state = reconcileBasket(savedIds, catalog);

  // Only a successfully loaded, valid fresh catalogue may prune stale IDs.
  // Catalogue errors throw inside reconcileBasket before storage is touched.
  if (state.droppedIds.length) writeStoredBasketIds(state.ids);
  return state;
}
