const detailRoot = document.querySelector("[data-detail-root]");
const detailTitle = document.querySelector("[data-detail-title]");
const detailCategory = document.querySelector("[data-detail-category]");
const detailCharacter = document.querySelector("[data-detail-character]");
const detailAge = document.querySelector("[data-detail-age]");
const detailDifficulty = document.querySelector("[data-detail-difficulty]");
const detailDescription = document.querySelector("[data-detail-description]");
const detailPreview = document.querySelector("[data-detail-preview]");
const detailPlaceholder = document.querySelector("[data-detail-placeholder]");
const printLink = document.querySelector("[data-action-print]");
const pdfLink = document.querySelector("[data-action-pdf]");
let activePrintSession = null;

const DETAIL_CATEGORY_LABELS = {
  rettungshunde: "Rettungshunde",
  tiere: "Tiere",
  fahrzeuge: "Fahrzeuge",
  alphabet: "Alphabet",
  lernen: "Lernen",
  figuren: "Figuren & Helden",
  jahreszeiten: "Jahreszeiten & Feste",
  seasonal: "Jahreszeiten",
};

const DETAIL_DIFFICULTY_LABELS = {
  easy: "Einfach",
  normal: "Mittel",
  detailed: "Detailliert",
};

function setAction(link, href) {
  if (!link) return;
  if (href) {
    link.href = href;
    link.removeAttribute("aria-disabled");
    link.classList.remove("is-disabled");
  } else {
    link.removeAttribute("href");
    link.setAttribute("aria-disabled", "true");
    link.classList.add("is-disabled");
  }
}

function startHtmlPrint(href) {
  activePrintSession?.cleanup();

  const printUrl = new URL(href, window.location.href);
  printUrl.searchParams.set("embedded", "1");

  const frame = document.createElement("iframe");
  frame.title = "Druckansicht";
  frame.tabIndex = -1;
  frame.setAttribute("aria-hidden", "true");
  frame.style.position = "fixed";
  frame.style.width = "1px";
  frame.style.height = "1px";
  frame.style.right = "0";
  frame.style.bottom = "0";
  frame.style.border = "0";
  frame.style.opacity = "0";
  frame.style.pointerEvents = "none";

  let printWindow = null;
  let cleaned = false;

  function cleanup() {
    if (cleaned) return;
    cleaned = true;
    window.removeEventListener("message", handleMessage);
    printWindow?.removeEventListener("afterprint", cleanup);
    frame.remove();
    if (activePrintSession?.frame === frame) activePrintSession = null;
  }

  function openFallback() {
    cleanup();
    window.location.assign(href);
  }

  function handleMessage(event) {
    if (event.origin !== window.location.origin || event.source !== frame.contentWindow) return;
    if (!event.data || typeof event.data !== "object") return;

    if (event.data.type === "coloring-pages-print-error") {
      openFallback();
      return;
    }

    if (event.data.type !== "coloring-pages-print-ready") return;

    printWindow = frame.contentWindow;
    if (!printWindow) {
      openFallback();
      return;
    }

    window.removeEventListener("message", handleMessage);
    printWindow.addEventListener("afterprint", cleanup, { once: true });

    try {
      printWindow.focus();
      printWindow.print();
    } catch {
      openFallback();
    }
  }

  window.addEventListener("message", handleMessage);
  frame.src = printUrl.toString();
  activePrintSession = { frame, cleanup };
  document.body.append(frame);
}

printLink?.addEventListener("click", (event) => {
  if (!printLink.href || printLink.getAttribute("aria-disabled") === "true") return;
  event.preventDefault();
  startHtmlPrint(printLink.href);
});

async function loadDetail() {
  const id = new URLSearchParams(window.location.search).get("id");
  if (!id) return;

  try {
    const response = await fetch("catalog.json", { cache: "no-store" });
    if (!response.ok) return;

    const catalog = await response.json();
    if (!Array.isArray(catalog)) return;

    const entry = catalog.find((item) => item && item.id === id);
    if (!entry) return;

    const categoryLabel = DETAIL_CATEGORY_LABELS[entry.category] || entry.category;
    const difficultyLabel = DETAIL_DIFFICULTY_LABELS[entry.difficulty] || entry.difficulty;

    document.title = `${entry.title} | Coloring Pages`;
    detailRoot?.setAttribute("data-loaded-id", entry.id);
    if (detailTitle) detailTitle.textContent = entry.title;
    if (detailCategory) detailCategory.textContent = `🐾 ${categoryLabel}`;
    if (detailCharacter) {
      detailCharacter.textContent = entry.character ? `🐶 ${entry.character}` : "";
      detailCharacter.hidden = !entry.character;
    }
    if (detailAge) {
      detailAge.textContent = `${entry.age} Jahre`;
      detailAge.classList.toggle("age-older", entry.age === "4-8");
    }
    if (detailDifficulty) {
      detailDifficulty.textContent = difficultyLabel;
      detailDifficulty.className = entry.difficulty === "easy" ? "easy" : entry.difficulty === "detailed" ? "detailed" : "medium";
    }
    if (detailDescription) {
      detailDescription.textContent =
        `Diese Malvorlage „${entry.title}“ ist für den A4-Druck vorbereitet und kann direkt gedruckt oder als PDF heruntergeladen werden.`;
    }

    const breadcrumbCurrent = document.querySelector("[data-breadcrumb-current]");
    if (breadcrumbCurrent) breadcrumbCurrent.textContent = entry.title;

    const breadcrumbCategory = document.querySelector("[data-breadcrumb-category]");
    if (breadcrumbCategory) breadcrumbCategory.textContent = categoryLabel;

    if (detailPreview && entry.preview) {
      detailPreview.src = entry.preview;
      detailPreview.alt = `Vorschau: ${entry.title}`;
      detailPreview.hidden = false;
      if (detailPlaceholder) detailPlaceholder.hidden = true;
    }

    setAction(printLink, `print.html?id=${encodeURIComponent(entry.id)}`);
    setAction(pdfLink, entry.pdf);
  } catch {
    // The static fallback remains usable when catalog.json is absent or invalid.
  }
}

loadDetail();
