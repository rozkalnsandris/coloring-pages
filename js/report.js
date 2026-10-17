// Optional, privacy-minimal per-activity error reporting; never blocks printing.
(() => {
  const root = document.querySelector("[data-detail-root]");
  const openButton = document.querySelector("[data-report-open]");
  const panel = document.querySelector("[data-report-panel]");
  const closeButton = document.querySelector("[data-report-close]");
  const form = document.querySelector("[data-report-form]");
  const status = document.querySelector("[data-report-status]");
  const submit = document.querySelector("[data-report-submit]");
  const challengeMount = document.querySelector("[data-report-turnstile]");
  if (!root || !openButton || !panel || !form || !status || !submit || !challengeMount) return;

  let activityId = "";
  let page = 1;
  let token = "";
  let widgetId = null;
  let siteKeyPromise = null;
  let scriptPromise = null;
  let busy = false;
  const ACTIVITY_UNAVAILABLE = "activity_unavailable";
  const ACTIVITY_UNAVAILABLE_MESSAGE = "Diese Malvorlage ist nicht mehr verfügbar. Bitte lade die Seite neu oder wähle eine andere Vorlage.";
  function say(message) { status.textContent = message; }
  function markActivityUnavailable() {
    activityId = "";
    panel.hidden = true;
    openButton.hidden = true;
    openButton.setAttribute("aria-expanded", "false");
    say(ACTIVITY_UNAVAILABLE_MESSAGE);
  }
  function close() {
    if (busy) return;
    panel.hidden = true;
    openButton.setAttribute("aria-expanded", "false");
    openButton.focus();
  }
  function loadScript() {
    if (window.turnstile) return Promise.resolve();
    if (!scriptPromise) {
      scriptPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
        script.async = true;
        script.onload = () => window.turnstile ? resolve() : reject(new Error("Turnstile unavailable"));
        script.onerror = () => reject(new Error("Turnstile unavailable"));
        document.head.append(script);
      });
    }
    return scriptPromise;
  }
  async function showChallenge() {
    if (!siteKeyPromise) {
      siteKeyPromise = fetch("/api/report/config", {
        headers: { accept: "application/json" }, cache: "no-store",
      }).then(async (response) => {
        if (!response.ok) throw new Error("Report endpoint unavailable");
        const config = await response.json();
        if (typeof config.siteKey !== "string" || !config.siteKey) throw new Error("Site key unavailable");
        return config.siteKey;
      });
    }
    const [siteKey] = await Promise.all([siteKeyPromise, loadScript()]);
    if (widgetId !== null) {
      window.turnstile.reset(widgetId);
    } else {
      widgetId = window.turnstile.render(challengeMount, {
        sitekey: siteKey,
        action: "report",
        callback: (value) => { token = value; },
        "expired-callback": () => { token = ""; },
        "error-callback": () => { token = ""; say("Sicherheitsprüfung nicht verfügbar."); },
      });
    }
  }
  document.addEventListener("ausmalwiese:detail-loaded", (event) => {
    const id = event.detail?.id;
    if (typeof id !== "string" || !/^[a-z0-9][a-z0-9_-]{0,79}$/i.test(id)) return;
    activityId = id;
    page = Math.max(1, Number(root.dataset.pageIndex || 0) + 1);
    openButton.hidden = false;
  });
  document.addEventListener("ausmalwiese:page-change", (event) => {
    if (Number.isInteger(event.detail?.index)) page = event.detail.index + 1;
  });
  openButton.addEventListener("click", async () => {
    if (!activityId) return;
    panel.hidden = false;
    openButton.setAttribute("aria-expanded", "true");
    say("");
    form.reset();
    token = "";
    form.querySelector('input[name="reason"]')?.focus();
    try {
      await showChallenge();
    } catch {
      siteKeyPromise = null;
      say("Die Meldung ist gerade nicht verfügbar. Bitte versuche es später erneut.");
    }
  });
  closeButton?.addEventListener("click", close);
  panel.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || !activityId) return;
    const reason = form.elements.namedItem("reason")?.value;
    if (!reason) return;
    if (!token) { say("Bitte schließe zuerst die Sicherheitsprüfung ab."); return; }
    busy = true;
    submit.disabled = true;
    closeButton.disabled = true;
    say("");
    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify({ id: activityId, page, reason, turnstile: token }),
      });
      const result = await response.json().catch(() => null);
      if (response.status === 409 && result?.ok === false && result?.error === ACTIVITY_UNAVAILABLE) {
        markActivityUnavailable();
        return;
      }
      if (!response.ok || result?.ok !== true) throw new Error("not sent");
      panel.hidden = true;
      openButton.setAttribute("aria-expanded", "false");
      say("Danke! Deine Meldung wurde gesendet.");
      openButton.focus();
    } catch {
      say("Die Meldung konnte nicht gesendet werden. Bitte versuche es später erneut.");
    } finally {
      token = "";
      if (widgetId !== null) window.turnstile?.reset(widgetId);
      busy = false;
      submit.disabled = false;
      closeButton.disabled = false;
    }
  });
})();
