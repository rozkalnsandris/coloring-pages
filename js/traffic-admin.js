(() => {
  const CATEGORY_LABELS = {
    tiere: "Animals",
    fahrzeuge: "Vehicles",
    alphabet: "Alphabet",
    lernen: "Learning",
    figuren: "Characters & Heroes",
    jahreszeiten: "Seasons & Holidays",
    seasonal: "Seasons & Holidays",
  };

  const els = {
    status: document.querySelector("[data-traffic-page-status]"),
    uniqueVisitors: document.querySelector("[data-stats-unique-visitors]"),
    uniqueVisitorsLabel: document.querySelector("[data-stats-unique-visitors-label]"),
    visits: document.querySelector("[data-stats-visits]"),
    totalViews: document.querySelector("[data-stats-total-views]"),
    recentViews: document.querySelector("[data-stats-recent-views]"),
    crawlerRequests: document.querySelector("[data-stats-crawler-requests]"),
    instagram7: document.querySelector("[data-instagram-7]"),
    instagram30: document.querySelector("[data-instagram-30]"),
    instagramProfile: document.querySelector("[data-instagram-profile]"),
    instagramStory: document.querySelector("[data-instagram-story]"),
    instagramReel: document.querySelector("[data-instagram-reel]"),
    instagramNote: document.querySelector("[data-instagram-note]"),
    trafficStatus: document.querySelector("[data-traffic-status]"),
    visitsNote: document.querySelector("[data-traffic-visits-note]"),
    viewed: document.querySelector("[data-stats-viewed]"),
    viewedEmpty: document.querySelector("[data-stats-viewed-empty]"),
    crawlers: document.querySelector("[data-stats-crawlers]"),
    crawlersEmpty: document.querySelector("[data-stats-crawlers-empty]"),
    table: document.querySelector("[data-traffic-table]"),
    tableEmpty: document.querySelector("[data-traffic-table-empty]"),
    search: document.querySelector("[data-traffic-search]"),
    sort: document.querySelector("[data-traffic-sort]"),
    refresh: document.querySelector("[data-traffic-refresh]"),
    loadMore: document.querySelector("[data-traffic-load-more]"),
  };

  const CATALOG_PAGE_SIZE = 20;
  const numberFormat = new Intl.NumberFormat("en-GB");
  let rows = [];
  let visibleLimit = CATALOG_PAGE_SIZE;

  function number(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function normalize(value) {
    return String(value || "").trim().toLocaleLowerCase("en");
  }

  function formatNumber(value) {
    return numberFormat.format(number(value));
  }

  function categoryLabel(value) {
    return CATEGORY_LABELS[value] || value || "–";
  }

  function instagramCounts(data) {
    if (data?.instagram_attribution_version !== 1 || !Array.isArray(data?.campaigns)) return null;
    const counts = {profile:0, story:0, reel:0};
    for (const item of data.campaigns) {
      const match = /^instagram-(profile|story|reel)$/.exec(String(item.campaign || ""));
      if (match) counts[match[1]] += number(item.landing_count);
    }
    return {counts, total:counts.profile + counts.story + counts.reel};
  }

  function renderInstagram(data7, data30) {
    const week = instagramCounts(data7);
    const month = instagramCounts(data30);
    els.instagram7.textContent = week ? formatNumber(week.total) : "–";
    els.instagram30.textContent = month ? formatNumber(month.total) : "–";
    for (const [key, el] of [["profile",els.instagramProfile],["story",els.instagramStory],["reel",els.instagramReel]]) {
      el.textContent = month ? formatNumber(month.counts[key]) : "–";
    }
    els.instagramNote.textContent = !week || !month
      ? "Instagram attribution unavailable until the matching Stats Worker is activated."
      : "UTM-tagged Instagram landing events, not unique people or verified Instagram referrals. Refreshes and internal navigation are excluded when detectable.";
  }

  function createTopItem(row, index) {
    const item = document.createElement("li");
    item.className = "stats-top-item";

    const rank = document.createElement("span");
    rank.className = "stats-top-rank";
    rank.textContent = String(index + 1);

    const image = document.createElement("img");
    image.className = "stats-top-thumb";
    image.src = row.thumb;
    image.alt = "";
    image.loading = "lazy";

    const copy = document.createElement("div");
    copy.className = "stats-top-copy";
    const link = document.createElement("a");
    link.href = "detail.html?id=" + encodeURIComponent(row.id);
    link.textContent = row.title;
    const meta = document.createElement("span");
    meta.textContent = categoryLabel(row.category);
    copy.append(link, meta);

    const metric = document.createElement("strong");
    metric.className = "stats-top-metric";
    metric.textContent = "👁 " + formatNumber(row.recent_views);
    metric.setAttribute("aria-label", formatNumber(row.recent_views) + " coloring page views in the last 7 days");

    item.append(rank, image, copy, metric);
    return item;
  }

  function renderTopList() {
    const sorted = [...rows]
      .filter((row) => number(row.recent_views) > 0)
      .sort((a, b) =>
        number(b.recent_views) - number(a.recent_views)
        || number(b.view_count) - number(a.view_count)
        || String(a.title).localeCompare(String(b.title), "de")
      )
      .slice(0, 10);

    els.viewed.replaceChildren(...sorted.map(createTopItem));
    els.viewedEmpty.hidden = sorted.length !== 0;
  }

  function renderCrawlers(crawlers) {
    const source = Array.isArray(crawlers) ? crawlers : [];
    const crawlerRows = source.map((crawler) => {
      const tr = document.createElement("tr");
      const name = document.createElement("td");
      name.textContent = crawler.name || "Other crawler";
      const requests = document.createElement("td");
      requests.className = "stats-number";
      requests.textContent = formatNumber(crawler.requests);
      const paths = document.createElement("td");
      paths.textContent = (Array.isArray(crawler.paths) ? crawler.paths : [])
        .map((item) => (item.path || "/") + " (" + formatNumber(item.requests) + ")")
        .join(" · ");
      tr.append(name, requests, paths);
      return tr;
    });
    els.crawlers.replaceChildren(...crawlerRows);
    els.crawlersEmpty.hidden = crawlerRows.length !== 0;
  }

  function tableSort(a, b, mode) {
    if (mode === "title") return String(a.title).localeCompare(String(b.title), "de");
    const key = mode === "views" ? "view_count" : "recent_views";
    return number(b[key]) - number(a[key])
      || number(b.view_count) - number(a.view_count)
      || String(a.title).localeCompare(String(b.title), "de");
  }

  function createTableRow(row) {
    const tr = document.createElement("tr");

    const page = document.createElement("td");
    const wrap = document.createElement("div");
    wrap.className = "stats-page-cell";
    const image = document.createElement("img");
    image.src = row.thumb;
    image.alt = "";
    image.loading = "lazy";
    const link = document.createElement("a");
    link.href = "detail.html?id=" + encodeURIComponent(row.id);
    link.textContent = row.title;
    wrap.append(image, link);
    page.append(wrap);

    const category = document.createElement("td");
    category.textContent = categoryLabel(row.category);

    const views = document.createElement("td");
    views.className = "stats-number";
    views.textContent = formatNumber(row.view_count);

    const recentViews = document.createElement("td");
    recentViews.className = "stats-number";
    recentViews.textContent = formatNumber(row.recent_views);

    tr.append(page, category, views, recentViews);
    return tr;
  }

  function renderTable() {
    const query = normalize(els.search?.value);
    const mode = els.sort?.value || "recentViews";
    const visible = rows
      .filter((row) => {
        if (!query) return true;
        return normalize(row.title).includes(query)
          || normalize(categoryLabel(row.category)).includes(query)
          || normalize(row.id).includes(query);
      })
      .sort((a, b) => tableSort(a, b, mode));

    const visibleRows = visible.slice(0, visibleLimit);
    els.table.replaceChildren(...visibleRows.map(createTableRow));
    els.tableEmpty.hidden = visible.length !== 0;
    els.loadMore.hidden = visibleRows.length >= visible.length;
  }

  function resetTableLimit() {
    visibleLimit = CATALOG_PAGE_SIZE;
    renderTable();
  }

  async function load() {
    els.refresh.disabled = true;
    els.status.textContent = "Loading traffic analytics …";
    try {
      const [catalogResponse, overview, traffic, instagram7, instagram30] = await Promise.all([
        fetch("catalog.json", {cache: "no-store"}),
        window.ColoringStats.getOverview(),
        window.ColoringStats.getTraffic(7),
        window.ColoringStats.getCampaigns ? window.ColoringStats.getCampaigns(7).catch(() => null) : Promise.resolve(null),
        window.ColoringStats.getCampaigns ? window.ColoringStats.getCampaigns(30).catch(() => null) : Promise.resolve(null),
      ]);
      if (!catalogResponse.ok) throw new Error("catalog request failed: " + catalogResponse.status);
      const catalog = await catalogResponse.json();
      if (!Array.isArray(catalog)) throw new Error("catalog response is not an array");

      const statsById = new Map(
        (Array.isArray(overview.pages) ? overview.pages : [])
          .map((item) => [String(item.page_id), item])
      );

      rows = catalog
        .filter((entry) => entry && entry.id && entry.title && entry.thumb)
        .map((entry) => {
          const stats = statsById.get(String(entry.id)) || {};
          return {
            id: String(entry.id),
            title: entry.title,
            category: entry.category,
            thumb: entry.thumb,
            view_count: number(stats.view_count),
            recent_views: number(stats.recent_views),
          };
        });

      // Historical D1/IP-HMAC visits are an approximation, never unique people.
      // The newer privacy Worker retires this metric: absence must not become zero.
      const uniqueVisitorsAvailable = traffic.unique_visitors_status === "available"
        && traffic.unique_visitors_basis === "worker-d1-daily-hmac-ip"
        && Number.isSafeInteger(traffic.unique_visitors)
        && traffic.unique_visitors >= 0
        && /^\d{4}-\d{2}-\d{2}$/.test(traffic.unique_visitors_date || "");
      els.uniqueVisitors.textContent = uniqueVisitorsAvailable
        ? formatNumber(traffic.unique_visitors) : "N/A";
      if (els.uniqueVisitorsLabel) {
        els.uniqueVisitorsLabel.textContent = uniqueVisitorsAvailable
          ? "Approx. daily unique IPs · " + traffic.unique_visitors_date
          : "Daily unique IPs · unavailable";
      }
      els.visits.textContent = formatNumber(traffic.visits);
      els.totalViews.textContent = formatNumber(overview.totals?.view_count);
      els.recentViews.textContent = formatNumber(overview.totals?.recent_views);
      els.crawlerRequests.textContent = formatNumber(traffic.crawler_requests);
      renderInstagram(instagram7, instagram30);
      els.trafficStatus.textContent = traffic.sampled ? "Sampled · User-Agent heuristic" : "User-Agent heuristic";
      if (els.visitsNote) {
        const ipNote = uniqueVisitorsAvailable
          ? "Approx. daily unique IPs is the Stats Worker's historical D1/IP-HMAC estimate, not an exact people count. "
          : "The historical daily unique-IP estimate is unavailable or retired; N/A is not a zero count. ";
        const sampleNote = traffic.sampled ? " (sampled)" : " (may be sampled)";
        els.visitsNote.textContent = ipNote
          + "Website visits is a separate Cloudflare analytics metric" + sampleNote
          + ", not unique people. Crawler requests use User-Agent classification and must not be subtracted from visits.";
      }

      renderTopList();
      renderCrawlers(traffic.crawlers);
      visibleLimit = CATALOG_PAGE_SIZE;
      renderTable();

      const catalogIds = new Set(rows.map((row) => row.id));
      const unknown = (Array.isArray(overview.pages) ? overview.pages : [])
        .filter((item) => !catalogIds.has(String(item.page_id))).length;
      const time = new Intl.DateTimeFormat("en-GB", {hour: "2-digit", minute: "2-digit"}).format(new Date());
      const sampling = traffic.sampled ? " · sampled analytics" : "";
      els.status.textContent = unknown
        ? "Updated at " + time + sampling + " · " + unknown + " stats ID" + (unknown === 1 ? "" : "s") + " not in the current catalog"
        : "Updated at " + time + sampling;
    } catch (error) {
      els.status.textContent = "Could not load traffic analytics.";
      els.trafficStatus.textContent = "Traffic analytics unavailable";
      console.error(error);
    } finally {
      els.refresh.disabled = false;
    }
  }

  els.search?.addEventListener("input", resetTableLimit);
  els.sort?.addEventListener("change", resetTableLimit);
  els.loadMore?.addEventListener("click", () => {
    visibleLimit += CATALOG_PAGE_SIZE;
    renderTable();
  });
  els.refresh?.addEventListener("click", load);

  if (!window.ColoringStats?.getOverview || !window.ColoringStats?.getTraffic) {
    els.status.textContent = "Traffic analytics API is unavailable.";
  } else {
    load();
  }
})();
