const DEFAULT_ORIGIN = "https://coloring.rozkalns.net";
const PAGE_ID_RE = /^[a-z0-9][a-z0-9_-]{0,79}$/i;
const VISITOR_ID_RE = /^[a-z0-9][a-z0-9._:-]{5,127}$/i;

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
     ORDER BY recent_prints DESC, print_count DESC, page_id ASC
     LIMIT ?`
  ).bind(limit).all();
  return json({popular:popular.results||[],trending:trending.results||[],window_days:7});
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
    if (request.method==="GET" && path==="/api/stats/page") return pageStats(env,request);
    if (request.method==="POST" && path==="/api/stats/print") return recordPrint(env,request);
    if (request.method==="POST" && path==="/api/stats/like") return toggleLike(env,request);
    return json({error:"not_found"},404);
  },
};
