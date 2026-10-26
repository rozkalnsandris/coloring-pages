// #199 pure preview cursor/navigation for "Mein Malbuch erstellen".
// Consumes an already validated ordered preview plan. No DOM, storage, network,
// rendering, ZIP, download, analytics, or print side effects.

function checkedPlan(plan) {
  if (!plan || typeof plan !== "object" || Array.isArray(plan) ||
      !Number.isInteger(plan.sheetCount) || plan.sheetCount < 1 ||
      !Array.isArray(plan.items) || plan.items.length !== plan.sheetCount) {
    throw new TypeError("Valid nonempty book preview plan required");
  }
  plan.items.forEach((item, index) => {
    if (!item || typeof item !== "object" || Array.isArray(item) ||
        item.sheetNumber !== index + 1 ||
        item.sheetCount !== plan.sheetCount ||
        (item.kind !== "cover" && item.kind !== "artwork")) {
      throw new TypeError("Contiguous preview items required");
    }
  });
  return plan;
}

function snapshot(plan, sheetNumber) {
  const checked = checkedPlan(plan);
  if (!Number.isInteger(sheetNumber) ||
      sheetNumber < 1 || sheetNumber > checked.sheetCount) {
    throw new RangeError("Preview sheet number out of range");
  }
  const item = Object.freeze({ ...checked.items[sheetNumber - 1] });
  return Object.freeze({
    sheetNumber,
    sheetCount: checked.sheetCount,
    hasPrevious: sheetNumber > 1,
    hasNext: sheetNumber < checked.sheetCount,
    item,
  });
}

export function createBookPreviewCursor(plan) {
  return snapshot(plan, 1);
}

export function setBookPreviewSheet(plan, sheetNumber) {
  return snapshot(plan, sheetNumber);
}

export function moveBookPreviewCursor(plan, cursor, direction) {
  const checked = checkedPlan(plan);
  if (!cursor || typeof cursor !== "object" ||
      !Number.isInteger(cursor.sheetNumber) ||
      cursor.sheetCount !== checked.sheetCount ||
      cursor.sheetNumber < 1 || cursor.sheetNumber > checked.sheetCount) {
    throw new TypeError("Current preview cursor does not match the plan");
  }
  if (direction !== -1 && direction !== 1) {
    throw new RangeError("Preview direction must be -1 or 1");
  }
  const next = Math.min(
    checked.sheetCount,
    Math.max(1, cursor.sheetNumber + direction),
  );
  return snapshot(checked, next);
}
