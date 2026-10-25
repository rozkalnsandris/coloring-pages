"""Read-only structural check of synthetic GoatCounter v2.7.0 SQLite fixtures.

No network, subprocess, secrets, credentials or LIVE paths. This is NOT
a GDPR assessment, full data-retention audit or runtime privacy certificate.
The test instance must be stopped, checkpointed and copied into a temporary
directory before the command runs. Only synthetic page IDs/data are permitted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import quote

TAG = "arp242/goatcounter@7e91d8a9bdbb0dd48496e498c5680f8f3477a1b4"
MARKER = ".ausmalwiese-goatcounter-offline-only"
MARKER_BYTES = b"AUSMALWIESE_GOATCOUNTER_SYNTHETIC_V1\n"
DB_NAME = "goatcounter-test.sqlite3"
ID_RE = re.compile(r"[0-9]{7}\Z")
PREFIX = "goatcounter-offline-"

# Version-specific v2.7.0 table inventory; unknown tables fail closed.
# Empty referrer ref_counts are duplicate aggregate page/time/count data,
# not an individually identifying referrer dimension.
TABLES = frozenset({
    "sites", "users", "api_tokens", "hits", "bots", "paths", "campaigns",
    "browsers", "systems", "refs", "hit_counts", "ref_counts", "hit_stats",
    "browser_stats", "system_stats", "location_stats", "size_stats",
    "language_stats", "campaign_stats", "exports", "locations",
    "languages", "store",
})
DISALLOWED_ROWS = frozenset({
    "hits", "bots", "campaigns", "browsers", "systems",
    "browser_stats", "system_stats", "location_stats", "size_stats",
    "language_stats", "campaign_stats", "exports", "store",
})
COLS = {
    "sites": {"site_id", "settings"},
    "paths": {"site_id", "path_id", "path"},
    "refs": {"ref_id", "ref", "ref_scheme"},
    "hit_counts": {"site_id", "path_id", "hour", "total"},
    "ref_counts": {"site_id", "path_id", "ref_id", "hour", "total"},
    "hit_stats": {"site_id", "path_id", "day", "stats"},
    "hits": {"site_id", "path_id", "created_at", "session"},
    "bots": {"site_id", "path", "user_agent", "created_at", "bot"},
    "store": {"key", "value"},
}
class ProbeStop(ValueError):
    """Stable, non-sensitive failure code; no raw database values."""


def _stop(code: str) -> None:
    raise ProbeStop(code)


def _fixture_db(root_arg: str | Path) -> Path:
    root = Path(root_arg).absolute()
    tmp = Path(tempfile.gettempdir()).resolve()
    if (root.parent != tmp or not root.name.startswith(PREFIX)
            or root.is_symlink() or not root.is_dir()
            or root.resolve() != root):
        _stop("NOT_ISOLATED_TEMP_ROOT")
    marker = root / MARKER
    if (marker.is_symlink() or not marker.is_file()
            or marker.stat().st_size != len(MARKER_BYTES)
            or marker.read_bytes() != MARKER_BYTES):
        _stop("SYNTHETIC_FIXTURE_MARKER")
    db = root / DB_NAME
    if db.is_symlink() or not db.is_file():
        _stop("NO_SYNTHETIC_SQLITE")
    for suffix in ("-wal", "-shm", "-journal"):
        if (root / (DB_NAME + suffix)).exists():
            _stop("UNCHECKPOINTED_SQLITE")
    if db.stat().st_size > 32 * 1024 * 1024:
        _stop("FIXTURE_TOO_LARGE")
    return db


def _count(conn: sqlite3.Connection, table: str) -> int:
    if table not in TABLES:
        _stop("UNREVIEWED_TABLE")
    return int(conn.execute("SELECT count(*) FROM " + table).fetchone()[0])


def _timestamp(value: object, *, day: bool) -> bool:
    if not isinstance(value, str):
        return False
    try:
        if day:
            return dt.date.fromisoformat(value).isoformat() == value
        stamp = dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return (stamp.minute == 0 and stamp.second == 0
                and stamp.microsecond == 0 and stamp.strftime("%Y-%m-%d %H:%M:%S") == value)
    except ValueError:
        return False


def inspect_fixture(root: str | Path, *, page_id: str, expected_views: int) -> str:
    """Check synthetic fixture schema, forbidden tables and expected counts.

    Does not inspect raw SQLite pages, logs, backups, runtime routing,
    hidden dimensions in unrelated tables or logs, or legal requirements.
    """
    if not isinstance(page_id, str) or ID_RE.fullmatch(page_id) is None:
        _stop("EXPECTED_PUBLIC_ID")
    if type(expected_views) is not int or expected_views < 1 or expected_views > 500:
        _stop("EXPECTED_VIEWS")
    db = _fixture_db(root)
    uri = "file:" + quote(str(db), safe="/") + "?mode=ro&immutable=1"
    try:
        with sqlite3.connect(uri, uri=True, timeout=0.2) as conn:
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            check = conn.execute("PRAGMA quick_check").fetchone()
            if check is None or check[0] != "ok":
                _stop("SQLITE_INTEGRITY")
            got = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            got.difference_update({"sqlite_sequence"})
            if got != TABLES:
                _stop("SCHEMA_IDENTITY")
            for table, needed in COLS.items():
                columns = {row[1] for row in conn.execute("PRAGMA table_info(" + table + ")")}
                if not needed.issubset(columns):
                    _stop("SCHEMA_COLUMNS")
            for table in sorted(DISALLOWED_ROWS):
                if _count(conn, table):
                    _stop("FORBIDDEN_ROWS_" + table.upper())
            sites = conn.execute("SELECT site_id, settings FROM sites").fetchall()
            if len(sites) != 1:
                _stop("SITE_COUNT")
            try:
                settings = json.loads(sites[0]["settings"])
            except (ValueError, TypeError):
                _stop("SITE_SETTINGS")
            if (not isinstance(settings, dict)
                    or type(settings.get("collect")) is not int
                    or settings.get("collect") != 1
                    or settings.get("ignore_ips") not in (None, [])):
                _stop("SITE_COLLECTION_NOT_MINIMAL")
            site_id = sites[0]["site_id"]
            # v2.7.0 always has a static blank-referrer sentinel (ref_id=1).
            # Anything else would mean retaining referrer metadata.
            refs = conn.execute(
                "SELECT ref_id, ref, ref_scheme FROM refs"
            ).fetchall()
            if (len(refs) != 1 or refs[0]["ref_id"] != 1
                    or refs[0]["ref"] != "" or refs[0]["ref_scheme"] != "o"):
                _stop("REFERRER_STORED")
            wanted_path = "/coloring-page/" + page_id
            paths = conn.execute("SELECT site_id, path_id, path FROM paths").fetchall()
            if len(paths) != 1 or paths[0]["site_id"] != site_id or paths[0]["path"] != wanted_path:
                _stop("PATH_ALLOWLIST")
            path_id = paths[0]["path_id"]
            counts = conn.execute(
                "SELECT site_id, path_id, hour, total FROM hit_counts"
            ).fetchall()
            if not counts:
                _stop("NO_AGGREGATE_COUNTS")
            hourly = {}
            for r in counts:
                if (r["site_id"] != site_id or r["path_id"] != path_id
                        or type(r["total"]) is not int or r["total"] < 1
                        or not _timestamp(r["hour"], day=False)):
                    _stop("AGGREGATE_ROW_INVALID")
                if r["hour"] in hourly:
                    _stop("AGGREGATE_DUPLICATE_HOUR")
                hourly[r["hour"]] = r["total"]
            if sum(hourly.values()) != expected_views:
                _stop("PAGEVIEW_TOTAL_MISMATCH")

            # GoatCounter v2.7.0 also populates ref_counts when Referrer
            # collection is OFF, pointing to the shared empty-ref sentinel.
            # These contain no extra visitor dimension when they exactly
            # duplicate the hourly per-page totals.
            refs_hourly = {}
            refs_count = conn.execute(
                "SELECT site_id, path_id, ref_id, hour, total FROM ref_counts"
            ).fetchall()
            for r in refs_count:
                if (r["site_id"] != site_id or r["path_id"] != path_id
                        or r["ref_id"] != 1
                        or type(r["total"]) is not int or r["total"] < 1
                        or not _timestamp(r["hour"], day=False)):
                    _stop("REF_AGGREGATE_ROW_INVALID")
                if r["hour"] in refs_hourly:
                    _stop("REF_AGGREGATE_DUPLICATE_HOUR")
                refs_hourly[r["hour"]] = r["total"]
            if refs_hourly != hourly:
                _stop("REF_AGGREGATE_MISMATCH")

            # v2.7.0 stores a JSON array of 24 hourly counts per day/path
            # in hit_stats.stats (see cron/hit_stat.go). This must exactly
            # match the hourly hit_counts to prevent hidden payloads and
            # inconsistencies from receiving a false PASS.
            daily_expected = {}
            for hour, total in hourly.items():
                day = hour[:10]
                h = int(hour[11:13])
                daily_expected.setdefault(day, [0] * 24)[h] += total
            daily_actual = {}
            daily = conn.execute(
                "SELECT site_id, path_id, day, stats FROM hit_stats"
            ).fetchall()
            if not daily:
                _stop("NO_DAILY_STATS")
            for r in daily:
                if (r["site_id"] != site_id or r["path_id"] != path_id
                        or not _timestamp(r["day"], day=True)):
                    _stop("DAILY_ROW_INVALID")
                if r["day"] in daily_actual:
                    _stop("DAILY_ROW_DUPLICATE")
                try:
                    stats = json.loads(r["stats"])
                except (ValueError, TypeError):
                    _stop("DAILY_STATS_FORMAT")
                if (not isinstance(stats, list) or len(stats) != 24
                        or any(type(v) is not int or v < 0 for v in stats)):
                    _stop("DAILY_STATS_FORMAT")
                daily_actual[r["day"]] = stats
            if daily_actual != daily_expected:
                _stop("DAILY_COUNTS_MISMATCH")
    except sqlite3.DatabaseError:
        _stop("SQLITE_READ_OR_SCHEMA_ERROR")
    return "PASS_STRUCTURAL_SYNTHETIC_ONLY_NOT_RUNTIME_OR_PRIVACY_PROOF"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-test-root", required=True)
    parser.add_argument("--expected-page-id", required=True)
    parser.add_argument("--expected-views", required=True, type=int)
    args = parser.parse_args()
    try:
        result = inspect_fixture(
            args.synthetic_test_root,
            page_id=args.expected_page_id,
            expected_views=args.expected_views,
        )
    except (ProbeStop, OSError) as exc:
        code = str(exc) if isinstance(exc, ProbeStop) else "FIXTURE_IO_ERROR"
        print("GOATCOUNTER_OFFLINE=STOP CODE=" + code)
        return 2
    print("GOATCOUNTER_OFFLINE=" + result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
