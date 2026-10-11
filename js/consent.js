(() => {
  "use strict";
  // Consent preferences alone are kept to remember the visitor's privacy choice.
  // The persistent visitor identifier is never read before purpose-specific opt-in.
  const KEY = "coloring-pages-consent-v1";
  const ID_KEY = "coloring-pages-visitor-v1";
  // A narrowly scoped 24-hour recovery credential is never read for Like or Print.
  const PENDING_KEY = "coloring-pages-erasure-pending-v1";
  const RECOVERY_MS = 24 * 60 * 60 * 1000;
  const VERSION = 1;
  const legal = "datenschutz.html";
  const read = () => {
    try {
      const record = JSON.parse(localStorage.getItem(KEY) || "null");
      if (record && record.version === VERSION &&
          typeof record.like === "boolean" && typeof record.print === "boolean" &&
          typeof record.decided_at === "string") return record;
    } catch {}
    return null;
  };
  let choice = read();
  let storageFault = false;
  // Fresh preference each time; cross-tab withdrawal fails closed.
  const allows = (purpose) => !storageFault &&
    (purpose === "like" || purpose === "print") &&
    read()?.[purpose] === true;

  const banner = document.createElement("section");
  banner.className = "privacy-banner";
  banner.setAttribute("role", "region");
  banner.setAttribute("aria-label", "Datenschutzeinstellungen");
  banner.innerHTML = [
    '<div class="privacy-banner-row">',
      '<p class="privacy-banner-copy">Mit deiner Einwilligung speichern wir eine Browserkennung für Likes und Druckstatistiken. ',
      'Auch ohne Einwilligung kannst du kostenlos drucken. ',
      '<a href="' + legal + '">Datenschutz</a></p>',
      '<div class="privacy-banner-actions">',
        '<button type="button" data-consent-deny>Alle ablehnen</button>',
        '<button type="button" data-consent-settings>Einstellungen</button>',
        '<button type="button" data-consent-accept>Alle akzeptieren</button>',
      '</div>',
    '</div>',
    '<div class="privacy-banner-options" data-consent-options hidden>',
      '<p>Du entscheidest getrennt über die beiden freiwilligen Funktionen:</p>',
      '<label><input type="checkbox" data-consent-like> Gefällt mir auf späteren Besuchen wiedererkennen</label>',
      '<label><input type="checkbox" data-consent-print> Druckabsichten mit Browserkennung zählen</label>',
      '<p>Ohne Zustimmung bleibt A4-Drucken möglich. Gezählte Druckaktionen sind keine bestätigten Ausdrucke.</p>',
      '<p>Wenn du Gefällt mir abwählst oder Alle ablehnen wählst, versuchen wir, deine gespeicherten Likes zu löschen. Dadurch können Like-Zahlen sinken. Bei älteren Kennungen oder Fehlern helfen wir dir über den Datenschutzkontakt – sende keine Browserkennung per E-Mail.</p>',
      '<div class="privacy-options-actions">',
        '<button type="button" data-consent-erase hidden>Meine gespeicherten Likes löschen</button>',
        '<button type="button" data-consent-save>Auswahl speichern</button>',
        '<button type="button" data-consent-cancel>Zurück</button>',
      '</div>',
    '</div>',
    '<p class="privacy-consent-error" data-consent-error role="status" hidden></p>'
  ].join("");

  const footer = document.createElement("footer");
  footer.className = "privacy-footer";
  const reopen = document.createElement("button");
  reopen.type = "button";
  reopen.textContent = "Datenschutzeinstellungen";
  const erasureFeedback = document.createElement("span");
  erasureFeedback.className = "privacy-erasure-feedback";
  erasureFeedback.setAttribute("role", "status");
  erasureFeedback.setAttribute("aria-live", "polite");
  erasureFeedback.hidden = true;
  const rights = document.createElement("a");
  rights.href = "mailto:andris@rozkalns.net?subject=Ausmalwiese%20Datenschutz%20Loeschanfrage";
  rights.textContent = "Datenschutzanfrage (ohne Browserkennung)";
  const retryErasureButton = document.createElement("button");
  retryErasureButton.type = "button";
  retryErasureButton.textContent = "Löschung erneut versuchen";
  retryErasureButton.hidden = true;
  footer.append(reopen, rights, retryErasureButton, erasureFeedback);
  document.body.append(banner, footer);

  const options = banner.querySelector("[data-consent-options]");
  const like = banner.querySelector("[data-consent-like]");
  const print = banner.querySelector("[data-consent-print]");
  const error = banner.querySelector("[data-consent-error]");
  const settings = banner.querySelector("[data-consent-settings]");
  const eraseButton = banner.querySelector("[data-consent-erase]");
  let erasing = false;
  let lastFocus = null;

  function show(advanced = false) {
    lastFocus = document.activeElement;
    banner.hidden = false;
    document.body.classList.add("has-privacy-banner");
    options.hidden = !advanced;
    like.checked = Boolean(choice?.like);
    print.checked = Boolean(choice?.print);
    eraseButton.hidden = !choice?.like || erasing;
    error.hidden = true;
    (advanced ? like : settings).focus();
  }
  function hide() {
    banner.hidden = true;
    document.body.classList.remove("has-privacy-banner");
    lastFocus?.focus?.();
  }
  function save(next) {
    const previous = choice;
    try {
      // Before the first valid consent, discard legacy ID without reading it.
      // Do not delete an existing ID if one still-consented purpose remains.
      if (previous === null) localStorage.removeItem(ID_KEY);
      const record = {
        version: VERSION, like: Boolean(next.like), print: Boolean(next.print),
        decided_at: new Date().toISOString()
      };
      localStorage.setItem(KEY, JSON.stringify(record));
      choice = record;
      storageFault = false;
      if (!record.like && !record.print) localStorage.removeItem(ID_KEY);
    } catch {
      // No permission is activated if storage cannot record it.
      choice = null; // fail closed even after a partially written/revoked record
      storageFault = true;
      error.textContent = "Deine Auswahl konnte nicht gespeichert werden. Bitte versuche es erneut.";
      error.hidden = false;
      return false;
    }
    hide();
    document.dispatchEvent(new CustomEvent("coloring-consent-changed", {
      detail: { like: choice.like, print: choice.print }
    }));
    return true;
  }

  function eraseStatus(message) {
    erasureFeedback.textContent = message;
    erasureFeedback.hidden = false;
  }

  // This value is used only to finish a deletion already requested by the user.
  // Never use it as a replacement analytics/Like/Print identifier.
  function pendingProof() {
    try {
      const raw = localStorage.getItem(PENDING_KEY);
      if (!raw) return "";
      const item = JSON.parse(raw);
      if (item && /^v2-[0-9a-f]{64}$/.test(item.visitor_id) &&
          Number.isFinite(item.expires_at) && item.expires_at > Date.now() &&
          item.expires_at <= Date.now() + RECOVERY_MS) return item.visitor_id;
      localStorage.removeItem(PENDING_KEY);
    } catch {
      try { localStorage.removeItem(PENDING_KEY); } catch {}
    }
    return "";
  }

  function refreshRetry() {
    retryErasureButton.hidden = !pendingProof();
    retryErasureButton.disabled = erasing;
  }

  function storePendingProof(proof) {
    if (!/^v2-[0-9a-f]{64}$/.test(proof)) return false;
    try {
      // Never extend the same proof's deadline on repeated attempts.
      if (pendingProof() === proof) return true;
      localStorage.setItem(PENDING_KEY, JSON.stringify({
        visitor_id: proof, expires_at: Date.now() + RECOVERY_MS
      }));
      refreshRetry();
      return true;
    } catch { return false; }
  }

  function clearPendingProof(proof) {
    try {
      if (pendingProof() === proof) localStorage.removeItem(PENDING_KEY);
    } catch {}
    refreshRetry();
  }

  async function eraseProof(proof) {
    if (erasing) return;
    erasing = true;
    retryErasureButton.disabled = true;
    eraseButton.disabled = true;
    try {
      const result = await window.ColoringStats.eraseLikesWithProof(proof);
      if (result?.ok !== true) throw new Error("unconfirmed deletion");
      clearPendingProof(proof);
      eraseStatus("Deine gespeicherten Likes wurden für diese Browserkennung gelöscht.");
    } catch {
      eraseStatus(pendingProof()
        ? "Einwilligung widerrufen; Löschung nicht bestätigt. Du kannst die Löschung innerhalb von 24 Stunden erneut auslösen oder den Datenschutzkontakt nutzen. Keine Browserkennung per E-Mail senden."
        : "Einwilligung widerrufen; Löschung nicht bestätigt. Bitte nutze den Datenschutzkontakt ohne Browserkennung.");
    } finally {
      erasing = false;
      eraseButton.disabled = false;
      refreshRetry();
    }
  }

  // Ordinary Like withdrawal is itself a user-directed deletion request.
  // First-visit rejection and Print-only withdrawal never read the visitor ID.
  async function changeConsent(next) {
    if (erasing) return;
    const previous = read();
    const revokeLike = !storageFault && previous?.like === true && !next.like;
    const proof = revokeLike ? (window.ColoringStats?.getErasureProof?.() || "") : "";
    // Store only an erasure-purpose proof, before retiring the original ID.
    if (revokeLike && proof) storePendingProof(proof);
    if (!save(next)) return;
    if (!revokeLike) { refreshRetry(); return; }
    // Print opt-in remains independent; the next Print may create a fresh ID.
    try { localStorage.removeItem(ID_KEY); } catch {}
    if (!proof) {
      eraseStatus("Einwilligung widerrufen; Löschung nicht bestätigt. Bei älteren Kennungen oder fehlendem Nachweis kontaktiere den Datenschutzkontakt. Bitte keine Browserkennung senden.");
      refreshRetry();
      return;
    }
    await eraseProof(proof);
  }

  async function requestLikeErasure() {
    if (erasing || !allows("like")) return;
    if (!window.confirm("Deine gespeicherten Likes werden gelöscht. Das kann die sichtbaren Like-Zahlen verringern. Einverstanden?")) return;
    await changeConsent({like:false, print:Boolean(read()?.print)});
  }

  async function retryPendingErasure() {
    if (erasing) return;
    const proof = pendingProof();
    if (!proof) { refreshRetry(); return; }
    if (!window.confirm("Die frühere Löschung ist nicht bestätigt. Jetzt die Löschung erneut versuchen?")) return;
    await eraseProof(proof);
  }

  retryErasureButton.addEventListener("click", retryPendingErasure);
  eraseButton.addEventListener("click", requestLikeErasure);

  banner.querySelector("[data-consent-deny]").addEventListener("click", () =>
    changeConsent({like:false, print:false}));
  banner.querySelector("[data-consent-accept]").addEventListener("click", () =>
    changeConsent({like:true, print:true}));
  settings.addEventListener("click", () => show(true));
  banner.querySelector("[data-consent-save]").addEventListener("click", () =>
    changeConsent({like:like.checked, print:print.checked}));
  banner.querySelector("[data-consent-cancel]").addEventListener("click", () => {
    if (choice) hide(); else show(false);
  });
  reopen.addEventListener("click", () => show(true));

  window.ColoringConsent = { allows, openSettings: () => show(true) };
  refreshRetry();
  if (choice) hide(); else {
    banner.hidden = false;
    document.body.classList.add("has-privacy-banner");
    footer.hidden = true;
    // The footer re-open control is only needed once a decision exists.
  }
  document.addEventListener("coloring-consent-changed", () => {
    footer.hidden = false;
  });
  window.addEventListener("storage", (event) => {
    if (event.key === PENDING_KEY || event.key === null) refreshRetry();
    if (event.key !== KEY && event.key !== null) return;
    choice = read();
    if (!choice) {
      banner.hidden = false;
      document.body.classList.add("has-privacy-banner");
      footer.hidden = true;
    } else {
      hide();
      footer.hidden = false;
    }
    document.dispatchEvent(new CustomEvent("coloring-consent-changed", {
      detail: {like: Boolean(choice?.like), print: Boolean(choice?.print)}
    }));
  });
})();
