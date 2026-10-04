const printCanvas = document.querySelector("[data-print-canvas]");
const printPlaceholder = document.querySelector("[data-print-placeholder]");
const printButton = document.querySelector("[data-print-button]");
const printStatus = document.querySelector("[data-print-status]");
const printParams = new URLSearchParams(window.location.search);
const embeddedPrint = printParams.get("embedded") === "1";

const PDFJS_MODULE =
  "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.3.289/build/pdf.min.mjs";
const PDFJS_WORKER =
  "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.3.289/build/pdf.worker.min.mjs";
const PRINT_DPI = 150;
const PDF_POINTS_PER_INCH = 72;

function notifyParent(type, id) {
  if (!embeddedPrint || window.parent === window) return;
  window.parent.postMessage({ type, id }, window.location.origin);
}

async function renderPdf(pdfUrl) {
  if (!printCanvas) throw new Error("print canvas unavailable");

  const pdfjsLib = await import(PDFJS_MODULE);
  pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER;

  const loadingTask = pdfjsLib.getDocument({ url: pdfUrl });
  const pdf = await loadingTask.promise;
  if (pdf.numPages !== 1) throw new Error("print PDF must contain exactly one page");

  const page = await pdf.getPage(1);
  const viewport = page.getViewport({ scale: PRINT_DPI / PDF_POINTS_PER_INCH });
  const context = printCanvas.getContext("2d", { alpha: false });
  if (!context) throw new Error("print canvas context unavailable");

  printCanvas.width = Math.ceil(viewport.width);
  printCanvas.height = Math.ceil(viewport.height);

  context.fillStyle = "#fff";
  context.fillRect(0, 0, printCanvas.width, printCanvas.height);

  await page.render({
    canvasContext: context,
    viewport,
    intent: "print",
  }).promise;

  printCanvas.hidden = false;
}

async function loadPrintPage() {
  const id = printParams.get("id");
  if (!id) {
    if (printStatus) printStatus.textContent = "Keine Malvorlage ausgewählt.";
    if (printPlaceholder) {
      printPlaceholder.textContent = "Wähle zuerst eine Malvorlage aus der Übersicht aus.";
    }
    return;
  }

  try {
    const response = await fetch("catalog.json", { cache: "no-store" });
    if (!response.ok) throw new Error("catalog unavailable");

    const catalog = await response.json();
    const entry = Array.isArray(catalog)
      ? catalog.find((item) => item && item.id === id)
      : null;

    if (!entry || !entry.pdf) throw new Error("entry unavailable");

    document.title = `${entry.title} drucken | Coloring Pages`;
    await renderPdf(entry.pdf);

    if (printPlaceholder) printPlaceholder.hidden = true;
    if (printStatus) printStatus.textContent = entry.title;
    if (printButton) printButton.disabled = false;
    notifyParent("coloring-pages-print-ready", id);
  } catch {
    if (printPlaceholder) {
      printPlaceholder.textContent =
        "Diese Malvorlage kann gerade nicht gedruckt werden. Bitte versuche es später erneut.";
    }
    if (printStatus) {
      printStatus.textContent = "Die PDF-Druckdatei ist noch nicht verfügbar.";
    }
    notifyParent("coloring-pages-print-error", id);
  }
}

printButton?.addEventListener("click", () => window.print());
loadPrintPage();
