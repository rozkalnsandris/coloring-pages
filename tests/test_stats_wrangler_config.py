"""Offline contract for the reviewed Stats Worker Wrangler config."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "cloudflare" / "wrangler.stats-worker.jsonc"
WORKER = ROOT / "cloudflare" / "stats-worker.js"
EXPECTED_WORKER_BLOB = "dd5a2859d55b9ef2d9fb9a9d8bf0a535d25a5ba4"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


class StatsWranglerConfigTests(unittest.TestCase):
    def load(self):
        return json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_exact_top_level_shape(self):
        cfg = self.load()
        self.assertEqual(
            set(cfg),
            {
                "name",
                "main",
                "compatibility_date",
                "workers_dev",
                "keep_vars",
                "d1_databases",
                "ratelimits",
                "secrets",
            },
        )
        self.assertEqual(cfg["name"], "coloring-pages-stats-v1")
        self.assertEqual(cfg["main"], "cloudflare/stats-worker.js")
        self.assertEqual(cfg["compatibility_date"], "2026-10-06")
        self.assertIs(cfg["workers_dev"], False)
        self.assertIs(cfg["keep_vars"], True)
        for forbidden in ("routes", "route", "triggers", "vars", "account_id"):
            self.assertNotIn(forbidden, cfg)

    def test_exact_d1_binding(self):
        self.assertEqual(
            self.load()["d1_databases"],
            [
                {
                    "binding": "DB",
                    "database_name": "coloring-pages-stats-v1",
                    "database_id": "f8ac8f1d-a230-4bc4-af13-557c1b91b273",
                }
            ],
        )

    def test_exact_rate_limiter_binding(self):
        self.assertEqual(
            self.load()["ratelimits"],
            [
                {
                    "name": "RATE_LIMITER",
                    "namespace_id": "1152026106",
                    "simple": {"limit": 100, "period": 60},
                }
            ],
        )

    def test_secret_names_only(self):
        self.assertEqual(
            self.load()["secrets"],
            {"required": ["CF_ANALYTICS_API_TOKEN", "VISITOR_HMAC_KEY"]},
        )

    def test_privacy_draft_does_not_repin_reviewed_production_blob(self):
        # PR #183 intentionally changes stats-worker.js for the source-only
        # privacy redesign. The reviewed Production Wrangler config remains
        # bound to the older exact blob until a separate post-#182 deployment
        # contract and LIVE authorization exist.
        self.assertNotEqual(git_blob_sha1(WORKER.read_bytes()), EXPECTED_WORKER_BLOB)


if __name__ == "__main__":
    unittest.main()
