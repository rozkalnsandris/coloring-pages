import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import worker from "../cloudflare/report-worker.mjs";

const ORIGIN = "https://ausmalwiese.de";
const REASONS = ["print", "image", "craft", "wrong", "other"];
const defaults = { id: "1234567", page: 1, reason: "print" };

function setup({ emailError = null } = {}) {
  const mail = [];
  const env = {
    EMAIL: {
      send: async (message) => {
        if (emailError !== null) throw emailError;
        mail.push(message);
        return { messageId: "accepted-1" };
      },
    },
  };
  return { env, mail };
}

function request(payload = defaults, {
  origin = ORIGIN,
  method = "POST",
  url = ORIGIN + "/api/report",
  headers = {},
} = {}) {
  return new Request(url, {
    method,
    headers: { origin, "content-type": "application/json", ...headers },
    body: method === "POST" ? JSON.stringify(payload) : undefined,
  });
}

async function call(env, payload = defaults, params) {
  const response = await worker.fetch(request(payload, params), env);
  return { status: response.status, body: await response.json() };
}

async function captureErrorLogs(run) {
  const logs = [];
  const original = console.error;
  console.error = (...args) => logs.push(args);
  try {
    return { value: await run(), logs };
  } finally {
    console.error = original;
  }
}

test("all five allowed reasons send one fixed structured email through EMAIL binding", async () => {
  for (const reason of REASONS) {
    const { env, mail } = setup();
    const { status, body } = await call(env, { ...defaults, reason, page: 2 });
    assert.equal(status, 200);
    assert.deepEqual(body, { ok: true });
    assert.equal(mail.length, 1);
    assert.deepEqual(Object.keys(mail[0]), ["to", "from", "subject", "text"]);
    assert.equal(mail[0].to, "info@ausmalwiese.de");
    assert.deepEqual(mail[0].from, {
      email: "info@ausmalwiese.de",
      name: "Ausmalwiese",
    });
    assert.equal(mail[0].subject, "[Ausmalwiese] Fehler gemeldet: 1234567");
    assert.match(mail[0].text, /^Neue Fehlermeldung\n/);
    assert.match(mail[0].text, /\nSeite: 2\n/);
    assert.match(mail[0].text, /https:\/\/ausmalwiese.de\/detail.html\?id=1234567&page=2\n$/);
  }
});

test("invalid id, page, reason, extra data and contact parameters are denied", async () => {
  const { env, mail } = setup();
  const cases = [
    { ...defaults, id: "../admin" },
    { ...defaults, id: "1234567\r\nBcc: attacker@example.test" },
    { ...defaults, page: 0 },
    { ...defaults, page: "1" },
    { ...defaults, reason: "unknown" },
    { ...defaults, email: "attacker@example.test" },
    { ...defaults, to: "evil@example.test" },
    { ...defaults, message: "free text is not accepted" },
  ];
  for (const payload of cases) {
    const response = await call(env, payload);
    assert.equal(response.status, 400);
    assert.deepEqual(response.body, { ok: false });
  }
  assert.equal(mail.length, 0);
});

test("body and content type are bounded", async () => {
  const { env, mail } = setup();
  const wrongType = await worker.fetch(new Request(ORIGIN + "/api/report", {
    method: "POST",
    headers: { origin: ORIGIN, "content-type": "text/plain" },
    body: JSON.stringify(defaults),
  }), env);
  assert.equal(wrongType.status, 400);

  const tooLarge = await worker.fetch(new Request(ORIGIN + "/api/report", {
    method: "POST",
    headers: { origin: ORIGIN, "content-type": "application/json", "content-length": "2049" },
    body: JSON.stringify(defaults),
  }), env);
  assert.equal(tooLarge.status, 400);
  assert.equal(mail.length, 0);
});

test("only same-origin browser POST to the exact report path is accepted", async () => {
  const { env, mail } = setup();
  for (const origin of ["https://wrong.example", "https://www.ausmalwiese.de", ""]) {
    assert.equal((await call(env, defaults, { origin })).status, 403);
  }
  assert.equal((await call(env, defaults, {
    headers: { "sec-fetch-site": "cross-site" },
  })).status, 403);

  const get = await worker.fetch(request(null, { method: "GET" }), env);
  assert.equal(get.status, 405);

  const config = await worker.fetch(request(null, {
    url: ORIGIN + "/api/report/config",
    method: "GET",
  }), env);
  assert.equal(config.status, 404);

  const wrong = await worker.fetch(request(null, {
    url: ORIGIN + "/api/private",
    method: "GET",
  }), env);
  assert.equal(wrong.status, 404);
  assert.equal(mail.length, 0);
});

test("missing binding fails closed without a send attempt", async () => {
  const missing = await call({}, defaults);
  assert.equal(missing.status, 503);
  assert.deepEqual(missing.body, { ok: false });
});

test("email send failure logs only one sanitized provider code", async () => {
  const providerError = new Error("provider detail must stay private");
  providerError.code = "E_SENDER_NOT_VERIFIED";
  const broken = setup({ emailError: providerError });
  const payload = { id: "7654321", page: 7, reason: "craft" };
  const { value: failed, logs } = await captureErrorLogs(
    () => call(broken.env, payload),
  );

  assert.equal(failed.status, 503);
  assert.deepEqual(failed.body, { ok: false });
  assert.equal(broken.mail.length, 0);
  assert.deepEqual(logs, [[{
    event: "report_email_send_failed",
    code: "E_SENDER_NOT_VERIFIED",
  }]]);

  const serialized = JSON.stringify(logs);
  for (const forbidden of [
    "provider detail must stay private",
    "7654321",
    "craft",
    "info@ausmalwiese.de",
    "https://ausmalwiese.de",
  ]) {
    assert.ok(!serialized.includes(forbidden), forbidden);
  }
});

test("malformed email error codes are logged only as UNKNOWN", async () => {
  const invalidCodes = [
    "sender_not_verified",
    "E_BAD-DASH",
    7,
    "E_" + "A".repeat(63),
  ];

  for (const code of invalidCodes) {
    const providerError = new Error("private provider detail");
    providerError.code = code;
    const broken = setup({ emailError: providerError });
    const { value: failed, logs } = await captureErrorLogs(
      () => call(broken.env, defaults),
    );

    assert.equal(failed.status, 503);
    assert.deepEqual(failed.body, { ok: false });
    assert.deepEqual(logs, [[{
      event: "report_email_send_failed",
      code: "UNKNOWN",
    }]]);
    assert.ok(!JSON.stringify(logs).includes("private provider detail"));
  }
});

test("worker has no Brevo, Turnstile, rate-limit, catalog or recipient input path", () => {
  const source = readFileSync(new URL("../cloudflare/report-worker.mjs", import.meta.url), "utf8");
  for (const forbidden of [
    "brevo", "BREVO", "turnstile", "TURNSTILE", "REPORT_RATE", "REPORT_DUP",
    "/api/report/config", "/catalog.json", "cf-connecting-ip", "REPORT_TO",
  ]) {
    assert.ok(!source.includes(forbidden), forbidden);
  }
  assert.match(source, /env\.EMAIL\.send/);
  assert.match(source, /const FIXED_DESTINATION = "info@ausmalwiese\.de"/);
  assert.match(source, /await env\.EMAIL\.send\(buildEmail\(payload, reason, link\)\)/);
  assert.doesNotMatch(source, /EmailMessage|cloudflare:email|to: undefined/);
  assert.doesNotMatch(source, /error\.message|error\.stack/);
});

test("detail UI has five radio choices and no Turnstile dependency", () => {
  const html = readFileSync(new URL("../detail.html", import.meta.url), "utf8");
  const js = readFileSync(new URL("../js/detail.js", import.meta.url), "utf8");
  const client = readFileSync(new URL("../js/report.js", import.meta.url), "utf8");
  const css = readFileSync(new URL("../css/report.css", import.meta.url), "utf8");

  assert.equal((html.match(/type="radio" name="reason"/g) || []).length, 5);
  for (const code of REASONS) assert.ok(html.includes('value="' + code + '"'));
  assert.match(html, /data-report-status role="status" aria-live="polite"/);
  assert.match(html, /data-action-print/);
  assert.match(html, /data-report-close/);
  assert.match(html, /<noscript>/);
  assert.doesNotMatch(html, /data-report-turnstile|turnstile/i);
  assert.doesNotMatch(html, /<input[^>]+type="email"/i);

  assert.match(js, /ausmalwiese:page-change/);
  assert.match(js, /const initialIndex =/);
  assert.match(client, /data-report-submit/);
  assert.match(client, /ausmalwiese:detail-loaded/);
  assert.match(client, /JSON\.stringify\(\{ id: activityId, page, reason \}\)/);
  assert.doesNotMatch(client, /turnstile|\/api\/report\/config|activity_unavailable/i);
  assert.doesNotMatch(css, /turnstile/i);
  assert.match(css, /:focus-visible/);
  assert.match(client, /say\("✓ Danke! Deine Meldung wurde gesendet\.", "success"\)/);
  assert.match(client, /say\("Die Meldung konnte nicht gesendet werden\. Bitte versuche es später erneut\.", "error"\)/);
  assert.match(css, /\.report-status\[data-state="success"\]/);
  assert.match(css, /\.report-status\[data-state="error"\]/);
});

test("all report JavaScript is syntactically valid", () => {
  for (const file of ["js/report.js", "js/detail.js", "cloudflare/report-worker.mjs"]) {
    const result = spawnSync(process.execPath, ["--check", file], { encoding: "utf8" });
    assert.equal(result.status, 0, file + ": " + result.stderr);
  }
});
