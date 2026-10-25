import hashlib
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path: str)->str:
    return (ROOT/path).read_text(encoding="utf-8")
class HomeRankingLayoutTests(unittest.TestCase):
    def test_home_keeps_large_hero_and_shows_browse_before_discovery(self):
        html = read("index.html")
        css = read("css/app.css")
        js = read("js/app.js")

        hero = html.index('id="hero" class="hero"')
        discover = html.index('id="entdecken"')
        categories = html.index('id="kategorien"')
        newest = html.index('id="neu"')
        about = html.index('id="ueber-uns"')
        self.assertLess(hero, categories)
        self.assertLess(categories, newest)
        self.assertLess(newest, discover)
        self.assertLess(discover, about)
        self.assertIn('class="hero-art"', html)
        self.assertIn('data-search-form', html)

        self.assertIn('data-ranking-root', html)
        self.assertIn('role="tablist"', html)
        self.assertIn('data-ranking-tab="trending"', html)
        self.assertIn('data-ranking-tab="popular"', html)
        self.assertIn('aria-selected="true"', html)
        self.assertIn('data-ranking-section="trending"', html)
        self.assertIn('data-ranking-section="popular"', html)
        self.assertIn('data-ranking-gallery="trending"', html)
        self.assertIn('data-ranking-gallery="popular"', html)
        self.assertNotIn('id="beliebt"', html)
        self.assertNotIn('id="trending"', html)

        self.assertIn('window.ColoringStats.getRankings(6)', js)
        self.assertIn('function setRankingTab', js)
        self.assertNotIn('rankingRoot.hidden=false', js)
        self.assertIn('aria-busy="true"', html)
        self.assertIn('data-ranking-status role="status"', html)
        self.assertIn('button.disabled = !available.get', js)
        self.assertIn('rankingsUnavailable();', js)
        self.assertIn('.ranking-gallery { min-height:', css)
        self.assertNotIn('data-ranking-root aria-labelledby="discover-title" hidden', html)
        self.assertIn('available.get("trending")', js)
        self.assertIn('"ArrowLeft"', js)
        self.assertIn('"ArrowRight"', js)

        self.assertIn('.ranking-tabs {', css)
        self.assertIn('.ranking-tab.is-active', css)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr))', css)
def test_detail_tracks_print_intent_and_aggregate_like():
    html=read("detail.html"); js=read("js/detail.js")
    assert 'data-action-like' in html
    assert 'ColoringStats?.trackPrint?.(loadedEntryId)' in js
    assert 'ColoringStats.addLike(loadedEntryId)' in js
    assert 'aria-pressed' in html
def test_cloudflare_stats_contract_keeps_rpi5_out_of_state():
    worker=read("cloudflare/stats-worker.js"); schema=read("cloudflare/stats-schema.sql"); docs=read("docs/CLOUDFLARE_STATS_V1.md")
    assert '"/api/stats/rankings"' in worker
    assert 'path==="/api/stats/print") return legacyPersonalizedRetired' in worker
    assert 'path==="/api/stats/like") return legacyPersonalizedRetired' in worker
    assert "legacy_personalized_api_retired" in worker
    assert "cloudflare_traffic_version:1" in worker
    assert "http_requests:httpRequests" in worker
    assert 'path==="/api/stats/visit"' in worker
    assert "RATE_LIMITER" in worker
    assert "CREATE TABLE IF NOT EXISTS page_stats" in schema
    assert "CREATE TABLE IF NOT EXISTS daily_visitors" not in schema
    assert "VISITOR_HMAC_KEY" not in worker
    assert "PRIMARY KEY (page_id, visitor_hash)" in schema
    assert "Raspberry Pi" in docs
    assert "print intent" in docs
def test_stats_frontend_uses_aggregate_endpoints_without_persistent_identity():
    js=read("js/stats.js")
    assert '"/like-aggregate"' in js
    assert '${API_BASE}/print-aggregate' in js
    for forbidden in ('getVisitorId', 'visitor_id', 'localStorage', 'sessionStorage', 'randomUUID'):
        assert forbidden not in js


class TrendingSqlRegressionTests(unittest.TestCase):
    def test_trending_sql_is_executable_and_ranks_seven_utc_days(self):
        import sqlite3

        worker = read("cloudflare/stats-worker.js")
        marker = "const trending = await env.DB.prepare("
        assert worker.count(marker) == 1
        sql = worker.split(marker, 1)[1].split("`", 2)[1]

        with sqlite3.connect(":memory:") as db:
            db.executescript(read("cloudflare/stats-schema.sql"))
            db.executemany(
                "INSERT INTO page_stats (page_id, print_count, like_count) VALUES (?, ?, ?)",
                [
                    ("alpha", 8, 0),
                    ("beta", 8, 9),
                    ("gamma", 3, 0),
                    ("edge", 1, 0),
                    ("expired", 90, 0),
                ],
            )
            db.executescript("""
                INSERT INTO daily_prints (page_id, day, print_count) VALUES
                  ('alpha', date('now'), 4),
                  ('beta', date('now', '-1 days'), 4),
                  ('gamma', date('now', '-2 days'), 4),
                  ('edge', date('now', '-6 days'), 1),
                  ('expired', date('now', '-7 days'), 15);
            """)
            rows = db.execute(sql, (6,)).fetchall()
            assert [(row[0], row[1], row[2]) for row in rows] == [
                ("alpha", 4, 8),
                ("beta", 4, 8),
                ("gamma", 4, 3),
                ("edge", 1, 1),
            ]
            assert [row[3] for row in rows] == [0, 9, 0, 0]
            assert len(db.execute(sql, (2,)).fetchall()) == 2


class AdminStatsDashboardTests(unittest.TestCase):
    def test_overview_endpoint_is_aggregate_and_read_only(self):
        worker = read("cloudflare/stats-worker.js")
        start = worker.index("async function overviewStats")
        end = worker.index("function crawlerName", start)
        overview = worker[start:end]

        self.assertIn('path==="/api/stats/overview"', worker)
        self.assertIn("FROM page_stats", overview)
        self.assertIn("FROM daily_prints", overview)
        self.assertIn("recent_prints", overview)
        self.assertNotIn("daily_visitors", overview)
        response = overview[overview.rindex("return json({"):]
        self.assertNotIn("visitor_hash", response)
        self.assertNotIn("FROM likes", overview)
        self.assertNotIn("INSERT ", overview)
        self.assertNotIn("UPDATE ", overview)
        self.assertNotIn("DELETE ", overview)

    def test_admin_dashboard_is_shipped_noindex_and_unlinked(self):
        html = read("stats.html")
        public_home = read("index.html")
        dockerfile = read("Dockerfile")

        self.assertIn('name="robots" content="noindex,nofollow,noarchive"', html)
        self.assertIn("data-stats-total-prints", html)
        self.assertIn("Total likes", html)
        self.assertIn("Print actions in the last 7 days", html)
        self.assertNotIn("data-stats-qr-total", html)
        self.assertNotIn("data-stats-kita-landing", html)
        self.assertIn("data-stats-popular", html)
        self.assertIn("data-stats-trending", html)
        self.assertIn("data-stats-table", html)
        self.assertIn('href="traffic.html"', html)
        self.assertNotIn("data-stats-visits", html)
        self.assertNotIn("data-stats-crawlers", html)
        self.assertNotIn('href="stats.html"', public_home)
        self.assertNotIn('href="traffic.html"', public_home)
        self.assertIn("stats.html traffic.html", dockerfile)
        self.assertIn('<html lang="en">', html)
        self.assertIn("Internal dashboard", html)
        self.assertIn("Refresh", html)
        self.assertIn('id="stats-catalog-table"', html)
        self.assertIn("data-stats-load-more", html)
        self.assertIn("More", html)

    def test_published_pages_counts_actual_a4_sheets(self):
        admin = read("js/stats-admin.js")
        html = read("stats.html")

        self.assertIn("function publishedPageCount(entry)", admin)
        self.assertIn("Array.isArray(entry?.pages) && entry.pages.length > 0", admin)
        self.assertIn('typeof entry?.print === "string" && entry.print ? 1 : 0', admin)
        self.assertIn("page_count: publishedPageCount(entry)", admin)
        self.assertIn("rows.reduce((total, row) => total + row.page_count, 0)", admin)
        self.assertNotIn("els.publishedPages.textContent = formatNumber(rows.length);", admin)
        self.assertIn("Published pages", html)

    def test_admin_dashboard_uses_read_only_shared_stats_api(self):
        shared = read("js/stats.js")
        admin = read("js/stats-admin.js")

        self.assertIn("async function getOverview()", shared)
        self.assertIn('requestJson("/overview")', shared)
        self.assertIn("window.ColoringStats.getOverview()", admin)
        self.assertIn('fetch("catalog.json", {cache: "no-store"})', admin)
        self.assertNotIn("toggleLike", admin)
        self.assertNotIn("trackPrint", admin)
        self.assertNotIn('method: "POST"', admin)
        self.assertIn('new Intl.NumberFormat("en-GB")', admin)
        self.assertIn('new Intl.DateTimeFormat("en-GB"', admin)
        self.assertIn("const CATALOG_PAGE_SIZE = 20;", admin)
        self.assertIn("visible.slice(0, visibleLimit)", admin)
        self.assertIn("visibleLimit += CATALOG_PAGE_SIZE", admin)
        self.assertIn('addEventListener("input", resetTableLimit)', admin)
        self.assertIn('addEventListener("change", resetTableLimit)', admin)


class CloudflareUniqueVisitorTests(unittest.TestCase):

    def test_daily_visitor_hmac_is_removed_but_campaign_visit_route_remains(self):
        worker = read("cloudflare/stats-worker.js")
        schema = read("cloudflare/stats-schema.sql")
        cleanup = read("cloudflare/stats-remove-daily-visitor-hmac.sql")

        self.assertNotIn("CREATE TABLE IF NOT EXISTS daily_visitors", schema)
        self.assertNotIn("VISITOR_HMAC_KEY", worker)
        self.assertNotIn("hmacSha256", worker)
        self.assertIn('path==="/api/stats/visit"', worker)
        visitor = worker[worker.index("async function recordVisitor"):worker.index("async function trafficStats")]
        self.assertNotIn("CF-Connecting-IP", visitor)
        self.assertNotIn("daily_visitors", visitor)
        self.assertIn("campaignEventStatement", visitor)

        traffic = worker[worker.index("async function trafficStats"):worker.index("async function recordView")]
        self.assertNotIn("FROM daily_visitors", traffic)
        self.assertIn('uniqueVisitorsStatus = "removed"', traffic)
        self.assertIn('unique_visitors_basis:"removed-no-persistent-visitor-metric"', traffic)
        self.assertIn("DROP TABLE IF EXISTS daily_visitors", cleanup)

    def test_public_pages_track_visit_without_creating_browser_identity(self):
        shared = read("js/stats.js")

        self.assertIn("function trackVisit()", shared)
        self.assertIn("${API_BASE}/visit", shared)
        track_visit = shared[shared.index("function trackVisit"):shared.index("function trackView")]
        self.assertNotIn("getVisitorId", track_visit)
        self.assertNotIn("visitor_id", track_visit)
        self.assertIn('fetch(`${API_BASE}/visit`', track_visit)
        self.assertIn("keepalive: true", track_visit)
        self.assertNotIn("sendBeacon", track_visit)
        self.assertIn('location.pathname === "/"', shared)
        self.assertIn('location.pathname === "/index.html"', shared)
        self.assertIn('location.pathname === "/detail.html"', shared)
        self.assertNotIn('location.pathname === "/stats.html"', shared)
        self.assertNotIn('location.pathname === "/traffic.html"', shared)


class AdminTrafficAnalyticsTests(unittest.TestCase):
    def test_detail_views_are_anonymous_aggregate_events(self):
        schema = read("cloudflare/stats-schema.sql")
        worker = read("cloudflare/stats-worker.js")
        shared = read("js/stats.js")
        detail = read("js/detail.js")

        self.assertIn("CREATE TABLE IF NOT EXISTS daily_views", schema)
        self.assertIn('path==="/api/stats/view"', worker)
        self.assertIn("INSERT INTO daily_views", worker)
        self.assertIn("function trackView(pageId)", shared)
        self.assertIn("ColoringStats?.trackView?.(entry.id)", detail)
        track_view = shared[shared.index("function trackView"):shared.index("function trackPrint")]
        self.assertNotIn("getVisitorId", track_view)
        self.assertNotIn("visitor_id", track_view)

    def test_traffic_proxy_is_fixed_read_only_cloudflare_analytics(self):
        worker = read("cloudflare/stats-worker.js")
        start = worker.index("async function trafficStats")
        end = worker.index("async function recordView", start)
        traffic = worker[start:end]

        self.assertIn('path==="/api/stats/traffic"', worker)
        self.assertIn("httpRequestsAdaptiveGroups", traffic)
        self.assertIn("query AdminVisits($zoneTag: string, $filter: filter)", traffic)
        self.assertIn("query AdminCrawlers($zoneTag: string, $filter: filter)", traffic)
        self.assertNotIn("query AdminUniqueVisitors", traffic)
        self.assertNotIn("httpRequests1dGroups", traffic)
        self.assertNotIn("uniq { uniques }", traffic)
        self.assertNotIn("FROM daily_visitors", traffic)
        self.assertIn("unique_visitors_date", traffic)
        self.assertIn('unique_visitors_basis:"removed-no-persistent-visitor-metric"', traffic)
        self.assertIn("dimensions { datetimeHour }", traffic)
        self.assertIn("sum { visits }", traffic)
        self.assertIn("visitsRows.reduce", traffic)
        self.assertIn("userAgent_like", traffic)
        self.assertIn("clientRequestPath", traffic)
        self.assertNotIn("query AdminTraffic(", traffic)
        self.assertIn("CF_ANALYTICS_API_TOKEN", worker)
        self.assertIn("CF_ZONE_TAG", worker)
        self.assertNotIn("clientIP", traffic)
        self.assertNotIn("visitor_hash", traffic)

    def test_traffic_uses_only_cloudflare_aggregates(self):
        html = read("traffic.html")
        js = read("js/traffic-admin.js")
        worker = read("cloudflare/stats-worker.js")
        stats = read("stats.html")
        shared = read("js/stats.js")
        self.assertIn('href="traffic.html"', stats)
        self.assertIn('name="robots" content="noindex,nofollow,noarchive"', html)
        self.assertIn('href="stats.html"', html)
        self.assertIn('data-traffic-days', html)
        self.assertIn('data-stats-visits', html)
        self.assertIn('data-stats-crawler-requests', html)
        self.assertIn('data-traffic-unique', html)
        self.assertIn('data-traffic-requests', html)
        self.assertIn('data-traffic-visits-availability', html)
        self.assertIn('data-traffic-requests-availability', html)
        self.assertNotIn('<td>Available</td>', html)
        self.assertIn('data-stats-crawlers', html)
        self.assertNotIn('data-instagram-', html)
        self.assertIn("Instagram, QR &amp; Kita", html)
        self.assertIn("Provider API verification required", html)
        self.assertIn("Page views by coloring page", html)
        self.assertNotIn('data-stats-total-views', html)
        self.assertNotIn('data-traffic-table', html)
        self.assertNotIn('data-stats-unique-visitors', html)
        self.assertIn("getTraffic(days)", js)
        self.assertNotIn("getOverview(", js)
        self.assertNotIn("getCampaigns(", js)
        self.assertNotIn("catalog.json", js)
        self.assertNotIn("daily_visitors", js)
        self.assertNotIn("traffic.unique_visitors", js)
        self.assertNotIn('method: "POST"', js)
        self.assertIn('async function getTraffic(days = 7)', shared)
        self.assertIn("httpRequestsAdaptiveGroups", worker)
        self.assertIn('const host = "ausmalwiese.de";', worker)
        self.assertIn('http_requests_basis:"cloudflare-http-eyeball-requests"', worker)
        self.assertIn('error:"analytics_zone_unavailable"', worker)
        self.assertIn("CF_ANALYTICS_API_TOKEN", worker)
        self.assertIn("CF_ZONE_TAG", worker)
        self.assertIn("noindex,nofollow,noarchive", html)

    @unittest.skipUnless(shutil.which("node"), "Node required for traffic rendering simulation")
    def test_traffic_displays_cloudflare_metrics_and_fail_closed_states(self):
        harness = r"""
const fs=require('node:fs'),vm=require('node:vm');
const code=fs.readFileSync('js/traffic-admin.js','utf8');
async function render(metric, selectedDays='7'){
  const nodes=new Map();
  const document={
    querySelector:(selector)=>{
      if(!nodes.has(selector))nodes.set(selector,{
        textContent:'',value:selector==='[data-traffic-days]'?selectedDays:'',
        hidden:false,disabled:false,addEventListener(){},replaceChildren(...items){this.items=items},
      });
      return nodes.get(selector);
    },
    createElement:(kind)=>({tag:kind,textContent:'',className:'',append(){}}),
  };
  const window={ColoringStats:{getTraffic:async(days)=>({
    range_days:days,visits:635,crawler_requests:1459,crawlers:[],sampled:true,...metric
  })}};
  vm.runInNewContext(code,{document,window,Intl,Date,console});
  await new Promise(resolve=>setImmediate(resolve));
  return {
    visitors:nodes.get('[data-traffic-unique]').textContent,
    visits:nodes.get('[data-stats-visits]').textContent,
    requests:nodes.get('[data-traffic-requests]').textContent,
    crawlers:nodes.get('[data-stats-crawler-requests]').textContent,
    visitsState:nodes.get('[data-traffic-visits-availability]').textContent,
    requestsState:nodes.get('[data-traffic-requests-availability]').textContent,
    note:nodes.get('[data-traffic-visits-note]').textContent,
    status:nodes.get('[data-traffic-page-status]').textContent,
  };
}
(async()=>{
  const v=await render({unique_visitors:12345,unique_visitors_status:'available',
    unique_visitors_basis:'worker-d1-daily-hmac-ip'});
  if(v.visitors!=='N/A'||v.visits!=='–'||v.requests!=='–'||v.crawlers!=='–'
    ||v.visitsState!=='Unavailable'||v.requestsState!=='Unavailable'
    ||!v.note.includes('not independently verified')||!v.status.includes('hostname not verified'))
    throw Error('Legacy or wrong-host metrics must be hidden '+JSON.stringify(v));
  const thirty=await render({analytics_host:'ausmalwiese.de',cloudflare_traffic_version:1,http_requests:8091},'30');
  if(thirty.visits!=='635'||thirty.requests!=='8,091'||!thirty.note.includes('Worker-declared')
    ||!thirty.visitsState.includes('host declared by Worker')
    ||!thirty.requestsState.includes('sampled'))
    throw Error('Cloudflare host-proof rendering failed '+JSON.stringify(thirty));
  const missing=await render({analytics_host:'ausmalwiese.de',cloudflare_traffic_version:1});
  if(missing.requests!=='N/A'||!missing.requestsState.includes('Unavailable')
    ||missing.visits!=='635')
    throw Error('Missing request field must be unavailable, not zero '+JSON.stringify(missing));
  const invalid=await render({visits:null});
  if(invalid.visits!=='–'||invalid.requests!=='–'||!invalid.status.includes('unavailable')
    ||invalid.visitsState!=='Unavailable'||invalid.requestsState!=='Unavailable')
    throw Error('Invalid provider data must not be coerced to zero '+JSON.stringify(invalid));
  console.log('CLOUDFLARE_ONLY_TRAFFIC=PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
        result = subprocess.run(["node", "-e", harness], cwd=ROOT,
                                text=True, capture_output=True, timeout=20, check=False)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("CLOUDFLARE_ONLY_TRAFFIC=PASS", result.stdout)


class KitaCampaignStatsTests(unittest.TestCase):
    def test_campaign_schema_is_aggregate_and_allowlisted(self):
        schema = read("cloudflare/stats-schema.sql")
        worker = read("cloudflare/stats-worker.js")
        self.assertIn("CREATE TABLE IF NOT EXISTS daily_campaign_events", schema)
        self.assertIn("PRIMARY KEY (campaign, event, page_id, day)", schema)
        self.assertIn('const CAMPAIGN_IDS = new Set(["dortmund-01"])', worker)
        self.assertIn("INSERT INTO daily_campaign_events", worker)
        self.assertIn('path==="/api/stats/campaigns"', worker)
        campaign = worker[worker.index("async function campaignStats"):worker.index("function crawlerName")]
        self.assertNotIn("visitor_hash", campaign)
        self.assertNotIn("CF-Connecting-IP", campaign)

    def test_campaign_is_carried_through_existing_funnel(self):
        shared = read("js/stats.js")
        app = read("js/app.js")
        kita = read("js/kita.js")
        detail = read("js/detail.js")
        self.assertIn('new Set(["dortmund-01"])', shared)
        self.assertIn('trackVisit?.("landing")', kita)
        self.assertIn('params.set("campaign","dortmund-01")', app)
        self.assertIn("payload.campaign = campaign", shared)
        self.assertIn("ColoringStats?.trackView?.(entry.id)", detail)
        self.assertIn("ColoringStats?.trackPrint?.(loadedEntryId)", detail)

    def test_campaign_api_is_preserved_but_removed_from_engagement_dashboard(self):
        html = read("stats.html")
        shared = read("js/stats.js")
        admin = read("js/stats-admin.js")
        self.assertNotIn("data-stats-kita-landing", html)
        self.assertNotIn("data-stats-kita-catalog", html)
        self.assertNotIn("data-stats-kita-detail", html)
        self.assertNotIn("data-stats-kita-prints", html)
        self.assertNotIn("data-stats-qr-total", html)
        self.assertNotIn("data-stats-qr-recent", html)
        self.assertIn("async function getCampaigns(days = 30)", shared)
        self.assertNotIn("getCampaigns", admin)
        self.assertNotIn('method: "POST"', admin)
