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
