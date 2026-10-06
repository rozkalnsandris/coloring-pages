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
    status: document.querySelector("[data-stats-status]"),
    totalPrints: document.querySelector("[data-stats-total-prints]"),
    totalLikes: document.querySelector("[data-stats-total-likes]"),
    recentPrints: document.querySelector("[data-stats-recent-prints]"),
    publishedPages: document.querySelector("[data-stats-published-pages]"),
    popular: document.querySelector("[data-stats-popular]"),
    popularEmpty: document.querySelector("[data-stats-popular-empty]"),
    trending: document.querySelector("[data-stats-trending]"),
    trendingEmpty: document.querySelector("[data-stats-trending-empty]"),
    table: document.querySelector("[data-stats-table]"),
    tableEmpty: document.querySelector("[data-stats-table-empty]"),
    search: document.querySelector("[data-stats-search]"),
    sort: document.querySelector("[data-stats-sort]"),
    refresh: document.querySelector("[data-stats-refresh]"),
    loadMore: document.querySelector("[data-stats-load-more]"),
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

  function createTopItem(row, index, kind) {
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
    metric.textContent = kind === "recent"
      ? "🔥 " + formatNumber(row.recent_prints)
      : "🖨 " + formatNumber(row.print_count);
    metric.setAttribute(
      "aria-label",
      kind === "recent"
        ? formatNumber(row.recent_prints) + " print actions in the last 7 days"
        : formatNumber(row.print_count) + " print actions in total"
    );

    item.append(rank, image, copy, metric);
    return item;
  }

  function renderTopList(target, empty, source, kind) {
    const metricKey = kind === "recent" ? "recent_prints" : "print_count";
    const sorted = [...source]
      .filter((row) => number(row[metricKey]) > 0)
      .sort((a, b) =>
        number(b[metricKey]) - number(a[metricKey])
        || number(b.print_count) - number(a.print_count)
        || number(b.like_count) - number(a.like_count)
        || String(a.title).localeCompare(String(b.title), "de")
      )
      .slice(0, 10);

    target.replaceChildren(...sorted.map((row, index) => createTopItem(row, index, kind)));
    empty.hidden = sorted.length !== 0;
  }

  function tableSort(a, b, mode) {
    if (mode === "title") return String(a.title).localeCompare(String(b.title), "de");
    const key = mode === "recent" ? "recent_prints" : mode === "likes" ? "like_count" : "print_count";
    return number(b[key]) - number(a[key])
      || number(b.print_count) - number(a.print_count)
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

    const prints = document.createElement("td");
    prints.className = "stats-number";
    prints.textContent = formatNumber(row.print_count);

    const recent = document.createElement("td");
    recent.className = "stats-number";
    recent.textContent = formatNumber(row.recent_prints);

    const likes = document.createElement("td");
    likes.className = "stats-number";
    likes.textContent = formatNumber(row.like_count);

    tr.append(page, category, prints, recent, likes);
    return tr;
  }

  function renderTable() {
    const query = normalize(els.search?.value);
    const mode = els.sort?.value || "prints";
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
    if (els.loadMore) {
      els.loadMore.hidden = visibleRows.length >= visible.length;
    }
  }

  function resetTableLimit() {
    visibleLimit = CATALOG_PAGE_SIZE;
    renderTable();
  }

  async function load() {
    els.refresh.disabled = true;
    els.status.textContent = "Loading statistics …";
    try {
      const [catalogResponse, overview] = await Promise.all([
        fetch("catalog.json", {cache: "no-store"}),
        window.ColoringStats.getOverview(),
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
            print_count: number(stats.print_count),
            like_count: number(stats.like_count),
            recent_prints: number(stats.recent_prints),
          };
        });

      els.totalPrints.textContent = formatNumber(overview.totals?.print_count);
      els.totalLikes.textContent = formatNumber(overview.totals?.like_count);
      els.recentPrints.textContent = formatNumber(overview.totals?.recent_prints);
      els.publishedPages.textContent = formatNumber(rows.length);

      renderTopList(els.popular, els.popularEmpty, rows, "prints");
      renderTopList(els.trending, els.trendingEmpty, rows, "recent");
      visibleLimit = CATALOG_PAGE_SIZE;
      renderTable();

      const catalogIds = new Set(rows.map((row) => row.id));
      const unknown = (Array.isArray(overview.pages) ? overview.pages : [])
        .filter((item) => !catalogIds.has(String(item.page_id))).length;
      const time = new Intl.DateTimeFormat("en-GB", {hour: "2-digit", minute: "2-digit"}).format(new Date());
      els.status.textContent = unknown
        ? "Updated at " + time + " · " + unknown + " stats ID" + (unknown === 1 ? "" : "s") + " not in the current catalog"
        : "Updated at " + time;
    } catch (error) {
      els.status.textContent = "Could not load statistics.";
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

  if (!window.ColoringStats?.getOverview) {
    els.status.textContent = "Statistics API is unavailable.";
  } else {
    load();
  }
})();
