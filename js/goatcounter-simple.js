/* GoatCounter SIMPLE #442: inactive until the separately approved /count ingress is ready. */
(() => {
  "use strict";

  const tag = document.querySelector("script[data-goatcounter-simple]");
  const enabled = tag?.getAttribute("data-goatcounter-simple") === "enabled";
  if (!enabled || !["ausmalwiese.de", "www.ausmalwiese.de"].includes(location.hostname)) return;
  if (window.goatcounter) return; // Never compete with another GoatCounter integration.

  let queued = null;
  let attempted = false;

  // Upstream count.v5.js includes the entire location.search as `q`.
  // Permit only the three exact, known Instagram campaign parameters.
  function campaignQuery() {
    const params = new URLSearchParams(location.search);
    const allowed = ["utm_source", "utm_medium", "utm_campaign"];
    if ([...params.keys()].some(key => !allowed.includes(key))) return "";
    if (params.getAll("utm_source").length !== 1 || params.get("utm_source") !== "instagram"
        || params.getAll("utm_medium").length !== 1 || params.get("utm_medium") !== "social"
        || params.getAll("utm_campaign").length !== 1
        || !["profile", "story", "reel"].includes(params.get("utm_campaign"))) return "";
    return "?" + allowed.map(key =>
      encodeURIComponent(key) + "=" + encodeURIComponent(params.get(key))).join("&");
  }

  function referrer() {
    const campaign = campaignQuery();
    if (campaign) {
      return "Instagram " + new URLSearchParams(campaign).get("utm_campaign");
    }
    try {
      const source = new URL(document.referrer);
      return ["https:", "http:"].includes(source.protocol) ? source.origin : "";
    } catch {
      return "";
    }
  }

  function flush() {
    if (!queued || typeof window.goatcounter?.count !== "function") return;
    const payload = queued;
    queued = null;
    try {
      if (!window.goatcounter.filter?.()) window.goatcounter.count(payload);
    } catch {
      // Optional measurement must never affect site navigation, Like, or printing.
    }
  }

  function track(path, title) {
    if (attempted) return;
    attempted = true; // No resend, even if the network or script fails.
    queued = {path, title, referrer: referrer()};
    flush();
  }

  window.GoatCounterSimple = {
    home() {
      track("/", "Ausmalwiese");
    },
    detail(id, title) {
      if (typeof id !== "string" || !/^[0-9]{7}$/.test(id)) return;
      track("/ausmalbild/" + id, typeof title === "string" ? title.slice(0, 100) : "Ausmalbild");
    },
  };

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
    // Keep upstream bot filtering, sessions and transport unchanged.
    // Override only its undocumented raw-query inclusion before the first count.
    if (typeof window.goatcounter?.get_data !== "function") {
      queued = null;
      return;
    }
    const originalGetData = window.goatcounter.get_data;
    window.goatcounter.get_data = function(vars) {
      const data = originalGetData(vars);
      data.q = campaignQuery();
      return data;
    };
    flush();
  }, {once: true});
  remote.addEventListener("error", () => { queued = null; }, {once: true});
  document.head.append(remote);

  if (location.pathname === "/" || location.pathname === "/index.html") {
    window.GoatCounterSimple.home();
  }
})();
