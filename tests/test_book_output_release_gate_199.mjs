import test from "node:test";
import assert from "node:assert/strict";
import {
  BOOK_COVER_BROWSER_RENDER_OPTIONS,
  BOOK_OUTPUT_RELEASE,
  planBookOutputControls,
} from "../js/book-output-release-gate.mjs";

test("production release flags fail closed for covered ZIP and all combined printing", () => {
  assert.deepEqual(BOOK_OUTPUT_RELEASE, {
    coveredZip: false,
    combinedPrint: false,
  });
  assert.equal(Object.isFrozen(BOOK_OUTPUT_RELEASE), true);

  const plain = planBookOutputControls({
    basketSheetCount: 3,
    coverEnabled: false,
  });
  assert.equal(plain.zipEnabled, true, "existing coverless ZIP remains available");
  assert.equal(plain.printEnabled, false);
  assert.equal(plain.zipStatus, "");
  assert.match(plain.printStatus, /noch nicht verfügbar/);

  const covered = planBookOutputControls({
    basketSheetCount: 3,
    coverEnabled: true,
  });
  assert.equal(covered.zipEnabled, false);
  assert.equal(covered.printEnabled, false);
  assert.match(covered.zipStatus, /Deckblatt.*noch nicht verfügbar/);
});

test("hypothetical reviewed release can enable only the explicitly approved action", () => {
  const coveredZipOnly = planBookOutputControls({
    basketSheetCount: 2,
    coverEnabled: true,
    release: { coveredZip: true, combinedPrint: false },
  });
  assert.equal(coveredZipOnly.zipEnabled, true);
  assert.equal(coveredZipOnly.printEnabled, false);
  assert.equal(coveredZipOnly.zipStatus, "");

  const fullyReleased = planBookOutputControls({
    basketSheetCount: 2,
    coverEnabled: true,
    release: { coveredZip: true, combinedPrint: true },
  });
  assert.equal(fullyReleased.zipEnabled, true);
  assert.equal(fullyReleased.printEnabled, true);
  assert.equal(fullyReleased.printStatus, "");
});

test("empty or busy state disables every output even under hypothetical release", () => {
  const release = { coveredZip: true, combinedPrint: true };
  for (const state of [
    { basketSheetCount: 0, coverEnabled: false, busy: false },
    { basketSheetCount: 3, coverEnabled: false, busy: true },
    { basketSheetCount: 3, coverEnabled: true, busy: true },
  ]) {
    const result = planBookOutputControls({ ...state, release });
    assert.equal(result.zipEnabled, false);
    assert.equal(result.printEnabled, false);
  }
});

test("browser cover render options are fixed, finite and privacy-neutral", () => {
  assert.deepEqual(BOOK_COVER_BROWSER_RENDER_OPTIONS, {
    strokeWidthPx: 20,
    lineGapPx: 120,
  });
  assert.equal(Object.isFrozen(BOOK_COVER_BROWSER_RENDER_OPTIONS), true);
  assert.equal(JSON.stringify(BOOK_COVER_BROWSER_RENDER_OPTIONS).includes("name"), false);
  assert.equal(JSON.stringify(BOOK_COVER_BROWSER_RENDER_OPTIONS).includes("title"), false);
});

test("invalid control/release state fails closed", () => {
  for (const input of [
    undefined,
    {},
    { basketSheetCount: -1, coverEnabled: false },
    { basketSheetCount: 6, coverEnabled: false },
    { basketSheetCount: 1.5, coverEnabled: false },
    { basketSheetCount: 1, coverEnabled: "yes" },
    { basketSheetCount: 1, coverEnabled: false, busy: 1 },
    {
      basketSheetCount: 1,
      coverEnabled: false,
      release: { coveredZip: true },
    },
  ]) {
    assert.throws(() => planBookOutputControls(input), TypeError);
  }
});
