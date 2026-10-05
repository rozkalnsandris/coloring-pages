const printPages = document.querySelector("[data-print-pages]");
const printPlaceholder = document.querySelector("[data-print-placeholder]");
const printButton = document.querySelector("[data-print-button]");
const printStatus = document.querySelector("[data-print-status]");
const printParams = new URLSearchParams(window.location.search);
const embeddedPrint = printParams.get("embedded") === "1";

const A4_PAGE_WIDTH_MM = 210;
const A4_PAGE_HEIGHT_MM = 297;

function notifyParent(type, id) {
  if (!embeddedPrint || window.parent === window) return;
  window.parent.postMessage({ type, id }, window.location.origin);
}

function entryPrintPages(entry) {
  if (Array.isArray(entry.pages) && entry.pages.length > 0) {
    const urls = entry.pages.map((page) =>
      typeof page?.print === "string" ? page.print : "",
    );
    return urls.some((url) => !url) ? [] : urls;
  }
  return typeof entry.print === "string" && entry.print ? [entry.print] : [];
}

function printOrientation(width, height) {
  return width > height ? "landscape" : "portrait";
}

function isCanonicalA4Raster(width, height) {
  return (
    (width === 2480 && height === 3508) ||
    (width === 3508 && height === 2480)
  );
}

function a4CanvasSize(width, height) {
  if (isCanonicalA4Raster(width, height)) {
    return { width, height };
  }

  const landscape = printOrientation(width, height) === "landscape";
  const pageWidth = landscape ? A4_PAGE_HEIGHT_MM : A4_PAGE_WIDTH_MM;
  const pageHeight = landscape ? A4_PAGE_WIDTH_MM : A4_PAGE_HEIGHT_MM;
  const a4Ratio = pageWidth / pageHeight;
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

function renderImageToCanvas(image) {
  const canvas = document.createElement("canvas");
  canvas.setAttribute("aria-hidden", "true");

  const canvasSize = a4CanvasSize(image.naturalWidth, image.naturalHeight);
  canvas.width = canvasSize.width;
  canvas.height = canvasSize.height;

  const context = canvas.getContext("2d", { alpha: true });
  if (!context) throw new Error("print canvas context unavailable");

  const offsetX = Math.floor((canvas.width - image.naturalWidth) / 2);
  const offsetY = Math.floor((canvas.height - image.naturalHeight) / 2);

  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(
    image,
    offsetX,
    offsetY,
    image.naturalWidth,
    image.naturalHeight,
  );
  return canvas;
}

async function renderPrintImages(imageUrls) {
  if (!printPages) throw new Error("print pages container unavailable");
  const images = await Promise.all(imageUrls.map((url) => loadImage(url)));

  const sheets = images.map((image, index) => {
    if (!image.naturalWidth || !image.naturalHeight) {
      throw new Error("print image has no dimensions");
    }
    const sheet = document.createElement("section");
    const orientation = printOrientation(image.naturalWidth, image.naturalHeight);
    sheet.className = `print-sheet is-${orientation}`;
    sheet.setAttribute(
      "aria-label",
      `A4-Druckseite ${index + 1} von ${images.length}`,
    );
    sheet.append(renderImageToCanvas(image));
    return sheet;
  });

  printPages.replaceChildren(...sheets);
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
    const imageUrls = entry ? entryPrintPages(entry) : [];

    if (!entry || imageUrls.length === 0) throw new Error("entry unavailable");

    document.title = `${entry.title} drucken | Coloring Pages`;
    await renderPrintImages(imageUrls);

    if (printStatus) {
      printStatus.textContent = imageUrls.length > 1
        ? `${entry.title} · ${imageUrls.length} Seiten`
        : entry.title;
    }
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
