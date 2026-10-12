(() => {
  const API_BASE = "/api/stats";
  const VISITOR_KEY = "coloring-pages-visitor-v1";
  const CAMPAIGN_IDS = new Set(["dortmund-01"]);

  function currentCampaign() {
    const value = new URLSearchParams(location.search).get("campaign") || "";
    return CAMPAIGN_IDS.has(value) ? value : "";
  }

  const V3_RE = /^v3-[0-9a-f]{64}$/;
  let credentialGeneration = 0;
  function getVisitorId(create = false, purpose = "like") {
    if (window.ColoringConsent?.allows?.(purpose) !== true) return "";
    try {
      const id = localStorage.getItem(VISITOR_KEY) || "";
      return V3_RE.test(id) ? id : ""; // never reuse legacy v1/v2 for writes
    } catch { return ""; }
  }
  function getCredentialForRotation() {
    if (window.ColoringConsent?.allows?.("like") !== true
      && window.ColoringConsent?.allows?.("print") !== true) return "";
    try {
      const id = localStorage.getItem(VISITOR_KEY) || "";
      return V3_RE.test(id) ? id : "";
    } catch { return ""; }
  }
  // Classify only after an existing purpose-specific opt-in. Never send
  // weak/legacy credentials to normal personalized endpoints.
  function getLegacyCredentialKind() {
    if (window.ColoringConsent?.allows?.("like") !== true
        && window.ColoringConsent?.allows?.("print") !== true) return "";
    try {
      const id = localStorage.getItem(VISITOR_KEY) || "";
      if (!id || V3_RE.test(id)) return "";
      return /^v2-[0-9a-f]{64}$/.test(id) ? "v2" : "weak";
    } catch {
      return "unavailable";
    }
  }
  function cancelPendingCredential() { credentialGeneration++; }
  async function changeCredential(next, priorId = "") {
    const generation = credentialGeneration;
    const result = await requestJson("/credential", {
      method: "POST",
      body: JSON.stringify({version:1,like:!!next.like,print:!!next.print,
        ...(priorId ? {prior_id:priorId} : {})}),
    });
    if (generation !== credentialGeneration
        || window.ColoringConsent?.current?.()?.like !== !!next.like
        || window.ColoringConsent?.current?.()?.print !== !!next.print)
      throw new Error("consent changed during issuance");
    if (next.like || next.print) {
      if (!result.ok || !V3_RE.test(result.visitor_id)) throw new Error("credential unconfirmed");
      localStorage.setItem(VISITOR_KEY,result.visitor_id);
    } else if (result.ok !== true) throw new Error("revocation unconfirmed");
    document.dispatchEvent(new CustomEvent("coloring-consent-changed", {detail:next}));
    return result;
  }
  async function ensureCredential(purpose) {
    if (window.ColoringConsent?.allows?.(purpose) !== true) return "";
    const id = getVisitorId(false,purpose);
    if (id) return id;
    // Never mint a replacement automatically from an old localStorage choice.
    window.ColoringConsent?.requireFreshConsent?.();
    return "";
  }
  function handleExpiredCredential(error, submittedId) {
    if (error?.code === "credential_expired")
      window.ColoringConsent?.requireFreshConsent?.(submittedId);
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
    if (!response.ok) {
      // Only the server's explicit credential_expired response triggers renewal.
      let code = "";
      if (response.status === 403) {
        try { code = (await response.json())?.error || ""; } catch {}
      }
      const error = new Error(`stats request failed: ${response.status}`);
      error.code = code;
      throw error;
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

  async function getPage(pageId) {
    const visitorId = getVisitorId(false);
    const query = new URLSearchParams({page_id: pageId});
    if (visitorId) {
      try {
        return await requestJson("/page", {
          method: "POST",
          body: JSON.stringify({page_id: pageId, visitor_id: visitorId}),
        });
      } catch (error) {
        if (error?.code !== "credential_expired") throw error;
        handleExpiredCredential(error,visitorId);
      }
    } else if (window.ColoringConsent?.allows?.("like") === true) {
      window.ColoringConsent?.requireFreshConsent?.();
    }
    return requestJson(`/page?${query}`);
  }

  async function toggleLike(pageId) {
    if (window.ColoringConsent?.allows?.("like") !== true) throw new Error("like consent required");
    const visitorId = await ensureCredential("like");
    if (!visitorId) throw new Error("visitor ID unavailable");
    try {
      return await requestJson("/like", {
        method: "POST",
        body: JSON.stringify({page_id: pageId, visitor_id: visitorId}),
      });
    } catch (error) {
      handleExpiredCredential(error,visitorId);
      throw error;
    }
  }

  // Read the retired v2 credential solely for user-directed Like erasure.
  // Normal Like/Print/status paths remain strictly v3-only.
  function getErasureProof() {
    if (window.ColoringConsent?.allows?.("like") !== true) return "";
    try {
      const id = localStorage.getItem(VISITOR_KEY) || "";
      return /^v2-[0-9a-f]{64}$/.test(id) ? id : "";
    } catch {
      return ""; // blocked storage must not falsely confirm deletion
    }
  }

  async function eraseLikesWithProof(visitorId) {
    if (!/^v2-[0-9a-f]{64}$/.test(visitorId)) throw new Error("erasure proof unavailable");
    return requestJson("/erase-likes", {
      method: "POST",
      body: JSON.stringify({visitor_id: visitorId}),
    });
  }

  function trackVisit() {
    const stage = arguments[0] || "";
    const campaign = currentCampaign();
    const body = campaign && (stage === "landing" || stage === "catalog")
      ? {campaign,stage}
      : {};
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
    if (window.ColoringConsent?.allows?.("print") !== true) return;
    // Telemetry may fail; never delay or prevent A4 printing.
    void (async () => {
      const visitorId = await ensureCredential("print");
      if (!visitorId) return;
      const payload = {page_id:pageId,visitor_id:visitorId};
      const campaign = currentCampaign();
      if (campaign) payload.campaign = campaign;
      try {
        // A keepalive fetch can inspect credential_expired; sendBeacon cannot.
        await requestJson("/print", {
          method:"POST",keepalive:true,body:JSON.stringify(payload)
        });
      } catch (error) {
        handleExpiredCredential(error,visitorId);
      }
    })().catch(() => {});
  }

  window.ColoringStats = {getRankings, getOverview, getTraffic, getCampaigns, getPage, toggleLike, getErasureProof, eraseLikesWithProof, getCredentialForRotation, getLegacyCredentialKind, cancelPendingCredential, changeCredential, trackVisit, trackView, trackPrint};

  const homePath = location.pathname === "/" || location.pathname === "/index.html";
  const detailPath = location.pathname === "/detail.html";
  if (homePath) trackVisit(currentCampaign() ? "catalog" : "");
  if (detailPath) trackVisit();
})();
