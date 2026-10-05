import hashlib
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "coloring-pages-migrate-legacy-print-scale"
LOADER = importlib.machinery.SourceFileLoader(
    "coloring_pages_migrate_legacy_print_scale",
    str(MODULE_PATH),
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
migration = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(migration)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LegacyPrintScaleMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.content = Path(self.tempdir.name) / "content"
        for relative in (
            "originals/single-001",
            "originals/multi-001",
            "public/media/single-001",
            "public/media/multi-001",
            "state/drive-ingest",
        ):
            (self.content / relative).mkdir(parents=True, exist_ok=True)
        (self.content / "state/drive-ingest/.lock").write_bytes(b"")

        single_source = self.content / "originals/single-001/source.png"
        self._source(single_source, (1024, 1536), (0, 0, 0))
        multi_1 = self.content / "originals/multi-001/source-1.png"
        multi_2 = self.content / "originals/multi-001/source-2.png"
        self._source(multi_1, (1055, 1491), (20, 20, 20))
        self._source(multi_2, (1055, 1491), (40, 40, 40))

        single_print = self.content / "public/media/single-001/print.png"
        multi_print_1 = self.content / "public/media/multi-001/print-1.png"
        multi_print_2 = self.content / "public/media/multi-001/print-2.png"
        Image.open(single_source).save(single_print, format="PNG")
        Image.open(multi_1).save(multi_print_1, format="PNG")
        Image.open(multi_2).save(multi_print_2, format="PNG")

        self.single_entry = {
            "id": "single-001",
            "title": "Single",
            "thumb": "/media/single-001/thumb.webp",
            "preview": "/media/single-001/preview.webp",
            "print": "/media/single-001/print.png",
        }
        self.multi_entry = {
            "id": "multi-001",
            "title": "Multi",
            "thumb": "/media/multi-001/thumb.webp",
            "preview": "/media/multi-001/preview-1.webp",
            "print": "/media/multi-001/print-1.png",
            "pages": [
                {
                    "preview": "/media/multi-001/preview-1.webp",
                    "print": "/media/multi-001/print-1.png",
                },
                {
                    "preview": "/media/multi-001/preview-2.webp",
                    "print": "/media/multi-001/print-2.png",
                },
            ],
        }
        self.other_entry = {"id": "other-001", "title": "Other", "print": "/x.png"}
        self.catalog_path = self.content / "public/catalog.json"
        self.catalog_path.write_text(
            json.dumps(
                [self.other_entry, self.single_entry, self.multi_entry],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(self.catalog_path, 0o644)

        self.contract = {
            "runtime": {"shared_lock": "state/drive-ingest/.lock"},
            "targets": [
                self._target(
                    "single-001",
                    1,
                    "source.png",
                    single_source,
                    "/media/single-001/print.png",
                ),
                self._target(
                    "multi-001",
                    1,
                    "source-1.png",
                    multi_1,
                    "/media/multi-001/print-1.png",
                ),
                self._target(
                    "multi-001",
                    2,
                    "source-2.png",
                    multi_2,
                    "/media/multi-001/print-2.png",
                ),
            ],
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def _source(self, path: Path, size: tuple[int, int], ink: tuple[int, int, int]):
        image = Image.new("RGB", size, "white")
        for x in range(size[0] // 3, size[0] // 3 + 30):
            for y in range(size[1] // 3, size[1] // 3 + 30):
                image.putpixel((x, y), ink)
        image.save(path, format="PNG")

    def _target(
        self,
        page_id: str,
        page_index: int,
        source_file: str,
        source: Path,
        current_print: str,
    ):
        return {
            "id": page_id,
            "page_index": page_index,
            "source_file": source_file,
            "source_sha256": sha256(source),
            "source_size_bytes": source.stat().st_size,
            "current_print": current_print,
        }

    def test_plan_is_read_only_and_generates_exact_a4_outputs(self):
        catalog_before = self.catalog_path.read_bytes()
        source_before = {
            target["source_file"]: (
                self.content / "originals" / target["id"] / target["source_file"]
            ).read_bytes()
            for target in self.contract["targets"]
        }

        plan, bodies, _ = migration.build_plan(self.content, self.contract)

        self.assertEqual(plan["target_pages"], 3)
        self.assertEqual(plan["target_activities"], 2)
        self.assertEqual(self.catalog_path.read_bytes(), catalog_before)
        for target in self.contract["targets"]:
            self.assertEqual(
                (
                    self.content
                    / "originals"
                    / target["id"]
                    / target["source_file"]
                ).read_bytes(),
                source_before[target["source_file"]],
            )
        for item in plan["targets"]:
            self.assertEqual((item["width"], item["height"]), (2480, 3508))
            self.assertAlmostEqual(item["dpi_x"], 300.0, delta=1.0)
            self.assertAlmostEqual(item["dpi_y"], 300.0, delta=1.0)
            self.assertIn("-a4-", item["new_print"])
            self.assertEqual(
                hashlib.sha256(
                    bodies[(item["id"], item["page_index"])]
                ).hexdigest(),
                item["new_print_sha256"],
            )
            self.assertFalse(
                migration.public_path(self.content, item["new_print"]).exists()
            )

    def test_apply_preserves_sources_old_media_order_and_unrelated_entry(self):
        plan, _, _ = migration.build_plan(self.content, self.contract)
        expected_plan_sha = migration.plan_sha256(plan)
        source_before = {
            (target["id"], target["source_file"]): (
                self.content / "originals" / target["id"] / target["source_file"]
            ).read_bytes()
            for target in self.contract["targets"]
        }
        old_print_before = {
            item["current_print"]: migration.public_path(
                self.content, item["current_print"]
            ).read_bytes()
            for item in plan["targets"]
        }

        applied = migration.execute_apply(
            self.content,
            self.contract,
            expected_plan_sha,
        )

        self.assertEqual(migration.plan_sha256(applied), expected_plan_sha)
        final = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in final], ["other-001", "single-001", "multi-001"])
        self.assertEqual(final[0], self.other_entry)
        self.assertEqual(final[1]["thumb"], self.single_entry["thumb"])
        self.assertEqual(final[1]["preview"], self.single_entry["preview"])
        self.assertIn("-a4-", final[1]["print"])
        self.assertIn("-a4-", final[2]["print"])
        self.assertEqual(final[2]["print"], final[2]["pages"][0]["print"])
        self.assertIn("-a4-", final[2]["pages"][1]["print"])
        self.assertEqual(self.catalog_path.stat().st_mode & 0o777, 0o644)

        for key, body in source_before.items():
            self.assertEqual(
                (self.content / "originals" / key[0] / key[1]).read_bytes(),
                body,
            )
        for url, body in old_print_before.items():
            self.assertEqual(migration.public_path(self.content, url).read_bytes(), body)
        for item in applied["targets"]:
            new_path = migration.public_path(self.content, item["new_print"])
            self.assertTrue(new_path.is_file())
            self.assertEqual(sha256(new_path), item["new_print_sha256"])

    def test_source_drift_fails_before_any_new_print_write(self):
        source = self.content / "originals/single-001/source.png"
        source.write_bytes(source.read_bytes() + b"drift")
        with self.assertRaisesRegex(migration.MigrationError, "source size drifted"):
            migration.build_plan(self.content, self.contract)
        self.assertFalse(any(self.content.glob("public/media/**/*-a4-*.png")))

    def test_owner_bound_plan_rejects_target_catalog_drift_before_write(self):
        plan, _, _ = migration.build_plan(self.content, self.contract)
        expected = migration.plan_sha256(plan)
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        catalog[1]["print"] = "/media/single-001/other.png"
        self.catalog_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(migration.MigrationError, "current print URL drifted"):
            migration.execute_apply(self.content, self.contract, expected)
        self.assertFalse(any(self.content.glob("public/media/**/*-a4-*.png")))

    def test_repository_contract_is_bounded_to_exact_16_historical_pages(self):
        contract = json.loads(
            (ROOT / "deploy/legacy-print-scale-migration-v1.json").read_text(
                encoding="utf-8"
            )
        )
        migration.validate_contract(contract)
        self.assertEqual(len(contract["targets"]), 16)
        self.assertEqual(
            len({target["id"] for target in contract["targets"]}),
            15,
        )
        self.assertTrue(contract["mutation"]["private_sources_immutable"])
        self.assertTrue(contract["mutation"]["existing_media_immutable"])
        self.assertFalse(contract["mutation"]["delete_allowed"])
        self.assertFalse(contract["mutation"]["overwrite_allowed"])


if __name__ == "__main__":
    unittest.main()
