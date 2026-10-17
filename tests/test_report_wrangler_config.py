#!/usr/bin/env python3
"""Offline validation for the report Worker Wrangler config (#249)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "cloudflare" / "wrangler.report.json"
WORKER = ROOT / "cloudflare" / "report-worker.mjs"
EXPECTED_WORKER_SHA256 = "f3c3f9902666d957abb16c5a29cfc4cb73263ccab2e88400e3281aae7ca92f1b"

ROUTES = [
    {"pattern": "ausmalwiese.de/api/report", "zone_name": "ausmalwiese.de"},
    {"pattern": "ausmalwiese.de/api/report/config", "zone_name": "ausmalwiese.de"},
    {"pattern": "www.ausmalwiese.de/api/report", "zone_name": "ausmalwiese.de"},
    {"pattern": "www.ausmalwiese.de/api/report/config", "zone_name": "ausmalwiese.de"},
]
SECRETS = [
    "TURNSTILE_SITE_KEY",
    "TURNSTILE_SECRET",
    "BREVO_API_KEY",
    "REPORT_TO",
]


class ReportWranglerConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_closed_top_level_contract(self):
        self.assertEqual(
            set(self.config),
            {
                "name",
                "main",
                "compatibility_date",
                "workers_dev",
                "preview_urls",
                "no_bundle",
                "routes",
                "secrets",
                "ratelimits",
            },
        )
        self.assertEqual(self.config["name"], "coloring-pages-report-v1")
        self.assertEqual(self.config["main"], "./report-worker.mjs")
        self.assertEqual(self.config["compatibility_date"], "2026-10-17")
        self.assertIs(self.config["workers_dev"], False)
        self.assertIs(self.config["preview_urls"], False)
        self.assertIs(self.config["no_bundle"], True)
        self.assertNotIn("vars", self.config)
        self.assertNotIn("account_id", self.config)
        self.assertNotIn("zone_id", self.config)

    def test_exact_worker_source_is_pinned(self):
        raw = WORKER.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_WORKER_SHA256)
        text = raw.decode("utf-8")
        self.assertIn('const BREVO_URL = "https://api.brevo.com/v3/smtp/email";', text)
        self.assertIn('"/api/report/config"', text)
        self.assertIn('"/api/report"', text)

    def test_only_four_narrow_report_routes(self):
        self.assertEqual(self.config["routes"], ROUTES)
        patterns = [route["pattern"] for route in self.config["routes"]]
        self.assertEqual(len(patterns), len(set(patterns)))
        for pattern in patterns:
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("#", pattern)
            self.assertNotIn("/api/stats", pattern)
            self.assertTrue(
                pattern.startswith("ausmalwiese.de/")
                or pattern.startswith("www.ausmalwiese.de/")
            )

    def test_required_values_are_names_only(self):
        self.assertEqual(self.config["secrets"], {"required": SECRETS})
        serialized = json.dumps(self.config, sort_keys=True)
        self.assertNotIn("@", serialized)
        self.assertNotIn("api-key", serialized.lower())
        self.assertNotIn("secret_value", serialized.lower())

    def test_exact_rate_limit_bindings(self):
        limits = self.config["ratelimits"]
        self.assertEqual([item["name"] for item in limits], ["REPORT_RATE", "REPORT_DUP"])
        self.assertEqual(limits[0]["simple"], {"limit": 12, "period": 60})
        self.assertEqual(limits[1]["simple"], {"limit": 1, "period": 60})
        namespace_ids = [item["namespace_id"] for item in limits]
        self.assertEqual(len(namespace_ids), len(set(namespace_ids)))
        for value in namespace_ids:
            self.assertIsInstance(value, str)
            self.assertTrue(value.isdigit())
            self.assertGreater(int(value), 0)
            self.assertLessEqual(int(value), 4294967295)

    def test_secret_file_patterns_are_ignored(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("cloudflare/*.secrets.json", ignored)
        self.assertIn("cloudflare/*.secrets.env", ignored)


if __name__ == "__main__":
    unittest.main()
