const DEFAULT_ORIGIN = "https://coloring.rozkalns.net";
// Fixed public hostnames; do not accept a different hostname merely because
// another allowed site supplied it as its Origin header.
const STATS_WRITE_ORIGINS = new Set([
  DEFAULT_ORIGIN,
  "https://ausmalwiese.de",
  "https://www.ausmalwiese.de",
]);
const PAGE_ID_RE = /^[a-z0-9][a-z0-9_-]{0,79}$/i;
const VISITOR_ID_RE = /^v3-[0-9a-f]{64}$/;
const V2_ERASURE_RE = /^v2-[0-9a-f]{64}$/;
// No legacy credential may write a Like/Print, even when cached JS sends it.
const ANALYTICS_API = "https://api.cloudflare.com/client/v4/graphql";
const ANALYTICS_RANGE_DAYS = new Set([7, 30]);
const CAMPAIGN_IDS = new Set(["dortmund-01"]);
const INSTAGRAM_CAMPAIGN_IDS = new Set(["instagram-profile", "instagram-story", "instagram-reel"]);
const CAMPAIGN_STAGES = new Set(["landing", "catalog"]);
const CAMPAIGN_EVENTS = new Set(["landing", "catalog", "detail", "print"]);
// One shared QR URL for all printed sheets. No page/user identifiers or open redirects.
const PRINT_QR_HOST = "ausmalwiese.de";
const PRINT_QR_DESTINATION = "https://coloring.rozkalns.net/";

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}
function printQrRedirect() {
  return new Response(null, {
    status: 302,
    headers: {
      "location": PRINT_QR_DESTINATION,
      "cache-control": "no-store, max-age=0",
      "referrer-policy": "no-referrer",
      "x-robots-tag": "noindex, nofollow",
      "x-content-type-options": "nosniff",
    },
  });
}

function qrPrefetchOrVerifiedBot(request) {
  const purpose = [request.headers.get("purpose"), request.headers.get("sec-purpose"),
    request.headers.get("x-moz")].filter(Boolean).join(" ");
  return /\bprefetch\b/i.test(purpose) || request.cf?.botManagement?.verifiedBot === true;
}

async function printQrVisit(env, request) {
  // Let a person reach home even if analytics is temporarily unavailable.
  if (!qrPrefetchOrVerifiedBot(request)) {
    try {
      await env.DB.prepare(
        `INSERT INTO daily_print_qr_scans (day, scan_count)
         VALUES (date('now'), 1)
         ON CONFLICT(day) DO UPDATE SET scan_count=scan_count+1`
      ).run();
    } catch {
      // Count unavailable; don't block the QR link or leak database details.
    }
  }
  return printQrRedirect();
}

function validPageId(value) { return typeof value === "string" && PAGE_ID_RE.test(value); }
function validVisitorId(value) { return typeof value === "string" && VISITOR_ID_RE.test(value); }
function validErasureProof(value) { return typeof value === "string" && V2_ERASURE_RE.test(value); }
function validCampaign(value) {
  return typeof value === "string" && (CAMPAIGN_IDS.has(value) || INSTAGRAM_CAMPAIGN_IDS.has(value));
}

async function sha256(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte)=>byte.toString(16).padStart(2,"0")).join("");
}
async function hmacSha256(secret, value) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    {name:"HMAC",hash:"SHA-256"},
    false,
    ["sign"]
  );
  const digest = await crypto.subtle.sign("HMAC",key,encoder.encode(value));
  return [...new Uint8Array(digest)].map((byte)=>byte.toString(16).padStart(2,"0")).join("");
}
async function parseBody(request) {
  const body = await request.json().catch(()=>null);
  if (!body || !validPageId(body.page_id)) return null;
  return body;
}
function allowedWriteOrigin(request, env) {
  // Check the actual request target as well as the browser-supplied Origin:
  // the three public hosts share one Worker but are not same-origin with each other.
  const targetOrigin = new URL(request.url).origin;
  if (!STATS_WRITE_ORIGINS.has(targetOrigin)) return false;
  const origin = request.headers.get("origin");
  const fetchSite = request.headers.get("sec-fetch-site");
  if (origin && origin !== targetOrigin) return false;
  return !fetchSite || fetchSite === "same-origin" || fetchSite === "none";
}
async function rateLimit(env, visitorId, action) {
  if (!env.RATE_LIMITER || !visitorId) return true;
  const {success} = await env.RATE_LIMITER.limit({key:`${action}:${visitorId}`});
  return success;
}
function campaignEventStatement(env, campaign, event, pageId = "") {
  if (!validCampaign(campaign) || !CAMPAIGN_EVENTS.has(event)) return null;
  // Instagram is landing attribution only; it cannot increment details or prints.
  if (INSTAGRAM_CAMPAIGN_IDS.has(campaign) && event !== "landing") return null;
  const pageEvent = event === "detail" || event === "print";
  if (pageEvent ? !validPageId(pageId) : pageId !== "") return null;
  return env.DB.prepare(
    `INSERT INTO daily_campaign_events (campaign, event, page_id, day, event_count)
     VALUES (?, ?, ?, date('now'), 1)
     ON CONFLICT(campaign, event, page_id, day)
     DO UPDATE SET event_count=event_count+1`
  ).bind(campaign,event,pageId);
}
async function rankings(env, request) {
  const url = new URL(request.url);
  const limit = Math.min(20, Math.max(1, Number(url.searchParams.get("limit")) || 6));
  const popular = await env.DB.prepare(
    `SELECT p.page_id,p.print_count,p.like_count+COALESCE(a.like_count,0) AS like_count
     FROM page_stats p
     LEFT JOIN archived_like_totals a ON a.page_id=p.page_id
     WHERE p.print_count>0
     ORDER BY p.print_count DESC,like_count DESC,p.page_id ASC
     LIMIT ?`
  ).bind(limit).all();
  const trending = await env.DB.prepare(
    `SELECT d.page_id,
            SUM(d.print_count) AS recent_prints,
            COALESCE(p.print_count, 0) AS print_count,
            COALESCE(p.like_count,0)+COALESCE(a.like_count,0) AS like_count
     FROM daily_prints d
     LEFT JOIN page_stats p ON p.page_id=d.page_id
     LEFT JOIN archived_like_totals a ON a.page_id=d.page_id
     WHERE d.day >= date('now', '-6 days')
     GROUP BY d.page_id
     HAVING recent_prints > 0
     ORDER BY recent_prints DESC, print_count DESC, d.page_id ASC
     LIMIT ?`
  ).bind(limit).all();
  return json({popular:popular.results||[],trending:trending.results||[],window_days:7});
}
async function overviewStats(env) {
  const totals = await env.DB.prepare(
    `SELECT COALESCE(SUM(p.print_count),0) AS print_count,
            COALESCE(SUM(p.like_count+COALESCE(a.like_count,0)),0) AS like_count,
            COUNT(*) AS tracked_pages
     FROM page_stats p
     LEFT JOIN archived_like_totals a ON a.page_id=p.page_id`
  ).first();
  const engagement = await env.DB.prepare(
    `SELECT p.page_id,
            p.print_count,
            p.like_count+COALESCE(a.like_count,0) AS like_count,
            COALESCE(r.recent_prints, 0) AS recent_prints
     FROM page_stats p
     LEFT JOIN archived_like_totals a ON a.page_id=p.page_id
     LEFT JOIN (
       SELECT page_id, SUM(print_count) AS recent_prints
       FROM daily_prints
       WHERE day >= date('now', '-6 days')
       GROUP BY page_id
     ) r ON r.page_id = p.page_id`
  ).all();
  const views = await env.DB.prepare(
    `SELECT page_id,
            SUM(view_count) AS view_count,
            SUM(CASE WHEN day >= date('now', '-6 days') THEN view_count ELSE 0 END) AS recent_views
     FROM daily_views
     GROUP BY page_id`
  ).all();
  const pageMap = new Map();
  for (const row of engagement.results || []) {
    pageMap.set(String(row.page_id), {
      page_id: String(row.page_id),
      print_count: Number(row.print_count || 0),
      like_count: Number(row.like_count || 0),
      recent_prints: Number(row.recent_prints || 0),
      view_count: 0,
      recent_views: 0,
    });
  }
  for (const row of views.results || []) {
    const pageId = String(row.page_id);
    const current = pageMap.get(pageId) || {
      page_id: pageId,
      print_count: 0,
      like_count: 0,
      recent_prints: 0,
      view_count: 0,
      recent_views: 0,
    };
    current.view_count = Number(row.view_count || 0);
    current.recent_views = Number(row.recent_views || 0);
    pageMap.set(pageId, current);
  }

  const qrTotals = await env.DB.prepare(
    `SELECT COALESCE(SUM(scan_count), 0) AS qr_scan_count,
            COALESCE(SUM(CASE WHEN day >= date('now', '-6 days')
                         THEN scan_count ELSE 0 END), 0) AS recent_qr_scans
     FROM daily_print_qr_scans`
  ).first();
  const pages = [...pageMap.values()].sort((a, b) =>
    b.view_count - a.view_count
    || b.print_count - a.print_count
    || a.page_id.localeCompare(b.page_id)
  );
  return json({
    totals: {
      print_count: Number(totals?.print_count || 0),
      like_count: Number(totals?.like_count || 0),
      tracked_pages: pages.length,
      qr_scan_count: Number(qrTotals?.qr_scan_count || 0),
      recent_qr_scans: Number(qrTotals?.recent_qr_scans || 0),
      recent_prints: pages.reduce((sum, row) => sum + row.recent_prints, 0),
      view_count: pages.reduce((sum, row) => sum + row.view_count, 0),
      recent_views: pages.reduce((sum, row) => sum + row.recent_views, 0),
    },
    pages,
    window_days: 7,
  });
}

async function campaignStats(env, request) {
  const url = new URL(request.url);
  const requestedDays = Number(url.searchParams.get("days")) || 30;
  const days = ANALYTICS_RANGE_DAYS.has(requestedDays) ? requestedDays : 30;
  const modifier = "-" + String(days - 1) + " days";
  const rows = await env.DB.prepare(
    `SELECT campaign,
            SUM(CASE WHEN event = 'landing' THEN event_count ELSE 0 END) AS landing_count,
            SUM(CASE WHEN event = 'catalog' THEN event_count ELSE 0 END) AS catalog_count,
            SUM(CASE WHEN event = 'detail' THEN event_count ELSE 0 END) AS detail_count,
            SUM(CASE WHEN event = 'print' THEN event_count ELSE 0 END) AS print_count
     FROM daily_campaign_events
     WHERE day >= date('now', ?)
     GROUP BY campaign
     ORDER BY campaign ASC`
  ).bind(modifier).all();
  return json({
    range_days:days,
    campaigns:(rows.results || []).map((row)=>({
      campaign:String(row.campaign),
      landing_count:Number(row.landing_count || 0),
      catalog_count:Number(row.catalog_count || 0),
      detail_count:Number(row.detail_count || 0),
      print_count:Number(row.print_count || 0),
    })),
    counting_basis:"aggregate-event-counts-not-unique-kitas",
    instagram_attribution_version:1,
  });
}

function crawlerName(userAgent) {
  const ua = String(userAgent || "").toLowerCase();
  const known = [
    ["googlebot", "Googlebot"],
    ["bingbot", "Bingbot"],
    ["duckduckbot", "DuckDuckBot"],
    ["yandexbot", "YandexBot"],
    ["baiduspider", "Baiduspider"],
    ["applebot", "Applebot"],
    ["oai-searchbot", "OAI-SearchBot"],
    ["gptbot", "GPTBot"],
    ["chatgpt-user", "ChatGPT-User"],
    ["claude-searchbot", "Claude-SearchBot"],
    ["claudebot", "ClaudeBot"],
    ["perplexitybot", "PerplexityBot"],
    ["bytespider", "Bytespider"],
    ["facebookexternalhit", "Facebook crawler"],
  ];
  for (const [needle, label] of known) {
    if (ua.includes(needle)) return label;
  }
  if (ua.includes("crawler")) return "Other crawler";
  if (ua.includes("spider")) return "Other spider";
  if (ua.includes("bot")) return "Other bot";
  return "Other automated client";
}

async function queryCloudflareAnalytics(env, query, variables) {
  if (!env.CF_ANALYTICS_API_TOKEN || !env.CF_ZONE_TAG) {
    return {error:"analytics_not_configured",status:503};
  }
  const response = await fetch(ANALYTICS_API, {
    method: "POST",
    headers: {
      authorization: "Bearer " + env.CF_ANALYTICS_API_TOKEN,
      "content-type": "application/json",
    },
    body: JSON.stringify({query, variables}),
  });
  if (!response.ok) return {error:"analytics_upstream_failed",status:502};
  const body = await response.json().catch(()=>null);
  if (!body || (Array.isArray(body.errors) && body.errors.length)) {
    return {error:"analytics_query_failed",status:502};
  }
  return {data:body.data,status:200};
}

async function recordVisitor(env, request) {
  if (!allowedWriteOrigin(request,env)) return json({error:"forbidden"},403);
  const secret = String(env.VISITOR_HMAC_KEY || "");
  const ip = request.headers.get("CF-Connecting-IP") || "";
  if (secret.length < 32 || !ip) return json({error:"visitor_tracking_unavailable"},503);
  const body = await request.json().catch(()=>({}));
  const day = new Date().toISOString().slice(0,10);
  const host = new URL(env.PUBLIC_ORIGIN || DEFAULT_ORIGIN).hostname;
  const visitorHash = await hmacSha256(secret,`${day}\n${host}\n${ip}`);
  const statements = [
    env.DB.prepare(
      `INSERT OR IGNORE INTO daily_visitors (day, visitor_hash)
       VALUES (?, ?)`
    ).bind(day,visitorHash),
    env.DB.prepare("DELETE FROM daily_visitors WHERE day < date('now', '-1 day')"),
  ];
  const purpose = [request.headers.get("purpose"), request.headers.get("sec-purpose"),
    request.headers.get("x-moz")].filter(Boolean).join(" ");
  const instagramEligible = !INSTAGRAM_CAMPAIGN_IDS.has(body.campaign)
    || (!/\b(prefetch|prerender)\b/i.test(purpose)
      && request.cf?.botManagement?.verifiedBot !== true);
  if (instagramEligible && validCampaign(body.campaign) && CAMPAIGN_STAGES.has(body.stage)) {
    const campaign = campaignEventStatement(env,body.campaign,body.stage);
    if (campaign) statements.push(campaign);
  }
  await env.DB.batch(statements);
  return json({ok:true},201);
}

async function trafficStats(env, request) {
  const url = new URL(request.url);
  const requestedDays = Number(url.searchParams.get("days")) || 7;
  const days = ANALYTICS_RANGE_DAYS.has(requestedDays) ? requestedDays : 7;
  const host = env.CF_ANALYTICS_HOST || new URL(env.PUBLIC_ORIGIN || DEFAULT_ORIGIN).hostname;
  const end = new Date();
  const start = new Date(end.getTime() - days * 86400000);
  const commonFilter = {
    datetime_geq: start.toISOString(),
    datetime_lt: end.toISOString(),
    requestSource: "eyeball",
    clientRequestHTTPHost: host,
  };

  const visitsQuery = [
    "query AdminVisits($zoneTag: string, $filter: filter) {",
    " viewer { zones(filter: { zoneTag: $zoneTag }) {",
    "  visits: httpRequestsAdaptiveGroups(limit: 1000, orderBy: [datetimeHour_ASC], filter: $filter) {",
    "   sum { visits }",
    "   avg { sampleInterval }",
    "   dimensions { datetimeHour }",
    "  }",
    " } } }",
  ].join("\n");
  const visitsResult = await queryCloudflareAnalytics(env, visitsQuery, {
    zoneTag: env.CF_ZONE_TAG,
    filter: commonFilter,
  });
  if (visitsResult.error) return json({error:visitsResult.error},visitsResult.status);

  let uniqueVisitors = null;
  let uniqueVisitorsDate = null;
  let uniqueVisitorsStatus = "unavailable";
  try {
    const latestUniqueVisitorRow = await env.DB.prepare(
      `SELECT day, COUNT(*) AS unique_visitors
       FROM daily_visitors
       WHERE day >= date('now', '-1 day')
       GROUP BY day
       ORDER BY day DESC
       LIMIT 1`
    ).first();
    if (latestUniqueVisitorRow?.day && Number.isFinite(Number(latestUniqueVisitorRow?.unique_visitors))) {
      uniqueVisitors = Number(latestUniqueVisitorRow.unique_visitors);
      uniqueVisitorsDate = String(latestUniqueVisitorRow.day);
      uniqueVisitorsStatus = "available";
    } else {
      uniqueVisitorsStatus = "empty";
    }
  } catch {}

  const crawlerQuery = [
    "query AdminCrawlers($zoneTag: string, $filter: filter) {",
    " viewer { zones(filter: { zoneTag: $zoneTag }) {",
    "  crawlers: httpRequestsAdaptiveGroups(limit: 500, orderBy: [count_DESC], filter: $filter) {",
    "   count",
    "   avg { sampleInterval }",
    "   dimensions { clientRequestPath userAgent }",
    "  }",
    " } } }",
  ].join("\n");
  const crawlerFilter = {
    ...commonFilter,
    edgeResponseStatus_geq: 200,
    edgeResponseStatus_lt: 400,
    OR: [
      {userAgent_like:"%bot%"},
      {userAgent_like:"%crawler%"},
      {userAgent_like:"%spider%"},
      {userAgent_like:"%slurp%"},
      {userAgent_like:"%ChatGPT-User%"},
      {userAgent_like:"%facebookexternalhit%"},
    ],
  };
  const crawlerResult = await queryCloudflareAnalytics(env, crawlerQuery, {
    zoneTag: env.CF_ZONE_TAG,
    filter: crawlerFilter,
  });
  if (crawlerResult.error) return json({error:crawlerResult.error},crawlerResult.status);

  const visitsRows = visitsResult.data?.viewer?.zones?.[0]?.visits || [];
  const crawlerRows = crawlerResult.data?.viewer?.zones?.[0]?.crawlers || [];
  const visits = visitsRows.reduce((sum, row) => sum + Number(row.sum?.visits || 0), 0);
  let sampled = visitsRows.some((row) => Number(row.avg?.sampleInterval || 1) > 1);

  const crawlerMap = new Map();
  for (const row of crawlerRows) {
    sampled ||= Number(row.avg?.sampleInterval || 1) > 1;
    const name = crawlerName(row?.dimensions?.userAgent);
    const path = String(row?.dimensions?.clientRequestPath || "/");
    const count = Number(row?.count || 0);
    if (!crawlerMap.has(name)) crawlerMap.set(name,{name,requests:0,paths:new Map()});
    const crawler = crawlerMap.get(name);
    crawler.requests += count;
    crawler.paths.set(path,(crawler.paths.get(path)||0)+count);
  }
  const crawlers = [...crawlerMap.values()].map((crawler)=>({
    name:crawler.name,
    requests:crawler.requests,
    paths:[...crawler.paths.entries()]
      .map(([path,requests])=>({path,requests}))
      .sort((a,b)=>b.requests-a.requests||a.path.localeCompare(b.path))
      .slice(0,5),
  })).sort((a,b)=>b.requests-a.requests||a.name.localeCompare(b.name));

  return json({
    range_days:days,
    unique_visitors:uniqueVisitors,
    unique_visitors_date:uniqueVisitorsDate,
    unique_visitors_status:uniqueVisitorsStatus,
    unique_visitors_basis:"worker-d1-daily-hmac-ip",
    visits,
    crawler_requests:crawlers.reduce((sum,crawler)=>sum+crawler.requests,0),
    crawlers,
    sampled,
    crawler_classification:"user-agent heuristic",
  });
}

async function recordView(env, request) {
  if (!allowedWriteOrigin(request,env)) return json({error:"forbidden"},403);
  const body = await parseBody(request);
  if (!body) return json({error:"invalid request"},400);
  const statements = [
    env.DB.prepare(
      `INSERT INTO daily_views (page_id, day, view_count)
       VALUES (?, date('now'), 1)
       ON CONFLICT(page_id, day) DO UPDATE SET view_count=view_count+1`
    ).bind(body.page_id),
  ];
  const campaign = campaignEventStatement(env,body.campaign,"detail",body.page_id);
  if (campaign) statements.push(campaign);
  await env.DB.batch(statements);
  return json({ok:true},201);
}


// A browser consent event is a claim, not independently proven parental consent.
// Production must supply a controller-approved TTL; missing config fails closed.
function consentTtl(env) {
  const ttl = Number(env.CONSENT_TTL_SECONDS);
  return Number.isSafeInteger(ttl) && ttl >= 3600 && ttl <= 31536000 ? ttl : 0;
}
function strictWrite(request) {
  const target = new URL(request.url).origin;
  return STATS_WRITE_ORIGINS.has(target)
    && request.headers.get("origin") === target
    && request.headers.get("sec-fetch-site") === "same-origin"
    && request.headers.get("content-type")?.split(";")[0] === "application/json";
}
const credentialActiveSql = "visitor_hash = ? AND expires_at > unixepoch()";
async function credential(env, request) {
  if (!strictWrite(request)) return json({error:"forbidden"},403);
  const length = Number(request.headers.get("content-length") || "0");
  if (!Number.isFinite(length) || length > 512) return json({error:"too_large"},413);
  const raw = await request.text();
  if (raw.length > 512) return json({error:"too_large"},413);
  let body;
  try { body = JSON.parse(raw); } catch { return json({error:"invalid_request"},400); }
  if (!body || typeof body !== "object" || Array.isArray(body)
    || typeof body.like !== "boolean" || typeof body.print !== "boolean"
    || body.version !== 1 || (body.prior_id !== undefined && !validVisitorId(body.prior_id))
    || Object.keys(body).some(k=>!["like","print","version","prior_id"].includes(k))) {
    return json({error:"invalid_request"},400);
  }
  const oldId = body.prior_id || "";
  if (!oldId && !body.like && !body.print) return json({error:"invalid_request"},400);
  if (!env.RATE_LIMITER) return json({error:"credential_unavailable"},503);
  const ip = request.headers.get("CF-Connecting-IP");
  if (!ip) return json({error:"credential_unavailable"},503);
  if (!(await rateLimit(env,ip,"credential"))) return json({error:"rate_limited"},429);
  const oldHash = oldId ? await sha256(oldId) : "";
  if (!body.like && !body.print) {
    const results = await env.DB.batch([
      env.DB.prepare("DELETE FROM likes WHERE visitor_hash = ?").bind(oldHash),
      env.DB.prepare("DELETE FROM visitor_credentials WHERE visitor_hash = ?").bind(oldHash),
    ]);
    if (results.some(r=>r?.success !== true)) return json({error:"revocation_unconfirmed"},503);
    return json({ok:true,revoked:true});
  }
  const ttl = consentTtl(env);
  if (!ttl) return json({error:"credential_config_unavailable"},503);
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  const id = "v3-" + [...bytes].map(b=>b.toString(16).padStart(2,"0")).join("");
  const newHash = await sha256(id);
  const flags = [Number(body.like),Number(body.print),body.version];
  if (!oldId) {
    const result = await env.DB.prepare(
      `INSERT INTO visitor_credentials
         (visitor_hash,like_allowed,print_allowed,notice_version,expires_at)
         VALUES (?,?,?,?,unixepoch()+?)`
    ).bind(newHash,...flags,ttl).run();
    if (result?.success !== true || result?.meta?.changes !== 1)
      return json({error:"issuance_unconfirmed"},503);
  } else {
    // Single D1 transaction: mint new scope, carry retained Likes, remove revoked
    // Likes and the old credential. A missing/expired old token cannot mint.
    const batch = await env.DB.batch([
      env.DB.prepare(
        `INSERT INTO visitor_credentials
         (visitor_hash,like_allowed,print_allowed,notice_version,expires_at)
         SELECT ?,?,?,?,unixepoch()+? FROM visitor_credentials
         WHERE visitor_hash=? AND expires_at>unixepoch()`
      ).bind(newHash,...flags,ttl,oldHash),
      env.DB.prepare(
        `UPDATE likes SET visitor_hash=?
         WHERE visitor_hash=? AND ?=1
         AND EXISTS (SELECT 1 FROM visitor_credentials WHERE visitor_hash=?)`
      ).bind(newHash,oldHash,Number(body.like),newHash),
      env.DB.prepare(
        `DELETE FROM likes WHERE visitor_hash=? AND ?=0
         AND EXISTS (SELECT 1 FROM visitor_credentials WHERE visitor_hash=?)`
      ).bind(oldHash,Number(body.like),newHash),
      env.DB.prepare(
        `DELETE FROM visitor_credentials WHERE visitor_hash=?
         AND EXISTS (SELECT 1 FROM visitor_credentials WHERE visitor_hash=?)`
      ).bind(oldHash,newHash),
    ]);
    if (batch.some(r=>r?.success!==true)) return json({error:"rotation_unconfirmed"},503);
    if (batch[0]?.meta?.changes !== 1) return json({error:"expired_or_unknown_credential"},409);
  }
  return json({ok:true,visitor_id:id,version:3});
}

async function pageStats(env, request) {
  const url = new URL(request.url);
  const posted = request.method === "POST";
  if (posted && !strictWrite(request)) return json({error:"forbidden"},403);
  // Reject all personalized legacy GET URLs, including cached clients.
  if (!posted && url.searchParams.has("visitor_id")) return json({error:"legacy_credential_forbidden"},403);
  const body = posted ? await request.json().catch(()=>null) : null;
  const pageId = posted ? body?.page_id : (url.searchParams.get("page_id") || "");
  if (!validPageId(pageId)) return json({error:"invalid_page_id"},400);
  const id = posted ? body?.visitor_id : "";
  if (posted && !validVisitorId(id)) return json({error:"credential_required"},403);
  let liked = false;
  if (posted) {
    const hash = await sha256(id);
    const row = await env.DB.prepare(
      `SELECT (SELECT 1 FROM visitor_credentials
        WHERE visitor_hash=? AND like_allowed=1 AND expires_at>unixepoch()) AS active,
        (SELECT 1 FROM likes WHERE page_id=? AND visitor_hash=?) AS liked`
    ).bind(hash,pageId,hash).first();
    if (!row?.active) return json({error:"credential_expired"},403);
    liked = Boolean(row.liked);
  }
  const stats = await env.DB.prepare("SELECT p.print_count,p.like_count+COALESCE(a.like_count,0) AS like_count FROM page_stats p LEFT JOIN archived_like_totals a ON a.page_id=p.page_id WHERE p.page_id=?").bind(pageId).first();
  return json({page_id:pageId,print_count:Number(stats?.print_count||0),like_count:Number(stats?.like_count||0),liked});
}
async function recordPrint(env, request) {
  if (!strictWrite(request)) return json({error:"forbidden"},403);
  const body = await parseBody(request);
  if (!body || !validVisitorId(body.visitor_id)) return json({error:"credential_required"},403);
  if (!(await rateLimit(env,body.visitor_id,"print"))) return json({error:"rate_limited"},429);
  const hash = await sha256(body.visitor_id);
  // Each counter write checks active Print consent inside the SQL write.
  // A prior JavaScript check would race with credential revocation.
  const statements = [
    env.DB.prepare(
      `INSERT INTO page_stats(page_id,print_count,updated_at)
       SELECT ?,1,datetime('now') FROM visitor_credentials
       WHERE visitor_hash=? AND print_allowed=1 AND expires_at>unixepoch()
       ON CONFLICT(page_id) DO UPDATE
       SET print_count=print_count+1,updated_at=datetime('now')`
    ).bind(body.page_id,hash),
    env.DB.prepare(
      `INSERT INTO daily_prints(page_id,day,print_count)
       SELECT ?,date('now'),1 FROM visitor_credentials
       WHERE visitor_hash=? AND print_allowed=1 AND expires_at>unixepoch()
       ON CONFLICT(page_id,day) DO UPDATE SET print_count=print_count+1`
    ).bind(body.page_id,hash),
  ];
  if (validCampaign(body.campaign)) statements.push(env.DB.prepare(
    `INSERT INTO daily_campaign_events(campaign,event,page_id,day,event_count)
     SELECT ?,'print',?,date('now'),1 FROM visitor_credentials
     WHERE visitor_hash=? AND print_allowed=1 AND expires_at>unixepoch()
     ON CONFLICT(campaign,event,page_id,day) DO UPDATE SET event_count=event_count+1`
  ).bind(body.campaign,body.page_id,hash));
  const result = await env.DB.batch(statements);
  if (result.some(r=>r?.success!==true)) return json({error:"print_unconfirmed"},503);
  if (result[0]?.meta?.changes !== 1) return json({error:"credential_expired"},403);
  return json({ok:true},201);
}
async function eraseLikes(env, request) {
  // Only a separately confirmed, user-invoked deletion request may carry a
  // high-entropy v2 browser credential. Never accept a leaked/weak legacy ID.
  if (!allowedWriteOrigin(request, env)
      || request.headers.get("origin") !== new URL(request.url).origin
      || request.headers.get("sec-fetch-site") !== "same-origin") {
    return json({error:"forbidden"},403);
  }
  if (request.headers.get("content-type")?.split(";")[0] !== "application/json")
    return json({error:"unsupported_media_type"},415);
  const length = Number(request.headers.get("content-length") || "0");
  if (!Number.isFinite(length) || length > 256) return json({error:"too_large"},413);
  const raw = await request.text();
  if (raw.length > 256) return json({error:"too_large"},413);
  let body;
  try { body = JSON.parse(raw); } catch { return json({error:"invalid_request"},400); }
  if (!body || Array.isArray(body) || typeof body !== "object"
      || Object.keys(body).length !== 1 || !validErasureProof(body.visitor_id)) {
    return json({error:"invalid_request"},400);
  }
  if (!env.RATE_LIMITER) return json({error:"erasure_unavailable"},503);
  if (!(await rateLimit(env,body.visitor_id,"erase"))) return json({error:"rate_limited"},429);

  const hash = await sha256(body.visitor_id);
  // A successful response confirms this deletion against the current D1 table
  // only. An old credential reused by a stale client may create a new Like later.
  const result = await env.DB.prepare("DELETE FROM likes WHERE visitor_hash = ?").bind(hash).run();
  if (result?.success !== true) return json({error:"erasure_unconfirmed"},503);
  if (!result?.meta?.changes) return json({error:"no_matching_active_records"},404);
  return json({ok:true,matched:true});
}

async function toggleLike(env, request) {
  if (!strictWrite(request)) return json({error:"forbidden"},403);
  const body = await parseBody(request);
  if (!body || !validVisitorId(body.visitor_id)) return json({error:"credential_required"},403);
  if (!(await rateLimit(env,body.visitor_id,"like"))) return json({error:"rate_limited"},429);
  const hash = await sha256(body.visitor_id);
  const state = await env.DB.prepare(
    `SELECT (SELECT 1 FROM visitor_credentials
      WHERE visitor_hash=? AND like_allowed=1 AND expires_at>unixepoch()) AS active,
     (SELECT 1 FROM likes WHERE page_id=? AND visitor_hash=?) AS liked`
  ).bind(hash,body.page_id,hash).first();
  if (!state?.active) return json({error:"credential_expired"},403);
  if (state.liked) {
    const removed = await env.DB.prepare("DELETE FROM likes WHERE page_id=? AND visitor_hash=?").bind(body.page_id,hash).run();
    if (removed?.success !== true) return json({error:"like_unconfirmed"},503);
  } else {
    // Critical: authorization and insertion are one SQL statement, not two
    // interleaved requests. A revoked/expired token cannot recreate a Like.
    const inserted = await env.DB.prepare(
      `INSERT INTO likes(page_id,visitor_hash)
       SELECT ?,visitor_hash FROM visitor_credentials
       WHERE visitor_hash=? AND like_allowed=1 AND expires_at>unixepoch()
       ON CONFLICT(page_id,visitor_hash) DO NOTHING`
    ).bind(body.page_id,hash).run();
    if (inserted?.success !== true) return json({error:"like_unconfirmed"},503);
  }
  const stillActive = await env.DB.prepare(
    "SELECT 1 AS active FROM visitor_credentials WHERE visitor_hash=? AND like_allowed=1 AND expires_at>unixepoch()"
  ).bind(hash).first();
  if (!stillActive) return json({error:"credential_expired"},403);
  const stats = await env.DB.prepare("SELECT p.like_count+COALESCE(a.like_count,0) AS like_count,p.print_count FROM page_stats p LEFT JOIN archived_like_totals a ON a.page_id=p.page_id WHERE p.page_id=?").bind(body.page_id).first();
  const persisted = await env.DB.prepare("SELECT 1 AS liked FROM likes WHERE page_id = ? AND visitor_hash = ?").bind(body.page_id,hash).first();
  return json({page_id:body.page_id,liked:Boolean(persisted),like_count:Number(stats?.like_count||0),print_count:Number(stats?.print_count||0)});
}

// Source-only next-generation endpoints; not used by the legacy v3 frontend.
// Do not enable until the D1 additive migration and Like TTL/legal release gates pass.
// The host-only cookie is scoped only to /api/stats/like, never /api/stats/print.
const LIKE_COOKIE_NAME = "__Secure-aw-like-v1";
const LIKE_COOKIE_RE = /^l1-[0-9a-f]{64}$/;
const LIKE_COOKIE_PATH = "/api/stats/like";
const LIKE_COOKIE_TTL_SECONDS = 180 * 24 * 60 * 60;
function likeCookieTtl(_env) {
  // Fixed 180 days from consent. Reads and Like clicks never renew it.
  return LIKE_COOKIE_TTL_SECONDS;
}
function readLikeCookie(request) {
  const matches = (request.headers.get("cookie") || "").split(";")
    .map(value=>value.trim())
    .filter(value=>value.startsWith(LIKE_COOKIE_NAME + "="));
  if (matches.length !== 1) return "";
  const token = matches[0].slice(LIKE_COOKIE_NAME.length + 1);
  return LIKE_COOKIE_RE.test(token) ? token : "";
}
function likeSetCookie(token, ttl = 0) {
  return LIKE_COOKIE_NAME + "=" + token + "; Path=" + LIKE_COOKIE_PATH
    + "; Max-Age=" + ttl + "; Secure; HttpOnly; SameSite=Lax";
}
function cookieJson(data, status = 200, setCookie = "") {
  const response = json(data, status);
  if (setCookie) response.headers.set("set-cookie", setCookie);
  return response;
}
async function cookieLikeSession(env, request) {
  const token = readLikeCookie(request);
  if (!token) return null;
  const hash = await sha256(token);
  const valid = await env.DB.prepare(
    "SELECT 1 AS valid FROM like_cookie_sessions WHERE cookie_hash=? AND expires_at>unixepoch()"
  ).bind(hash).first();
  return valid ? hash : null;
}
async function boundedLikeJson(request, allowedKeys) {
  const length = Number(request.headers.get("content-length") || "0");
  if (!Number.isFinite(length) || length > 256) return null;
  const raw = await request.text();
  if (raw.length > 256) return null;
  let body;
  try { body = JSON.parse(raw); } catch { return null; }
  if (!body || typeof body !== "object" || Array.isArray(body)
      || Object.keys(body).some(key=>!allowedKeys.includes(key))) return null;
  return body;
}
async function likeCookieState(env, pageId, hash) {
  const stats = await env.DB.prepare(
    "SELECT p.print_count,p.like_count+COALESCE(a.like_count,0) AS like_count FROM page_stats p LEFT JOIN archived_like_totals a ON a.page_id=p.page_id WHERE p.page_id=?"
  ).bind(pageId).first();
  const liked = hash ? await env.DB.prepare(
    "SELECT 1 AS liked FROM likes WHERE page_id=? AND visitor_hash=?"
  ).bind(pageId,hash).first() : null;
  return {page_id:pageId,liked:Boolean(liked),
    like_count:Number(stats?.like_count||0),print_count:Number(stats?.print_count||0)};
}
async function cookieLikeRoutes(env, request, path) {
  // Proof of an HttpOnly cookie returned by the browser after issuance.
  if (path === "/api/stats/like/session" && request.method === "GET") {
    return json({consented:Boolean(await cookieLikeSession(env,request))});
  }
  // Read-only aggregate + cookie-scoped state: no creation or renewal on GET.
  if (path === "/api/stats/like/state" && request.method === "GET") {
    const pageId = new URL(request.url).searchParams.get("page_id") || "";
    if (!validPageId(pageId)) return json({error:"invalid_page_id"},400);
    const hash = await cookieLikeSession(env,request);
    return json({...await likeCookieState(env,pageId,hash),consented:Boolean(hash)});
  }
  if (!["/api/stats/like/consent","/api/stats/like/choice",
        "/api/stats/like/forget"].includes(path) || request.method !== "POST")
    return json({error:"not_found"},404);
  if (!strictWrite(request)) return json({error:"forbidden"},403);
  if (path === "/api/stats/like/consent") {
    const body = await boundedLikeJson(request,["accept","version"]);
    if (!body || body.accept !== true || body.version !== 1
        || Object.keys(body).length !== 2) return json({error:"invalid_request"},400);
    const prior = await cookieLikeSession(env,request);
    if (prior) return json({ok:true,already_consented:true});
    const ttl = likeCookieTtl(env);
    const ip = request.headers.get("CF-Connecting-IP");
    if (!ttl || !env.RATE_LIMITER || !ip)
      return json({error:"like_consent_unavailable"},503);
    if (!(await rateLimit(env,ip,"like-consent")))
      return json({error:"rate_limited"},429);
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    const token = "l1-" + [...bytes].map(b=>b.toString(16).padStart(2,"0")).join("");
    const hash = await sha256(token);
    const insert = await env.DB.prepare(
      "INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,1,unixepoch()+?)"
    ).bind(hash,ttl).run();
    if (insert?.success !== true || insert?.meta?.changes !== 1)
      return json({error:"like_consent_unconfirmed"},503);
    return cookieJson({ok:true},201,likeSetCookie(token,ttl));
  }
  const hash = await cookieLikeSession(env,request);
  if (!hash) return json({error:"like_cookie_required"},403);
  if (path === "/api/stats/like/forget") {
    const body = await boundedLikeJson(request,["confirm"]);
    if (!body || body.confirm !== true || Object.keys(body).length !== 1)
      return json({error:"invalid_request"},400);
    const batch = await env.DB.batch([
      env.DB.prepare("DELETE FROM likes WHERE visitor_hash=?").bind(hash),
      env.DB.prepare("DELETE FROM like_cookie_sessions WHERE cookie_hash=?").bind(hash),
    ]);
    if (batch.some(result=>result?.success !== true)
        || batch[1]?.meta?.changes !== 1)
      return json({error:"erasure_unconfirmed"},503);
    return cookieJson({ok:true,revoked:true},200,likeSetCookie("",0));
  }
  const body = await boundedLikeJson(request,["page_id","liked"]);
  if (!body || !validPageId(body.page_id) || typeof body.liked !== "boolean"
      || Object.keys(body).length !== 2)
    return json({error:"invalid_request"},400);
  if (!env.RATE_LIMITER || !(await rateLimit(env,hash,"like-choice")))
    return json({error:"rate_limited_or_unavailable"},429);
  // Desired-state changes are idempotent and checked against a live session
  // inside each SQL mutation: expired/revoked cookies cannot create a Like.
  const result = body.liked ? await env.DB.prepare(
    "INSERT INTO likes(page_id,visitor_hash) SELECT ?,cookie_hash FROM like_cookie_sessions WHERE cookie_hash=? AND expires_at>unixepoch() ON CONFLICT(page_id,visitor_hash) DO NOTHING"
  ).bind(body.page_id,hash).run() : await env.DB.prepare(
    "DELETE FROM likes WHERE page_id=? AND visitor_hash=? AND EXISTS(SELECT 1 FROM like_cookie_sessions WHERE cookie_hash=? AND expires_at>unixepoch())"
  ).bind(body.page_id,hash,hash).run();
  if (result?.success !== true) return json({error:"like_unconfirmed"},503);
  const stillActive = await env.DB.prepare(
    "SELECT 1 AS valid FROM like_cookie_sessions WHERE cookie_hash=? AND expires_at>unixepoch()"
  ).bind(hash).first();
  if (!stillActive) return json({error:"like_cookie_expired"},403);
  return json(await likeCookieState(env,body.page_id,hash));
}
async function eraseLegacyV3(env, request) {
  // Only an explicit user-directed v3 deletion; never permit new v3 writes.
  if (!strictWrite(request)) return json({error:"forbidden"},403);
  const body=await boundedLikeJson(request,["visitor_id"]);
  if (!body || Object.keys(body).length!==1 || !validVisitorId(body.visitor_id))
    return json({error:"invalid_request"},400);
  const hash=await sha256(body.visitor_id);
  if (!env.RATE_LIMITER) return json({error:"erasure_unavailable"},503);
  if (!(await rateLimit(env,hash,"legacy-v3-erasure"))) return json({error:"rate_limited"},429);
  const results=await env.DB.batch([
    env.DB.prepare("DELETE FROM likes WHERE visitor_hash=?").bind(hash),
    env.DB.prepare("DELETE FROM visitor_credentials WHERE visitor_hash=?").bind(hash),
  ]);
  if (results.length!==2 || results.some(x=>x?.success!==true))
    return json({error:"erasure_unconfirmed"},503);
  // A v3 credential can exist without an active Like. Separate those
  // outcomes; do not imply Like erasure when only credential was revoked.
  // D1 mutation counts must be numeric; null or missing is not proof.
  const likesDeleted=results[0]?.meta?.changes;
  const credentialsRevoked=results[1]?.meta?.changes;
  if (!Number.isSafeInteger(likesDeleted) || likesDeleted < 0
      || !Number.isSafeInteger(credentialsRevoked) || credentialsRevoked < 0
      || credentialsRevoked > 1)
    return json({error:"erasure_unconfirmed"},503);
  if (!likesDeleted && !credentialsRevoked)
    return json({error:"no_matching_active_records"},404);
  return json({ok:true,matched:true,likes_deleted:likesDeleted,
    credential_revoked:credentialsRevoked===1});
}

async function recordAggregatePrint(env, request) {
  if (!strictWrite(request)) return json({error:"forbidden"},403);
  const body = await boundedLikeJson(request,["page_id","campaign"]);
  if (!body || !validPageId(body.page_id)
      || (body.campaign !== undefined && !validCampaign(body.campaign)))
    return json({error:"invalid_request"},400);
  const ip = request.headers.get("CF-Connecting-IP");
  // IP is used transiently for abuse-limiting only: no persistent per-print ID.
  if (!ip || !env.RATE_LIMITER) return json({error:"print_unavailable"},503);
  if (!(await rateLimit(env,ip,"aggregate-print")))
    return json({error:"rate_limited"},429);
  const writes = [
    env.DB.prepare("INSERT INTO page_stats(page_id,print_count,updated_at) VALUES (?,1,datetime('now')) ON CONFLICT(page_id) DO UPDATE SET print_count=print_count+1,updated_at=datetime('now')").bind(body.page_id),
    env.DB.prepare("INSERT INTO daily_prints(page_id,day,print_count) VALUES (?,date('now'),1) ON CONFLICT(page_id,day) DO UPDATE SET print_count=print_count+1").bind(body.page_id),
  ];
  const campaign = campaignEventStatement(env,body.campaign,"print",body.page_id);
  if (campaign) writes.push(campaign);
  const result = await env.DB.batch(writes);
  if (result.some(item=>item?.success !== true)) return json({error:"print_unconfirmed"},503);
  return json({ok:true},201);
}


/* Source-only bounded expiry; this PR does NOT configure or activate a Cron.
 * D1.batch is transactional: archive page-level counts once, drop expired
 * per-browser votes (the existing DELETE trigger adjusts active count), then
 * remove expired pseudonymous sessions. Legacy votes have no session row.
 */
const EXPIRED_COOKIE_SELECTOR = "SELECT cookie_hash FROM like_cookie_sessions WHERE expires_at<=?1 ORDER BY expires_at,cookie_hash LIMIT 100";
const ARCHIVE_COOKIE_SQL = `
  INSERT INTO archived_like_totals(page_id,like_count)
  SELECT l.page_id, COUNT(*) FROM likes l
  WHERE l.visitor_hash IN (${EXPIRED_COOKIE_SELECTOR})
  GROUP BY l.page_id
  ON CONFLICT(page_id) DO UPDATE SET like_count=archived_like_totals.like_count+excluded.like_count
`;
const DELETE_EXPIRED_COOKIE_LIKES_SQL = `
  DELETE FROM likes WHERE visitor_hash IN (${EXPIRED_COOKIE_SELECTOR})
`;
const DELETE_EXPIRED_COOKIE_SESSIONS_SQL = `
  DELETE FROM like_cookie_sessions WHERE cookie_hash IN (${EXPIRED_COOKIE_SELECTOR})
`;
async function archiveExpiredCookieLikes(env) {
  // Freeze one UTC cutoff for the archive and both deletions.
  const cutoff = Math.floor(Date.now()/1000);
  const rows = await env.DB.batch([
    env.DB.prepare(ARCHIVE_COOKIE_SQL).bind(cutoff),
    env.DB.prepare(DELETE_EXPIRED_COOKIE_LIKES_SQL).bind(cutoff),
    env.DB.prepare(DELETE_EXPIRED_COOKIE_SESSIONS_SQL).bind(cutoff),
  ]);
  if (rows.length!==3 || rows.some(row=>row?.success!==true))
    throw new Error("expiry_archive_unconfirmed");
  return {expired_sessions:Number(rows[2]?.meta?.changes||0)};
}

export default {
  async scheduled(_controller, env, _ctx) {
    // A source handler is not a deployed Cron trigger.
    return archiveExpiredCookieLikes(env);
  },
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    if (path === "/q" && url.hostname === PRINT_QR_HOST) {
      if (request.method === "GET") return printQrVisit(env, request);
      if (request.method === "HEAD") return printQrRedirect();
      return new Response(null, {status:405, headers:{"allow":"GET, HEAD","cache-control":"no-store"}});
    }
    if (path.startsWith("/api/stats/like/")) return cookieLikeRoutes(env,request,path);
    if (request.method==="POST" && path==="/api/stats/print-aggregate") return recordAggregatePrint(env,request);
    if (request.method==="GET" && path==="/api/stats/rankings") return rankings(env,request);
    if (request.method==="GET" && path==="/api/stats/overview") return overviewStats(env);
    if (request.method==="GET" && path==="/api/stats/campaigns") return campaignStats(env,request);
    if (request.method==="GET" && path==="/api/stats/traffic") return trafficStats(env,request);
    if (request.method==="GET" && path==="/api/stats/page") return pageStats(env,request);
    if (request.method==="POST" && path==="/api/stats/page") return json({error:"legacy_personalized_api_retired"},410);
    if (request.method==="POST" && path==="/api/stats/visit") return recordVisitor(env,request);
    if (request.method==="POST" && path==="/api/stats/view") return recordView(env,request);
    if (request.method==="POST" && path==="/api/stats/print") return json({error:"legacy_personalized_api_retired"},410);
    if (request.method==="POST" && path==="/api/stats/like") return json({error:"legacy_personalized_api_retired"},410);
    if (request.method==="POST" && path==="/api/stats/erase-likes") return eraseLikes(env,request);
    if (request.method==="POST" && path==="/api/stats/erase-legacy-v3") return eraseLegacyV3(env,request);
    if (request.method==="POST" && path==="/api/stats/credential") return json({error:"legacy_personalized_api_retired"},410);
    return json({error:"not_found"},404);
  },
};
