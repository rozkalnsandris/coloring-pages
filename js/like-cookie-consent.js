(() => {
  "use strict";
  // A voluntary Like-only notice, opened by Like or the privacy-settings
  // control. No banner on arrival, no JS access to HttpOnly Like cookies.
  let consented=false,changing=false,legacyAttempted=false;
  const banner=document.createElement("section");
  banner.className="privacy-banner";
  banner.setAttribute("role","region");
  banner.setAttribute("aria-label","Gefällt-mir-Datenschutzeinstellungen");
  banner.innerHTML=[
    '<div class="privacy-banner-row">',
    '<p class="privacy-banner-copy">Wenn Sie „Gefällt mir“ nutzen möchten, ',
    'können wir Ihre Auswahl auf späteren Besuchen mit einem Cookie ',
    'wiedererkennen. Ohne Zustimmung bleibt das Drucken verfügbar. ',
    '<a href="datenschutz.html">Datenschutz</a></p>',
    '<div class="privacy-banner-actions">',
    '<button type="button" data-like-deny>Ablehnen</button>',
    '<button type="button" data-like-accept>Zustimmen</button>',
    '<button type="button" data-like-close>Schließen</button>',
    '</div></div>',
    '<div class="privacy-options-actions">',
    '<button type="button" data-like-forget>Meine gespeicherten Likes löschen</button>',
    '<button type="button" data-like-old>Alte Likes löschen (falls vorhanden)</button>',
    '</div>',
    '<p class="privacy-consent-error" data-like-feedback role="status" aria-live="polite" hidden></p>'
  ].join("");
  banner.hidden=true;
  const footer=document.createElement("footer");
  footer.className="privacy-footer";
  const settings=document.createElement("button");
  settings.type="button";
  settings.textContent="Gefällt-mir-Datenschutzeinstellungen";
  footer.append(settings);
  document.body.append(banner,footer);
  const feedback=banner.querySelector("[data-like-feedback]");
  const accept=banner.querySelector("[data-like-accept]");
  const forget=banner.querySelector("[data-like-forget]");
  let lastFocus=null;
  const allows=purpose=>purpose==="like" && consented && !changing;
  function syncFromServer(value) {
    const next=value===true;
    if(changing||next===consented)return;
    consented=next;
    document.dispatchEvent(new CustomEvent("coloring-consent-changed",
      {detail:{like:consented,print:false}}));
  }
  function openSettings() {
    lastFocus=document.activeElement;
    feedback.hidden=true;
    banner.hidden=false;
    document.body.classList.add("has-privacy-banner");
    accept.hidden=consented;
    forget.hidden=!consented;
    (consented?forget:accept).focus();
  }
  function close() {
    banner.hidden=true;
    document.body.classList.remove("has-privacy-banner");
    lastFocus?.focus?.();
  }
  function announce(message) {
    feedback.textContent=message;
    feedback.hidden=false;
  }
  async function setChoice(activate) {
    if(changing)return;
    if(!activate) { close();return; }
    changing=true;accept.disabled=true;
    try {
      if(!window.ColoringStats?.enableLikeCookie)throw new Error("unavailable");
      await window.ColoringStats.enableLikeCookie();
      consented=true;
      close();
    } catch {
      announce("Die Cookie-Einwilligung konnte nicht bestätigt werden. Es wurde kein Like gespeichert.");
    } finally {
      changing=false;accept.disabled=false;
      if(consented)document.dispatchEvent(new CustomEvent("coloring-consent-changed",
        {detail:{like:true,print:false}}));
    }
  }
  async function revoke() {
    if(changing||!consented)return;
    if(!window.confirm("Ihre gespeicherten Likes werden entfernt. Die Like-Zahlen können sinken. Fortfahren?"))return;
    changing=true;forget.disabled=true;
    try {
      const result=await window.ColoringStats.disableLikeCookie();
      if(result?.revoked!==true)throw new Error("unconfirmed");
      consented=false;
      close();
      document.dispatchEvent(new CustomEvent("coloring-consent-changed",
        {detail:{like:false,print:false}}));
    } catch {
      announce("Löschung nicht bestätigt. Bitte nutzen Sie den Datenschutzkontakt ohne Browserkennung.");
    } finally {changing=false;forget.disabled=false;}
  }
  async function eraseOld() {
    if(changing||legacyAttempted)return;
    if(!window.confirm("Alte Likes einmalig löschen? Dies betrifft nur eine noch vorhandene sichere ältere Browserkennung."))return;
    legacyAttempted=true;changing=true;
    try {
      await window.ColoringStats.eraseLegacyLikes();
      announce("Löschung der aktuell gespeicherten alten Likes bestätigt.");
    } catch {
      announce("Löschung nicht bestätigt. Alte Kennung bitte nicht per E-Mail senden. Kontakt: Datenschutz.");
    } finally {changing=false;}
  }
  banner.querySelector("[data-like-accept]").addEventListener("click",()=>setChoice(true));
  banner.querySelector("[data-like-deny]").addEventListener("click",()=>setChoice(false));
  banner.querySelector("[data-like-close]").addEventListener("click",close);
  banner.querySelector("[data-like-forget]").addEventListener("click",revoke);
  banner.querySelector("[data-like-old]").addEventListener("click",eraseOld);
  settings.addEventListener("click",openSettings);
  window.ColoringConsent={allows,openSettings,syncFromServer,
    current:()=>({like:consented,print:false})};
})();