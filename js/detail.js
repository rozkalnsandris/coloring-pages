const detailRoot = document.querySelector("[data-detail-root]");
const detailTitle = document.querySelector("[data-detail-title]");
const detailCategory = document.querySelector("[data-detail-category]");
const detailCharacter = document.querySelector("[data-detail-character]");
const detailAge = document.querySelector("[data-detail-age]");
const detailDifficulty = document.querySelector("[data-detail-difficulty]");
const detailPagesBadge = document.querySelector("[data-detail-pages]");
const detailDescription = document.querySelector("[data-detail-description]");
const detailPreview = document.querySelector("[data-detail-preview]");
const detailPlaceholder = document.querySelector("[data-detail-placeholder]");
const pageSwitcher = document.querySelector("[data-detail-page-switcher]");
const printLink = document.querySelector("[data-action-print]");
const printLabel = document.querySelector("[data-action-print-label]");
const pngLink = document.querySelector("[data-action-png]");
const pngLabel = document.querySelector("[data-action-png-label]");
const likeButton=document.querySelector("[data-action-like]");
const likeLabel=document.querySelector("[data-action-like-label]");
const likeCount=document.querySelector("[data-action-like-count]");
const likeStatus=document.querySelector("[data-like-status]");
let activePrintSession=null;
let loadedEntryId="";

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

function entryPages(entry) {
  if (Array.isArray(entry.pages) && entry.pages.length > 0) {
    const pages = entry.pages.map((page) => ({
      preview: typeof page?.preview === "string" ? page.preview : "",
      print: typeof page?.print === "string" ? page.print : "",
    }));
    return pages.some((page) => !page.preview && !page.print) ? [] : pages;
  }

  if (entry.preview || entry.print) {
    return [{
      preview: typeof entry.preview === "string" ? entry.preview : "",
      print: typeof entry.print === "string" ? entry.print : "",
    }];
  }
  return [];
}

function selectPage(entry, pages, pageIndex) {
  const page = pages[pageIndex];
  if (!page) return;

  const previewUrl = page.preview || page.print;
  if (detailPreview && previewUrl) {
    detailPreview.src = previewUrl;
    detailPreview.alt = pages.length > 1
      ? `Vorschau: ${entry.title}, Seite ${pageIndex + 1}`
      : `Vorschau: ${entry.title}`;
    detailPreview.hidden = false;
    if (detailPlaceholder) detailPlaceholder.hidden = true;
  }

  setAction(pngLink, page.print);
  if (pngLabel) {
    pngLabel.textContent = pages.length > 1
      ? `PNG Seite ${pageIndex + 1} herunterladen`
      : "PNG herunterladen";
  }

  pageSwitcher?.querySelectorAll("[data-page-index]").forEach((button) => {
    const selected = Number(button.dataset.pageIndex) === pageIndex;
    button.classList.toggle("is-active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}

function renderPageSwitcher(entry, pages) {
  if (!pageSwitcher) return;
  pageSwitcher.replaceChildren();

  if (pages.length <= 1) {
    pageSwitcher.hidden = true;
    return;
  }

  pages.forEach((page, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "detail-page-thumb";
    button.dataset.pageIndex = String(index);
    button.setAttribute("aria-pressed", String(index === 0));
    button.setAttribute("aria-label", `Seite ${index + 1} anzeigen`);

    const image = document.createElement("img");
    image.src = page.preview || page.print;
    image.alt = "";
    image.loading = "lazy";

    const label = document.createElement("span");
    label.textContent = `Seite ${index + 1}`;

    button.append(image, label);
    button.addEventListener("click", () => selectPage(entry, pages, index));
    pageSwitcher.append(button);
  });

  pageSwitcher.hidden = false;
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

printLink?.addEventListener("click",(event)=>{
  if (!printLink.href || printLink.getAttribute("aria-disabled")==="true") return;
  event.preventDefault();
  if (loadedEntryId) window.ColoringStats?.trackPrint?.(loadedEntryId);
  startHtmlPrint(printLink.href);
});
function renderLikeState(data) {
  if (!likeButton) return;
  const liked=Boolean(data?.liked);
  likeButton.classList.toggle("is-liked",liked);
  likeButton.setAttribute("aria-pressed",String(liked));
  const heart=likeButton.querySelector(".like-heart");
  if (heart) heart.textContent=liked ? "♥" : "♡";
  if (likeLabel) likeLabel.textContent="Gefällt mir";
  if (likeCount) likeCount.textContent=String(Number(data?.like_count||0));
}
async function hydrateLikeState(pageId) {
  if (!likeButton || !window.ColoringStats?.getPage) return;
  try {
    const data=await window.ColoringStats.getPage(pageId);
    renderLikeState(data);
    likeButton.disabled=false;
    likeButton.classList.remove("is-disabled");
  } catch {
    if (likeStatus) {
      likeStatus.textContent = "Gefällt mir ist gerade nicht verfügbar.";
      likeStatus.hidden = false;
    }
  }
}
likeButton?.addEventListener("click",async()=>{
  if (!loadedEntryId || likeButton.disabled || !window.ColoringStats?.toggleLike) return;
  if (likeStatus) {
    likeStatus.textContent = "";
    likeStatus.hidden = true;
  }
  likeButton.disabled=true;
  try {
    renderLikeState(await window.ColoringStats.toggleLike(loadedEntryId));
  } catch {
    if (likeStatus) {
      likeStatus.textContent = "Gefällt mir konnte nicht gespeichert werden. Bitte versuche es erneut.";
      likeStatus.hidden = false;
    }
  } finally {
    likeButton.disabled=false;
  }
});

function markMissingDetailNoindex() {
  // Only confirmed absent IDs are excluded; a failed catalog fetch is not proof.
  let robots = document.querySelector('meta[name="robots"]');
  if (!robots) {
    robots = document.createElement("meta");
    robots.setAttribute("name", "robots");
    document.head.append(robots);
  }
  robots.setAttribute("content", "noindex");
}

async function loadDetail() {
  const id = new URLSearchParams(window.location.search).get("id");
  if (!id) return;

  try {
    const response = await fetch("catalog.json", { cache: "no-store" });
    if (!response.ok) throw new Error("catalog unavailable");

    const catalog = await response.json();
    if (!Array.isArray(catalog)) throw new Error("invalid catalog");

    const entry = catalog.find((item) => item && item.id === id);
    if (!entry) {
      markMissingDetailNoindex();
      throw new Error("entry unavailable");
    }

    const pages = entryPages(entry);
    if (!pages.length) throw new Error("pages unavailable");
    const categoryLabel = DETAIL_CATEGORY_LABELS[entry.category] || entry.category;
    const difficultyLabel = DETAIL_DIFFICULTY_LABELS[entry.difficulty] || entry.difficulty;

    document.title = `${entry.title} | Coloring Pages`;
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      const summary = pages.length > 1
        ? `kostenlose Malaktivität mit ${pages.length} A4-Seiten`
        : "kostenlose A4-Malvorlage";
      metaDescription.setAttribute(
        "content",
        `${entry.title} – ${summary} für Kinder. Als PNG herunterladen oder direkt ausdrucken.`
      );
    }
    detailRoot?.setAttribute("data-loaded-id",entry.id);
    loadedEntryId=entry.id;
    window.ColoringStats?.trackView?.(entry.id);
    if (detailTitle) detailTitle.textContent = entry.title;
    const detailBadges = document.querySelector(".detail-badges");
    if (detailBadges) detailBadges.hidden = false;
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
    if (detailPagesBadge) {
      detailPagesBadge.textContent = `${pages.length} Seiten`;
      detailPagesBadge.hidden = pages.length <= 1;
    }
    if (detailDescription) {
      detailDescription.textContent = pages.length > 1
        ? `Diese Aktivität „${entry.title}“ besteht aus ${pages.length} A4-Seiten. Mit A4 drucken werden alle Seiten in einem Druckvorgang geöffnet; PNG kannst du seitenweise herunterladen.`
        : `Diese Malvorlage „${entry.title}“ ist für den A4-Druck vorbereitet und kann direkt gedruckt oder als PNG heruntergeladen werden.`;
    }

    const breadcrumbCurrent = document.querySelector("[data-breadcrumb-current]");
    if (breadcrumbCurrent) breadcrumbCurrent.textContent = entry.title;

    const breadcrumbCategory = document.querySelector("[data-breadcrumb-category]");
    if (breadcrumbCategory) breadcrumbCategory.textContent = categoryLabel;

    renderPageSwitcher(entry, pages);
    if (pages.length) selectPage(entry, pages, 0);

    const allPrintable = pages.length > 0 && pages.every((page) => page.print);
    setAction(printLink, allPrintable ? `print.html?id=${encodeURIComponent(entry.id)}` : "");
    if (printLabel) {
      printLabel.textContent=pages.length>1 ? `A4 drucken (${pages.length} Seiten)` : "A4 drucken";
    }
    await hydrateLikeState(entry.id);
  } catch {
    const message = "Diese Malvorlage ist gerade nicht verfügbar. Bitte versuche es später erneut oder wähle ein anderes Motiv aus der Übersicht.";
    if (detailTitle) detailTitle.textContent = "Malvorlage nicht verfügbar";
    if (detailDescription) detailDescription.textContent = message;
    const status = document.querySelector("[data-detail-status]");
    if (status) status.textContent = message;
  }
}

loadDetail();
