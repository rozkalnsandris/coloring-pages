"""#169 exact immutable dog preview migration: source-only, simulated content root."""
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/coloring-pages-preview-8774852-migrate"
LOADER = importlib.machinery.SourceFileLoader("dog_migration_executor", str(TOOL))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(mod)


class ExactPreviewMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = b"RIFF\x00\x00\x00\x00WEBPsimulated-pixels"
        for rel in ("originals/8774852", "public/media/8774852", "state/drive-ingest"):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        (self.root / "state/drive-ingest/.lock").write_bytes(b"")
        files = {
            "originals/8774852/source.png":
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 +
                (2480).to_bytes(4, "big") + (3508).to_bytes(4, "big") + b"simulated",
            "public/media/8774852/preview.webp": b"old-preview",
            "public/media/8774852/thumb.webp": b"old-thumb",
            "public/media/8774852/print.png": b"old-print",
        }
        for rel, body in files.items():
            (self.root / rel).write_bytes(body)
        self.entry = {
            "age": "3-6", "category": "tiere", "character": "", "difficulty": "easy",
            "id": "8774852", "language": "de",
            "preview": "/media/8774852/preview.webp",
            "print": "/media/8774852/print.png",
            "thumb": "/media/8774852/thumb.webp", "title": "Hund zum Ausmalen"
        }
        self.other = {"id": "unrelated", "preview": "/other/preview.webp"}
        self.catalog = [self.other, self.entry]
        (self.root / "public/catalog.json").write_text(
            json.dumps(self.catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        self.contract = json.loads(
            (ROOT / "deploy/preview-8774852-migration-plan-v1.json").read_text()
        )
        b = self.contract["baseline"]
        b["catalog"]["entry_count"] = len(self.catalog)
        b["catalog"]["sha256"] = mod.sha((self.root / "public/catalog.json").read_bytes())
        b["catalog"]["entry"] = self.entry
        for item in [b["source"], *b["current"].values()]:
            payload = (self.root / item["path"]).read_bytes()
            item["sha256"] = mod.sha(payload)
            item["size_bytes"] = len(payload)
        c = self.contract["candidate"]
        c["candidate_sha256"] = mod.sha(self.data)
        # For a fake source in test fixtures the proof contract must accept synthetic data;
        # override only the verifier, never the production executor or plan.
        self.actual_verify = mod.verify_render
        mod.verify_render = lambda data, c: mod.require(
            mod.sha(data) == c["candidate"]["candidate_sha256"] and
            len(data) == c["candidate"]["candidate_size_bytes"], "fixture proof"
        )
        self.addCleanup(setattr, mod, "verify_render", self.actual_verify)
        c["candidate_size_bytes"] = len(self.data)
        c["candidate_filename"] = "preview-" + mod.sha(self.data) + ".webp"
        c["candidate_public_url"] = "/media/8774852/" + c["candidate_filename"]
        self.original_contract_check = mod.contract_check
        mod.contract_check = lambda c: None  # Only for simulated data; actual plan is checked separately.
        self.addCleanup(setattr, mod, "contract_check", self.original_contract_check)

    def renderer(self, source):
        self.assertEqual(source, self.root / "originals/8774852/source.png")
        return self.data

    def test_check_does_not_write(self):
        before = (self.root / "public/catalog.json").read_bytes()
        result = mod.execute(self.root, self.contract, apply=False, renderer=self.renderer)
        self.assertEqual(result["candidate_sha256"], mod.sha(self.data))
        self.assertEqual((self.root / "public/catalog.json").read_bytes(), before)
        self.assertFalse((self.root / "public/media/8774852" /
                          self.contract["candidate"]["candidate_filename"]).exists())

    def test_apply_switches_only_preview_and_preserves_immutable_files(self):
        protected = {
            item["path"]: (self.root / item["path"]).read_bytes()
            for item in [self.contract["baseline"]["source"],
                         *self.contract["baseline"]["current"].values()]
        }
        result = mod.execute(self.root, self.contract, apply=True, renderer=self.renderer)
        dest = self.root / "public/media/8774852" / self.contract["candidate"]["candidate_filename"]
        self.assertEqual(dest.read_bytes(), self.data)
        self.assertEqual(dest.stat().st_mode & 0o777, 0o644)
        after = json.loads((self.root / "public/catalog.json").read_bytes())
        self.assertEqual(after[0], self.other)
        self.assertEqual(after[1], {**self.entry, "preview": result["candidate_public_url"]})
        for rel, data in protected.items():
            self.assertEqual((self.root / rel).read_bytes(), data)

    def test_bad_catalog_hash_aborts_without_writes(self):
        self.contract["baseline"]["catalog"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(mod.MigrationError, "hash drift"):
            mod.execute(self.root, self.contract, apply=True, renderer=self.renderer)
        self.assertFalse(list((self.root / "public/media/8774852").glob("preview-*")))

    def test_bad_render_candidate_aborts_without_writes(self):
        with self.assertRaisesRegex(mod.MigrationError, "fixture proof"):
            mod.execute(self.root, self.contract, apply=True,
                        renderer=lambda _: b"wrong")
        self.assertFalse(list((self.root / "public/media/8774852").glob("preview-*")))

    def test_existing_new_filename_aborts_without_writes(self):
        target = self.root / "public/media/8774852" / self.contract["candidate"]["candidate_filename"]
        target.write_bytes(b"collision")
        with self.assertRaisesRegex(mod.MigrationError, "already exists"):
            mod.execute(self.root, self.contract, apply=True, renderer=self.renderer)
        self.assertEqual(target.read_bytes(), b"collision")

    def test_source_drift_detected_after_render_before_first_write(self):
        def drift(source):
            source.write_bytes(source.read_bytes() + b"changed")
            return self.data
        with self.assertRaisesRegex(mod.MigrationError, "size drift"):
            mod.execute(self.root, self.contract, apply=True, renderer=drift)
        self.assertFalse(list((self.root / "public/media/8774852").glob("preview-*")))

    def test_candidate_plan_production_identity(self):
        prod = json.loads(
            (ROOT / "deploy/preview-8774852-migration-plan-v1.json").read_text()
        )
        self.original_contract_check(prod)
        self.assertEqual(mod.IMAGE, prod["producer"]["runtime_image"])
        self.assertIn('"run", "-i"', TOOL.read_text(encoding="utf-8"))
        self.assertIn('"--network=none"', TOOL.read_text(encoding="utf-8"))
        self.assertIn('"--pull=never"', TOOL.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
