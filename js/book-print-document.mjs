// #199 stage a cover-aware book through the existing #206 detached print
// document pipeline. This never mounts sheets, enables UI, calls window.print(),
// writes storage, sends telemetry, or proves physical/browser print quality.
import { prepareBookPrintMediaFromBundle } from "./book-print-media.mjs";
import { stagePreparedBasketPrintDocument } from "./print-basket-print-staged-document.mjs";

export async function stageBookPrintDocument(
  bundle,
  {
    decode,
    blobFactory,
    documentRef = globalThis.document,
    signal,
  } = {},
) {
  if (signal?.aborted) throw new Error("Book print document staging aborted");
  const prepared = prepareBookPrintMediaFromBundle(bundle);
  if (signal?.aborted) throw new Error("Book print document staging aborted");
  return stagePreparedBasketPrintDocument(prepared, {
    decode,
    blobFactory,
    documentRef,
    signal,
  });
}
