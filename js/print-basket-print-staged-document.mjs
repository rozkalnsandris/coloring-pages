// #206 source-only composition of already validated public A4 print PNGs.
// Caller MUST first use prepareBasketPrintMedia with a fresh catalog and
// unchanged session selection. Nothing here fetches, mounts or prints sheets.
// Up to five native-resolution canvases may consume roughly 174 MiB.
import { decodeBasketPrintMedia } from "./print-basket-print-decode.mjs";
import { stageBasketPrintCanvases } from "./print-basket-print-canvas.mjs";
import { stageBasketPrintTextFooters } from "./print-basket-print-footer.mjs";

// Compose one complete, ordered set of detached A4 sections with safe text
// branding. Caller owns result.dispose() after the eventual print/close path.
// Decode closes ImageBitmaps; canvas/footer stages manage their own lifetimes.
// A future UI integration still needs physical/browser pagination and margins QA.
export async function stagePreparedBasketPrintDocument(
  prepared,
  { decode, blobFactory, documentRef = globalThis.document, signal } = {},
) {
  const decoded = await decodeBasketPrintMedia(prepared, {
    decode, blobFactory, signal,
  });
  let canvases;
  try {
    canvases = stageBasketPrintCanvases(decoded, { documentRef, signal });
    if (signal?.aborted) throw new Error("Print document staging aborted");
    return stageBasketPrintTextFooters(canvases, { documentRef, signal });
  } catch (error) {
    // Safe even when the underlying stage already released its resources.
    try { canvases?.dispose(); } catch { /* best effort */ }
    try { decoded.release(); } catch { /* best effort */ }
    throw error;
  }
}
