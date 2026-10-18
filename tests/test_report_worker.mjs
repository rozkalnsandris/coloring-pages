import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import worker from "../cloudflare/report-worker.mjs";

const ORIGIN = "https://ausmalwiese.de";
const REASONS = ["print", "image", "craft", "wrong", "other"];
const defaults = { id: "1234567", page: 1, reason: "print" };

function setup({ failEmail = false } = {}) {
  const mail = [];
  const env = {
    EMAIL: {
      send: async (message) => {
        if (failEmail) throw new Error("email unavailable");
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

test("all five allowed reasons send one plain-text email through EMAIL binding", async () => {
  for (const reason of REASONS) {
    const { env, mail } = setup();
    const { status, body } = await call(env, { ...defaults, reason, page: 2 });
    assert.equal(status, 200);
    assert.deepEqual(body, { ok: true });
    assert.equal(mail.length, 1);
    assert.equal(mail[0].to, undefined);
    assert.deepEqual(mail[0].from, { email: "info@ausmalwiese.de", name: "Ausmalwiese" });
    assert.equal(mail[0].subject, "[Ausmalwiese] Fehler gemeldet: 1234567");
    assert.match(mail[0].text, /Seite: 2/);
    assert.match(mail[0].text, /https:\/\/ausmalwiese.de\/detail.html\?id=1234567&page=2/);
  }
});

test("invalid id, page, reason, extra data and contact parameters are denied", async () => {
  const { env, mail } = setup();
  const cases = [
    { ...defaults, id: "../admin" },
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

test("missing binding and email send errors fail closed without false success", async () => {
  const missing = await call({}, defaults);
  assert.equal(missing.status, 503);
  assert.deepEqual(missing.body, { ok: false });

  const broken = setup({ failEmail: true });
  const failed = await call(broken.env, defaults);
  assert.equal(failed.status, 503);
  assert.deepEqual(failed.body, { ok: false });
  assert.equal(broken.mail.length, 0);
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
  assert.match(source, /to: undefined/);
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
});

test("all report JavaScript is syntactically valid", () => {
  for (const file of ["js/report.js", "js/detail.js", "cloudflare/report-worker.mjs"]) {
    const result = spawnSync(process.execPath, ["--check", file], { encoding: "utf8" });
    assert.equal(result.status, 0, file + ": " + result.stderr);
  }
});
