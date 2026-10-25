"""Synthetic, disconnected tests of the GoatCounter SQLite structural gate.

These unit tests do not start GoatCounter, send visitor requests, touch
Cloudflare, inspect RPi5, or demonstrate GDPR/TDDDG compliance.
"""
import contextlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import goatcounter_offline_privacy_probe as probe  # noqa: E402


class SyntheticGoatCounterFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix=probe.PREFIX)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / probe.MARKER).write_bytes(probe.MARKER_BYTES)
        self.db = self.root / probe.DB_NAME
        self.id = "0427183"
        self.views = 2
        self._create_synthetic_schema()

    def _create_synthetic_schema(self):
        schemas = {
            "sites": "site_id integer, settings text",
            "paths": "site_id integer, path_id integer, path text",
            "refs": "ref_id integer, ref text, ref_scheme text",
            "hit_counts": "site_id integer, path_id integer, hour text, total integer",
            "hit_stats": "site_id integer, path_id integer, day text, stats text",
            "bots": "site_id integer, path text, bot integer, user_agent text, created_at text",
            "hits": "site_id integer, path_id integer, session blob, created_at text",
            "store": "key text, value blob",
        }
        with sqlite3.connect(self.db) as con:
            for table in sorted(probe.TABLES):
                definition = schemas.get(table, "test_sentinel integer")
                con.execute("CREATE TABLE " + table + " (" + definition + ")")
            con.execute(
                "INSERT INTO sites VALUES(?, ?)",
                (1, json.dumps({"collect": 1, "ignore_ips": []})),
            )
            con.execute(
                "INSERT INTO paths VALUES(1, 9, ?)",
                ("/coloring-page/" + self.id,),
            )
            con.execute("INSERT INTO refs VALUES(1, '', 'o')")
            con.execute(
                "INSERT INTO hit_counts VALUES(1, 9, '2026-10-25 11:00:00', 2)"
            )
            con.execute("INSERT INTO hit_stats VALUES(1, 9, '2026-10-25', '{}')")

    def mutate(self, sql, args=()):
        with sqlite3.connect(self.db) as con:
            con.execute(sql, args)

    def run_probe(self):
        return probe.inspect_fixture(
            self.root, page_id=self.id, expected_views=self.views
        )

    def assert_stops(self, code):
        with self.assertRaisesRegex(probe.ProbeStop, "^" + code + "$"):
            self.run_probe()

    def test_structural_baseline_and_leading_zero_string(self):
        self.assertEqual(
            self.run_probe(),
            "PASS_STRUCTURAL_SYNTHETIC_ONLY_NOT_RUNTIME_OR_PRIVACY_PROOF",
        )

    def test_session_defaults_zero_rejected(self):
        self.mutate("UPDATE sites SET settings='{\"collect\": 0}'")
        self.assert_stops("SITE_COLLECTION_NOT_MINIMAL")

    def test_session_bit_rejected(self):
        self.mutate("UPDATE sites SET settings='{\"collect\": 129}'")
        self.assert_stops("SITE_COLLECTION_NOT_MINIMAL")

    def test_boolean_collect_rejected(self):
        self.mutate("UPDATE sites SET settings='{\"collect\": true}'")
        self.assert_stops("SITE_COLLECTION_NOT_MINIMAL")

    def test_explicit_ip_ignore_list_rejected(self):
        self.mutate(
            "UPDATE sites SET settings='{\"collect\": 1, \"ignore_ips\": [\"203.0.113.1\"]}'"
        )
        self.assert_stops("SITE_COLLECTION_NOT_MINIMAL")

    def test_individual_hit_record_rejected(self):
        self.mutate(
            "INSERT INTO hits VALUES(1, 9, ?, '2026-10-25 11:08:00')",
            (b"opaque-session",),
        )
        self.assert_stops("FORBIDDEN_ROWS_HITS")

    def test_bot_raw_user_agent_record_rejected(self):
        self.mutate(
            "INSERT INTO bots VALUES(1, ?, 20, ?, '2026-10-25 11:05:00')",
            ("/coloring-page/0427183", "SyntheticBot/1.0"),
        )
        self.assert_stops("FORBIDDEN_ROWS_BOTS")

    def test_stored_session_map_rejected(self):
        self.mutate("INSERT INTO store VALUES('session', 'synthetic')")
        self.assert_stops("FORBIDDEN_ROWS_STORE")

    def test_browser_and_ref_dimensions_rejected(self):
        for table in ("browser_stats", "ref_counts", "location_stats"):
            with self.subTest(table=table):
                self.mutate("INSERT INTO " + table + " VALUES(1)")
                self.assert_stops("FORBIDDEN_ROWS_" + table.upper())
                self.mutate("DELETE FROM " + table)

    def test_nonblank_referrer_rejected(self):
        self.mutate(
            "INSERT INTO refs VALUES(2, 'https://example.invalid/', 'u')"
        )
        self.assert_stops("REFERRER_STORED")

    def test_arbitrary_or_unpublished_page_rejected(self):
        self.mutate(
            "UPDATE paths SET path='/coloring-page/extra?ip=203.0.113.1'"
        )
        self.assert_stops("PATH_ALLOWLIST")

    def test_aggregate_count_mismatch_rejected(self):
        self.mutate("UPDATE hit_counts SET total=3")
        self.assert_stops("PAGEVIEW_TOTAL_MISMATCH")

    def test_other_page_in_hourly_aggregate_rejected(self):
        self.mutate("UPDATE hit_counts SET path_id=123")
        self.assert_stops("AGGREGATE_ROW_INVALID")

    def test_bad_hour_boundary_rejected(self):
        self.mutate("UPDATE hit_counts SET hour='2026-10-25 11:02:00'")
        self.assert_stops("AGGREGATE_ROW_INVALID")

    def test_unknown_schema_table_rejected(self):
        self.mutate("CREATE TABLE visitor_ids (ip text)")
        self.assert_stops("SCHEMA_IDENTITY")

    def test_uncheckpointed_wal_rejected(self):
        (self.root / (probe.DB_NAME + "-wal")).write_bytes(b"synthetic")
        self.assert_stops("UNCHECKPOINTED_SQLITE")

    def test_missing_fixture_marker_rejected(self):
        (self.root / probe.MARKER).unlink()
        self.assert_stops("SYNTHETIC_FIXTURE_MARKER")

    def test_other_path_outside_isolated_temp_rejected(self):
        with self.assertRaisesRegex(
            probe.ProbeStop, "^NOT_ISOLATED_TEMP_ROOT$"
        ):
            probe.inspect_fixture(
                ROOT, page_id=self.id, expected_views=self.views
            )

    def test_disallowed_test_id_type_rejected(self):
        with self.assertRaisesRegex(probe.ProbeStop, "^EXPECTED_PUBLIC_ID$"):
            probe.inspect_fixture(self.root, page_id=427183, expected_views=2)

    def test_cli_stop_output_discloses_no_raw_database_data(self):
        self.mutate(
            "INSERT INTO bots VALUES(1, ?, 20, ?, '2026-10-25 11:05:00')",
            ("/coloring-page/0427183", "PrivateSyntheticAgent/123"),
        )
        stream = io.StringIO()
        with mock.patch(
            "sys.argv",
            ["probe", "--synthetic-test-root", str(self.root),
             "--expected-page-id", self.id, "--expected-views", "2"],
        ), contextlib.redirect_stdout(stream):
            status = probe.main()
        self.assertEqual(status, 2)
        self.assertEqual(
            stream.getvalue().strip(),
            "GOATCOUNTER_OFFLINE=STOP CODE=FORBIDDEN_ROWS_BOTS",
        )


if __name__ == "__main__":
    unittest.main()
