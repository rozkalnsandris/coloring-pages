// #206 source-only print lifecycle gate for an already validated staged basket.
// This module is deliberately NOT imported by print-basket-ui.mjs. It cannot
// fetch catalogue/media, enable a button, mutate storage, or record analytics.
// A future reviewed UI integration may call it from one explicit visitor action.
//
// MDN documents window.print() as blocking while the print dialog is open.
// Cleanup therefore happens immediately after print() returns (or throws).
// afterprint is not treated as proof that paper was physically printed.
const MAX_SHEETS = 5;

function checkedStagedDocument(staged) {
  const plan = staged?.plan;
  const sheets = staged?.sheets;
  if (!staged || staged.disposed || typeof staged.dispose !== "function" ||
      !plan || !Array.isArray(plan.pages) ||
      !Number.isInteger(plan.sheetCount) ||
      plan.sheetCount < 1 || plan.sheetCount > MAX_SHEETS ||
      !Array.isArray(sheets) || sheets.length !== plan.sheetCount ||
      plan.pages.length !== plan.sheetCount) {
    throw new TypeError("Complete undisposed staged print document required");
  }

  const elements = new Set();
  const urls = new Set();
  for (let index = 0; index < sheets.length; index++) {
    const sheet = sheets[index];
    const page = plan.pages[index];
    if (!sheet || sheet.page !== page ||
        !["portrait", "landscape"].includes(sheet.orientation) ||
        !sheet.element || typeof sheet.element.className !== "string" ||
        sheet.element.className !==
          "print-sheet is-" + sheet.orientation + " has-text-footer" ||
        sheet.element.isConnected || sheet.element.parentNode ||
        sheet.element.parentElement ||
        elements.has(sheet.element) ||
        typeof page?.printUrl !== "string" || !page.printUrl ||
        urls.has(page.printUrl)) {
      throw new TypeError("Detached ordered A4 print sheets required");
    }
    elements.add(sheet.element);
    urls.add(page.printUrl);
  }
  return sheets;
}

function checkedMount(mount) {
  if (!mount || mount.isConnected !== true ||
      typeof mount.replaceChildren !== "function" ||
      !Number.isInteger(mount.childElementCount) ||
      mount.childElementCount !== 0) {
    throw new TypeError("Empty connected print mount required");
  }
  return mount;
}

function clearMount(mount) {
  try { mount?.replaceChildren?.(); } catch { /* best effort after print attempt */ }
}

// Takes ownership of a VALID staged document. Once validation succeeds, every
// later exit path disposes its native A4 canvases exactly once.
// The caller must provide a dedicated empty connected mount whose print CSS
// hides unrelated page UI; that UI/CSS wiring is intentionally not built here.
export function printStagedBasketDocumentOnce(
  staged,
  { mount, print = globalThis.print, signal } = {},
) {
  let owned = false;
  let target;
  try {
    const sheets = checkedStagedDocument(staged);
    owned = true;
    target = checkedMount(mount);
    if (typeof print !== "function") {
      throw new TypeError("Browser print capability required");
    }
    if (signal?.aborted) throw new Error("Basket print aborted");

    target.replaceChildren(...sheets.map(sheet => sheet.element));
    if (signal?.aborted) throw new Error("Basket print aborted");

    print();
    return Object.freeze({
      sheetCount: sheets.length,
      orientations: Object.freeze(sheets.map(sheet => sheet.orientation)),
    });
  } finally {
    if (owned) {
      clearMount(target);
      try { staged.dispose(); } catch { /* best effort after print attempt */ }
    }
  }
}
