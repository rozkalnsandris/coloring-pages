const printPages = document.querySelector("[data-print-pages]");
const printPlaceholder = document.querySelector("[data-print-placeholder]");
const printButton = document.querySelector("[data-print-button]");
const printStatus = document.querySelector("[data-print-status]");
const printBack = document.querySelector("[data-print-back]");
const printParams = new URLSearchParams(window.location.search);
const embeddedPrint = printParams.get("embedded") === "1";
const returnId = printParams.get("id");
if (printBack && returnId) {
  printBack.href = `detail.html?id=${encodeURIComponent(returnId)}`;
  printBack.textContent = "← Zur Malvorlage";
}

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

// /q redirect and aggregate D1 count verified LIVE; owner confirmed a physical
// 20 mm A4 QR scan (2026-10-11). Keep the asset-load text-only fallback.
const PRINT_QR_ROUTE_VERIFIED = true;
const PRINT_QR_ASSET = "assets/ausmalwiese-qr-dots.svg?v=75b511627ba4d760";

function buildPrintBrandFooter(withQr) {
  const footer = document.createElement("footer");
  footer.className = `print-branding ${withQr ? "has-qr" : "text-only"}`;
  footer.setAttribute("aria-label", "Ausmalwiese – Malspaß zum Ausdrucken");
  // Match the site's existing CSS-based colored paw and wordmark exactly.
  footer.innerHTML = `
    <div class="print-brand-identity">
      <span class="brand-paw print-brand-paw" aria-hidden="true">
        <i></i><i></i><i></i><i></i><i></i>
      </span>
      <div class="print-brand-copy">
        <span class="brand-word print-brand-word"><span>Ausmal</span><span class="brand-wiese"><b>w</b><b>i</b><b>e</b><b>s</b><b>e</b></span></span>
        <span class="print-brand-url">ausmalwiese.de</span>
      </div>
    </div>
    <div class="print-brand-prompt">Noch mehr Ausmalbilder?<strong>${withQr ? "Einfach scannen!" : "auf ausmalwiese.de"}</strong></div>
  `;
  if (withQr) {
    const image = document.createElement("img");
    image.className = "print-brand-qr";
    image.src = PRINT_QR_ASSET;
    image.alt = "QR-Code: https://ausmalwiese.de/q";
    image.width = 76;
    image.height = 76;
    footer.append(image);
  }
  return footer;
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


// Preserve native A4 pixels: fit the visible drawing, not its white page,
// into the existing print area above the 22mm branding and 2mm gap.
function visibleInkBounds(canvas) {
  const ctx = canvas.getContext("2d");
  if (!ctx || typeof ctx.getImageData !== "function") return null;
  const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let left = canvas.width, top = canvas.height, right = -1, bottom = -1;
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const i = (y * canvas.width + x) * 4;
      if (pixels[i] >= 250 && pixels[i + 1] >= 250 && pixels[i + 2] >= 250) continue;
      left = Math.min(left, x);
      right = Math.max(right, x);
      top = Math.min(top, y);
      bottom = Math.max(bottom, y);
    }
  }
  return right >= left ? { left, top, right, bottom } : null;
}

function fitLandscapeInkBounds(bounds, width, height) {
  if (!bounds || width !== 3508 || height !== 2480) return null;
  const mmX = 297 / width, mmY = 210 / height;
  const inkWidth = (bounds.right - bounds.left + 1) * mmX;
  const inkHeight = (bounds.bottom - bounds.top + 1) * mmY;
  if (inkWidth <= 0 || inkHeight <= 0) return null;
  // 15mm page sides/top, 39mm footer clearance, plus a 2mm ink guard.
  const scale = Math.min(1, 263 / inkWidth, 152 / inkHeight);
  const centerX = (bounds.left + bounds.right + 1) * mmX / 2;
  const centerY = (bounds.top + bounds.bottom + 1) * mmY / 2;
  return {
    scale,
    offsetX: 148.5 - centerX * scale,
    offsetY: 93 - centerY * scale,
  };
}

function applyLandscapeInkFit(sheet, canvas) {
  if (canvas.width !== 3508 || canvas.height !== 2480) return;
  try {
    const placement = fitLandscapeInkBounds(
      visibleInkBounds(canvas), canvas.width, canvas.height,
    );
    if (!placement) return;
    sheet.style.setProperty("--print-ink-x", placement.offsetX.toFixed(4) + "mm");
    sheet.style.setProperty("--print-ink-y", placement.offsetY.toFixed(4) + "mm");
    sheet.style.setProperty("--print-ink-scale", placement.scale.toFixed(6));
    sheet.classList.add("has-landscape-ink-fit");
  } catch {
    // Security/readback failure: keep the existing safe contain layout.
  }
}

async function renderPrintImages(imageUrls) {
  if (!printPages) throw new Error("print pages container unavailable");
  const images = await Promise.all(imageUrls.map((url) => loadImage(url)));
  // Never print a broken/unverified QR. Asset failure degrades to text-only.
  const qrReady = PRINT_QR_ROUTE_VERIFIED
    ? await loadImage(PRINT_QR_ASSET).then(() => true, () => false)
    : false;

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
    sheet.classList.add(qrReady ? "has-brand-qr" : "has-text-footer");
    const artwork = document.createElement("div");
    artwork.className = "print-artwork";
    const canvas = renderImageToCanvas(image);
    artwork.append(canvas);
    if (orientation === "landscape") applyLandscapeInkFit(sheet, canvas);
    sheet.append(artwork, buildPrintBrandFooter(qrReady));
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

    document.title = `${entry.title} drucken | Ausmalwiese`;
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
