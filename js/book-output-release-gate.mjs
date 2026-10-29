// #199 explicit fail-closed release gate for visitor-facing book output actions.
// Source capability may exist before product release evidence. These defaults
// remain false until the corresponding real-browser/device/privacy/physical QA
// and owner review are recorded in canonical project evidence.
export const BOOK_OUTPUT_RELEASE = Object.freeze({
  coveredZip: false,
  combinedPrint: false,
});

// Reviewed source-only cover renderer configuration. This is not itself release
// evidence: long/invalid text still fails closed in the existing layout pipeline.
export const BOOK_COVER_BROWSER_RENDER_OPTIONS = Object.freeze({
  strokeWidthPx: 20,
  lineGapPx: 120,
});

function checkedRelease(release) {
  if (!release || typeof release !== "object" || Array.isArray(release) ||
      typeof release.coveredZip !== "boolean" ||
      typeof release.combinedPrint !== "boolean") {
    throw new TypeError("Valid book output release flags required");
  }
  return release;
}

export function planBookOutputControls(
  {
    basketSheetCount,
    coverEnabled,
    busy = false,
    release = BOOK_OUTPUT_RELEASE,
  } = {},
) {
  if (!Number.isInteger(basketSheetCount) ||
      basketSheetCount < 0 || basketSheetCount > 5 ||
      typeof coverEnabled !== "boolean" ||
      typeof busy !== "boolean") {
    throw new TypeError("Valid book output control state required");
  }
  const flags = checkedRelease(release);
  const hasSelection = basketSheetCount > 0;

  const zipEnabled = hasSelection &&
    !busy &&
    (!coverEnabled || flags.coveredZip);
  const printEnabled = hasSelection &&
    !busy &&
    flags.combinedPrint;

  return Object.freeze({
    zipEnabled,
    printEnabled,
    zipStatus: coverEnabled && !flags.coveredZip
      ? "ZIP mit Deckblatt ist noch nicht verfügbar."
      : "",
    printStatus: flags.combinedPrint
      ? ""
      : "Alles drucken ist noch nicht verfügbar.",
  });
}
