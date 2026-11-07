"""Issue #455: source-only legacy-ID migration planning and redirect continuity."""

import hashlib
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "coloring-pages-legacy-id-plan"

LOADER = importlib.machinery.SourceFileLoader("legacy_id_plan", str(TOOL))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)

BASELINE_LEGACY_IDS = [
    "cp-000008", "cp-000007", "cp-000006", "cp-000005", "cp-000004",
    "cp-000003", "cp-000002", "cp-000001",
    "halloween-hexenhut-labyrinth-001", "obst-pflanzen-zuordnen-001",
    "wetter-zuordnen-001", "verkehrsmittel-wege-zuordnen-001",
    "tiere-futter-zuordnen-001", "tiere-lebensraeume-zuordnen-001",
    "weihnachtskugel-muster-001", "kuerbis-gesicht-001", "block-figur-001",
    "farben-zuordnen-001", "halloween-geist-001",
    "halloween-kuerbis-geist-002", "halloween-hexe-001",
    "herbst-kaetzchen-001", "halloween-fledermaus-001", "halloween-001",
    "halloween-kuerbis-001", "figuren-001", "dino-001", "lapsa-003",
    "lapsa-001", "bauarbeiter-hund-001",
]


def entry(activity_id, pages=1):
    root = f"/media/{activity_id}"
    item = {
        "id": activity_id,
        "title": f"Fixture {activity_id}",
        "thumb": f"{root}/thumb.webp",
        "preview": f"{root}/preview.webp",
        "print": f"{root}/print.png",
    }
    if pages > 1:
        item["preview"] = f"{root}/preview-1.webp"
        item["print"] = f"{root}/print-1.png"
        item["pages"] = [
            {"preview": f"{root}/preview-{n}.webp", "print": f"{root}/print-{n}.png"}
            for n in range(1, pages + 1)
        ]
    return item


class LegacyIdPlanTests(unittest.TestCase):
    def catalog(self):
        return [entry("0000000"), entry("9999999"), *map(entry, BASELINE_LEGACY_IDS)]

    def build(self):
        candidates = iter(range(1, 1000))
        with mock.patch.object(MODULE.secrets, "randbelow", side_effect=lambda _: next(candidates)):
            return MODULE.build_plan(self.catalog(), "a" * 64, 30)

    def test_all_30_reviewed_legacy_forms_are_covered_once(self):
        plan = self.build()
        self.assertEqual(plan["schema"], "rozkalns.coloring-pages.legacy-id-migration-plan.v1")
        self.assertEqual(plan["mode"], "DRY_RUN_ONLY")
        self.assertEqual(plan["issue"], 455)
        self.assertEqual(plan["legacy_count"], 30)
        self.assertEqual(
            [item["old_id"] for item in plan["mappings"]],
            BASELINE_LEGACY_IDS,
        )
        new_ids = [item["new_id"] for item in plan["mappings"]]
        self.assertEqual(len(set(new_ids)), 30)
        self.assertTrue(all(len(value) == 7 and value.isdigit() for value in new_ids))
        self.assertFalse(set(new_ids) & {"0000000", "9999999"})
        self.assertEqual(plan["manifest_sha256"], MODULE.manifest_digest(plan))

    def test_collision_is_skipped_and_leading_zero_is_preserved(self):
        catalog = [entry("0000001"), entry("legacy-001")]
        with mock.patch.object(MODULE.secrets, "randbelow", side_effect=[1, 2]):
            plan = MODULE.build_plan(catalog, "b" * 64, 1)
        self.assertEqual(plan["mappings"][0]["new_id"], "0000002")

    def test_multi_page_media_redirects_are_exact_and_do_not_chain(self):
        catalog = [entry("1234567"), entry("legacy-activity", pages=3)]
        with mock.patch.object(MODULE.secrets, "randbelow", return_value=7654321):
            plan = MODULE.build_plan(catalog, "c" * 64, 1)
        mapping = plan["mappings"][0]
        self.assertEqual(mapping["new_id"], "7654321")
        sources = [pair["from"] for pair in mapping["media"]]
        targets = [pair["to"] for pair in mapping["media"]]
        self.assertIn("/media/legacy-activity/preview-3.webp", sources)
        self.assertIn("/media/7654321/preview-3.webp", targets)
        self.assertTrue(all(source.startswith("/media/legacy-activity/") for source in sources))
        self.assertTrue(all(target.startswith("/media/7654321/") for target in targets))
        self.assertFalse(set(targets) & set(sources))

    def test_verify_rejects_tamper_stale_mapping_collision_and_missing_id(self):
        plan = self.build()
        cases = []

        tampered = json.loads(json.dumps(plan))
        tampered["mappings"][0]["new_id"] = "1234567"
        cases.append(tampered)

        collision = json.loads(json.dumps(plan))
        collision["mappings"][0]["new_id"] = "9999999"
        collision["manifest_sha256"] = MODULE.manifest_digest(collision)
        cases.append(collision)

        missing = json.loads(json.dumps(plan))
        missing["mappings"].pop()
        missing["legacy_count"] -= 1
        missing["manifest_sha256"] = MODULE.manifest_digest(missing)
        cases.append(missing)

        for candidate in cases:
            with self.subTest(candidate=candidate["legacy_count"]):
                with self.assertRaises(MODULE.PlanError):
                    MODULE.verify_manifest(candidate, self.catalog(), "a" * 64, 30)

    def test_manifest_is_bound_to_exact_catalog_snapshot(self):
        plan = self.build()
        with self.assertRaisesRegex(MODULE.PlanError, "another catalogue"):
            MODULE.verify_manifest(plan, self.catalog(), "b" * 64, 30)

    def test_unsafe_media_or_legacy_ids_fail_closed(self):
        bad_media = entry("legacy-001")
        bad_media["thumb"] = "/media/other/thumb.webp"
        with self.assertRaisesRegex(MODULE.PlanError, "media path is not ID-bound"):
            MODULE.build_plan([bad_media], "a" * 64, 1)

        with self.assertRaisesRegex(MODULE.PlanError, "unsafe activity ID"):
            MODULE.build_plan([entry("Bad ID")], "a" * 64, 1)

    def test_nginx_candidate_is_exact_quoted_and_fallthrough_by_default(self):
        plan = self.build()
        snippet = MODULE.render_nginx_snippet(plan)
        self.assertIn('map $arg_id $legacy_activity_redirect_id {', snippet)
        self.assertIn('map $uri $legacy_media_redirect_uri {', snippet)
        self.assertEqual(snippet.count('default "";'), 2)
        for item in plan["mappings"]:
            self.assertIn(f'"{item["old_id"]}" "{item["new_id"]}";', snippet)
        self.assertNotIn("rewrite ", snippet)
        self.assertNotIn("proxy_pass", snippet)
        self.assertIn("308", snippet)

    def test_cli_requires_exact_catalog_hash_and_emits_no_files(self):
        catalog = [entry("1234567"), entry("legacy-001")]
        raw = (json.dumps(catalog, ensure_ascii=False) + "\n").encode()
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "catalog.json"
            path.write_bytes(raw)
            before = sorted(p.name for p in root.iterdir())
            result = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    "--catalog", str(path),
                    "--expected-catalog-sha256", digest,
                    "--expected-legacy-count", "1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            after = sorted(p.name for p in root.iterdir())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, after)
        document = json.loads(result.stdout)
        self.assertEqual(document["catalog_sha256"], digest)
        self.assertEqual(document["legacy_count"], 1)

    def test_cli_stale_hash_and_wrong_legacy_count_fail_without_plan(self):
        catalog = [entry("legacy-001")]
        raw = json.dumps(catalog).encode()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.json"
            path.write_bytes(raw)
            stale = subprocess.run(
                [
                    sys.executable, str(TOOL), "--catalog", str(path),
                    "--expected-catalog-sha256", "0" * 64,
                    "--expected-legacy-count", "1",
                ],
                capture_output=True, text=True, check=False,
            )
            wrong_count = subprocess.run(
                [
                    sys.executable, str(TOOL), "--catalog", str(path),
                    "--expected-catalog-sha256", hashlib.sha256(raw).hexdigest(),
                    "--expected-legacy-count", "30",
                ],
                capture_output=True, text=True, check=False,
            )
        for result in (stale, wrong_count):
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("LEGACY_ID_PLAN_ERROR:", result.stderr)


if __name__ == "__main__":
    unittest.main()
