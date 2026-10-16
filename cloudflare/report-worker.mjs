// Source-only Worker for Ausmalwiese error reporting (#240).
// Route the exact same-origin /api/report* paths separately from /api/stats/*.
// Never accept email addresses or URLs from visitors.
const ORIGINS = new Set(["https://ausmalwiese.de", "https://www.ausmalwiese.de"]);
const REASONS = Object.freeze({
  print: "Drucken funktioniert nicht",
  image: "Bild ist abgeschnitten oder fehlerhaft",
  craft: "Ausschneiden/Kleben passt nicht",
  wrong: "Falsche oder unpassende Vorlage",
  other: "Anderer Fehler",
});
const PAGE_ID = /^[a-z0-9][a-z0-9_-]{0,79}$/i;
const URL_BASE = "https://ausmalwiese.de";

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
    },
  });
}
function configured(env) {
  return Boolean(env?.TURNSTILE_SITE_KEY && env?.TURNSTILE_SECRET &&
    env?.REPORT_FROM && env?.REPORT_TO && env?.NOTIFY_OPS?.send &&
    env?.REPORT_RATE?.limit && env?.REPORT_DUP?.limit);
}
function sanitizedTitle(title) {
  if (typeof title !== "string") return "";
  return title.replace(/[\x00-\x1f\x7f]/g, " ").trim().slice(0, 120);
}
async function digest(value) {
  const result = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(result), (part) => part.toString(16).padStart(2, "0")).join("");
}
async function readPayload(request) {
  if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get("content-type") || "")) return null;
  const length = request.headers.get("content-length");
  if (length && (!/^\d+$/.test(length) || Number(length) > 4096)) return null;
  const raw = await request.text();
  if (raw.length > 4096) return null;
  try {
    const value = JSON.parse(raw);
    if (!value || Array.isArray(value) || typeof value !== "object" ||
      Object.keys(value).some((key) => !["id", "page", "reason", "turnstile"].includes(key))) return null;
    return value;
  } catch {
    return null;
  }
}
async function verifyChallenge(env, token, hostname) {
  const form = new FormData();
  form.set("secret", env.TURNSTILE_SECRET);
  form.set("response", token);
  const response = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST", body: form, redirect: "error",
  });
  if (!response.ok) return false;
  const result = await response.json();
  return result?.success === true && result.hostname === hostname && result.action === "report";
}
async function catalogEntry(id) {
  const response = await fetch(URL_BASE + "/catalog.json", {
    method: "GET", headers: { accept: "application/json" },
    cache: "no-store", redirect: "error",
  });
  if (!response.ok) return null;
  const catalog = await response.json();
  if (!Array.isArray(catalog)) return null;
  const match = catalog.find((item) => item && item.id === id);
  if (!match || !sanitizedTitle(match.title)) return null;
  const pages = Array.isArray(match.pages) && match.pages.length > 0
    ? match.pages.length
    : (match.print || match.preview ? 1 : 0);
  return pages > 0 && pages <= 12 ? { title: sanitizedTitle(match.title), pages } : null;
}
async function submit(request, env, url) {
  const origin = request.headers.get("origin");
  if (origin !== url.origin || request.headers.get("sec-fetch-site") === "cross-site") {
    return json({ ok: false }, 403);
  }
  if (!configured(env)) return json({ ok: false }, 503);
  const payload = await readPayload(request);
  if (!payload || typeof payload.id !== "string" || !PAGE_ID.test(payload.id) ||
    typeof payload.reason !== "string" || !Object.hasOwn(REASONS, payload.reason) ||
    !Number.isInteger(payload.page) || payload.page < 1 || payload.page > 12 ||
    typeof payload.turnstile !== "string" || payload.turnstile.length < 1 || payload.turnstile.length > 2048) {
    return json({ ok: false }, 400);
  }
  const clientIp = request.headers.get("cf-connecting-ip");
  if (!clientIp || clientIp.length > 64) return json({ ok: false }, 403);
  try {
    const key = await digest(clientIp);
    const allowance = await env.REPORT_RATE.limit({ key });
    if (allowance?.success !== true) return json({ ok: false }, 429);
    if (!await verifyChallenge(env, payload.turnstile, url.hostname)) return json({ ok: false }, 403);
    const entry = await catalogEntry(payload.id);
    if (!entry || payload.page > entry.pages) return json({ ok: false }, 400);
    const duplicateKey = await digest(key + ":" + payload.id + ":" + payload.page + ":" + payload.reason);
    const duplicate = await env.REPORT_DUP.limit({ key: duplicateKey });
    if (duplicate?.success !== true) return json({ ok: false }, 429);
    const link = URL_BASE + "/detail.html?id=" + encodeURIComponent(payload.id) + "&page=" + payload.page;
    const reason = REASONS[payload.reason];
    const result = await env.NOTIFY_OPS.send({
      from: env.REPORT_FROM,
      to: env.REPORT_TO,
      subject: "[Ausmalwiese] Fehler gemeldet: " + payload.id,
      text: [
        "Neue Fehlermeldung", "Grund: " + reason,
        "Vorlage: " + entry.title, "ID: " + payload.id,
        "Seite: " + payload.page + " von " + entry.pages,
        "Link: " + link,
      ].join("\n"),
    });
    if (!result || typeof result.messageId !== "string" || !result.messageId) {
      return json({ ok: false }, 503);
    }
    return json({ ok: true }, 200);
  } catch {
    // Do not leak addresses, challenge secrets or upstream error data to the caller.
    return json({ ok: false }, 503);
  }
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!ORIGINS.has(url.origin)) return json({ ok: false }, 404);
    if (url.pathname === "/api/report/config" && request.method === "GET") {
      if (!configured(env)) return json({ ok: false }, 503);
      return json({ siteKey: env.TURNSTILE_SITE_KEY });
    }
    if (url.pathname !== "/api/report") return json({ ok: false }, 404);
    if (request.method !== "POST") return json({ ok: false }, 405);
    return submit(request, env, url);
  },
};
