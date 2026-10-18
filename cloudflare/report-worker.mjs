// Minimal source-only Worker for Ausmalwiese error reporting (#264).
// One same-origin POST endpoint, one Cloudflare Email Service binding.
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
const REPORT_FROM = "info@ausmalwiese.de";
const EMAIL_ERROR_CODE = /^E_[A-Z0-9_]{1,62}$/;

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
  return Boolean(env?.EMAIL && typeof env.EMAIL.send === "function");
}

function sanitizedEmailErrorCode(error) {
  if (!error || typeof error !== "object") return "UNKNOWN";
  let code;
  try {
    code = error.code;
  } catch {
    return "UNKNOWN";
  }
  return typeof code === "string" && code.length <= 64 && EMAIL_ERROR_CODE.test(code)
    ? code
    : "UNKNOWN";
}

async function readPayload(request) {
  if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get("content-type") || "")) return null;
  const length = request.headers.get("content-length");
  if (length && (!/^\d+$/.test(length) || Number(length) > 2048)) return null;
  const raw = await request.text();
  if (raw.length > 2048) return null;
  try {
    const value = JSON.parse(raw);
    if (!value || Array.isArray(value) || typeof value !== "object" ||
      Object.keys(value).some((key) => !["id", "page", "reason"].includes(key))) return null;
    return value;
  } catch {
    return null;
  }
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
    !Number.isInteger(payload.page) || payload.page < 1 || payload.page > 12) {
    return json({ ok: false }, 400);
  }

  const link = URL_BASE + "/detail.html?id=" + encodeURIComponent(payload.id) + "&page=" + payload.page;
  const reason = REASONS[payload.reason];
  try {
    await env.EMAIL.send({
      to: undefined,
      from: { email: REPORT_FROM, name: "Ausmalwiese" },
      subject: "[Ausmalwiese] Fehler gemeldet: " + payload.id,
      text: [
        "Neue Fehlermeldung",
        "Grund: " + reason,
        "ID: " + payload.id,
        "Seite: " + payload.page,
        "Link: " + link,
      ].join("\n"),
    });
    return json({ ok: true }, 200);
  } catch (error) {
    console.error({
      event: "report_email_send_failed",
      code: sanitizedEmailErrorCode(error),
    });
    return json({ ok: false }, 503);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!ORIGINS.has(url.origin)) return json({ ok: false }, 404);
    if (url.pathname !== "/api/report") return json({ ok: false }, 404);
    if (request.method !== "POST") return json({ ok: false }, 405);
    return submit(request, env, url);
  },
};
