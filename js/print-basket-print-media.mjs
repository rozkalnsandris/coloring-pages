// Source-only cross-activity print media preparation for #206.
// Reuse the reviewed basket print plan and ZIP's bounded same-origin PNG reader.
// This is a transport/PNG-structure preflight, NOT decoded print sheets.
// A later renderer must decode all images and verify actual A4 pagination,
// mixed orientations, footer/QR and browser printing before enabling a click.
import { buildBasketPrintPlan } from "./print-basket-print-plan.mjs";
import { fetchBasketPrintPngBytes } from "./print-basket-zip-fetch.mjs";

export async function prepareBasketPrintMedia(
  savedIds, freshCatalog, previousBasket, { origin, fetcher, signal } = {},
) {
  // Reject stale selection, replaced print paths and sheet-count drift before IO.
  const plan = buildBasketPrintPlan(savedIds, freshCatalog, previousBasket);
  const downloads = await fetchBasketPrintPngBytes(plan.pages, {
    origin, fetcher, signal,
  });
  if (signal?.aborted) throw new Error("Print media preparation aborted");
  if (downloads.length !== plan.sheetCount) {
    throw new Error("Incomplete print media set");
  }

  // All PNGs were structurally checked, including CRC and A4 RGB dimensions.
  // The byte buffers are owned by the caller and never changed here.
  const sheets = downloads.map((download, index) => {
    const page = plan.pages[index];
    if (download.url !== page.printUrl || !(download.bytes instanceof Uint8Array)) {
      throw new Error("Print media order or byte identity mismatch");
    }
    const view = new DataView(
      download.bytes.buffer, download.bytes.byteOffset, download.bytes.byteLength,
    );
    const width = view.getUint32(16, false);
    const height = view.getUint32(20, false);
    const orientation = width > height ? "landscape" : "portrait";
    return Object.freeze({ page, bytes: download.bytes, width, height, orientation });
  });
  if (signal?.aborted) throw new Error("Print media preparation aborted");
  return Object.freeze({ plan, sheets: Object.freeze(sheets) });
}
