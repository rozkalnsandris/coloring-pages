import hashlib
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "coloring-pages-regenerate-derivatives"
LOADER = importlib.machinery.SourceFileLoader(
    "coloring_pages_regenerate_derivatives",
    str(MODULE_PATH),
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
regen = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(regen)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExistingDerivativeRegenerationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.content = self.root / "content"
        for relative in (
            "originals/farben-zuordnen-001",
            "public/media/farben-zuordnen-001",
            "state/drive-ingest",
        ):
            (self.content / relative).mkdir(parents=True, exist_ok=True)
        (self.content / "state/drive-ingest/.lock").write_bytes(b"")

        self.source = self.content / "originals/farben-zuordnen-001/source.png"
        source_image = Image.new("RGB", (1024, 1536), "white")
        for x in range(250, 400):
            for y in range(500, 650):
                source_image.putpixel((x, y), (255, 32, 64))
        source_image.save(self.source, format="PNG")

        self.media = self.content / "public/media/farben-zuordnen-001"
        thumb = source_image.copy()
        thumb.thumbnail((400, 566), Image.Resampling.LANCZOS)
        thumb.save(self.media / "thumb.webp", format="WEBP", lossless=True, quality=100, method=6)
        preview = source_image.copy()
        preview.thumbnail((1000, 1414), Image.Resampling.LANCZOS)
        preview.save(self.media / "preview.webp", format="WEBP", lossless=True, quality=100, method=6)
        source_image.convert("RGBA").save(self.media / "print.png", format="PNG", optimize=True)

        self.before_entry = {
            "id": "farben-zuordnen-001",
            "title": "Farben zuordnen",
            "character": "",
            "category": "lernen",
            "age": "3-6",
            "difficulty": "easy",
            "language": "de",
            "thumb": "/media/farben-zuordnen-001/thumb.webp",
            "preview": "/media/farben-zuordnen-001/preview.webp",
            "print": "/media/farben-zuordnen-001/print.png",
        }
        self.other_entry = {
            "id": "other-001",
            "title": "Other",
            "thumb": "/media/other-001/thumb.webp",
        }
        (self.content / "public/catalog.json").write_text(
            json.dumps([self.other_entry, self.before_entry], ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

        corrected = {}
        for name in regen.FILES:
            digest = sha256(self.media / name)
            corrected[name] = {
                "size_bytes": (self.media / name).stat().st_size,
                "sha256": digest,
                "versioned_filename": regen.content_addressed_filename(name, digest),
            }

        self.after_entry = dict(self.before_entry)
        self.after_entry["thumb"] = (
            "/media/farben-zuordnen-001/" + corrected["thumb.webp"]["versioned_filename"]
        )
        self.after_entry["preview"] = (
            "/media/farben-zuordnen-001/" + corrected["preview.webp"]["versioned_filename"]
        )
        self.after_entry["print"] = (
            "/media/farben-zuordnen-001/" + corrected["print.png"]["versioned_filename"]
        )

        self.contract = {
            "schema": regen.CONTRACT_SCHEMA,
            "issue": 74,
            "page": {
                "id": "farben-zuordnen-001",
                "source_relative_path": "originals/farben-zuordnen-001/source.png",
                "source_size_bytes": self.source.stat().st_size,
                "source_sha256": sha256(self.source),
                "catalog_entry_before": self.before_entry,
                "catalog_entry_after": self.after_entry,
                "corrected_derivatives": corrected,
            },
            "runtime": {
                "content_root": "/srv/coloring-pages-content",
                "shared_lock": "state/drive-ingest/.lock",
                "regenerator_entrypoint": (
                    "/usr/local/bin/coloring-pages-regenerate-derivatives"
                ),
            },
            "cache_identity": {
                "strategy": "full-sha256-content-addressed-filename",
                "stable_immutable_urls_must_not_be_overwritten": True,
                "catalog_is_switch_point": True,
            },
            "mutation": {
                "allowed_new_targets": [
                    "public/media/farben-zuordnen-001/"
                    + corrected[name]["versioned_filename"]
                    for name in regen.FILES
                ],
                "stable_media_must_remain_unchanged": [
                    f"public/media/farben-zuordnen-001/{name}"
                    for name in regen.FILES
                ],
                "catalog_target": "public/catalog.json",
                "catalog_mutation_scope": list(regen.MEDIA_FIELDS),
                "forbidden_targets": [
                    "originals/farben-zuordnen-001/source.png",
                ],
                "publish_order": [
                    "write-content-addressed-media-exclusively",
                    "fsync-media-directory",
                    "atomically-switch-catalog-entry-media-fields",
                ],
            },
            "failure": {
                "retry": False,
                "rollback": False,
                "cleanup": False,
                "alternate_mutation_path": False,
                "after_first_persistent_write": "STOP",
            },
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def test_check_has_no_persistent_mutation(self):
        stable_before = {
            name: (self.media / name).read_bytes()
            for name in regen.FILES
        }
        catalog_before = (self.content / "public/catalog.json").read_bytes()
        source_before = self.source.read_bytes()

        result = regen.execute(self.content, self.contract, apply=False)

        self.assertEqual(self.source.read_bytes(), source_before)
        self.assertEqual(
            (self.content / "public/catalog.json").read_bytes(),
            catalog_before,
        )
        for name in regen.FILES:
            self.assertEqual((self.media / name).read_bytes(), stable_before[name])
            self.assertFalse((self.media / result[name]).exists())

    def test_apply_publishes_new_cache_identity_and_preserves_stable_files(self):
        stable_before = {
            name: (self.media / name).read_bytes()
            for name in regen.FILES
        }
        source_before = self.source.read_bytes()

        result = regen.execute(self.content, self.contract, apply=True)

        self.assertEqual(self.source.read_bytes(), source_before)
        for name in regen.FILES:
            self.assertEqual((self.media / name).read_bytes(), stable_before[name])
            versioned = self.media / result[name]
            self.assertEqual(versioned.read_bytes(), stable_before[name])
            self.assertEqual(
                versioned.name,
                regen.content_addressed_filename(name, sha256(self.media / name)),
            )

        catalog = json.loads(
            (self.content / "public/catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog[0], self.other_entry)
        self.assertEqual(catalog[1], self.after_entry)
        for key, value in self.before_entry.items():
            if key not in regen.MEDIA_FIELDS:
                self.assertEqual(catalog[1][key], value)

    def test_baseline_drift_fails_before_first_write(self):
        (self.media / "thumb.webp").write_bytes(b"drift")

        with self.assertRaisesRegex(
            regen.RegenerationError,
            "corrected derivative size drifted",
        ):
            regen.execute(self.content, self.contract, apply=True)

        for item in self.contract["page"]["corrected_derivatives"].values():
            self.assertFalse((self.media / item["versioned_filename"]).exists())

    def test_repository_contract_uses_full_sha_content_addressed_urls(self):
        contract = json.loads(
            (ROOT / "deploy/existing-derivative-regeneration-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["issue"], 74)
        self.assertEqual(
            contract["cache_identity"]["strategy"],
            "full-sha256-content-addressed-filename",
        )
        self.assertTrue(
            contract["cache_identity"]["stable_immutable_urls_must_not_be_overwritten"]
        )
        self.assertEqual(
            contract["mutation"]["catalog_mutation_scope"],
            ["thumb", "preview", "print"],
        )
        for name, item in contract["page"]["corrected_derivatives"].items():
            self.assertEqual(
                item["versioned_filename"],
                regen.content_addressed_filename(name, item["sha256"]),
            )
            expected_url = (
                f"/media/farben-zuordnen-001/{item['versioned_filename']}"
            )
            field = name.split(".")[0]
            self.assertEqual(
                contract["page"]["catalog_entry_after"][field],
                expected_url,
            )


if __name__ == "__main__":
    unittest.main()
