// #199 in-memory orchestration for the optional A4 book-cover PNG.
// Composes the already reviewed render -> RGB -> encode -> independent decode
// verification gates. It does not attach DOM, download, persist, transmit, ZIP,
// print, publish, log visitor text, or enable any visitor-facing action.
import { renderBookCoverCanvas } from "./book-cover-canvas-render.mjs";
import { extractBookCoverRgb } from "./book-cover-canvas-rgb.mjs";
import { encodeBookCoverRgbPng } from "./book-cover-rgb-png-encoder.mjs";
import { verifyBookCoverPngDecodedRgb } from "./book-cover-png-decoded-verify.mjs";

function checkedServices(services) {
  if (!services || typeof services !== "object" ||
      typeof services.render !== "function" ||
      typeof services.extract !== "function" ||
      typeof services.encode !== "function" ||
      typeof services.verify !== "function") {
    throw new TypeError("Complete book cover PNG pipeline services required");
  }
  return services;
}

function throwIfAborted(signal) {
  if (signal?.aborted) throw new Error("Book cover PNG pipeline aborted");
}

// Exported for deterministic unit coverage of orchestration only. Production
// callers should use buildBookCoverPng(), which binds the reviewed services.
export async function runBookCoverPngPipeline(
  cover,
  options,
  {
    documentRef,
    fonts,
    signal,
    services,
  },
) {
  const ops = checkedServices(services);
  throwIfAborted(signal);

  let rendered = null;
  let rgb = null;
  try {
    rendered = await ops.render(
      cover,
      options,
      { documentRef, fonts, signal },
    );
    throwIfAborted(signal);

    rgb = ops.extract(rendered, { signal });
    rendered = null; // extract owns and disposes the canvas.
    throwIfAborted(signal);

    const png = await ops.encode(rgb);
    throwIfAborted(signal);
    if (!(png instanceof Uint8Array) || png.length === 0) {
      throw new TypeError("Encoded book cover PNG bytes required");
    }

    const verification = await ops.verify(png, rgb);
    throwIfAborted(signal);
    if (!verification || verification.ok !== true) {
      throw new Error("Book cover PNG verification failed");
    }

    return png;
  } finally {
    // Defensive cleanup if a substitute renderer/extractor fails to follow the
    // production ownership contract. Do not retain the giant canvas on error.
    try {
      if (rendered && rendered.disposed !== true &&
          typeof rendered.dispose === "function") {
        rendered.dispose();
      }
    } catch {
      // Keep the original pipeline outcome.
    }

    // The personalized pixels are no longer needed after PNG verification.
    // Wipe this mutable intermediate buffer on success and every failure path.
    try {
      if (rgb instanceof Uint8Array) rgb.fill(0);
    } catch {
      // Best effort only; do not mask the original pipeline error.
    }
  }
}

export async function buildBookCoverPng(
  cover,
  options,
  {
    documentRef = globalThis.document,
    fonts = documentRef?.fonts,
    signal,
  } = {},
) {
  return runBookCoverPngPipeline(
    cover,
    options,
    {
      documentRef,
      fonts,
      signal,
      services: {
        render: renderBookCoverCanvas,
        extract: extractBookCoverRgb,
        encode: encodeBookCoverRgbPng,
        verify: verifyBookCoverPngDecodedRgb,
      },
    },
  );
}
