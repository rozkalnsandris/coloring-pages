"""Disconnected tests for the source-only GoatCounter first-party contract.

No network, GoatCounter process, LIVE catalogue, RPi5 or production traffic is
used. These tests prove only deterministic request/catalog/reporting rules.
"""
from datetime import datetime, timezone
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import goatcounter_pageview_contract as contract  # noqa: E402


ORIGIN = "https://ausmalwiese.de"


def entry(page_id="0427183", **updates):
    value = {
        "id": page_id,
        "title": "Synthetic",
        "category": "tiere",
        "preview": f"/media/{page_id}/preview.webp",
        "print": f"/media/{page_id}/print.png",
    }
    value.update(updates)
    return value


class PageviewContractTests(unittest.TestCase):
    def accept(self, body=b'{"page_id":"0427183"}', catalog=None, **updates):
        args = {
            "method": "POST",
            "request_target": contract.CLIENT_ROUTE,
            "content_type": "application/json",
            "origin": ORIGIN,
            "expected_origin": ORIGIN,
            "raw_body": body,
            "catalog": [entry()] if catalog is None else catalog,
        }
        args.update(updates)
        return contract.accept_client_event(**args)

    def assert_stop(self, code, **kwargs):
        with self.assertRaisesRegex(contract.ContractStop, "^" + code + "$"):
            self.accept(**kwargs)

    def test_valid_leading_zero_id_builds_exact_backend_body(self):
        accepted = self.accept()
        self.assertEqual(accepted.page_id, "0427183")
        self.assertEqual(accepted.logical_path, "/coloring-page/0427183")
        self.assertEqual(
            accepted.goatcounter_body(),
            b'{"no_sessions":true,"hits":[{"path":"/coloring-page/0427183"}]}',
        )
        for forbidden in (
            b"campaign", b"ref", b"user_agent", b"session", b"query",
            b"ip", b"bot", b"cookie", b"utm",
        ):
            self.assertNotIn(forbidden, accepted.goatcounter_body())

    def test_multi_page_current_catalog_entry_is_countable_once_by_activity_id(self):
        catalog = [
            entry(
                pages=[
                    {
                        "preview": "/media/0427183/preview-1.webp",
                        "print": "/media/0427183/print-1.png",
                    },
                    {
                        "preview": "/media/0427183/preview-2.webp",
                        "print": "/media/0427183/print-2.png",
                    },
                ]
            )
        ]
        self.assertEqual(self.accept(catalog=catalog).page_id, "0427183")

    def test_unknown_unpublished_or_removed_id_is_rejected(self):
        self.assert_stop(
            "CLIENT_PAGE_NOT_PUBLISHED",
            catalog=[entry("1234567")],
        )

    def test_hidden_or_explicitly_invisible_catalog_entry_is_rejected(self):
        for catalog in ([entry(hidden=True)], [entry(visible=False)]):
            with self.subTest(catalog=catalog):
                self.assert_stop("CLIENT_PAGE_NOT_PUBLISHED", catalog=catalog)

    def test_unrenderable_entry_is_not_published_for_analytics(self):
        self.assert_stop(
            "CLIENT_PAGE_NOT_PUBLISHED",
            catalog=[entry(preview="", print="")],
        )

    def test_legacy_non_seven_digit_catalog_ids_are_ignored(self):
        catalog = [entry("legacy-slug"), entry()]
        self.assertEqual(
            contract.published_page_ids(catalog),
            frozenset({"0427183"}),
        )

    def test_duplicate_catalog_id_fails_closed(self):
        self.assert_stop(
            "CATALOG_DUPLICATE_ID",
            catalog=[entry(), entry()],
        )

    def test_malformed_catalog_shape_fails_closed(self):
        for catalog in ({"id": "0427183"}, [None], [{"title": "missing id"}]):
            with self.subTest(catalog=catalog):
                self.assert_stop("CATALOG_SHAPE", catalog=catalog)

    def test_only_exact_page_id_client_schema_is_allowed(self):
        bodies = [
            b'{"page_id":"0427183","campaign":"dortmund-01"}',
            b'{"page_id":"0427183","ref":"https://example.invalid"}',
            b'{"page_id":"0427183","ip":"203.0.113.1"}',
            b'{"page_id":"0427183","user_agent":"Synthetic"}',
            b'{"page_id":"0427183","bot":1}',
            b'{"page_id":"0427183","query":"utm_source=x"}',
            b'{"page_id":"0427183","session":"x"}',
            b'{"page_id":"0427183","created_at":"2026-10-25T12:00:00Z"}',
            b'{"page_id":"0427183","extra":null}',
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assert_stop("CLIENT_SCHEMA", body=body)

    def test_duplicate_json_key_is_rejected_before_catalog_lookup(self):
        self.assert_stop(
            "CLIENT_JSON_DUPLICATE_KEY",
            body=b'{"page_id":"0427183","page_id":"1234567"}',
        )

    def test_numeric_or_malformed_page_ids_are_rejected_without_coercion(self):
        for body in (
            b'{"page_id":427183}',
            b'{"page_id":"427183"}',
            b'{"page_id":"00427183"}',
            b'{"page_id":"042718x"}',
        ):
            with self.subTest(body=body):
                self.assert_stop("CLIENT_PAGE_ID", body=body)

    def test_route_and_method_are_exact_and_query_strings_are_rejected(self):
        self.assert_stop("CLIENT_ROUTE_OR_METHOD", method="GET")
        self.assert_stop(
            "CLIENT_ROUTE_OR_METHOD",
            request_target=contract.CLIENT_ROUTE + "?campaign=x",
        )
        self.assert_stop("CLIENT_ROUTE_OR_METHOD", request_target="/api/stats/view")

    def test_origin_must_match_exact_expected_https_origin(self):
        for origin in (
            "https://evil.example",
            "http://ausmalwiese.de",
            "https://ausmalwiese.de.evil.example",
        ):
            with self.subTest(origin=origin):
                self.assert_stop("CLIENT_ORIGIN", origin=origin)
        self.assert_stop(
            "CLIENT_ORIGIN",
            expected_origin="https://ausmalwiese.de:not-a-port",
        )

    def test_content_type_is_json_with_only_optional_utf8_charset(self):
        for content_type in (
            "application/json",
            "application/json; charset=UTF-8",
            'application/json; charset="utf-8"',
        ):
            with self.subTest(content_type=content_type):
                self.assertEqual(
                    self.accept(content_type=content_type).page_id,
                    "0427183",
                )
        for content_type in (
            "text/plain",
            "application/json; profile=x",
            "application/json; charset=latin1",
            "application/json; charset=utf-8; extra=x",
        ):
            with self.subTest(content_type=content_type):
                self.assert_stop("CLIENT_CONTENT_TYPE", content_type=content_type)

    def test_malformed_or_oversized_body_is_rejected(self):
        self.assert_stop("CLIENT_JSON", body=b"{")
        self.assert_stop("CLIENT_BODY_SIZE", body=b"")
        self.assert_stop(
            "CLIENT_BODY_SIZE",
            body=b'{"page_id":"0427183","padding":"' + b"x" * 200 + b'"}',
        )

    def test_backend_payload_is_built_from_id_not_caller_json(self):
        accepted = self.accept(
            body=json.dumps(
                {"page_id": "0427183"},
                separators=(",", ":"),
            ).encode("ascii")
        )
        self.assertEqual(
            accepted.goatcounter_payload(),
            {
                "no_sessions": True,
                "hits": [{"path": "/coloring-page/0427183"}],
            },
        )


class ReportingWindowTests(unittest.TestCase):
    def test_today_7d_30d_and_all_use_berlin_calendar_dates(self):
        now = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(
            contract.reporting_date_bounds(now, "today"),
            (
                datetime(2026, 10, 25).date(),
                datetime(2026, 10, 25).date(),
            ),
        )
        self.assertEqual(
            contract.reporting_date_bounds(now, "7d"),
            (
                datetime(2026, 10, 19).date(),
                datetime(2026, 10, 25).date(),
            ),
        )
        self.assertEqual(
            contract.reporting_date_bounds(now, "30d"),
            (
                datetime(2026, 9, 26).date(),
                datetime(2026, 10, 25).date(),
            ),
        )
        self.assertEqual(
            contract.reporting_date_bounds(now, "all"),
            (None, datetime(2026, 10, 25).date()),
        )

    def test_dst_change_does_not_turn_calendar_window_into_fixed_hours(self):
        # 2026-03-29 22:30 UTC is already 2026-03-30 in Europe/Berlin.
        now = datetime(2026, 3, 29, 22, 30, tzinfo=timezone.utc)
        self.assertEqual(
            contract.reporting_date_bounds(now, "7d"),
            (
                datetime(2026, 3, 24).date(),
                datetime(2026, 3, 30).date(),
            ),
        )

    def test_naive_time_and_unknown_period_fail_closed(self):
        with self.assertRaisesRegex(
            contract.ContractStop, "^REPORT_TIME_REQUIRED$"
        ):
            contract.reporting_date_bounds(datetime(2026, 10, 25), "7d")
        with self.assertRaisesRegex(contract.ContractStop, "^REPORT_PERIOD$"):
            contract.reporting_date_bounds(
                datetime(2026, 10, 25, tzinfo=timezone.utc),
                "90d",
            )


if __name__ == "__main__":
    unittest.main()
