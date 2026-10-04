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
        image = Image.new("RGB", (1024, 1536), "white")
        for x in range(250, 400):
            for y in range(500, 650):
                image.putpixel((x, y), (255, 32, 64))
        image.save(self.source, format="PNG")

        self.entry = {
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
        (self.content / "public/catalog.json").write_text(
            json.dumps([self.entry], ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        media = self.content / "public/media/farben-zuordnen-001"
        Image.new("L", (400, 566), 255).save(
            media / "thumb.webp", format="WEBP", lossless=True
        )
        Image.new("L", (1000, 1414), 255).save(
            media / "preview.webp", format="WEBP", lossless=True
        )
        Image.new("RGBA", (1024, 1536), (255, 255, 255, 255)).save(
            media / "print.png", format="PNG"
        )

        self.contract = {
            "schema": regen.CONTRACT_SCHEMA,
            "issue": 71,
            "page": {
                "id": "farben-zuordnen-001",
                "source_relative_path": "originals/farben-zuordnen-001/source.png",
                "source_size_bytes": self.source.stat().st_size,
                "source_sha256": sha256(self.source),
                "source_must_contain_color": True,
                "catalog_entry": self.entry,
                "current_derivatives": {
                    name: {
                        "size_bytes": (media / name).stat().st_size,
                        "sha256": sha256(media / name),
                    }
                    for name in regen.FILES
                },
            },
            "runtime": {
                "content_root": "/srv/coloring-pages-content",
                "shared_lock": "state/drive-ingest/.lock",
                "regenerator_entrypoint": (
                    "/usr/local/bin/coloring-pages-regenerate-derivatives"
                ),
            },
            "mutation": {
                "allowed_targets": [
                    f"public/media/farben-zuordnen-001/{name}"
                    for name in regen.FILES
                ],
                "forbidden_targets": [
                    "originals/farben-zuordnen-001/source.png",
                    "public/catalog.json",
                ],
                "replace_order": list(regen.FILES),
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
        media = self.content / "public/media/farben-zuordnen-001"
        before = {name: (media / name).read_bytes() for name in regen.FILES}
        source_before = self.source.read_bytes()
        catalog_before = (self.content / "public/catalog.json").read_bytes()

        result = regen.execute(self.content, self.contract, apply=False)

        self.assertEqual(set(result), set(regen.FILES))
        self.assertEqual(self.source.read_bytes(), source_before)
        self.assertEqual(
            (self.content / "public/catalog.json").read_bytes(),
            catalog_before,
        )
        for name in regen.FILES:
            self.assertEqual((media / name).read_bytes(), before[name])

    def test_apply_replaces_only_derivatives(self):
        source_before = self.source.read_bytes()
        catalog_before = (self.content / "public/catalog.json").read_bytes()
        media = self.content / "public/media/farben-zuordnen-001"
        old_hashes = {name: sha256(media / name) for name in regen.FILES}

        result = regen.execute(self.content, self.contract, apply=True)

        self.assertEqual(self.source.read_bytes(), source_before)
        self.assertEqual(
            (self.content / "public/catalog.json").read_bytes(),
            catalog_before,
        )
        for name in regen.FILES:
            self.assertEqual(sha256(media / name), result[name])
            self.assertNotEqual(result[name], old_hashes[name])
            self.assertFalse((media / f".{name}.issue71.tmp").exists())

        with Image.open(media / "preview.webp") as preview:
            self.assertTrue(regen.image_has_color(preview))
        with Image.open(media / "print.png") as print_image:
            self.assertTrue(regen.image_has_color(print_image))
            with Image.open(self.source) as source_image:
                self.assertEqual(
                    print_image.convert("RGBA").tobytes(),
                    source_image.convert("RGBA").tobytes(),
                )

    def test_baseline_drift_fails_before_temp_write(self):
        media = self.content / "public/media/farben-zuordnen-001"
        (media / "thumb.webp").write_bytes(b"drift")

        with self.assertRaisesRegex(
            regen.RegenerationError,
            "derivative size drifted",
        ):
            regen.execute(self.content, self.contract, apply=True)

        for name in regen.FILES:
            self.assertFalse((media / f".{name}.issue71.tmp").exists())

    def test_repository_contract_binds_live_baseline_and_image_wiring(self):
        contract = json.loads(
            (ROOT / "deploy/existing-derivative-regeneration-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["issue"], 71)
        self.assertEqual(contract["page"]["id"], "farben-zuordnen-001")
        self.assertEqual(contract["page"]["source_size_bytes"], 1044537)
        self.assertEqual(
            contract["page"]["source_sha256"],
            "8d8659b73112e879230322b3a356bfa15df3d627b59ab21861c6b8d8b4a5bf24",
        )
        self.assertEqual(
            contract["mutation"]["replace_order"],
            ["thumb.webp", "preview.webp", "print.png"],
        )
        self.assertEqual(
            set(contract["mutation"]["forbidden_targets"]),
            {
                "originals/farben-zuordnen-001/source.png",
                "public/catalog.json",
            },
        )

        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY tools/coloring-pages-regenerate-derivatives "
            "/usr/local/bin/coloring-pages-regenerate-derivatives",
            dockerfile,
        )
        self.assertIn(
            "COPY deploy/existing-derivative-regeneration-v1.json "
            "/usr/local/share/coloring-pages/existing-derivative-regeneration-v1.json",
            dockerfile,
        )


if __name__ == "__main__":
    unittest.main()
