// #199 explicit fail-closed release gate for visitor-facing book output actions.
// Source capability may exist before product release evidence. These defaults
// remain false until the corresponding real-browser/device/privacy/physical QA
// and owner review are recorded in canonical project evidence.
export const BOOK_OUTPUT_RELEASE = Object.freeze({
  coveredZip: false,
  combinedPrint: false,
});

export const BOOK_OUTPUT_QA_OVERRIDE_KEY =
  "__AUSMALWIESE_BOOK_OUTPUT_QA_RELEASE__";

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

function isLoopbackQaLocation(locationRef) {
  return locationRef?.protocol === "http:" &&
    (locationRef?.hostname === "127.0.0.1" ||
     locationRef?.hostname === "localhost");
}

export function resolveBookOutputRelease({
  locationRef = globalThis.location,
  override = globalThis[BOOK_OUTPUT_QA_OVERRIDE_KEY],
} = {}) {
  if (override === undefined || override === null) return BOOK_OUTPUT_RELEASE;
  if (!isLoopbackQaLocation(locationRef)) return BOOK_OUTPUT_RELEASE;
  const checked = checkedRelease(override);
  return Object.freeze({
    coveredZip: checked.coveredZip,
    combinedPrint: checked.combinedPrint,
  });
}

export const BOOK_OUTPUT_ACTIVE_RELEASE = resolveBookOutputRelease();

export function planBookOutputControls(
  {
    basketSheetCount,
    coverEnabled,
    busy = false,
    release = BOOK_OUTPUT_ACTIVE_RELEASE,
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
