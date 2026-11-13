import { getKitaPackage, resolveKitaPackage } from "./kita-packages.mjs";

const root = document.body;
const slug = root?.dataset?.kitaPackageSlug || "";
const definition = getKitaPackage(slug);
const list = document.querySelector("[data-kita-package-activities]");
const status = document.querySelector("[data-kita-package-status]");
const selectButton = document.querySelector("[data-kita-package-select]");

function setStatus(message) {
  if (status) status.textContent = message;
}

function renderActivity(item) {
  const row = document.createElement("li");
  row.className = "kita-package-activity";

  const step = document.createElement("p");
  step.className = "kita-package-step";
  step.textContent = "Aktivität " + item.position;

  const renderer = globalThis.createCatalogCard;
  if (typeof renderer !== "function") {
    throw new Error("catalog card renderer unavailable");
  }
  const card = renderer(item.entry);
  card.classList.add("kita-package-activity-card");

  const instruction = document.createElement("p");
  instruction.className = "kita-package-instruction";
  instruction.textContent = item.instruction;

  row.append(step, card, instruction);
  return row;
}

async function start() {
  if (!definition || !list || !status || !selectButton) return;

  try {
    const response = await fetch("/catalog.json", {
      cache: "no-store",
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error("catalog unavailable");
    const catalog = await response.json();
    if (!Array.isArray(catalog)) throw new Error("invalid catalog");

    const resolved = resolveKitaPackage(definition, catalog);
    list.replaceChildren(...resolved.activities.map(renderActivity));

    if (!resolved.complete) {
      selectButton.disabled = true;
      setStatus("Dieses Paket ist gerade unvollständig. Verfügbare Aktivitäten können weiterhin einzeln geöffnet werden.");
      return;
    }

    selectButton.disabled = false;
    setStatus("Alle 5 Aktivitäten sind verfügbar. Das Paket umfasst 5 A4-Druckseiten.");
    selectButton.addEventListener("click", () => {
      document.dispatchEvent(new CustomEvent("ausmalwiese:print-basket-replace", {
        detail: {
          ids: [...definition.activityIds],
          expectedSheets: definition.expectedSheets,
          open: true,
          label: definition.title,
        },
      }));
    });
  } catch {
    selectButton.disabled = true;
    setStatus("Das Herbst-Paket kann gerade nicht geladen werden. Einzelne Vorlagen findest du weiterhin im Katalog.");
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", start, { once: true });
} else {
  start();
}
