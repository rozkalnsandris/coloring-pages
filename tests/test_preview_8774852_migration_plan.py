"""Contract-only gates for issue #169, dog preview migration PLAN (no LIVE)."""
import importlib.machinery
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "deploy/preview-8774852-migration-plan-v1.json"
IMPORTER = ROOT / "tools/coloring-pages-import"
SOURCE_LOADER = importlib.machinery.SourceFileLoader("preview_plan_importer", str(IMPORTER))
SPEC = importlib.util.spec_from_loader(SOURCE_LOADER.name, SOURCE_LOADER)
importer = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(importer)

HEX = re.compile(r"^[0-9a-f]{64}$")


class PreviewMigrationPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_scope_and_immutable_source_baseline(self):
        p = self.plan
        self.assertEqual(p["schema"], "rozkalns.coloring-pages.single-preview-migration-plan.v1")
        self.assertEqual(p["status"], "SOURCE_PLAN_ONLY_NOT_LIVE_AUTHORIZED")
        self.assertEqual((p["issue"], p["page_id"]), (169, "8774852"))
        self.assertEqual(p["scope"], "preview-only-single-existing-activity")
        baseline = p["baseline"]
        self.assertEqual(baseline["content_root"], "/srv/coloring-pages-content")
        self.assertEqual(baseline["shared_lock"], "state/drive-ingest/.lock")
        self.assertEqual(baseline["catalog"]["entry_count"], 201)
        self.assertEqual(baseline["catalog"]["entry"]["id"], p["page_id"])
        self.assertEqual(
            baseline["catalog"]["entry"]["preview"], "/media/8774852/preview.webp"
        )
        self.assertNotIn("pages", baseline["catalog"]["entry"])
        self.assertEqual(
            (baseline["source"]["width"], baseline["source"]["height"]), (2480, 3508)
        )
        self.assertEqual(baseline["source"]["size_bytes"], 1032144)
        self.assertEqual(
            baseline["source"]["sha256"], baseline["current"]["print"]["sha256"]
        )
        self.assertEqual(
            baseline["source"]["size_bytes"], baseline["current"]["print"]["size_bytes"]
        )
        for info in [baseline["catalog"], baseline["source"], *baseline["current"].values()]:
            self.assertRegex(info["sha256"], HEX)
        self.assertEqual(
            {x["path"] for x in baseline["current"].values()},
            {
                "public/media/8774852/preview.webp",
                "public/media/8774852/thumb.webp",
                "public/media/8774852/print.png",
            },
        )

    def test_candidate_is_not_preapproved_or_published(self):
        p = self.plan
        producer = p["producer"]
        self.assertEqual(
            producer["source_revision"], "337f78988064536250a6094a01563233d81891ff"
        )
        self.assertEqual(
            producer["importer_blob_sha"], "6d95f40112dc0ffae51e29af8508c305cf680f3e"
        )
        self.assertTrue(
            producer["runtime_image"].endswith(
                "@sha256:2a80b56c20c37f4a530059c3e438c6627fd962786e6590dd914e59e86a837ba8"
            )
        )
        c = p["candidate"]
        self.assertEqual(c["source"], "private-approved-source-not-existing-preview")
        self.assertEqual(c["max_width"], importer.PREVIEW_MAX_WIDTH)
        self.assertEqual(c["watermark_text"], importer.PREVIEW_WATERMARK_TEXT)
        self.assertEqual(c["watermark_width_ratio"], importer.PREVIEW_WATERMARK_WIDTH_RATIO)
        self.assertEqual(c["watermark_opacity"], importer.PREVIEW_WATERMARK_OPACITY)
        self.assertEqual(c["watermark_angle_degrees"], importer.PREVIEW_WATERMARK_ANGLE)
        self.assertEqual((c["format"], c["lossless"], c["quality"], c["method"]),
                         ("WEBP", True, 100, 6))
        self.assertEqual(c["filename_template"], "preview-<full-64-hex-sha256>.webp")
        for key in ("candidate_sha256", "candidate_size_bytes",
                    "candidate_filename", "candidate_public_url"):
            self.assertIsNone(c[key])

    def test_only_preview_catalog_switch_and_no_mutation_authority(self):
        p = self.plan
        switch = p["catalog_switch"]
        self.assertEqual(switch["only_field"], "preview")
        self.assertEqual(switch["url_prefix"], "/media/8774852/")
        self.assertEqual(
            set(switch["preserve_exact_fields"]),
            set(p["baseline"]["catalog"]["entry"]) - {"preview"},
        )
        self.assertTrue(switch["require_exact_catalog_bytes_baseline"])
        self.assertTrue(switch["require_unique_page_id"])
        safeguards = p["safeguards"]
        for key in (
            "published_files_immutable", "exclusive_new_target_creation",
            "forbid_symlinks", "preserve_source_thumb_print_exact_bytes",
            "shared_writer_lock_required", "atomic_catalog_switch",
            "read_only_candidate_proof_before_live_authorization",
            "no_drive_upload_or_import", "no_retry_rollback_cleanup",
        ):
            self.assertIs(safeguards[key], True)


if __name__ == "__main__":
    unittest.main()
