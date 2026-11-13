import { reconcileBasket } from "./print-basket-selection.mjs";

const HERBST_ACTIVITY_IDS = Object.freeze([
  "7297970",
  "8611574",
  "4089571",
  "1481910",
  "2472924",
]);

const HERBST_INSTRUCTIONS = Object.freeze([
  "Male das Herbstbild aus und erzähle, was du entdeckst.",
  "Zähle die Blätter und trage die Anzahl ein.",
  "Verbinde die gleichen Herbstformen miteinander.",
  "Spure das H nach und probiere es anschließend selbst.",
  "Schneide die Eichelteile mit Begleitung aus und setze sie zusammen.",
]);

export const KITA_PACKAGES = Object.freeze([
  Object.freeze({
    slug: "herbst",
    title: "Herbst – 5 Aktivitäten",
    description: "Malen, zählen, Formen entdecken, Buchstaben nachspuren und basteln.",
    ageLabel: "4–6 Jahre",
    expectedSheets: 5,
    activityIds: HERBST_ACTIVITY_IDS,
    instructions: HERBST_INSTRUCTIONS,
  }),
]);

export function getKitaPackage(slug) {
  return KITA_PACKAGES.find((entry) => entry.slug === slug) || null;
}

export function resolveKitaPackage(definition, catalog) {
  if (!definition || !Array.isArray(definition.activityIds) ||
      definition.activityIds.length !== definition.instructions.length) {
    throw new TypeError("Valid Kita package definition required");
  }

  const reconciled = reconcileBasket(definition.activityIds, catalog);
  const byId = new Map(
    Array.isArray(catalog)
      ? catalog
          .filter((entry) => entry && typeof entry.id === "string")
          .map((entry) => [entry.id, entry])
      : []
  );
  const activities = reconciled.ids.map((id, index) => Object.freeze({
    entry: byId.get(id),
    instruction: definition.instructions[index],
    position: index + 1,
  }));
  const complete =
    reconciled.droppedIds.length === 0 &&
    reconciled.ids.length === definition.activityIds.length &&
    reconciled.sheetCount === definition.expectedSheets &&
    activities.every((item) => item.entry);

  return Object.freeze({
    complete,
    activities: Object.freeze(activities),
    sheetCount: reconciled.sheetCount,
    missingIds: Object.freeze([...reconciled.droppedIds]),
  });
}
