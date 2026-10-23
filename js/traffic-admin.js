(() => {
  // This page may render only Cloudflare HTTP Analytics returned by the fixed
  // read-only /api/stats/traffic proxy. D1 engagement and campaign events are
  // intentionally restricted to the separate Statistics dashboard.
  const els = {
    status: document.querySelector("[data-traffic-page-status]"),
    range: document.querySelector("[data-traffic-days]"),
    rangeLabel: document.querySelector("[data-traffic-range-label]"),
    refresh: document.querySelector("[data-traffic-refresh]"),
    unique: document.querySelector("[data-traffic-unique]"),
    visits: document.querySelector("[data-stats-visits]"),
    crawlers: document.querySelector("[data-stats-crawler-requests]"),
    crawlerStatus: document.querySelector("[data-traffic-status]"),
    crawlerTable: document.querySelector("[data-stats-crawlers]"),
    crawlerEmpty: document.querySelector("[data-stats-crawlers-empty]"),
    note: document.querySelector("[data-traffic-visits-note]"),
  };
  const fmt = new Intl.NumberFormat("en-GB");
  let requestNumber = 0;
  const validCount = value => Number.isSafeInteger(value) && value >= 0;

  function renderCrawlerRow(crawler) {
    const tr = document.createElement("tr");
    const name = document.createElement("td");
    const count = document.createElement("td");
    const paths = document.createElement("td");
    name.textContent = typeof crawler.name === "string" ? crawler.name : "Other crawler";
    count.className = "stats-number";
    count.textContent = fmt.format(crawler.requests);
    paths.textContent = (Array.isArray(crawler.paths) ? crawler.paths : [])
      .filter(item => item && typeof item.path === "string" && validCount(item.requests))
      .map(item => item.path + " (" + fmt.format(item.requests) + ")")
      .join(" · ");
    tr.append(name, count, paths);
    return tr;
  }

  function render(data, days) {
    if (data?.range_days !== days || !validCount(data.visits)
        || !validCount(data.crawler_requests) || !Array.isArray(data.crawlers)
        || typeof data.sampled !== "boolean") {
      throw new Error("invalid Cloudflare traffic analytics response");
    }
    // The zone-level uniq rollup cannot be claimed as hostname-specific.
    // Retired D1/IP-HMAC fields must not be read, even on a legacy Worker.
    els.unique.textContent = "N/A";
    els.visits.textContent = fmt.format(data.visits);
    els.crawlers.textContent = fmt.format(data.crawler_requests);
    els.rangeLabel.textContent = "Last " + days + " days";
    els.crawlerStatus.textContent = data.sampled
      ? "Cloudflare · sampled · User-Agent heuristic"
      : "Cloudflare · User-Agent heuristic";
    const validRows = data.crawlers.filter(row => row && validCount(row.requests));
    els.crawlerTable.replaceChildren(...validRows.map(renderCrawlerRow));
    els.crawlerEmpty.hidden = validRows.length !== 0;
    const hostProof = data.analytics_host === "ausmalwiese.de" && data.cloudflare_traffic_version === 1;
    els.note.textContent =
      "Unique visitors: N/A, because a hostname-scoped unique count has not been verified. " +
      "Cloudflare Website visits are not unique people; crawler request counts must not be subtracted from visits. " +
      (data.sampled ? "Provider sampling is active. " : "Provider data may be sampled. ") +
      (hostProof ? "Hostname: ausmalwiese.de (Worker-declared)."
        : "The active Worker's Cloudflare analytics hostname is not independently verified.");
    const clock = new Intl.DateTimeFormat("en-GB", {hour:"2-digit",minute:"2-digit"}).format(new Date());
    els.status.textContent = "Updated at " + clock + (data.sampled ? " · sampled analytics" : "");
  }

  async function load() {
    const token = ++requestNumber;
    const days = els.range.value === "30" ? 30 : 7;
    els.refresh.disabled = true;
    els.status.textContent = "Loading Cloudflare analytics …";
    try {
      const data = await window.ColoringStats.getTraffic(days);
      if (token === requestNumber) render(data, days);
    } catch (error) {
      if (token === requestNumber) {
        els.unique.textContent = "N/A";
        els.visits.textContent = "–";
        els.crawlers.textContent = "–";
        els.crawlerTable.replaceChildren();
        els.crawlerEmpty.hidden = false;
        els.status.textContent = "Cloudflare traffic analytics unavailable.";
        els.crawlerStatus.textContent = "Data unavailable";
        console.error(error);
      }
    } finally {
      if (token === requestNumber) els.refresh.disabled = false;
    }
  }

  els.range.addEventListener("change", load);
  els.refresh.addEventListener("click", load);
  if (typeof window.ColoringStats?.getTraffic === "function") load();
  else els.status.textContent = "Cloudflare traffic analytics API unavailable.";
})();
