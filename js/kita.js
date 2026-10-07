(() => {
  // Editorial references only. Titles, images and badges stay in catalog.json.
  // Use only visually reviewed generic artwork; never fill gaps by category.
  const EXAMPLE_IDS = ["3147286", "7078476", "cp-000008", "7884237", "2612596", "0821068"];
  const target = document.querySelector("[data-kita-examples]");
  const status = document.querySelector("[data-kita-status]");
  if (!target) return;

  // One shared pilot label, never a recipient ID. No cookies or storage added.
  const campaign = new URLSearchParams(location.search).get("campaign");
  function preserveCampaign(root) {
    if (campaign !== "dortmund-01") return;
    root.querySelectorAll("a[href]").forEach((link) => {
      const url = new URL(link.href, location.href);
      if (url.origin !== location.origin || !["/index.html", "/detail.html"].includes(url.pathname)) return;
      url.searchParams.set("campaign", campaign);
      link.href = url.href;
    });
  }
  preserveCampaign(document);
  // Reuse the existing visit metric and label only the shared pilot landing stage.
  window.ColoringStats?.trackVisit?.("landing");

  async function loadExamples() {
    try {
      const response = await fetch("catalog.json", {cache: "no-store"});
      if (!response.ok) throw new Error("catalog unavailable");
      const entries = await response.json();
      if (!Array.isArray(entries)) throw new Error("invalid catalog");
      const byId = new Map(entries.filter((entry) => entry && entry.id && entry.title && entry.thumb)
        .map((entry) => [String(entry.id), entry]));
      const cards = EXAMPLE_IDS.filter((id) => byId.has(id))
        .map((id) => createCatalogCard(byId.get(id)));
      target.replaceChildren(...cards);
      preserveCampaign(target);
      if (cards.length) {
        status.hidden = true;
        return;
      }
    } catch {
      // Keep the static catalogue CTA usable when examples cannot load.
    }
    status.textContent = "Die Beispiele sind gerade nicht verfügbar. Über „Alle Vorlagen ansehen“ kommst du zum Katalog.";
  }
  loadExamples();
})();
