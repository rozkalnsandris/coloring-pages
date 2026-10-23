"""Offline adversarial tests for the no-LIVE Stats Worker deploy guard."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import stats_worker_deploy_guard as guard  # noqa: E402


def inventory(version="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"):
    return {
        "schema": "ausmalwiese.stats-worker-sanitized-inventory.v1",
        "worker": guard.WORKER,
        "environment": "production",
        "version": version,
        "traffic_percent": 100,
        "routes": sorted(guard.ROUTES),
        "bindings": [
            {
                "name": name,
                "type": kind,
                "fingerprint": None if kind == "secret_text" else "a" * 64,
            }
            for name, kind in sorted(guard.BINDINGS.items())
        ],
    }


class StatsWorkerSourceGuardTests(unittest.TestCase):
    def test_current_privacy_worker_matches_exact_deploy_contract(self):
        result = guard.check_source_contract(ROOT)
        self.assertEqual(result["blob"], guard.BLOB)
        self.assertEqual(result["result"], "SOURCE_CONTRACT_OK_NOT_LIVE_PROOF")

    def test_offline_cli_only(self):
        source = (ROOT / "tools/stats_worker_deploy_guard.py").read_text(
            encoding="utf-8"
        )
        for forbidden in (
            "import subprocess", "import requests", "urllib.request",
            "os.system(", "subprocess.run(", "def deploy(",
        ):
            self.assertNotIn(forbidden, source)

    def test_exact_deploy_blob_is_current_privacy_worker(self):
        raw = (ROOT / guard.SOURCE_PATH).read_bytes()
        self.assertEqual(guard.git_blob_sha1(raw), guard.BLOB)
        source = raw.decode("utf-8")
        self.assertIn("legacy_personalized_api_retired", source)
        self.assertIn("/api/stats/print-aggregate", source)

    def _copy(self, location):
        for file in (
            guard.SOURCE_PATH,
            guard.CONTRACT_PATH,
            guard.CONFIG_PATH,
            guard.ADDITIVE_MIGRATION_PATH,
            guard.CLEANUP_MIGRATION_PATH,
        ):
            target = location / file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / file).read_bytes())

    def test_wrong_worker_bytes_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy(root)
            with (root / guard.SOURCE_PATH).open("ab") as handle:
                handle.write(b"\n// unreviewed\n")
            with self.assertRaisesRegex(guard.GuardFailure, "WORKER_BLOB_DRIFT"):
                guard.check_source_contract(root)

    def test_each_pinned_artifact_drift_fails(self):
        cases = (
            (guard.CONFIG_PATH, "CONFIG_BLOB_DRIFT"),
            (guard.ADDITIVE_MIGRATION_PATH, "ADDITIVE_MIGRATION_BLOB_DRIFT"),
            (guard.CLEANUP_MIGRATION_PATH, "CLEANUP_MIGRATION_BLOB_DRIFT"),
        )
        for rel, error in cases:
            with self.subTest(rel=rel), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._copy(root)
                with (root / rel).open("ab") as handle:
                    handle.write(b"\n-- unreviewed drift\n")
                with self.assertRaisesRegex(guard.GuardFailure, error):
                    guard.check_source_contract(root)

    def test_live_sequence_is_exact_and_separately_gated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy(root)
            path = root / guard.CONTRACT_PATH
            obj = json.loads(path.read_text())
            obj["live_sequence"][0], obj["live_sequence"][1] = (
                obj["live_sequence"][1],
                obj["live_sequence"][0],
            )
            path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(
                guard.GuardFailure, "CONTRACT_LIVE_SEQUENCE"
            ):
                guard.check_source_contract(root)

    def test_one_extra_route_in_contract_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy(root)
            path = root / guard.CONTRACT_PATH
            obj = json.loads(path.read_text())
            obj["routes"].append("other.example/*")
            path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(guard.GuardFailure, "CONTRACT_ROUTES"):
                guard.check_source_contract(root)

    def test_binding_missing_in_contract_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy(root)
            path = root / guard.CONTRACT_PATH
            obj = json.loads(path.read_text())
            del obj["bindings"]["RATE_LIMITER"]
            path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(guard.GuardFailure, "CONTRACT_BINDINGS"):
                guard.check_source_contract(root)

    def test_inventory_accepts_exact_seven_and_four(self):
        result = guard.check_sanitized_inventory(inventory())
        self.assertEqual(set(result["fingerprints"]), set(guard.BINDINGS))

    def test_missing_secret_rejected(self):
        obj = inventory()
        obj["bindings"] = [
            x for x in obj["bindings"] if x["name"] != "VISITOR_HMAC_KEY"
        ]
        with self.assertRaises(guard.GuardFailure):
            guard.check_sanitized_inventory(obj)

    def test_extra_binding_rejected(self):
        obj = inventory()
        obj["bindings"].append({
            "name": "DANGEROUS",
            "type": "secret_text",
            "fingerprint": None,
        })
        with self.assertRaises(guard.GuardFailure):
            guard.check_sanitized_inventory(obj)

    def test_duplicate_binding_rejected(self):
        obj = inventory()
        obj["bindings"][-1] = copy.deepcopy(obj["bindings"][0])
        with self.assertRaises(guard.GuardFailure):
            guard.check_sanitized_inventory(obj)

    def test_binding_type_drift_rejected(self):
        obj = inventory()
        obj["bindings"][0]["type"] = (
            "plain_text"
            if obj["bindings"][0]["type"] != "plain_text"
            else "rate_limiter"
        )
        with self.assertRaises(guard.GuardFailure):
            guard.check_sanitized_inventory(obj)

    def test_reject_secret_fingerprint_or_value(self):
        obj = inventory()
        secret = next(
            x for x in obj["bindings"] if x["type"] == "secret_text"
        )
        secret["fingerprint"] = "a" * 64
        with self.assertRaisesRegex(
            guard.GuardFailure, "INVENTORY_SECRET_EXPOSURE"
        ):
            guard.check_sanitized_inventory(obj)
        secret["fingerprint"] = None
        secret["value"] = "forbidden-even-in-fixture"
        with self.assertRaisesRegex(
            guard.GuardFailure, "INVENTORY_BINDING_FIELDS"
        ):
            guard.check_sanitized_inventory(obj)

    def test_untrusted_inventory_extra_keys_fail(self):
        obj = inventory()
        obj["account_id"] = "never accept output"
        with self.assertRaisesRegex(guard.GuardFailure, "INVENTORY_KEYS"):
            guard.check_sanitized_inventory(obj)

    def test_wrong_or_duplicated_route_rejected(self):
        obj = inventory()
        obj["routes"][-1] = obj["routes"][0]
        with self.assertRaisesRegex(guard.GuardFailure, "INVENTORY_ROUTES"):
            guard.check_sanitized_inventory(obj)
        obj["routes"][-1] = "elsewhere.example/*"
        with self.assertRaisesRegex(guard.GuardFailure, "INVENTORY_ROUTES"):
            guard.check_sanitized_inventory(obj)

    def test_traffic_split_rejected(self):
        for percent in (0, 99, True, "100"):
            obj = inventory()
            obj["traffic_percent"] = percent
            with self.assertRaises(guard.GuardFailure):
                guard.check_sanitized_inventory(obj)

    def test_version_and_worker_mismatch_rejected(self):
        for key, value in (
            ("worker", "other"),
            ("environment", "preview"),
            ("version", "e47f145f"),
        ):
            obj = inventory()
            obj[key] = value
            with self.assertRaises(guard.GuardFailure):
                guard.check_sanitized_inventory(obj)

    def test_compare_success_but_not_live_authorization(self):
        before = inventory()
        after = inventory("aaaaaaaa-bbbb-cccc-dddd-ffffffffffff")
        self.assertIsNone(guard.compare_sanitized_inventories(before, after))

    def test_same_version_or_changed_db_target_fails(self):
        before = inventory()
        with self.assertRaisesRegex(guard.GuardFailure, "VERSION_NOT_CHANGED"):
            guard.compare_sanitized_inventories(before, copy.deepcopy(before))
        after = inventory("aaaaaaaa-bbbb-cccc-dddd-ffffffffffff")
        next(
            x for x in after["bindings"] if x["name"] == "DB"
        )["fingerprint"] = "b" * 64
        with self.assertRaisesRegex(
            guard.GuardFailure, "BINDING_VALUE_OR_TARGET_DRIFT"
        ):
            guard.compare_sanitized_inventories(before, after)


if __name__ == "__main__":
    unittest.main()
