// #199 detached Canvas renderer for the optional A4 book cover.
// User title/name stay in caller memory and are painted locally only. This
// module does not attach DOM, persist/log/transmit text, encode PNG, build ZIP,
// enable printing, or prove visual/physical-print quality.
import { BOOK_COVER_A4_CONTRACT } from "./book-cover-a4-contract.mjs";
import {
  BOOK_COVER_FONT_SPEC,
  preflightBookCoverFont,
} from "./book-cover-font-preflight.mjs";
import { planBookCoverTextLayout } from "./book-cover-text-layout.mjs";

function checkedDocument(documentRef) {
  if (!documentRef || typeof documentRef.createElement !== "function") {
    throw new TypeError("Browser document required");
  }
  return documentRef;
}

function checkedCover(cover) {
  if (!cover || typeof cover !== "object" || Array.isArray(cover) ||
      typeof cover.title !== "string" || typeof cover.name !== "string") {
    throw new TypeError("In-memory cover title/name required");
  }
  return cover;
}

function checkedOptions(options) {
  if (!options || typeof options !== "object" || Array.isArray(options) ||
      !Number.isFinite(options.strokeWidthPx) || options.strokeWidthPx < 0 ||
      !Number.isFinite(options.lineGapPx) || options.lineGapPx < 0) {
    throw new TypeError("Finite non-negative cover rendering options required");
  }
  return options;
}

function clearCanvas(canvas) {
  try {
    canvas.width = 0;
    canvas.height = 0;
  } catch {
    // Best effort only for a partially allocated browser canvas.
  }
}

export async function renderBookCoverCanvas(
  cover,
  options,
  {
    documentRef = globalThis.document,
    fonts = documentRef?.fonts,
    signal,
  } = {},
) {
  const doc = checkedDocument(documentRef);
  const value = checkedCover(cover);
  const style = checkedOptions(options);
  if (signal?.aborted) throw new Error("Book cover rendering aborted");

  await preflightBookCoverFont(fonts);
  if (signal?.aborted) throw new Error("Book cover rendering aborted");

  const canvas = doc.createElement("canvas");
  if (!canvas || typeof canvas.getContext !== "function") {
    throw new TypeError("A4 cover canvas unavailable");
  }

  try {
    canvas.width = BOOK_COVER_A4_CONTRACT.width;
    canvas.height = BOOK_COVER_A4_CONTRACT.height;
    if (typeof canvas.setAttribute === "function") {
      canvas.setAttribute("aria-hidden", "true");
    }

    const context = canvas.getContext("2d", { alpha: false });
    if (!context ||
        typeof context.fillRect !== "function" ||
        typeof context.strokeText !== "function" ||
        typeof context.fillText !== "function" ||
        typeof context.measureText !== "function") {
      throw new TypeError("A4 cover 2D canvas context unavailable");
    }

    context.fillStyle = "#fff";
    context.fillRect(
      0,
      0,
      BOOK_COVER_A4_CONTRACT.width,
      BOOK_COVER_A4_CONTRACT.height,
    );

    const layout = planBookCoverTextLayout(context, value, style);
    if (signal?.aborted) throw new Error("Book cover rendering aborted");

    context.font = BOOK_COVER_FONT_SPEC;
    context.textAlign = "center";
    context.textBaseline = "alphabetic";
    context.lineWidth = style.strokeWidthPx;
    context.lineJoin = "round";
    context.strokeStyle = "#000";
    context.fillStyle = "#fff";

    for (const line of layout.lines) {
      if (signal?.aborted) throw new Error("Book cover rendering aborted");
      const textValue = line.kind === "title" ? value.title : value.name;
      context.strokeText(textValue, line.x, line.baselineY);
      context.fillText(textValue, line.x, line.baselineY);
    }

    if (signal?.aborted) throw new Error("Book cover rendering aborted");

    let disposed = false;
    return Object.freeze({
      canvas,
      layout,
      get disposed() {
        return disposed;
      },
      dispose() {
        if (disposed) return;
        disposed = true;
        clearCanvas(canvas);
      },
    });
  } catch (error) {
    clearCanvas(canvas);
    throw error;
  }
}
