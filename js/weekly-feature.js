(() => {
  "use strict";

  // Owner delegated random editorial selection on 2026-10-22 (#205).
  // IDs were drawn from the public https://ausmalwiese.de/catalog.json snapshot.
  // New/unlisted/expired IDs never fall back to other content.
  const CURATED_WEEKS = Object.freeze({
    "2026-W43": "3398005",
    "2026-W44": "0662291",
    "2026-W45": "3589168",
    "2026-W46": "3853527",
    "2026-W47": "9823291",
    "2026-W48": "2468053",
    "2026-W49": "3534071",
    "2026-W50": "5755734",
    "2026-W51": "8367735",
    "2026-W52": "1291018",
    "2026-W53": "2584849",
    "2027-W01": "7547459",
  });

  const section = document.querySelector("[data-weekly-feature]");
  const preview = document.querySelector("[data-weekly-preview]");
  const image = document.querySelector("[data-weekly-image]");
  const title = document.querySelector("[data-weekly-title]");
  const action = document.querySelector("[data-weekly-action]");

  function isoWeekInBerlin(instant = new Date()) {
    if (!(instant instanceof Date) || !Number.isFinite(instant.getTime())) return "";
    const parts = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit",
    }).formatToParts(instant);
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    const year = Number(values.year);
    const month = Number(values.month);
    const day = Number(values.day);
    if (!year || !month || !day) return "";
    const date = new Date(Date.UTC(year, month - 1, day));
    // Thursday determines the ISO week-year, even at New Year.
    date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
    const weekYear = date.getUTCFullYear();
    const first = new Date(Date.UTC(weekYear, 0, 1));
    const week = Math.ceil(((date - first) / 86400000 + 1) / 7);
    return weekYear + "-W" + String(week).padStart(2, "0");
  }

  function approvedEntry(catalog, schedule, week) {
    if (!Array.isArray(catalog) || !schedule
        || !Object.prototype.hasOwnProperty.call(schedule, week)) return null;
    const id = schedule[week];
    if (typeof id !== "string" || !/^[0-9]{7}$/.test(id)) return null;
    return catalog.find((entry) => entry && String(entry.id) === id
      && typeof entry.title === "string" && entry.title.trim()
      && typeof entry.thumb === "string" && entry.thumb.trim()) || null;
  }

  function render(catalog, schedule = CURATED_WEEKS, instant = new Date()) {
    if (!section) return false;
    section.hidden = true;
    if (!preview || !image || !title || !action) return false;
    const selected = approvedEntry(catalog, schedule, isoWeekInBerlin(instant));
    if (!selected) return false;

    const params = new URLSearchParams({id: String(selected.id)});
    // Preserve only the existing allowlisted campaign in normal detail links.
    if (new URLSearchParams(location.search).get("campaign") === "dortmund-01") {
      params.set("campaign", "dortmund-01");
    }
    const href = "detail.html?" + params.toString();
    preview.href = href;
    preview.setAttribute("aria-label", selected.title + " ansehen");
    image.src = selected.thumb;
    image.alt = selected.title;
    title.textContent = selected.title;
    title.href = href;
    action.href = href;
    section.hidden = false;
    return true;
  }

  window.AusmalWeekly = Object.freeze({render, isoWeekInBerlin});
})();
