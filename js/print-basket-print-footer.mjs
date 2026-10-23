// #206 detached, text-only branding for already staged native-A4 print canvases.
// Reuse print.js / app.css brand classes but make no QR readiness claim.
// No DOM attachment to the document, printing, image/network request or source change.
const MAX_SHEETS = 5;

function makeFooter(doc) {
  const create = (tag, className = "") => {
    const node = doc.createElement(tag);
    if (!node || typeof node.append !== "function") {
      throw new TypeError("Print footer DOM element unavailable");
    }
    node.className = className;
    return node;
  };
  const footer = create("footer", "print-branding text-only");
  footer.setAttribute("aria-label", "Ausmalwiese – Malspaß zum Ausdrucken");

  const identity = create("div", "print-brand-identity");
  const paw = create("span", "brand-paw print-brand-paw");
  paw.setAttribute("aria-hidden", "true");
  for (let i = 0; i < 5; i++) paw.append(create("i"));

  const copy = create("div", "print-brand-copy");
  const word = create("span", "brand-word print-brand-word");
  const ausmal = create("span");
  ausmal.textContent = "Ausmal";
  const wiese = create("span", "brand-wiese");
  for (const letter of "wiese") {
    const bold = create("b");
    bold.textContent = letter;
    wiese.append(bold);
  }
  word.append(ausmal, wiese);
  const url = create("span", "print-brand-url");
  url.textContent = "ausmalwiese.de";
  copy.append(word, url);
  identity.append(paw, copy);

  const prompt = create("div", "print-brand-prompt");
  prompt.textContent = "Noch mehr Ausmalbilder?";
  const fallback = create("strong");
  fallback.textContent = "auf ausmalwiese.de";
  prompt.append(fallback);
  footer.append(identity, prompt);
  return footer;
}

function checkedRecords(staged) {
  const plan = staged?.plan, sheets = staged?.sheets;
  if (!staged || staged.disposed || typeof staged.dispose !== "function" ||
      !plan || !Array.isArray(plan.pages) ||
      !Number.isInteger(plan.sheetCount) ||
      plan.sheetCount < 1 || plan.sheetCount > MAX_SHEETS ||
      !Array.isArray(sheets) || sheets.length !== plan.sheetCount ||
      plan.pages.length !== plan.sheetCount) {
    throw new TypeError("Complete, undisposed A4 canvas stage required");
  }
  return sheets.map((sheet, index) => {
    const section = sheet?.element;
    const expected = "print-sheet is-" + sheet?.orientation;
    if (!sheet || sheet.page !== plan.pages[index] ||
        !["portrait", "landscape"].includes(sheet.orientation) ||
        !section || section.className !== expected ||
        section.isConnected === true ||
        typeof section.append !== "function") {
      throw new TypeError("Changed or attached staged print sheet");
    }
    return { section, originalClass: expected };
  });
}

// A future, separately reviewed UI owner must test browser pagination and
// invoke one print from a direct visitor click. This function does neither.
// Resource ownership passes to this result (or is released on any failure).
export function stageBasketPrintTextFooters(
  staged, { documentRef = globalThis.document, signal } = {},
) {
  let records = [];
  let footers = [];
  const cleanup = () => {
    for (let i = 0; i < records.length; i++) {
      try { footers[i]?.remove?.(); } catch { /* best effort */ }
      try { records[i].section.className = records[i].originalClass; } catch { /* best effort */ }
    }
  };
  try {
    if (signal?.aborted) throw new Error("Print footer staging aborted");
    records = checkedRecords(staged);
    if (typeof documentRef?.createElement !== "function") {
      throw new TypeError("Browser document unavailable");
    }
    // Prepare all footers before changing any print sheet.
    footers = records.map(() => makeFooter(documentRef));
    for (let i = 0; i < records.length; i++) {
      if (signal?.aborted) throw new Error("Print footer staging aborted");
      const record = records[i];
      record.section.className = record.originalClass + " has-text-footer";
      record.section.append(footers[i]);
    }
    if (signal?.aborted) throw new Error("Print footer staging aborted");
    let disposed = false;
    return Object.freeze({
      plan: staged.plan,
      sheets: staged.sheets,
      get disposed() { return disposed || staged.disposed; },
      dispose() {
        if (disposed) return;
        disposed = true;
        cleanup();
        staged.dispose();
      },
    });
  } catch (error) {
    cleanup();
    try { staged?.dispose?.(); } catch { /* best effort */ }
    throw error;
  }
}
