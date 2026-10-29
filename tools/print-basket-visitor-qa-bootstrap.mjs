const QA_RELEASE_KEY = "__AUSMALWIESE_BOOK_OUTPUT_QA_RELEASE__";
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

if (location.protocol !== "http:" ||
    !["127.0.0.1", "localhost"].includes(location.hostname)) {
  throw new Error("Loopback visitor QA origin required");
}

globalThis[QA_RELEASE_KEY] = Object.freeze({
  coveredZip: true,
  combinedPrint: true,
});

const response = await fetch("/catalog.json", {
  cache: "no-store",
  credentials: "omit",
  redirect: "error",
});
if (!response.ok || response.redirected) throw new Error("QA catalogue unavailable");
const catalog = await response.json();
if (!Array.isArray(catalog)) throw new Error("QA catalogue invalid");

const counts = new Map();
for (const entry of catalog) {
  if (typeof entry?.id === "string") {
    counts.set(entry.id, (counts.get(entry.id) || 0) + 1);
  }
}
const byId = new Map(
  catalog
    .filter((entry) =>
      entry && typeof entry.id === "string" && ID.test(entry.id) &&
      typeof entry.title === "string" && entry.title.trim() &&
      counts.get(entry.id) === 1)
    .map((entry) => [entry.id, entry]),
);

function parseIds(value) {
  const ids = String(value || "").split(/[\s,]+/).map((id) => id.trim()).filter(Boolean);
  if (!ids.length || ids.length > 5 || ids.some((id) => !ID.test(id)) ||
      new Set(ids).size !== ids.length) {
    throw new Error("Bitte 1–5 gültige, eindeutige Aktivitäts-IDs eingeben.");
  }
  return ids;
}

function renderCards(ids) {
  const host = document.querySelector("#qa-visitor-cards");
  const fragment = document.createDocumentFragment();
  for (const id of ids) {
    const entry = byId.get(id);
    if (!entry) throw new Error("Aktivität " + id + " ist im frischen Katalog nicht verfügbar.");
    const card = document.createElement("article");
    card.className = "coloring-card";
    const title = document.createElement("h2");
    const link = document.createElement("a");
    link.href = "/detail.html?id=" + encodeURIComponent(id);
    link.textContent = entry.title;
    title.append(link);
    card.append(title);
    fragment.append(card);
  }
  host.replaceChildren(fragment);
}

await import("/js/print-basket-ui.mjs");

const status = document.querySelector("#qa-visitor-status");
document.querySelector("#qa-visitor-load").addEventListener("click", () => {
  try {
    const ids = parseIds(document.querySelector("#qa-visitor-ids").value);
    renderCards(ids);
    status.textContent = ids.length + " Auswahlkarte(n) geladen. Jetzt „Hinzufügen“ verwenden.";
  } catch (error) {
    document.querySelector("#qa-visitor-cards").replaceChildren();
    status.textContent = "BLOCKED: " + (error?.message || "Ungültige Auswahl.");
  }
});
