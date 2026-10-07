const DEFAULT_ORIGIN = "https://coloring.rozkalns.net";
const PAGE_ID_RE = /^[a-z0-9][a-z0-9_-]{0,79}$/i;
const VISITOR_ID_RE = /^[a-z0-9][a-z0-9._:-]{5,127}$/i;
const ANALYTICS_API = "https://api.cloudflare.com/client/v4/graphql";
const ANALYTICS_RANGE_DAYS = new Set([7, 30]);

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
function validPageId(value) { return typeof value === "string" && PAGE_ID_RE.test(value); }
function validVisitorId(value) { return typeof value === "string" && VISITOR_ID_RE.test(value); }

async function sha256(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte)=>byte.toString(16).padStart(2,"0")).join("");
}
async function parseBody(request) {
  const body = await request.json().catch(()=>null);
  if (!body || !validPageId(body.page_id)) return null;
  return body;
}
function allowedWriteOrigin(request, env) {
  const expected = env.PUBLIC_ORIGIN || DEFAULT_ORIGIN;
  const origin = request.headers.get("origin");
  const fetchSite = request.headers.get("sec-fetch-site");
  if (origin && origin !== expected) return false;
  return !fetchSite || fetchSite === "same-origin" || fetchSite === "none";
}
async function rateLimit(env, visitorId, action) {
  if (!env.RATE_LIMITER || !visitorId) return true;
  const {success} = await env.RATE_LIMITER.limit({key:`${action}:${visitorId}`});
  return success;
}
async function rankings(env, request) {
  const url = new URL(request.url);
  const limit = Math.min(20, Math.max(1, Number(url.searchParams.get("limit")) || 6));
  const popular = await env.DB.prepare(
    `SELECT page_id, print_count, like_count
     FROM page_stats
     WHERE print_count > 0
     ORDER BY print_count DESC, like_count DESC, page_id ASC
     LIMIT ?`
  ).bind(limit).all();
  const trending = await env.DB.prepare(
    `SELECT d.page_id,
            SUM(d.print_count) AS recent_prints,
            COALESCE(p.print_count, 0) AS print_count,
            COALESCE(p.like_count, 0) AS like_count
     FROM daily_prints d
     LEFT JOIN page_stats p ON p.page_id = d.page_id
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
    `SELECT COALESCE(SUM(print_count), 0) AS print_count,
            COALESCE(SUM(like_count), 0) AS like_count,
            COUNT(*) AS tracked_pages
     FROM page_stats`
  ).first();
  const engagement = await env.DB.prepare(
    `SELECT p.page_id,
            p.print_count,
            p.like_count,
            COALESCE(r.recent_prints, 0) AS recent_prints
     FROM page_stats p
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
      recent_prints: pages.reduce((sum, row) => sum + row.recent_prints, 0),
      view_count: pages.reduce((sum, row) => sum + row.view_count, 0),
      recent_views: pages.reduce((sum, row) => sum + row.recent_views, 0),
    },
    pages,
    window_days: 7,
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

async function trafficStats(env, request) {
  const url = new URL(request.url);
  const requestedDays = Number(url.searchParams.get("days")) || 7;
  const days = ANALYTICS_RANGE_DAYS.has(requestedDays) ? requestedDays : 7;
  const host = env.CF_ANALYTICS_HOST || new URL(env.PUBLIC_ORIGIN || DEFAULT_ORIGIN).hostname;
  const end = new Date();
  const start = new Date(end.getTime() - days * 86400000);
  const query = [
    "query AdminTraffic($zoneTag: string, $start: Time, $end: Time, $host: string) {",
    " viewer { zones(filter: { zoneTag: $zoneTag }) {",
    "  summary: httpRequestsAdaptiveGroups(limit: 1, filter: { datetime_geq: $start, datetime_lt: $end, requestSource: \"eyeball\", clientRequestHTTPHost: $host }) { sum { visits } avg { sampleInterval } }",
    "  crawlers: httpRequestsAdaptiveGroups(limit: 500, orderBy: [count_DESC], filter: {",
    "   datetime_geq: $start, datetime_lt: $end, requestSource: \"eyeball\", clientRequestHTTPHost: $host,",
    "   edgeResponseStatus_geq: 200, edgeResponseStatus_lt: 400,",
    "   OR: [",
    "    { userAgent_like: \"%bot%\" },",
    "    { userAgent_like: \"%crawler%\" },",
    "    { userAgent_like: \"%spider%\" },",
    "    { userAgent_like: \"%slurp%\" },",
    "    { userAgent_like: \"%ChatGPT-User%\" },",
    "    { userAgent_like: \"%facebookexternalhit%\" }",
    "   ]",
    "  }) { count avg { sampleInterval } dimensions { clientRequestPath userAgent } }",
    " } } }",
  ].join("\n");
  const result = await queryCloudflareAnalytics(env, query, {
    zoneTag: env.CF_ZONE_TAG,
    start: start.toISOString(),
    end: end.toISOString(),
    host,
  });
  if (result.error) return json({error:result.error},result.status);

  const zone = result.data?.viewer?.zones?.[0];
  const summary = zone?.summary?.[0] || {};
  const crawlerMap = new Map();
  let sampled = Number(summary.avg?.sampleInterval || 1) > 1;
  for (const row of zone?.crawlers || []) {
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
    visits:Number(summary.sum?.visits || 0),
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
  await env.DB.prepare(
    `INSERT INTO daily_views (page_id, day, view_count)
     VALUES (?, date('now'), 1)
     ON CONFLICT(page_id, day) DO UPDATE SET view_count=view_count+1`
  ).bind(body.page_id).run();
  return json({ok:true},201);
}

async function pageStats(env, request) {
  const url = new URL(request.url);
  const pageId = url.searchParams.get("page_id") || "";
  const visitorId = url.searchParams.get("visitor_id") || "";
  if (!validPageId(pageId)) return json({error:"invalid page_id"},400);
  if (visitorId && !validVisitorId(visitorId)) return json({error:"invalid visitor_id"},400);
  const stats = await env.DB.prepare("SELECT print_count, like_count FROM page_stats WHERE page_id = ?").bind(pageId).first();
  let liked = false;
  if (visitorId) {
    const visitorHash = await sha256(visitorId);
    liked = Boolean(await env.DB.prepare("SELECT 1 AS liked FROM likes WHERE page_id = ? AND visitor_hash = ?").bind(pageId,visitorHash).first());
  }
  return json({page_id:pageId,print_count:Number(stats?.print_count||0),like_count:Number(stats?.like_count||0),liked});
}
async function recordPrint(env, request) {
  if (!allowedWriteOrigin(request,env)) return json({error:"forbidden"},403);
  const body = await parseBody(request);
  if (!body || !validVisitorId(body.visitor_id)) return json({error:"invalid request"},400);
  if (!(await rateLimit(env,body.visitor_id,"print"))) return json({error:"rate_limited"},429);
  await env.DB.batch([
    env.DB.prepare(
      `INSERT INTO page_stats (page_id, print_count, updated_at)
       VALUES (?, 1, datetime('now'))
       ON CONFLICT(page_id) DO UPDATE SET print_count=print_count+1, updated_at=datetime('now')`
    ).bind(body.page_id),
    env.DB.prepare(
      `INSERT INTO daily_prints (page_id, day, print_count)
       VALUES (?, date('now'), 1)
       ON CONFLICT(page_id, day) DO UPDATE SET print_count=print_count+1`
    ).bind(body.page_id),
  ]);
  return json({ok:true},201);
}
async function toggleLike(env, request) {
  if (!allowedWriteOrigin(request,env)) return json({error:"forbidden"},403);
  const body = await parseBody(request);
  if (!body || !validVisitorId(body.visitor_id)) return json({error:"invalid request"},400);
  if (!(await rateLimit(env,body.visitor_id,"like"))) return json({error:"rate_limited"},429);
  const visitorHash = await sha256(body.visitor_id);
  const existing = await env.DB.prepare("SELECT 1 AS liked FROM likes WHERE page_id = ? AND visitor_hash = ?").bind(body.page_id,visitorHash).first();
  if (existing) {
    await env.DB.prepare("DELETE FROM likes WHERE page_id = ? AND visitor_hash = ?").bind(body.page_id,visitorHash).run();
  } else {
    await env.DB.prepare("INSERT OR IGNORE INTO likes (page_id, visitor_hash) VALUES (?, ?)").bind(body.page_id,visitorHash).run();
  }
  const stats = await env.DB.prepare("SELECT like_count, print_count FROM page_stats WHERE page_id = ?").bind(body.page_id).first();
  return json({page_id:body.page_id,liked:!existing,like_count:Number(stats?.like_count||0),print_count:Number(stats?.print_count||0)});
}
export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (request.method==="GET" && path==="/api/stats/rankings") return rankings(env,request);
    if (request.method==="GET" && path==="/api/stats/overview") return overviewStats(env);
    if (request.method==="GET" && path==="/api/stats/traffic") return trafficStats(env,request);
    if (request.method==="GET" && path==="/api/stats/page") return pageStats(env,request);
    if (request.method==="POST" && path==="/api/stats/view") return recordView(env,request);
    if (request.method==="POST" && path==="/api/stats/print") return recordPrint(env,request);
    if (request.method==="POST" && path==="/api/stats/like") return toggleLike(env,request);
    return json({error:"not_found"},404);
  },
};
