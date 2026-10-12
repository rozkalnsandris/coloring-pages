(() => {
  "use strict";
  // Consent preferences alone are kept to remember the visitor's privacy choice.
  // The persistent visitor identifier is never read before purpose-specific opt-in.
  const KEY = "coloring-pages-consent-v1";
  const ID_KEY = "coloring-pages-visitor-v1";
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
  const allows = (purpose) => !storageFault && !erasing &&
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
  footer.append(reopen, rights, erasureFeedback);
  document.body.append(banner, footer);

  const options = banner.querySelector("[data-consent-options]");
  const like = banner.querySelector("[data-consent-like]");
  const print = banner.querySelector("[data-consent-print]");
  const error = banner.querySelector("[data-consent-error]");
  const settings = banner.querySelector("[data-consent-settings]");
  const eraseButton = banner.querySelector("[data-consent-erase]");
  let erasing = false;
  // No automatic re-submission of an ambiguous legacy erasure attempt.
  let legacyUpgradeEraseAttempted = false;
  let legacyUpgradeEraseConfirmed = false;
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

  // Fail closed on confirmed expiry or a missing credential; never mint silently.
  function requireFreshConsent(expiredId = "") {
    const current = read();
    if (erasing || !current || (!current.like && !current.print)) return false;
    try {
      const storedId = localStorage.getItem(ID_KEY) || "";
      // A delayed response must not wipe a new credential issued in another tab.
      if (expiredId && storedId !== expiredId) return false;
      if (!expiredId && storedId) {
        // Keep legacy v2 intact for an explicit, user-directed deletion.
        show(true);
        error.textContent = "Die bisherige Browserkennung kann nicht für neue Likes oder Druckstatistik verwendet werden. Bitte bestätige deine Auswahl erneut; alte Likes werden nicht automatisch übernommen.";
        error.hidden = false;
        return false;
      }
      window.ColoringStats?.cancelPendingCredential?.();
      localStorage.removeItem(KEY);
      localStorage.removeItem(ID_KEY);
      choice = null;
      storageFault = false;
    } catch {
      choice = null;
      storageFault = true;
    }
    show(false);
    footer.hidden = true;
    error.textContent = "Bitte stimme Likes und Druckstatistik erneut ausdrücklich zu. Ohne Einwilligung kannst du weiter drucken.";
    error.hidden = false;
    document.dispatchEvent(new CustomEvent("coloring-consent-changed", {
      detail:{like:false,print:false}
    }));
    return true;
  }

  function eraseStatus(message) {
    erasureFeedback.textContent = message;
    erasureFeedback.hidden = false;
  }

  async function eraseProof(proof) {
    if (erasing) return;
    erasing = true;
    eraseButton.disabled = true;
    try {
      const result = await window.ColoringStats.eraseLikesWithProof(proof);
      if (result?.ok !== true) throw new Error("unconfirmed deletion");
      eraseStatus("Löschung der aktuell gespeicherten Likes für diese Browserkennung bestätigt.");
    } catch {
      eraseStatus("Einwilligung widerrufen; Löschung nicht bestätigt. Bitte nutze den Datenschutzkontakt ohne Browserkennung. Alte Kennungen werden nicht für einen Wiederholungsversuch gespeichert.");
    } finally {
      erasing = false;
      eraseButton.disabled = false;
    }
  }

  // Ordinary Like withdrawal is itself a user-directed deletion request.
  // First-visit rejection and Print-only withdrawal never read the visitor ID.
  async function changeConsent(next) {
    if (erasing) return;
    const previous = read();
    const changed = previous?.like !== Boolean(next.like) ||
      previous?.print !== Boolean(next.print);
    const revokeLike = !storageFault && previous?.like === true && !next.like;
    // Never inspect a visitor token on first visit or after refusal.
    const legacyKind = previous && (previous.like || previous.print)
      ? (window.ColoringStats?.getLegacyCredentialKind?.() || "")
      : "";
    const upgrade = (next.like || next.print)
      && (legacyKind === "v2" || legacyKind === "weak");
    const upgradeErase = upgrade && legacyKind === "v2"
      && previous?.like === true && Boolean(next.like);
    const weakLike = upgrade && legacyKind === "weak"
      && previous?.like === true && Boolean(next.like);
    // Capture the v2 deletion proof only while Like permission is still active.
    const proof = (revokeLike || upgradeErase)
      ? (window.ColoringStats?.getErasureProof?.() || "") : "";
    const priorV3 = changed
      ? (window.ColoringStats?.getCredentialForRotation?.() || "") : "";
    if (legacyKind === "unavailable" && (next.like || next.print)) {
      show(true);
      error.textContent = "Die bisherige Browserkennung kann nicht sicher gelesen werden. Bitte prüfe die Browser-Speichereinstellungen.";
      error.hidden = false;
      return;
    }
    if (upgradeErase) {
      if (!proof || (legacyUpgradeEraseAttempted && !legacyUpgradeEraseConfirmed)) {
        show(true);
        error.textContent = "Löschung nicht bestätigt. Bitte nutze den Datenschutzkontakt; die alte Kennung wird nicht automatisch erneut übertragen.";
        error.hidden = false;
        return;
      }
      if (!window.confirm("Beim Wechsel zu einer neuen Browserkennung können deine bisherigen Likes nicht übernommen werden. Sollen die alten Likes jetzt einmalig gelöscht und die neue Einwilligung gespeichert werden?")) return;
    } else if (weakLike) {
      if (!window.confirm("Die alte Browserkennung ist nicht sicher zuzuordnen. Eine Löschung früherer Likes kann nicht bestätigt werden. Trotzdem eine neue Kennung für die freiwilligen Funktionen anlegen?")) return;
    }
    // Block all purpose-based requests before any async legacy erasure or
    // new consent event. Retain the old v2 proof until erasure is confirmed.
    erasing = true;
    eraseButton.disabled = true;
    window.ColoringStats?.cancelPendingCredential?.();
    try {
      if (upgradeErase && !legacyUpgradeEraseConfirmed) {
        legacyUpgradeEraseAttempted = true;
        const result = await window.ColoringStats.eraseLikesWithProof(proof);
        if (result?.ok !== true) throw new Error("legacy deletion unconfirmed");
        legacyUpgradeEraseConfirmed = true;
      }
      if (upgradeErase && localStorage.getItem(ID_KEY) !== proof)
        throw new Error("legacy credential changed in another tab");
      if (!save(next)) return;
      if (!changed && !upgrade) return;
      try { localStorage.removeItem(ID_KEY); } catch {}
      if (!priorV3 && !next.like && !next.print && !revokeLike) return;
      if (priorV3 || next.like || next.print) {
        if (!window.ColoringStats?.changeCredential) throw new Error("credential unavailable");
        const result = await window.ColoringStats.changeCredential(next,priorV3);
        if (result?.ok !== true) throw new Error("credential not confirmed");
      }
      if (upgradeErase) {
        eraseStatus("Löschung der bisherigen aktiven Likes für die alte Browserkennung bestätigt. Die neue Kennung übernimmt keine alten Likes.");
      } else if (weakLike) {
        eraseStatus("Löschung früherer Likes nicht bestätigt. Die alte Kennung konnte nicht zugeordnet werden; bitte nutze bei Bedarf den Datenschutzkontakt.");
      }
      if (revokeLike) {
        if (priorV3) {
          eraseStatus("Löschung der aktuell gespeicherten Likes für diese Browserkennung bestätigt.");
        } else if (proof) {
          // Legacy v2 is deletion-only, including Like -> Print-only changes.
          const result = await window.ColoringStats.eraseLikesWithProof(proof);
          if (result?.ok !== true) throw new Error("legacy erasure unconfirmed");
          eraseStatus("Löschung der aktuell gespeicherten Likes für diese Browserkennung bestätigt.");
        } else {
          throw new Error("legacy credential unavailable");
        }
      }
    } catch {
      if (legacyUpgradeEraseConfirmed) {
        eraseStatus("Alte Likes gelöscht; neue Browserkennung nicht bestätigt. Bitte überprüfe die Einstellungen.");
      } else {
        eraseStatus("Einwilligung nicht vollständig geändert; Löschung oder Kennung nicht bestätigt. Bitte nutze den Datenschutzkontakt ohne Browserkennung.");
      }
      error.textContent = "Der Wechsel konnte nicht bestätigt werden. Bitte nutze bei unsicherer Löschung den Datenschutzkontakt.";
      error.hidden = false;
    } finally {
      erasing = false;
      eraseButton.disabled = false;
      document.dispatchEvent(new CustomEvent("coloring-consent-changed", {
        detail:{like:allows("like"),print:allows("print")}
      }));
    }
  }

  async function requestLikeErasure() {
    if (erasing || !allows("like")) return;
    if (!window.confirm("Deine gespeicherten Likes werden gelöscht. Das kann die sichtbaren Like-Zahlen verringern. Einverstanden?")) return;
    await changeConsent({like:false, print:Boolean(read()?.print)});
  }

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

  window.ColoringConsent = { allows, current: read, openSettings: () => show(true), requireFreshConsent };
  if (choice) hide(); else {
    banner.hidden = false;
    document.body.classList.add("has-privacy-banner");
    footer.hidden = true;
    // The footer re-open control is only needed once a decision exists.
  }
  document.addEventListener("coloring-consent-changed", () => {
    footer.hidden = !read();
  });
  window.addEventListener("storage", (event) => {
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
