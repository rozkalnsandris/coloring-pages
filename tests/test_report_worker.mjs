import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { webcrypto } from "node:crypto";
import { spawnSync } from "node:child_process";
import worker from "../cloudflare/report-worker.mjs";

globalThis.crypto ||= webcrypto;
const ORIGIN = "https://ausmalwiese.de";
const REASONS = ["print", "image", "craft", "wrong", "other"];
const defaults = { id: "1234567", page: 1, reason: "print", turnstile: "a-token" };
function setup({ pages = 2, title = "Basteln", failEmail = false, emailStatus = 201, messageId = "accepted-1", challenge = true, rate = true, duplicate = true } = {}) {
  const mail = [];
  const siteverifyTokens = new Set();
  const duplicateKeys = new Set();
  const upstream = [];
  let rateCalls = 0;
  globalThis.fetch = async (url, options) => {
    upstream.push(String(url));
    if (String(url).endsWith("/siteverify")) {
      const token = options.body.get("response");
      const valid = challenge && !siteverifyTokens.has(token);
      siteverifyTokens.add(token);
      return Response.json({ success: valid, hostname: "ausmalwiese.de", action: "report" });
    }
    if (String(url) === ORIGIN + "/catalog.json") {
      return Response.json([{ id: "1234567", title, pages: Array.from({ length: pages }, () => ({ print: "/media/example.png" })) }]);
    }
    if (String(url) === "https://api.brevo.com/v3/smtp/email") {
      if (failEmail) throw new Error("email unavailable");
      if (emailStatus !== 201) return Response.json({ code: "provider-error" }, { status: emailStatus });
      const body = JSON.parse(options.body);
      mail.push({
        from: body.sender.email, to: body.to[0].email,
        text: body.textContent, subject: body.subject,
        raw: body, headers: options.headers,
      });
      return Response.json({ messageId }, { status: 201 });
    }
    throw new Error("Unexpected fetch");
  };
  const env = {
    TURNSTILE_SITE_KEY: "site-key", TURNSTILE_SECRET: "server-secret",
    BREVO_API_KEY: "mock-secret-key", REPORT_TO: "operator@example.test",
    REPORT_RATE: { limit: async () => ({ success: rate && ++rateCalls <= 20 }) },
    REPORT_DUP: { limit: async ({ key }) => {
      if (!duplicate || duplicateKeys.has(key)) return { success: false };
      duplicateKeys.add(key); return { success: true };
    } },
  };
  return { env, mail, upstream, siteverifyTokens };
}
function request(payload = defaults, { origin = ORIGIN, method = "POST", ip = "192.0.2.42", url = ORIGIN + "/api/report", headers = {} } = {}) {
  return new Request(url, {
    method,
    headers: { origin, "content-type": "application/json", "cf-connecting-ip": ip, ...headers },
    body: method === "POST" ? JSON.stringify(payload) : undefined,
  });
}
async function call(env, payload = defaults, params) {
  const response = await worker.fetch(request(payload, params), env);
  return { status: response.status, body: await response.json() };
}
test("all five allowed reasons send exactly one verified notification with canonical page link", async () => {
  for (const reason of REASONS) {
    const { env, mail } = setup();
    const { status, body } = await call(env, { ...defaults, reason, page: 2 });
    assert.equal(status, 200); assert.equal(body.ok, true);
    assert.equal(mail.length, 1);
    assert.equal(mail[0].from, "info@ausmalwiese.de");
    assert.equal(mail[0].to, "operator@example.test");
    assert.match(mail[0].text, /Seite: 2 von 2/);
    assert.match(mail[0].text, /https:\/\/ausmalwiese.de\/detail.html\?id=1234567&page=2/);
    assert.match(mail[0].text, /Vorlage: Basteln/);
  }
});
test("invalid id, page number, reason, extra data and untrusted contact parameters are denied", async () => {
  const { env, mail, upstream } = setup();
  const cases = [
    { ...defaults, id: "../admin" }, { ...defaults, id: "not-found" },
    { ...defaults, page: 0 }, { ...defaults, page: 3 },
    { ...defaults, page: "1" }, { ...defaults, reason: "unknown" },
    { ...defaults, email: "attacker@example.test" }, { ...defaults, to: "evil@example.test" },
  ];
  for (const [index, payload] of cases.entries()) {
    const response = await call(env, { ...payload, turnstile: "unique-invalid-" + index });
    assert.equal(response.status, 400);
    assert.equal(response.body.ok, false);
  }
  assert.equal(mail.length, 0);
  assert.ok(upstream.every((value) => value.includes("/siteverify") || value === ORIGIN + "/catalog.json"));
});
test("only same-origin browser POST is accepted", async () => {
  const { env, mail } = setup();
  for (const origin of ["https://wrong.example", "https://www.ausmalwiese.de", ""]) {
    assert.equal((await call(env, defaults, { origin })).status, 403);
  }
  const badSite = await call(env, defaults, { headers: { "sec-fetch-site": "cross-site" } });
  assert.equal(badSite.status, 403);
  const get = await worker.fetch(request(null, { method: "GET" }), env);
  assert.equal(get.status, 405);
  assert.equal(mail.length, 0);
});
test("bad or replayed Turnstile tokens fail closed", async () => {
  const { env, mail } = setup();
  assert.equal((await call(env, { ...defaults, turnstile: "token-a" })).status, 200);
  assert.equal((await call(env, { ...defaults, turnstile: "token-a" })).status, 403);
  assert.equal(mail.length, 1);
  const broken = setup({ challenge: false });
  assert.equal((await call(broken.env)).status, 403);
  assert.equal(broken.mail.length, 0);
});
test("duplicate and rate protections refuse further messages", async () => {
  const { env, mail } = setup();
  assert.equal((await call(env, { ...defaults, turnstile: "fresh-a" })).status, 200);
  assert.equal((await call(env, { ...defaults, turnstile: "fresh-b" })).status, 429);
  assert.equal(mail.length, 1);
  const rejected = setup({ rate: false });
  assert.equal((await call(rejected.env)).status, 429);
  assert.equal(rejected.mail.length, 0);
});
test("email errors and missing bindings never return a false success", async () => {
  const { env, mail } = setup({ failEmail: true });
  assert.equal((await call(env)).status, 503);
  assert.equal(mail.length, 0);
  delete env.BREVO_API_KEY;
  assert.equal((await call(env)).status, 503);
  env.BREVO_API_KEY = "mock-secret-key";
  delete env.REPORT_TO;
  assert.equal((await call(env)).status, 503);
  env.REPORT_TO = "bad address";
  assert.equal((await call(env)).status, 503);
});
test("Brevo API transport pins recipient, avoids identifiable tracking and never retries", async () => {
  const { env, mail, upstream } = setup();
  assert.equal((await call(env)).status, 200);
  assert.equal(mail.length, 1);
  assert.equal(mail[0].from, "info@ausmalwiese.de");
  assert.equal(mail[0].to, "operator@example.test");
  assert.equal(mail[0].raw.sender.name, "Ausmalwiese");
  assert.deepEqual(mail[0].raw.to, [{
    email: "operator@example.test", contactPixelTrackingConsent: false,
  }]);
  assert.equal(mail[0].headers["api-key"], "mock-secret-key");
  assert.equal(mail[0].headers["content-type"], "application/json");
  assert.equal(upstream.filter((url) => url === "https://api.brevo.com/v3/smtp/email").length, 1);
  const blocked = setup({ emailStatus: 429 });
  assert.equal((await call(blocked.env)).status, 503);
  assert.equal(blocked.mail.length, 0);
  assert.equal(blocked.upstream.filter((url) => url === "https://api.brevo.com/v3/smtp/email").length, 1);
  const missing = setup({ messageId: "" });
  assert.equal((await call(missing.env)).status, 503);
  const notCreated = setup({ emailStatus: 200 });
  assert.equal((await call(notCreated.env)).status, 503);
});
test("sanitizes catalog title and prevents subject/header injection", async () => {
  const { env, mail } = setup({ title: "Basteln\r\nBcc: attacker@example.test" });
  assert.equal((await call(env)).status, 200);
  assert.equal(mail.length, 1);
  assert.ok(!mail[0].text.includes("\r\nBcc:"));
  assert.ok(!mail[0].subject.includes("\n"));
  assert.ok(!mail[0].subject.includes("@"));
});
test("only available, correctly configured endpoints report enabled status", async () => {
  const { env, mail } = setup();
  const good = await worker.fetch(request(null, { url: ORIGIN + "/api/report/config", method: "GET" }), env);
  assert.equal(good.status, 200);
  assert.deepEqual(await good.json(), { siteKey: "site-key" });
  const wrong = await worker.fetch(request(null, { url: ORIGIN + "/api/private", method: "GET" }), env);
  assert.equal(wrong.status, 404);
  delete env.BREVO_API_KEY;
  const disabled = await worker.fetch(request(null, { url: ORIGIN + "/api/report/config", method: "GET" }), env);
  assert.equal(disabled.status, 503);
  assert.equal(mail.length, 0);
});
test("detail UI has five radio choices and works without uploading identity or blocking printing", () => {
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
  assert.doesNotMatch(html, /<input[^>]+type="email"/i);
  assert.match(js, /ausmalwiese:page-change/);
  assert.match(js, /const initialIndex =/);
  assert.match(client, /data-report-submit/);
  assert.match(client, /ausmalwiese:detail-loaded/);
  assert.match(css, /:focus-visible/);
});
test("all report JavaScript is syntactically valid", () => {
  for (const file of ["js/report.js", "js/detail.js", "cloudflare/report-worker.mjs"]) {
    const result = spawnSync(process.execPath, ["--check", file], { encoding: "utf8" });
    assert.equal(result.status, 0, file + ": " + result.stderr);
  }
});
