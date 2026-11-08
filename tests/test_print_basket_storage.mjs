import test from "node:test";
import assert from "node:assert/strict";
import {
  BASKET_STORAGE_KEY,
  readStoredBasketIds,
  writeStoredBasketIds,
  clearStoredBasketIds,
  restoreStoredBasket,
} from "../js/print-basket-storage.mjs";

class FakeStorage {
  constructor(initial = {}) {
    this.values = new Map(Object.entries(initial));
    this.setCalls = 0;
    this.removeCalls = 0;
  }
  getItem(key) {
    return this.values.has(key) ? this.values.get(key) : null;
  }
  setItem(key, value) {
    this.setCalls += 1;
    this.values.set(key, String(value));
  }
  removeItem(key) {
    this.removeCalls += 1;
    this.values.delete(key);
  }
}

function withSessionStorage(storage, callback) {
  const previous = Object.getOwnPropertyDescriptor(globalThis, "sessionStorage");
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    writable: true,
    value: storage,
  });
  try {
    return callback();
  } finally {
    if (previous) Object.defineProperty(globalThis, "sessionStorage", previous);
    else delete globalThis.sessionStorage;
  }
}

const one = (id) => ({ id, title: "Malvorlage", print: `/media/${id}/print.png` });
const multi = (id) => ({
  id,
  title: "Ausschneiden und kleben",
  pages: [
    { print: `/media/${id}/print-1.png` },
    { print: `/media/${id}/print-2.png` },
  ],
});

test("empty tab has no stored basket and performs no write", () => {
  const storage = new FakeStorage();
  withSessionStorage(storage, () => {
    assert.deepEqual(readStoredBasketIds(), []);
    assert.equal(storage.setCalls, 0);
    assert.equal(storage.removeCalls, 0);
  });
});

test("storage contains only the ordered catalogue ID array", () => {
  const storage = new FakeStorage();
  withSessionStorage(storage, () => {
    assert.deepEqual(writeStoredBasketIds(["0000001", "cut-2"]), ["0000001", "cut-2"]);
    assert.equal(storage.values.get(BASKET_STORAGE_KEY), '["0000001","cut-2"]');
    assert.deepEqual(readStoredBasketIds(), ["0000001", "cut-2"]);
  });
});

test("empty write removes the tab-scoped key instead of persisting noise", () => {
  const storage = new FakeStorage({ [BASKET_STORAGE_KEY]: '["1"]' });
  withSessionStorage(storage, () => {
    assert.deepEqual(writeStoredBasketIds([]), []);
    assert.equal(storage.values.has(BASKET_STORAGE_KEY), false);
    assert.equal(storage.removeCalls, 1);
  });
});

test("malformed, duplicate and unsafe stored values fail closed without rewriting them", () => {
  const badValues = [
    "{",
    "{}",
    '["1","1"]',
    '["../1"]',
    '["1",null]',
    '["1","2","3","4","5","6"]',
  ];
  for (const raw of badValues) {
    const storage = new FakeStorage({ [BASKET_STORAGE_KEY]: raw });
    withSessionStorage(storage, () => {
      assert.throws(() => readStoredBasketIds());
      assert.equal(storage.values.get(BASKET_STORAGE_KEY), raw);
      assert.equal(storage.setCalls, 0);
      assert.equal(storage.removeCalls, 0);
    });
  }
});

test("writes reject invalid caller state before touching sessionStorage", () => {
  const storage = new FakeStorage();
  withSessionStorage(storage, () => {
    assert.throws(() => writeStoredBasketIds(["1", "1"]));
    assert.throws(() => writeStoredBasketIds(["1", "https://example.com/x"]));
    assert.throws(() => writeStoredBasketIds(["1", "2", "3", "4", "5", "6"]));
    assert.equal(storage.setCalls, 0);
    assert.equal(storage.removeCalls, 0);
  });
});

test("fresh catalogue reconciliation prunes missing IDs and persists the reviewed order", () => {
  const storage = new FakeStorage({ [BASKET_STORAGE_KEY]: '["2","gone","1"]' });
  withSessionStorage(storage, () => {
    const state = restoreStoredBasket([one("1"), one("2")]);
    assert.deepEqual(state.ids, ["2", "1"]);
    assert.deepEqual(state.droppedIds, ["gone"]);
    assert.equal(state.sheetCount, 2);
    assert.equal(storage.values.get(BASKET_STORAGE_KEY), '["2","1"]');
    assert.equal(storage.setCalls, 1);
  });
});

test("multi-page activity is pruned atomically when restored state exceeds five sheets", () => {
  const storage = new FakeStorage({ [BASKET_STORAGE_KEY]: '["1","2","3","4","cut-1"]' });
  withSessionStorage(storage, () => {
    const state = restoreStoredBasket([one("1"), one("2"), one("3"), one("4"), multi("cut-1")]);
    assert.deepEqual(state.ids, ["1", "2", "3", "4"]);
    assert.deepEqual(state.droppedIds, ["cut-1"]);
    assert.equal(state.sheetCount, 4);
    assert.equal(storage.values.get(BASKET_STORAGE_KEY), '["1","2","3","4"]');
  });
});

test("valid restored state is not rewritten on every page load", () => {
  const storage = new FakeStorage({ [BASKET_STORAGE_KEY]: '["cut-1","2"]' });
  withSessionStorage(storage, () => {
    const state = restoreStoredBasket([multi("cut-1"), one("2")]);
    assert.deepEqual(state.ids, ["cut-1", "2"]);
    assert.equal(state.sheetCount, 3);
    assert.equal(storage.setCalls, 0);
    assert.equal(storage.removeCalls, 0);
  });
});

test("failed catalogue validation cannot silently clear a saved selection", () => {
  const raw = '["1","2"]';
  const storage = new FakeStorage({ [BASKET_STORAGE_KEY]: raw });
  withSessionStorage(storage, () => {
    assert.throws(() => restoreStoredBasket(null), TypeError);
    assert.equal(storage.values.get(BASKET_STORAGE_KEY), raw);
    assert.equal(storage.setCalls, 0);
    assert.equal(storage.removeCalls, 0);
  });
});

test("clear removes only the basket key", () => {
  const storage = new FakeStorage({
    [BASKET_STORAGE_KEY]: '["1"]',
    unrelated: "keep",
  });
  withSessionStorage(storage, () => {
    clearStoredBasketIds();
    assert.equal(storage.values.has(BASKET_STORAGE_KEY), false);
    assert.equal(storage.values.get("unrelated"), "keep");
  });
});

test("unavailable sessionStorage fails closed", () => {
  withSessionStorage(undefined, () => {
    assert.throws(() => readStoredBasketIds(), TypeError);
    assert.throws(() => writeStoredBasketIds(["1"]), TypeError);
    assert.throws(() => clearStoredBasketIds(), TypeError);
  });
});

test("legacy ID persists as new ID only after the new catalogue target exists", () => {
  const aliases={schema:"rozkalns.coloring-pages.legacy-id-aliases.v1",issue:457,source_catalog_sha256:"a".repeat(64),source_catalog_count:10,source_legacy_count:1,source_plan_manifest_sha256:"b".repeat(64),aliases_sha256:"c".repeat(64),aliases:[{old_id:"legacy-1",new_id:"1234567"}]};
  const storage=new FakeStorage({[BASKET_STORAGE_KEY]:'["legacy-1","1234567"]'});
  withSessionStorage(storage,()=>{const state=restoreStoredBasket([one("1234567")],aliases);assert.deepEqual(state.ids,["1234567"]);assert.equal(state.sheetCount,1);assert.equal(storage.values.get(BASKET_STORAGE_KEY),'["1234567"]');assert.equal(storage.setCalls,1);});
});
test("pre-cutover catalogue keeps a legacy basket ID unchanged", () => {
  const aliases={schema:"rozkalns.coloring-pages.legacy-id-aliases.v1",issue:457,source_catalog_sha256:"a".repeat(64),source_catalog_count:10,source_legacy_count:1,source_plan_manifest_sha256:"b".repeat(64),aliases_sha256:"c".repeat(64),aliases:[{old_id:"legacy-1",new_id:"1234567"}]};
  const storage=new FakeStorage({[BASKET_STORAGE_KEY]:'["legacy-1"]'});
  withSessionStorage(storage,()=>{const state=restoreStoredBasket([one("legacy-1")],aliases);assert.deepEqual(state.ids,["legacy-1"]);assert.equal(storage.values.get(BASKET_STORAGE_KEY),'["legacy-1"]');assert.equal(storage.setCalls,0);});
});
