import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "coloring-pages-migrate-png-only"
LOADER = importlib.machinery.SourceFileLoader("coloring_pages_migrate_png_only", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
migration = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(migration)


class LegacyPngMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.content = self.root / "content"
        for relative in ("originals", "public/media", "state/drive-ingest"):
            (self.content / relative).mkdir(parents=True, exist_ok=True)
        (self.content / "state/drive-ingest/.lock").write_bytes(b"")
        self.ids = ["alpha-001", "beta-001"]
        self.contract = {
            "schema": migration.CONTRACT_SCHEMA,
            "issue": 65,
            "expected_catalog_count": 2,
            "affected_ids": self.ids,
        }
        self.contract_path = self.root / "contract.json"
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        catalog = []
        for page_id in self.ids:
            original_dir = self.content / "originals" / page_id
            media_dir = self.content / "public/media" / page_id
            original_dir.mkdir()
            media_dir.mkdir()
            source = Image.new("L", (1024, 1536), 255)
            source.putpixel((200, 300), 0)
            source.save(original_dir / "source.png", format="PNG")
            (media_dir / "source.png").write_bytes((original_dir / "source.png").read_bytes())
            Image.new("L", (400, 600), 255).save(media_dir / "thumb.webp", format="WEBP")
            Image.new("L", (1000, 1500), 255).save(media_dir / "preview.webp", format="WEBP")
            (media_dir / "print.pdf").write_bytes(b"legacy-pdf")
            root = f"/media/{page_id}"
            catalog.append({
                "id": page_id,
                "title": page_id,
                "category": "tiere",
                "thumb": f"{root}/thumb.webp",
                "preview": f"{root}/preview.webp",
                "print": f"{root}/source.png",
                "pdf": f"{root}/print.pdf",
            })
        (self.content / "public/catalog.json").write_text(json.dumps(catalog), encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_check_is_read_only(self):
        before = (self.content / "public/catalog.json").read_bytes()
        catalog, hashes = migration.validate_legacy_state(self.content, self.contract)
        self.assertEqual(len(catalog), 2)
        self.assertEqual(set(hashes), set(self.ids))
        self.assertEqual((self.content / "public/catalog.json").read_bytes(), before)
        for page_id in self.ids:
            media = self.content / "public/media" / page_id
            self.assertFalse((media / "print.png").exists())
            self.assertTrue((media / "source.png").is_file())
            self.assertTrue((media / "print.pdf").is_file())

    def test_apply_migrates_catalog_and_media_without_touching_originals(self):
        catalog, hashes = migration.validate_legacy_state(self.content, self.contract)
        migration.apply_migration(self.content, self.contract, catalog, hashes)
        after = json.loads((self.content / "public/catalog.json").read_text(encoding="utf-8"))
        self.assertEqual({item["id"] for item in after}, set(self.ids))
        for entry in after:
            self.assertNotIn("pdf", entry)
            self.assertEqual(entry["print"], f"/media/{entry['id']}/print.png")
        self.assertEqual((self.content / "public/catalog.json").stat().st_mode & 0o777, 0o644)
        for page_id in self.ids:
            media = self.content / "public/media" / page_id
            self.assertTrue((media / "thumb.webp").is_file())
            self.assertTrue((media / "preview.webp").is_file())
            self.assertTrue((media / "print.png").is_file())
            self.assertEqual((media / "print.png").stat().st_mode & 0o777, 0o644)
            self.assertFalse((media / "source.png").exists())
            self.assertFalse((media / "print.pdf").exists())
            self.assertEqual(migration.sha256_file(self.content / "originals" / page_id / "source.png"), hashes[page_id])

    def test_unexpected_catalog_id_fails_before_mutation(self):
        catalog_path = self.content / "public/catalog.json"
        before = catalog_path.read_bytes()
        data = json.loads(before)
        data[0]["id"] = "unexpected-001"
        catalog_path.write_text(json.dumps(data), encoding="utf-8")
        modified = catalog_path.read_bytes()
        with self.assertRaisesRegex(migration.MigrationError, "IDs do not match"):
            migration.validate_legacy_state(self.content, self.contract)
        self.assertEqual(catalog_path.read_bytes(), modified)
        for page_id in self.ids:
            self.assertFalse((self.content / "public/media" / page_id / "print.png").exists())

    def test_public_private_source_mismatch_fails_before_mutation(self):
        media = self.content / "public/media/alpha-001"
        media.joinpath("source.png").write_bytes(b"different")
        with self.assertRaisesRegex(migration.MigrationError, "hash mismatch"):
            migration.validate_legacy_state(self.content, self.contract)
        self.assertFalse((media / "print.png").exists())

    def test_repository_contract_pins_exact_13_ids_and_runtime_boundary(self):
        contract = json.loads((ROOT / "deploy/legacy-png-migration-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], migration.CONTRACT_SCHEMA)
        self.assertEqual(contract["issue"], 65)
        self.assertEqual(contract["expected_catalog_count"], 13)
        self.assertEqual(
            contract["affected_ids"],
            [
                "bauarbeiter-hund-001",
                "dino-001",
                "farben-zuordnen-001",
                "figuren-001",
                "halloween-001",
                "halloween-fledermaus-001",
                "halloween-geist-001",
                "halloween-hexe-001",
                "halloween-kuerbis-001",
                "halloween-kuerbis-geist-002",
                "herbst-kaetzchen-001",
                "lapsa-001",
                "lapsa-003",
            ],
        )
        self.assertEqual(len(set(contract["affected_ids"])), 13)
        self.assertEqual(contract["runtime"]["network"], "none")
        self.assertTrue(contract["runtime"]["read_only_root"])
        self.assertEqual(contract["runtime"]["cap_drop"], ["ALL"])
        self.assertTrue(contract["runtime"]["no_new_privileges"])
        self.assertEqual(contract["runtime"]["shared_publish_lock"], "/srv/coloring-pages-content/state/drive-ingest/.lock")
        self.assertEqual(contract["rollback"], "none-after-first-mutation-fail-closed")

    def test_shared_publish_lock_rejects_concurrent_apply(self):
        with migration.acquire_content_lock(self.content):
            with self.assertRaisesRegex(migration.MigrationError, "lock is busy"):
                with migration.acquire_content_lock(self.content):
                    pass

    def test_dockerfile_contains_migration_tool_and_contract(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY tools/coloring-pages-migrate-png-only /usr/local/bin/coloring-pages-migrate-png-only", dockerfile)
        self.assertIn("COPY deploy/legacy-png-migration-v1.json /usr/local/share/coloring-pages/legacy-png-migration-v1.json", dockerfile)


if __name__ == "__main__":
    unittest.main()
