/* GoatCounter SIMPLE #442: consent-gated first-party activation. */
(() => {
  "use strict";

  const tag = document.querySelector("script[data-goatcounter-simple]");
  const consentMode = tag?.getAttribute("data-goatcounter-simple") === "consent";
  if (!consentMode || !["ausmalwiese.de", "www.ausmalwiese.de"].includes(location.hostname)) return;
  if (window.goatcounter || window.GoatCounterSimple) return;

  const panel = document.querySelector("[data-analytics-consent]");
  const allow = document.querySelector("[data-analytics-allow]");
  const deny = document.querySelector("[data-analytics-deny]");
  const settings = document.querySelector("[data-analytics-settings]");
  if (!panel || !allow || !deny || !settings) return; // Fail closed without withdrawal controls.

  const CONSENT_KEY = "ausmalwiese.analytics-consent.v1";
  let choice = "";
  let queued = null;
  let attempted = false;
  let remoteStarted = false;

  function readChoice() {
    try {
      const value = window.localStorage?.getItem(CONSENT_KEY);
      return value === "granted" || value === "denied" ? value : "";
    } catch {
      return "";
    }
  }

  function storeChoice(value) {
    choice = value;
    try {
      window.localStorage?.setItem(CONSENT_KEY, value);
    } catch {
      // Explicit current-page choice still applies; next page asks again.
    }
  }

  function showDecision() {
    panel.hidden = false;
    settings.hidden = true;
  }

  function hideDecision() {
    panel.hidden = true;
    settings.hidden = false;
  }

  function approvedCampaign() {
    const params = new URLSearchParams(location.search);
    if (params.getAll("utm_source").length !== 1 || params.get("utm_source") !== "instagram"
        || params.getAll("utm_medium").length !== 1 || params.get("utm_medium") !== "social"
        || params.getAll("utm_campaign").length !== 1
        || !["profile", "story", "reel"].includes(params.get("utm_campaign"))) return "";
    return params.get("utm_campaign");
  }

  function referrer() {
    const campaign = approvedCampaign();
    if (campaign) return "Instagram " + campaign;
    try {
      const source = new URL(document.referrer);
      return ["https:", "http:"].includes(source.protocol) ? source.origin : "";
    } catch {
      return "";
    }
  }

  function flush() {
    if (choice !== "granted" || !queued || typeof window.goatcounter?.count !== "function") return;
    const payload = queued;
    queued = null;
    try {
      if (!window.goatcounter.filter?.()) window.goatcounter.count(payload);
    } catch {
      // Optional measurement must never affect site navigation, Like, or printing.
    }
  }

  function startRemote() {
    if (choice !== "granted" || !queued || remoteStarted) return;
    remoteStarted = true;
    window.goatcounter = {
      no_onload: true,
      no_events: true,
      endpoint: location.origin + "/count",
    };
    const remote = document.createElement("script");
    remote.src = "https://gc.zgo.at/count.v5.js";
    remote.async = true;
    remote.crossOrigin = "anonymous";
    remote.integrity = "sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ";
    remote.addEventListener("load", () => {
      if (choice !== "granted") return;
      const getData = window.goatcounter?.get_data;
      if (typeof getData !== "function") { queued = null; return; }
      window.goatcounter.get_data = function(vars) {
        const data = getData.call(this, vars);
        const campaign = approvedCampaign();
        data.q = campaign
          ? "?utm_source=instagram&utm_medium=social&utm_campaign=" + campaign
          : "";
        return data;
      };
      flush();
    }, {once: true});
    remote.addEventListener("error", () => { queued = null; }, {once: true});
    document.head.append(remote);
  }

  function track(path, title) {
    if (attempted) return;
    attempted = true;
    queued = {path, title, referrer: referrer()};
    startRemote();
    flush();
  }

  function decide(value) {
    storeChoice(value);
    hideDecision();
    if (value === "granted") startRemote();
  }

  allow.addEventListener("click", () => decide("granted"));
  deny.addEventListener("click", () => decide("denied"));
  settings.addEventListener("click", showDecision);

  choice = readChoice();
  if (choice) hideDecision();
  else showDecision();

  window.GoatCounterSimple = {
    home() {
      track("/", "Ausmalwiese");
    },
    detail(id, title) {
      if (typeof id !== "string" || !/^[0-9]{7}$/.test(id)) return;
      track("/ausmalbild/" + id, typeof title === "string" ? title.slice(0, 100) : "Ausmalbild");
    },
  };

  if (location.pathname === "/" || location.pathname === "/index.html") {
    window.GoatCounterSimple.home();
  }
})();
