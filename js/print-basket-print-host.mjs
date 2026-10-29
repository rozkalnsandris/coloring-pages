// #199/#206 connected host for one already staged combined print job.
// MDN documents window.print() as blocking while the print dialog is open.
// The shared lifecycle therefore owns the staged A4 canvases through print()
// and releases them when print() returns or throws. afterprint is deliberately
// not used as evidence that paper was physically printed.
import { printStagedBasketDocumentOnce } from "./print-basket-print-lifecycle.mjs";

export const BASKET_PRINT_ACTIVE_CLASS = "basket-print-active";
export const BASKET_PRINT_MOUNT_CLASS = "basket-print-mount";

function checkedDocument(documentRef) {
  const body = documentRef?.body;
  if (!documentRef || typeof documentRef.createElement !== "function" ||
      !body || typeof body.append !== "function" ||
      !body.classList || typeof body.classList.add !== "function" ||
      typeof body.classList.remove !== "function") {
    throw new TypeError("Browser document with body required");
  }
  return { documentRef, body };
}

function checkedLifecycle(lifecycle) {
  if (typeof lifecycle !== "function") {
    throw new TypeError("Combined print lifecycle required");
  }
  return lifecycle;
}

function ownsStage(staged) {
  return !!staged && staged.disposed !== true && typeof staged.dispose === "function";
}

function disposeStage(staged) {
  try { staged?.dispose?.(); } catch { /* best effort before lifecycle ownership */ }
}

export function printStagedDocumentInBasketHost(
  staged,
  {
    documentRef = globalThis.document,
    print = globalThis.print,
    signal,
    lifecycle = printStagedBasketDocumentOnce,
  } = {},
) {
  const owned = ownsStage(staged);
  let handedOff = false;
  let mount = null;
  let body = null;

  try {
    const checked = checkedDocument(documentRef);
    body = checked.body;
    const runLifecycle = checkedLifecycle(lifecycle);
    if (typeof print !== "function") {
      throw new TypeError("Browser print capability required");
    }
    if (signal?.aborted) {
      throw new Error("Combined print host aborted");
    }

    mount = documentRef.createElement("section");
    if (!mount || typeof mount.setAttribute !== "function" ||
        typeof mount.remove !== "function") {
      throw new TypeError("Combined print mount unavailable");
    }
    mount.className = BASKET_PRINT_MOUNT_CLASS;
    mount.dataset.basketPrintMount = "";
    mount.setAttribute("aria-hidden", "true");

    body.append(mount);
    if (mount.isConnected !== true || mount.parentNode !== body ||
        mount.parentElement !== body ||
        !Number.isInteger(mount.childElementCount) ||
        mount.childElementCount !== 0) {
      throw new TypeError("Connected empty combined print mount required");
    }

    body.classList.add(BASKET_PRINT_ACTIVE_CLASS);
    if (signal?.aborted) {
      throw new Error("Combined print host aborted");
    }

    handedOff = true;
    return runLifecycle(staged, {
      mount,
      print,
      signal,
    });
  } finally {
    try { body?.classList?.remove(BASKET_PRINT_ACTIVE_CLASS); } catch { /* best effort */ }
    try { mount?.remove?.(); } catch { /* best effort */ }
    if (owned && !handedOff) disposeStage(staged);
  }
}
