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
  const allows = (purpose) => (purpose === "like" || purpose === "print") &&
    choice !== null && choice[purpose] === true;

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
      '<div class="privacy-options-actions">',
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
  footer.append(reopen);
  document.body.append(banner, footer);

  const options = banner.querySelector("[data-consent-options]");
  const like = banner.querySelector("[data-consent-like]");
  const print = banner.querySelector("[data-consent-print]");
  const error = banner.querySelector("[data-consent-error]");
  const settings = banner.querySelector("[data-consent-settings]");
  let lastFocus = null;

  function show(advanced = false) {
    lastFocus = document.activeElement;
    banner.hidden = false;
    document.body.classList.add("has-privacy-banner");
    options.hidden = !advanced;
    like.checked = Boolean(choice?.like);
    print.checked = Boolean(choice?.print);
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
      if (!record.like && !record.print) localStorage.removeItem(ID_KEY);
    } catch {
      // No permission is activated if storage cannot record it.
      choice = previous;
      error.textContent = "Deine Auswahl konnte nicht gespeichert werden. Bitte versuche es erneut.";
      error.hidden = false;
      return;
    }
    hide();
    document.dispatchEvent(new CustomEvent("coloring-consent-changed", {
      detail: { like: choice.like, print: choice.print }
    }));
  }

  banner.querySelector("[data-consent-deny]").addEventListener("click", () =>
    save({like:false, print:false}));
  banner.querySelector("[data-consent-accept]").addEventListener("click", () =>
    save({like:true, print:true}));
  settings.addEventListener("click", () => show(true));
  banner.querySelector("[data-consent-save]").addEventListener("click", () =>
    save({like:like.checked, print:print.checked}));
  banner.querySelector("[data-consent-cancel]").addEventListener("click", () => {
    if (choice) hide(); else show(false);
  });
  reopen.addEventListener("click", () => show(true));

  window.ColoringConsent = { allows, openSettings: () => show(true) };
  if (choice) hide(); else {
    banner.hidden = false;
    document.body.classList.add("has-privacy-banner");
    footer.hidden = true;
    // The footer re-open control is only needed once a decision exists.
  }
  document.addEventListener("coloring-consent-changed", () => {
    footer.hidden = false;
  });
})();
