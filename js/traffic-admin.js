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
    uniqueBrowsers: document.querySelector("[data-stats-unique-browsers]"),
    visits: document.querySelector("[data-stats-visits]"),
    totalViews: document.querySelector("[data-stats-total-views]"),
    recentViews: document.querySelector("[data-stats-recent-views]"),
    crawlerRequests: document.querySelector("[data-stats-crawler-requests]"),
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
      const [catalogResponse, overview, traffic] = await Promise.all([
        fetch("catalog.json", {cache: "no-store"}),
        window.ColoringStats.getOverview(),
        window.ColoringStats.getTraffic(7),
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

      els.uniqueBrowsers.textContent = formatNumber(overview.totals?.unique_browsers_7d);
      els.visits.textContent = formatNumber(traffic.visits);
      els.totalViews.textContent = formatNumber(overview.totals?.view_count);
      els.recentViews.textContent = formatNumber(overview.totals?.recent_views);
      els.crawlerRequests.textContent = formatNumber(traffic.crawler_requests);
      els.trafficStatus.textContent = traffic.sampled ? "Sampled · User-Agent heuristic" : "User-Agent heuristic";
      if (els.visitsNote && traffic.sampled) {
        els.visitsNote.textContent = "“Website visits” is Cloudflare’s sampled visit metric, not a count of unique people. One person can create multiple visits. “Crawler requests” is a separate request count and must not be subtracted from visits.";
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
