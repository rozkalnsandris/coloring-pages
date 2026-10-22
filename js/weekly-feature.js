(() => {
  "use strict";

  // Source-only, no scheduler, storage, extra HTTP call or hard-coded weekly IDs.
  // Imported UTC published_at is essential; unknown historical dates are NOT guessed.
  const DAY_MS = 86400000;
  const MINUTE_MS = 60000;
  const formatBerlin = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Berlin",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  });
  const section = document.querySelector("[data-weekly-feature]");
  const preview = document.querySelector("[data-weekly-preview]");
  const image = document.querySelector("[data-weekly-image]");
  const title = document.querySelector("[data-weekly-title]");
  const action = document.querySelector("[data-weekly-action]");

  function berlinParts(instant) {
    const values = Object.fromEntries(
      formatBerlin.formatToParts(instant).map((part) => [part.type, Number(part.value)])
    );
    return values;
  }

  function isoWeekFromMonday(monday) {
    const thursday = new Date(monday + 3 * DAY_MS);
    const year = thursday.getUTCFullYear();
    const januaryFourth = Date.UTC(year, 0, 4);
    const firstDay = new Date(januaryFourth).getUTCDay() || 7;
    const firstMonday = januaryFourth - (firstDay - 1) * DAY_MS;
    const week = 1 + Math.round((monday - firstMonday) / (7 * DAY_MS));
    return year + "-W" + String(week).padStart(2, "0");
  }

  function weekContext(instant = new Date()) {
    if (!(instant instanceof Date) || !Number.isFinite(instant.getTime())) return null;
    const p = berlinParts(instant);
    const date = Date.UTC(p.year, p.month - 1, p.day);
    const weekday = new Date(date).getUTCDay() || 7;
    let monday = date - (weekday - 1) * DAY_MS;
    // The previous ISO week remains active until Monday 00:10 Berlin time.
    if (weekday === 1 && p.hour * 60 + p.minute < 10) monday -= 7 * DAY_MS;
    return {monday, key: isoWeekFromMonday(monday), cutoff: monday + 10 * MINUTE_MS};
  }

  function isoWeekInBerlin(instant = new Date()) {
    return weekContext(instant)?.key || "";
  }

  function publicationCivilMillis(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value)) return null;
    const parsed = new Date(value);
    if (!Number.isFinite(parsed.getTime()) || parsed.toISOString().replace(".000Z", "Z") !== value) return null;
    const p = berlinParts(parsed);
    return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  }

  function weekHash(value) {
    let hash = 2166136261;
    for (let i = 0; i < value.length; i += 1) {
      hash = Math.imul(hash ^ value.charCodeAt(i), 16777619);
    }
    return hash >>> 0;
  }

  function deterministicPick(entries, weekKey) {
    return [...entries].sort((a, b) =>
      weekHash(weekKey + "|" + a.entry.id) - weekHash(weekKey + "|" + b.entry.id)
      || a.entry.id.localeCompare(b.entry.id)
    )[0] || null;
  }

  function choiceForMonday(entries, monday, excludeId = "") {
    const cutoff = monday + 10 * MINUTE_MS;
    const previousCutoff = cutoff - 7 * DAY_MS;
    const beforeCutoff = entries.filter((x) => x.when < cutoff);
    const fresh = beforeCutoff.filter((x) => x.when >= previousCutoff);
    const pool = fresh.length ? fresh : beforeCutoff;
    if (!pool.length) return null;
    // On weeks with no new publications, avoid last week's raw winner if possible.
    const eligible = !fresh.length && pool.length > 1 && excludeId
      ? pool.filter((x) => x.entry.id !== excludeId) : pool;
    return deterministicPick(eligible.length ? eligible : pool, isoWeekFromMonday(monday));
  }

  function chooseEntry(catalog, instant = new Date()) {
    const week = weekContext(instant);
    if (!week || !Array.isArray(catalog)) return null;
    const seen = new Set();
    const entries = [];
    for (const entry of catalog) {
      const id = entry?.id;
      if (typeof id !== "string" || !/^\d{7}$/.test(id) || seen.has(id)) continue;
      seen.add(id);
      if (typeof entry.title !== "string" || !entry.title.trim()
          || entry.thumb !== "/media/" + id + "/thumb.webp") continue;
      const when = publicationCivilMillis(entry.published_at);
      if (when === null) continue;
      entries.push({entry, when});
    }
    const lastWeek = choiceForMonday(entries, week.monday - 7 * DAY_MS);
    return choiceForMonday(entries, week.monday, lastWeek?.entry.id)?.entry || null;
  }

  function render(catalog, instant = new Date()) {
    if (!section) return false;
    section.hidden = true;
    if (!preview || !image || !title || !action) return false;
    const selected = chooseEntry(catalog, instant);
    if (!selected) return false;
    const params = new URLSearchParams({id: String(selected.id)});
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

  window.AusmalWeekly = Object.freeze({render, chooseEntry, isoWeekInBerlin});
})();
