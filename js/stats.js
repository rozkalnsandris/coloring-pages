(() => {
  const API_BASE = "/api/stats";
  const VISITOR_KEY = "coloring-pages-visitor-v1";

  function getVisitorId(create = false) {
    try {
      let value = localStorage.getItem(VISITOR_KEY);
      if (!value && create) {
        value = globalThis.crypto?.randomUUID?.() || `v-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        localStorage.setItem(VISITOR_KEY, value);
      }
      return value || "";
    } catch {
      return "";
    }
  }

  async function requestJson(path, options = {}) {
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
    if (!response.ok) throw new Error(`stats request failed: ${response.status}`);
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

  async function getPage(pageId) {
    const visitorId = getVisitorId(false);
    const query = new URLSearchParams({page_id: pageId});
    if (visitorId) query.set("visitor_id", visitorId);
    return requestJson(`/page?${query}`);
  }

  async function toggleLike(pageId) {
    const visitorId = getVisitorId(true);
    return requestJson("/like", {
      method: "POST",
      body: JSON.stringify({page_id: pageId, visitor_id: visitorId}),
    });
  }

  function trackVisit() {
    const body = "{}";
    if (navigator.sendBeacon) {
      try {
        const blob = new Blob([body], {type: "application/json"});
        if (navigator.sendBeacon(`${API_BASE}/visit`, blob)) return;
      } catch {}
    }
    fetch(`${API_BASE}/visit`, {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {"Content-Type": "application/json"},
      body,
    }).catch(() => {});
  }

  function trackView(pageId) {
    const body = JSON.stringify({page_id: pageId});
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
    const visitorId = getVisitorId(true);
    const body = JSON.stringify({page_id: pageId, visitor_id: visitorId});
    if (navigator.sendBeacon) {
      try {
        const blob = new Blob([body], {type: "application/json"});
        if (navigator.sendBeacon(`${API_BASE}/print`, blob)) return;
      } catch {}
    }
    fetch(`${API_BASE}/print`, {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {"Content-Type": "application/json"},
      body,
    }).catch(() => {});
  }

  window.ColoringStats = {getRankings, getOverview, getTraffic, getPage, toggleLike, trackVisit, trackView, trackPrint};

  const publicPath = location.pathname === "/" || location.pathname === "/index.html" || location.pathname === "/detail.html";
  if (publicPath) trackVisit();
})();
