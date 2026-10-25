// First-party GoatCounter pageview client for issue #376.
// Sends only a validated seven-digit page ID to the same-origin adapter.
// No cookies, browser storage, referrer, campaign or retry queue.
(() => {
  const ROUTE = "/api/pageview";
  const PAGE_ID_RE = /^[0-9]{7}$/;
  const attempted = new Set();

  function track(pageId) {
    if (typeof pageId !== "string" || !PAGE_ID_RE.test(pageId) || attempted.has(pageId)) {
      return false;
    }
    attempted.add(pageId);

    const body = JSON.stringify({ page_id: pageId });
    try {
      void fetch(ROUTE, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
        credentials: "omit",
        cache: "no-store",
        redirect: "error",
        referrerPolicy: "no-referrer",
        keepalive: true,
      }).catch(() => {});
    } catch {
      // Analytics is fail-open and deliberately not retried in this page lifetime.
    }
    return true;
  }

  window.AusmalPageviews = Object.freeze({ track });
})();
