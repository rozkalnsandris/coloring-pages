"""Issue #578: strict source-only Page Hero manifest contracts."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_landing_hero_manifest import (  # noqa: E402
    ManifestValidationError, parse_manifest, validate_data, validate_manifest_text,
)

MANIFEST = ROOT / "metadata/landing-hero.v1.json"


class LandingHeroManifestV1Tests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def reject(self, change):
        data = deepcopy(self.records)
        change(data)
        with self.assertRaises(ManifestValidationError):
            validate_data(data, ROOT)

    def test_owner_approved_indexed_and_browse_records(self):
        self.assertEqual(set(self.records), {"schema", "categories", "topics"})
        self.assertEqual(set(self.records["categories"]), {"fahrzeuge"})
        self.assertEqual(set(self.records["topics"]), {"herbst", "bauernhof", "weihnachten", "dinosaurier", "weltraum"})
        fahrzeuge = self.records["categories"]["fahrzeuge"]
        herbst = self.records["topics"]["herbst"]
        self.assertEqual((fahrzeuge["width"], fahrzeuge["height"], fahrzeuge["bytes"]),
                         (1755, 896, 163810))
        self.assertEqual((herbst["width"], herbst["height"], herbst["bytes"]),
                         (1755, 896, 119446))
        self.assertEqual(fahrzeuge["approval_ref"], "coloring-pages#573")
        self.assertEqual(herbst["approval_ref"], "coloring-pages#567")
        bauernhof = self.records["topics"]["bauernhof"]
        self.assertEqual((bauernhof["width"], bauernhof["height"], bauernhof["bytes"]), (1755, 896, 164350))
        self.assertEqual(bauernhof["approval_ref"], "coloring-pages#594")
        self.assertEqual(bauernhof["sha256"], "633c9565de757b6f0afaced8371ba5209fbb9dd3c41593441679450a98c51665")
        weihnachten = self.records["topics"]["weihnachten"]
        self.assertEqual((weihnachten["width"], weihnachten["height"], weihnachten["bytes"]), (1755, 896, 163468))
        self.assertEqual(weihnachten["approval_ref"], "coloring-pages#596")
        self.assertEqual(weihnachten["sha256"], "b5aaa55e6f9180a1dcd4bfceb03ba6285332390a0ad6c75bae819d8d6b34d1da")
        dinosaurier = self.records["topics"]["dinosaurier"]
        self.assertEqual((dinosaurier["width"], dinosaurier["height"], dinosaurier["bytes"]), (1755, 896, 163254))
        self.assertEqual(dinosaurier["approval_ref"], "coloring-pages#598")
        self.assertEqual(dinosaurier["sha256"], "93499504ac0f6fd5bc8abb12b5f733e2b9e87267a1b9a797ac8f8f8db4ec37c6")
        weltraum = self.records["topics"]["weltraum"]
        self.assertEqual((weltraum["width"], weltraum["height"], weltraum["bytes"]), (1755, 896, 120192))
        self.assertEqual(weltraum["approval_ref"], "coloring-pages#600")
        self.assertEqual(weltraum["sha256"], "e57be01a232ab2bb92ef6394e5bc4ec47728f49c41653e1c5b183733367f4e56")
        self.assertEqual(fahrzeuge["sha256"], "5cf25e6cdd6a5b719f8f8c34577d3e9cba28b6b3a3c71199b24559855d9575b5")
        self.assertEqual(herbst["sha256"], "d077de2efb5b291cf41140722958aa771fea6bd716da387a37458af700b0ad74")

    def test_source_assets_and_rendered_html_match(self):
        self.assertIs(validate_data(self.records, ROOT), self.records)
        self.assertEqual(validate_manifest_text(MANIFEST.read_text(encoding="utf-8")), self.records)

    def test_cli_validates_without_mutation(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/validate_landing_hero_manifest.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("source-only", result.stdout)

    def test_duplicate_json_keys_rejected_at_all_levels(self):
        raw = MANIFEST.read_text(encoding="utf-8")
        self.assertIn('"schema":', raw)
        duplicated = raw.replace('"schema":', '"schema": "duplicate", "schema":', 1)
        with self.assertRaises(ManifestValidationError):
            parse_manifest(duplicated)
        duplicated_nested = raw.replace('"width": 1755', '"width": 2, "width": 1755', 1)
        with self.assertRaises(ManifestValidationError):
            validate_manifest_text(duplicated_nested)

    def test_invalid_json_and_nonfinite_values(self):
        for raw in ('{', '{"schema": NaN, "categories": {}, "topics": {}}'):
            with self.subTest(raw=raw), self.assertRaises(ManifestValidationError):
                validate_manifest_text(raw)

    def test_root_unknown_key_and_missing_namespace(self):
        self.reject(lambda d: d.update({"other": {}}))
        self.reject(lambda d: d.pop("topics"))
        self.reject(lambda d: d.update({"schema": "other"}))
        self.reject(lambda d: d.update({"categories": []}))

    def test_rejects_entry_unknown_key_and_missing_field(self):
        self.reject(lambda d: d["categories"]["fahrzeuge"].update({"extra": "x"}))
        self.reject(lambda d: d["topics"]["herbst"].pop("approval_ref"))
        self.reject(lambda d: d["categories"]["fahrzeuge"].pop("sha256"))

    def test_rejects_invalid_ids_and_category_seed_membership(self):
        self.reject(lambda d: d["categories"].update({"Unknown": d["categories"].pop("fahrzeuge")}))
        self.reject(lambda d: d["categories"].update({"unknown": d["categories"].pop("fahrzeuge")}))
        self.reject(lambda d: d["topics"].update({"../herbst": d["topics"].pop("herbst")}))

    def test_unapproved_or_unavailable_topic_never_creates_art(self):
        def add_unapproved(d):
            new = deepcopy(d["topics"]["herbst"])
            new["image"] = "/assets/tanzen-topic-hero.webp"
            new["approval_ref"] = ""
            d["topics"]["tanzen"] = new
        self.reject(add_unapproved)

    def test_asset_urls_and_slug_path_are_closed(self):
        for url in (
            "https://example.com/a.webp", "/assets/../secret.webp",
            "/assets/tiere-topic-hero.webp", "data:image/webp;base64,AA",
            "/assets/herbst-topic-hero.webp?preview=1",
        ):
            with self.subTest(url=url):
                self.reject(lambda d: d["topics"]["herbst"].update({"image": url}))

    def test_rejects_wrong_digest_dimensions_size_or_types(self):
        for key, value in (
            ("bytes", 119445), ("bytes", True), ("width", 1754),
            ("height", 0), ("height", "896"), ("sha256", "a" * 64),
            ("sha256", "BAD"),
        ):
            with self.subTest(key=key, value=value):
                self.reject(lambda d: d["topics"]["herbst"].update({key: value}))

    def test_alt_intro_and_evidence_must_be_source_safe(self):
        for key, value in (
            ("alt", "<img>"), ("alt", ""), ("alt", "a" * 181),
            ("intro", "<script>"), ("intro", "a" * 301),
            ("provenance", "../private"), ("approval_ref", "unknown#567"),
            ("approval_ref", ""), ("approval_ref", "coloring-pages#0"),
        ):
            with self.subTest(key=key):
                self.reject(lambda d: d["topics"]["herbst"].update({key: value}))

    def local_copy(self, destination: Path):
        (destination / "metadata").mkdir()
        (destination / "assets").mkdir()
        for name in ("categories.json",):
            shutil.copyfile(ROOT / "metadata" / name, destination / "metadata" / name)
        for name in ("herbst", "fahrzeuge"):
            shutil.copyfile(ROOT / (name + ".html"), destination / (name + ".html"))
            shutil.copyfile(ROOT / "assets" / (name + "-topic-hero.webp"),
                            destination / "assets" / (name + "-topic-hero.webp"))
        shutil.copyfile(ROOT / "assets/bauernhof-topic-hero.webp",
                        destination / "assets/bauernhof-topic-hero.webp")
        shutil.copyfile(ROOT / "assets/weihnachten-topic-hero.webp",
                        destination / "assets/weihnachten-topic-hero.webp")
        shutil.copyfile(ROOT / "assets/dinosaurier-topic-hero.webp",
                        destination / "assets/dinosaurier-topic-hero.webp")
        shutil.copyfile(ROOT / "assets/weltraum-topic-hero.webp",
                        destination / "assets/weltraum-topic-hero.webp")

    def test_missing_and_corrupted_asset_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.local_copy(root)
            image = root / "assets/herbst-topic-hero.webp"
            image.unlink()
            with self.assertRaises(ManifestValidationError):
                validate_data(self.records, root)
            image.write_bytes(b"GIF89a")
            fake = deepcopy(self.records)
            fake["topics"]["herbst"]["bytes"] = 6
            fake["topics"]["herbst"]["sha256"] = hashlib.sha256(b"GIF89a").hexdigest()
            with self.assertRaises(ManifestValidationError):
                validate_data(fake, root)

    def test_mismatched_current_html_alt_or_size_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.local_copy(root)
            page = root / "herbst.html"
            content = page.read_text(encoding="utf-8")
            self.assertIn('alt="Ausmalwiese-Hund mit Kürbissen', content)
            page.write_text(content.replace('alt="Ausmalwiese-Hund mit Kürbissen',
                                            'alt="Falscher Hund mit Kürbissen', 1),
                            encoding="utf-8")
            with self.assertRaises(ManifestValidationError):
                validate_data(self.records, root)

    def test_manifest_cannot_create_runtime_topic_or_seo_route(self):
        self.assertNotIn("tanzen", self.records["topics"])
        self.assertIn("bauernhof", self.records["topics"])
        self.assertFalse((ROOT / "bauernhof.html").exists())
        self.assertFalse((ROOT / "weihnachten.html").exists())
        self.assertFalse((ROOT / "dinosaurier.html").exists())
        self.assertFalse((ROOT / "weltraum.html").exists())
        self.assertNotIn("ostern", self.records["topics"])
        self.assertEqual(set(self.records["topics"]), {"herbst", "bauernhof", "weihnachten", "dinosaurier", "weltraum"})
        for page in ("herbst.html", "fahrzeuge.html"):
            html = (ROOT / page).read_text(encoding="utf-8")
            self.assertNotIn("landing-hero.v1.json", html)
        self.assertNotIn("landing-hero.v1.json",
                         (ROOT / "js/topic-hero-content.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
