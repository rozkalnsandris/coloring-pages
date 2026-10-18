(() => {
  const API_BASE = "/api/stats";
  // One attempt per page ID during this document lifetime; nothing is persisted.
  const attemptedLikes = new Set();
  const CAMPAIGN_IDS = new Set(["dortmund-01"]);
  const INSTAGRAM_UTM_CAMPAIGNS = new Set(["profile", "story", "reel"]);

  // A tagged external landing is an aggregate event, never a distinct person.
  // No referrer URL, user identifier or campaign value is persisted by this client.
  function instagramLandingCampaign() {
    if (location.hostname !== "ausmalwiese.de" && location.hostname !== "www.ausmalwiese.de") return "";
    const params = new URLSearchParams(location.search);
    if (params.getAll("utm_source").length !== 1 || params.getAll("utm_medium").length !== 1
        || params.getAll("utm_campaign").length !== 1) return "";
    if (params.get("utm_source") !== "instagram" || params.get("utm_medium") !== "social") return "";
    const name = params.get("utm_campaign") || "";
    if (!INSTAGRAM_UTM_CAMPAIGNS.has(name)) return "";

    // Do not count browser refreshes or tagged internal links as new arrivals.
    const navigation = performance.getEntriesByType?.("navigation")?.[0];
    if (navigation?.type === "reload") return "";
    if (document.referrer) {
      try {
        const from = new URL(document.referrer);
        if (from.hostname === "ausmalwiese.de" || from.hostname === "www.ausmalwiese.de") return "";
      } catch {
        // Browser-referrer suppression does not prevent an explicit UTM landing.
      }
    }
    return "instagram-" + name;
  }

  function currentCampaign() {
    const value = new URLSearchParams(location.search).get("campaign") || "";
    return CAMPAIGN_IDS.has(value) ? value : "";
  }

  async function requestJson(path, options = {}, expectedStatus) {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      credentials: "same-origin",
      ...options,
      headers: {
        "Accept": "application/json",
        ...(options.body ? {"Content-Type": "application/json"} : {}),
        ...(options.headers || {}),
      },
    });
    if (!response.ok || (expectedStatus && response.status !== expectedStatus)) {
      throw new Error(`stats request failed: ${response.status}`);
    }
    return response.json();
  }

  async function getRankings(limit = 6) {
    const safeLimit = Math.min(20, Math.max(1, Number(limit) || 6));
    return requestJson(`/rankings?limit=${safeLimit}`);
  }

  async function getOverview() {
    return requestJson("/overview");
  }

  async function getTraffic(days = 7) {
    const safeDays = Number(days) === 30 ? 30 : 7;
    return requestJson(`/traffic?days=${safeDays}`);
  }

  async function getCampaigns(days = 30) {
    const safeDays = Number(days) === 7 ? 7 : 30;
    return requestJson(`/campaigns?days=${safeDays}`);
  }

  function validPageCounts(data, pageId) {
    return data?.page_id === pageId
      && Number.isSafeInteger(data.like_count) && data.like_count >= 0
      && Number.isSafeInteger(data.print_count) && data.print_count >= 0;
  }

  async function getPage(pageId) {
    const query = new URLSearchParams({page_id: pageId});
    const data = await requestJson(`/page?${query}`, {credentials: "omit"});
    if (!validPageCounts(data, pageId)) throw new Error("invalid page totals");
    return {page_id: pageId, like_count: data.like_count, print_count: data.print_count};
  }

  async function addLike(pageId) {
    if (attemptedLikes.has(pageId)) throw new Error("reaction already attempted");
    attemptedLikes.add(pageId);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const data = await requestJson("/like-aggregate", {
        method: "POST",
        credentials: "omit",
        signal: controller.signal,
        body: JSON.stringify({page_id: pageId}),
      }, 201);
      if (!validPageCounts(data, pageId) || data.reacted !== true || data.like_count < 1) {
        throw new Error("reaction unconfirmed");
      }
      return data;
    } finally {
      clearTimeout(timeout);
      // Never unlock or resend: an unconfirmed write may have committed.
    }
  }

  function trackVisit() {
    const stage = arguments[0] || "";
    const campaign = currentCampaign();
    const instagram = campaign ? "" : instagramLandingCampaign();
    const body = campaign && (stage === "landing" || stage === "catalog")
      ? {campaign,stage}
      : instagram ? {campaign:instagram,stage:"landing"} : {};
    fetch(`${API_BASE}/visit`, {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    }).catch(() => {});
  }

  function trackView(pageId) {
    const payload = {page_id: pageId};
    const campaign = currentCampaign();
    if (campaign) payload.campaign = campaign;
    const body = JSON.stringify(payload);
    if (navigator.sendBeacon) {
      try {
        const blob = new Blob([body], {type: "application/json"});
        if (navigator.sendBeacon(`${API_BASE}/view`, blob)) return;
      } catch {}
    }
    fetch(`${API_BASE}/view`, {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {"Content-Type": "application/json"},
      body,
    }).catch(() => {});
  }

  function trackPrint(pageId) {
    const payload = {page_id: pageId};
    const campaign = currentCampaign();
    if (campaign) payload.campaign = campaign;
    const body = JSON.stringify(payload);
    try {
      // Fetch lets this request explicitly omit cookies; no beacon/fallback resend.
      fetch(`${API_BASE}/print-aggregate`, {
        method: "POST",
        credentials: "omit",
        keepalive: true,
        headers: {"Content-Type": "application/json"},
        body,
      }).catch(() => {});
    } catch {
      // Telemetry must never prevent the print dialog from opening.
    }
  }

  window.ColoringStats = {getRankings, getOverview, getTraffic, getCampaigns, getPage, addLike, trackVisit, trackView, trackPrint};

  const homePath = location.pathname === "/" || location.pathname === "/index.html";
  const detailPath = location.pathname === "/detail.html";
  if (homePath) trackVisit(currentCampaign() ? "catalog" : "");
  if (detailPath) trackVisit();
})();
