import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path: str)->str:
    return (ROOT/path).read_text(encoding="utf-8")
def test_home_has_progressive_popular_and_trending_sections():
    html=read("index.html"); js=read("js/app.js")
    assert 'data-ranking-section="popular"' in html
    assert 'data-ranking-section="trending"' in html
    assert 'data-ranking-gallery="popular"' in html
    assert 'data-ranking-gallery="trending"' in html
    assert 'window.ColoringStats.getRankings(6)' in js
    assert 'section.hidden=false' in js
def test_detail_tracks_print_intent_and_reversible_like():
    html=read("detail.html"); js=read("js/detail.js")
    assert 'data-action-like' in html
    assert 'ColoringStats?.trackPrint?.(loadedEntryId)' in js
    assert 'ColoringStats.toggleLike(loadedEntryId)' in js
    assert 'aria-pressed' in html
def test_cloudflare_stats_contract_keeps_rpi5_out_of_state():
    worker=read("cloudflare/stats-worker.js"); schema=read("cloudflare/stats-schema.sql"); docs=read("docs/CLOUDFLARE_STATS_V1.md")
    assert '"/api/stats/rankings"' in worker
    assert '"/api/stats/print"' in worker
    assert '"/api/stats/like"' in worker
    assert "RATE_LIMITER" in worker
    assert "CREATE TABLE IF NOT EXISTS page_stats" in schema
    assert "PRIMARY KEY (page_id, visitor_hash)" in schema
    assert "Raspberry Pi" in docs
    assert "print intent" in docs
def test_stats_frontend_uses_first_party_random_id_only_on_engagement():
    js=read("js/stats.js")
    assert 'getVisitorId(false)' in js
    assert 'getVisitorId(true)' in js
    assert 'localStorage.getItem(VISITOR_KEY)' in js
    assert 'crypto?.randomUUID?.()' in js


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
        end = worker.index("async function pageStats", start)
        overview = worker[start:end]

        self.assertIn('path==="/api/stats/overview"', worker)
        self.assertIn("FROM page_stats", overview)
        self.assertIn("FROM daily_prints", overview)
        self.assertIn("recent_prints", overview)
        self.assertNotIn("visitor_hash", overview)
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
        self.assertIn("data-stats-popular", html)
        self.assertIn("data-stats-trending", html)
        self.assertIn("data-stats-table", html)
        self.assertNotIn('href="stats.html"', public_home)
        self.assertIn("stats.html", dockerfile)
        self.assertIn('<html lang="lv">', html)
        self.assertIn("Iekšējais pārskats", html)
        self.assertIn("Atjaunināt", html)

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
        self.assertIn('new Intl.NumberFormat("lv-LV")', admin)
        self.assertIn('new Intl.DateTimeFormat("lv-LV"', admin)
