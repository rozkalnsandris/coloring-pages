const printImage = document.querySelector("[data-print-image]");
const printPlaceholder = document.querySelector("[data-print-placeholder]");
const printButton = document.querySelector("[data-print-button]");
const printStatus = document.querySelector("[data-print-status]");

async function loadPrintPage() {
  const id = new URLSearchParams(window.location.search).get("id");
  if (!id) {
    if (printStatus) printStatus.textContent = "Keine Malvorlage ausgewählt.";
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
    printImage.src = entry.print;
    printImage.alt = entry.title;
    printImage.hidden = false;
    if (printPlaceholder) printPlaceholder.hidden = true;
    if (printStatus) printStatus.textContent = entry.title;
    if (printButton) printButton.disabled = false;
  } catch {
    if (printStatus) {
      printStatus.textContent = "Die druckbare Datei ist noch nicht verfügbar.";
    }
  }
}

printButton?.addEventListener("click", () => window.print());
loadPrintPage();
