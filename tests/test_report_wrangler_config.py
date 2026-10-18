#!/usr/bin/env python3
"""Offline validation for the minimal report Worker Wrangler config (#264)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "cloudflare" / "wrangler.report.json"
WORKER = ROOT / "cloudflare" / "report-worker.mjs"
EXPECTED_WORKER_SHA256 = "0ce800727794b863bf9b82609d59e519c913ba24cf3fe034dd67a96fea9cab19"

ROUTES = [
    {"pattern": "ausmalwiese.de/api/report", "zone_name": "ausmalwiese.de"},
    {"pattern": "www.ausmalwiese.de/api/report", "zone_name": "ausmalwiese.de"},
]
EMAIL_BINDING = [
    {"name": "EMAIL", "destination_address": "INFO@ausmalwiese.de"},
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
                "send_email",
            },
        )
        self.assertEqual(self.config["name"], "coloring-pages-report-v1")
        self.assertEqual(self.config["main"], "./report-worker.mjs")
        self.assertEqual(self.config["compatibility_date"], "2026-10-18")
        self.assertIs(self.config["workers_dev"], False)
        self.assertIs(self.config["preview_urls"], False)
        self.assertIs(self.config["no_bundle"], True)
        for forbidden in ("vars", "secrets", "ratelimits", "account_id", "zone_id"):
            self.assertNotIn(forbidden, self.config)

    def test_exact_worker_source_is_pinned(self):
        raw = WORKER.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_WORKER_SHA256)
        text = raw.decode("utf-8")
        self.assertIn('"/api/report"', text)
        self.assertIn("env.EMAIL.send", text)
        for forbidden in ("BREVO", "TURNSTILE", "REPORT_RATE", "REPORT_DUP", "/api/report/config"):
            self.assertNotIn(forbidden, text)

    def test_only_two_narrow_report_routes(self):
        self.assertEqual(self.config["routes"], ROUTES)
        patterns = [route["pattern"] for route in self.config["routes"]]
        self.assertEqual(len(patterns), len(set(patterns)))
        for pattern in patterns:
            self.assertNotIn("*", pattern)
            self.assertNotIn("?", pattern)
            self.assertNotIn("#", pattern)
            self.assertNotIn("/api/stats", pattern)
            self.assertTrue(pattern.endswith("/api/report"))

    def test_one_fixed_email_binding_and_no_personal_recipient(self):
        self.assertEqual(self.config["send_email"], EMAIL_BINDING)
        binding = self.config["send_email"][0]
        self.assertEqual(binding["name"], "EMAIL")
        self.assertEqual(binding["destination_address"], "INFO@ausmalwiese.de")
        serialized = json.dumps(self.config, sort_keys=True)
        self.assertNotIn("gmail.com", serialized.lower())
        self.assertNotIn("api-key", serialized.lower())
        self.assertNotIn("secret", serialized.lower())


if __name__ == "__main__":
    unittest.main()
