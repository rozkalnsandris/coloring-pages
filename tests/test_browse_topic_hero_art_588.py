"""#588: source-reviewed browse-only Topic art needs no indexed route."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_landing_hero_manifest import (  # noqa: E402
    ManifestValidationError, validate_data, validate_manifest_text,
)
from render_landing_hero_static import build_pages  # noqa: E402
from render_landing_hero_topic_js import render as render_browser_js  # noqa: E402


class BrowseTopicHeroArt588Tests(unittest.TestCase):
    def make_fixture(self, root: Path):
        for path in (
            "metadata/categories.json", "metadata/landing-hero.v1.json",
            "assets/fahrzeuge-topic-hero.webp",
            "assets/herbst-topic-hero.webp",
            "fahrzeuge.html", "herbst.html",
        ):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)

        # Test-only simulated reviewed art. These bytes and synthetic approval
        # reference are never added to production source or published.
        art = (root / "assets/tanzen-topic-hero.webp")
        shutil.copyfile(root / "assets/herbst-topic-hero.webp", art)
        metadata = json.loads(
            (root / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
        )
        record = deepcopy(metadata["topics"]["herbst"])
        record.update({
            "image": "/assets/tanzen-topic-hero.webp",
            "intro": "Tanzen-Ausmalbilder für Kinder zum Entdecken.",
            "alt": "Testmotiv für eine tanzende Figur",
            "provenance": "fixture-only-artwork",
            "approval_ref": "coloring-pages#999999",
        })
        record["bytes"] = art.stat().st_size
        record["sha256"] = hashlib.sha256(art.read_bytes()).hexdigest()
        metadata["topics"]["tanzen"] = record
        (root / "metadata/landing-hero.v1.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return metadata

    def test_browse_only_art_validates_and_generates_no_html_route(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.make_fixture(root)
            self.assertFalse((root / "tanzen.html").exists())
            self.assertIs(validate_data(payload, root), payload)
            self.assertEqual(
                set(validate_manifest_text(
                    (root / "metadata/landing-hero.v1.json").read_text(encoding="utf-8"),
                    root,
                )["topics"]), {"herbst", "tanzen"},
            )
            js = render_browser_js(root)
            self.assertIn('src: "/assets/tanzen-topic-hero.webp"', js)
            self.assertIn("Object.prototype.hasOwnProperty.call", js)
            self.assertNotIn("fetch(", js)
            self.assertEqual(
                set(build_pages(root)), {"fahrzeuge.html", "herbst.html"}
            )
            for name, output in build_pages(root).items():
                self.assertEqual(
                    output, (root / name).read_text(encoding="utf-8")
                )
            self.assertFalse((root / "tanzen.html").exists())

    def test_missing_corrupt_art_and_invalid_approval_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = self.make_fixture(root)
            art = root / "assets/tanzen-topic-hero.webp"
            art.unlink()
            with self.assertRaises(ManifestValidationError):
                validate_data(original, root)
            art.write_bytes(b"GIF89a")
            with self.assertRaises(ManifestValidationError):
                validate_data(original, root)
            shutil.copyfile(ROOT / "assets/herbst-topic-hero.webp", art)
            invalid = deepcopy(original)
            invalid["topics"]["tanzen"]["approval_ref"] = ""
            with self.assertRaises(ManifestValidationError):
                validate_data(invalid, root)
            invalid = deepcopy(original)
            invalid["topics"]["tanzen"]["image"] = "/assets/../secret.webp"
            with self.assertRaises(ManifestValidationError):
                validate_data(invalid, root)

    def test_reviewed_indexed_herbst_and_categories_still_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = self.make_fixture(root)
            (root / "herbst.html").unlink()
            with self.assertRaises(ManifestValidationError):
                validate_data(original, root)
            shutil.copyfile(ROOT / "herbst.html", root / "herbst.html")
            (root / "fahrzeuge.html").unlink()
            with self.assertRaises(ManifestValidationError):
                validate_data(original, root)

    def test_unexpected_static_topic_route_is_not_auto_generated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.make_fixture(root)
            # Even a valid matching new static Hero HTML must use a separate
            # reviewed indexed-route/generator migration: no implicit rollout.
            html = (root / "herbst.html").read_text(encoding="utf-8")
            record = payload["topics"]["tanzen"]
            old = payload["topics"]["herbst"]
            page = html.replace(old["image"], record["image"]).replace(
                old["alt"], record["alt"]
            )
            (root / "tanzen.html").write_text(page, encoding="utf-8")
            self.assertIs(validate_data(payload, root), payload)
            with self.assertRaises(ManifestValidationError):
                build_pages(root)

    def test_symlink_route_cannot_bypass_static_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = self.make_fixture(root)
            (root / "tanzen.html").symlink_to("herbst.html")
            with self.assertRaises(ManifestValidationError):
                validate_data(original, root)

    def test_no_real_art_or_source_route_added_by_this_change(self):
        self.assertFalse((ROOT / "tanzen.html").exists())
        actual = json.loads(
            (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(actual["topics"]), {"herbst"})
        self.assertNotIn("tanzen", actual["categories"])


if __name__ == "__main__":
    unittest.main()
