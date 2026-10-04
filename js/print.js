const printCanvas = document.querySelector("[data-print-canvas]");
const printPlaceholder = document.querySelector("[data-print-placeholder]");
const printButton = document.querySelector("[data-print-button]");
const printStatus = document.querySelector("[data-print-status]");
const printParams = new URLSearchParams(window.location.search);
const embeddedPrint = printParams.get("embedded") === "1";

const PRINT_CLEAR_LUMA = 240;
const PRINT_SOLID_LUMA = 180;
const A4_PAGE_WIDTH_MM = 210;
const A4_PAGE_HEIGHT_MM = 297;

function notifyParent(type, id) {
  if (!embeddedPrint || window.parent === window) return;
  window.parent.postMessage({ type, id }, window.location.origin);
}

function lineAlpha(luma) {
  if (luma >= PRINT_CLEAR_LUMA) return 0;
  if (luma <= PRINT_SOLID_LUMA) return 255;
  return Math.round(
    ((PRINT_CLEAR_LUMA - luma) / (PRINT_CLEAR_LUMA - PRINT_SOLID_LUMA)) * 255,
  );
}

function cleanLineArt(context, width, height) {
  const imageData = context.getImageData(0, 0, width, height);
  const { data } = imageData;

  for (let index = 0; index < data.length; index += 4) {
    const sourceAlpha = data[index + 3];
    if (sourceAlpha === 0) continue;

    const luma =
      0.2126 * data[index] +
      0.7152 * data[index + 1] +
      0.0722 * data[index + 2];

    const alpha = Math.round((sourceAlpha * lineAlpha(luma)) / 255);
    data[index] = 0;
    data[index + 1] = 0;
    data[index + 2] = 0;
    data[index + 3] = alpha;
  }

  context.clearRect(0, 0, width, height);
  context.putImageData(imageData, 0, 0);
}

function a4CanvasSize(width, height) {
  const a4Ratio = A4_PAGE_WIDTH_MM / A4_PAGE_HEIGHT_MM;
  const sourceRatio = width / height;

  if (sourceRatio > a4Ratio) {
    return { width, height: Math.ceil(width / a4Ratio) };
  }
  return { width: Math.ceil(height * a4Ratio), height };
}

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.decoding = "async";
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("print image unavailable"));
    image.src = url;
  });
}

async function renderPrintImage(imageUrl) {
  if (!printCanvas) throw new Error("print canvas unavailable");

  const image = await loadImage(imageUrl);
  if (!image.naturalWidth || !image.naturalHeight) {
    throw new Error("print image has no dimensions");
  }

  const canvasSize = a4CanvasSize(image.naturalWidth, image.naturalHeight);
  printCanvas.width = canvasSize.width;
  printCanvas.height = canvasSize.height;

  const context = printCanvas.getContext("2d", {
    alpha: true,
    willReadFrequently: true,
  });
  if (!context) throw new Error("print canvas context unavailable");

  const offsetX = Math.floor((printCanvas.width - image.naturalWidth) / 2);
  const offsetY = Math.floor((printCanvas.height - image.naturalHeight) / 2);

  context.clearRect(0, 0, printCanvas.width, printCanvas.height);
  context.drawImage(
    image,
    offsetX,
    offsetY,
    image.naturalWidth,
    image.naturalHeight,
  );
  cleanLineArt(context, printCanvas.width, printCanvas.height);

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

    if (!entry || !entry.print) throw new Error("entry unavailable");

    document.title = `${entry.title} drucken | Coloring Pages`;
    await renderPrintImage(entry.print);

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
      printStatus.textContent = "Die PNG-Druckdatei ist noch nicht verfügbar.";
    }
    notifyParent("coloring-pages-print-error", id);
  }
}

printButton?.addEventListener("click", () => window.print());
loadPrintPage();
