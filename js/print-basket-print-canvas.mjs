// Source-only A4 canvas staging for #206 cross-activity print.
// Input comes from decodeBasketPrintMedia after fresh-catalogue/PNG checks.
// This does NOT attach DOM, build the mandatory QR/text footer, enable the
// visitor print action, alter the original PNG bytes or assert browser A4 QA.
// Full-sheet canvases may consume ~174 MiB for five pages: keep the five-sheet
// limit and require constrained-mobile/browser testing before UI activation.

const MAX_SHEETS = 5;
export const MAX_BASKET_CANVAS_BYTES = 180 * 1024 * 1024;
const A4 = new Set(["2480x3508", "3508x2480"]);

function checkDecodedSet(decoded) {
  const plan = decoded?.plan, sheets = decoded?.sheets;
  if (!decoded || decoded.released || typeof decoded.release !== "function" ||
      !plan || !Array.isArray(plan.pages) || !Array.isArray(plan.imageUrls) ||
      !Number.isInteger(plan.sheetCount) ||
      plan.sheetCount < 1 || plan.sheetCount > MAX_SHEETS ||
      plan.pages.length !== plan.sheetCount ||
      plan.imageUrls.length !== plan.sheetCount ||
      !Array.isArray(sheets) || sheets.length !== plan.sheetCount) {
    throw new TypeError("Complete, unreleased A4 decoder output required");
  }
  let pixels = 0;
  const unique = new Set();
  for (let i = 0; i < sheets.length; i++) {
    const sheet = sheets[i], page = plan.pages[i];
    const size = sheet && sheet.width + "x" + sheet.height;
    if (!page || !sheet || sheet.page !== page ||
        typeof page.printUrl !== "string" ||
        page.printUrl !== plan.imageUrls[i] ||
        unique.has(page.printUrl) ||
        !Number.isInteger(sheet.width) || !Number.isInteger(sheet.height) ||
        !A4.has(size) || sheet.orientation !== (sheet.width > sheet.height ? "landscape" : "portrait") ||
        !sheet.bitmap || sheet.bitmap.width !== sheet.width ||
        sheet.bitmap.height !== sheet.height ||
        typeof sheet.bitmap.close !== "function") {
      throw new TypeError("Changed, repeated or invalid decoded A4 print page");
    }
    unique.add(page.printUrl);
    pixels += sheet.width * sheet.height * 4;
    if (pixels > MAX_BASKET_CANVAS_BYTES) throw new RangeError("A4 canvas memory budget exceeded");
  }
  return sheets;
}

function clearCanvases(records) {
  for (const { canvas } of records) {
    try { canvas.width = 0; canvas.height = 0; } catch { /* best effort */ }
  }
}

// Allocates DETACHED A4 sheets. A later review must attach the existing
// approved print-only branding/QR footer and test mixed-orientation pagination.
// The owner of this return value must dispose after printing / view close.
// decoded.release() is always called, even on failed drawing or cancellation.
export function stageBasketPrintCanvases(
  decoded, { documentRef = globalThis.document, signal } = {},
) {
  const records = [];
  try {
    if (signal?.aborted) throw new Error("A4 canvas staging aborted");
    const sheets = checkDecodedSet(decoded);
    if (typeof documentRef?.createElement !== "function") {
      throw new TypeError("Browser document unavailable");
    }

    for (let i = 0; i < sheets.length; i++) {
      if (signal?.aborted) throw new Error("A4 canvas staging aborted");
      const sheet = sheets[i];
      const canvas = documentRef.createElement("canvas");
      if (!canvas || typeof canvas.getContext !== "function") {
        throw new TypeError("A4 canvas unavailable");
      }
      // Track allocations before any drawing: a failed getContext/drawImage
      // must not retain one giant partially rendered raster.
      records.push({ canvas });
      canvas.width = sheet.width;
      canvas.height = sheet.height;
      canvas.setAttribute("aria-hidden", "true");
      const context = canvas.getContext("2d", { alpha: false });
      if (!context || typeof context.fillRect !== "function" ||
          typeof context.drawImage !== "function") {
        throw new TypeError("A4 canvas context unavailable");
      }
      // Fill opaque white, then copy each bitmap at native pixel dimensions;
      // never canvas.toDataURL/toBlob, shrink, rotate or re-encode the PNG.
      context.fillStyle = "#fff";
      context.fillRect(0, 0, sheet.width, sheet.height);
      context.drawImage(sheet.bitmap, 0, 0, sheet.width, sheet.height);
      if (signal?.aborted) throw new Error("A4 canvas staging aborted");

      const section = documentRef.createElement("section");
      const artwork = documentRef.createElement("div");
      if (!section || !artwork || typeof section.setAttribute !== "function" ||
          typeof artwork.append !== "function" || typeof section.append !== "function") {
        throw new TypeError("A4 sheet structure unavailable");
      }
      section.className = "print-sheet is-" + sheet.orientation;
      section.setAttribute("aria-label", "A4-Druckseite " + (i + 1) + " von " + sheets.length);
      artwork.className = "print-artwork";
      artwork.append(canvas);
      section.append(artwork);
      records[i].element = section;
      records[i].page = sheet.page;
      records[i].orientation = sheet.orientation;
    }

    if (signal?.aborted) throw new Error("A4 canvas staging aborted");
    const staged = Object.freeze(records.map(({ element, page, orientation }) =>
      Object.freeze({ element, page, orientation }),
    ));
    let disposed = false;
    return Object.freeze({
      plan: decoded.plan,
      sheets: staged,
      get disposed() { return disposed; },
      dispose() {
        if (disposed) return;
        disposed = true;
        clearCanvases(records);
      },
    });
  } catch (error) {
    clearCanvases(records);
    throw error;
  } finally {
    // Avoid holding five large ImageBitmaps alongside five large canvases.
    try { decoded?.release?.(); } catch { /* only best effort on faulty input */ }
  }
}
