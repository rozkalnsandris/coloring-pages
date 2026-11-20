"""#590: deterministic full-section source Hero template, two approved pages."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from render_landing_hero_sections import (  # noqa: E402
    ManifestValidationError, ROUTES, SCHEMA, build_pages,
    render_section, replace_section, validate_sections_data,
)
from validate_landing_hero_manifest import parse_manifest  # noqa: E402

SOURCE = ROOT / "metadata/landing-hero-sections.v1.json"
APPROVED = ROOT / "metadata/landing-hero.v1.json"
BASELINE_BLOBS = {
    "fahrzeuge.html": "01e0a287b83cdd54f950e4985e803a9e4d4b331f",
    "herbst.html": "05ed97b780478192c02f922bbeebdbd325b7b39e",
}


def git_blob_sha(markup: str) -> str:
    data = markup.encode("utf-8")
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


class StaticHeroSections590Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = parse_manifest(SOURCE.read_text(encoding="utf-8"))
        cls.art = json.loads(APPROVED.read_text(encoding="utf-8"))

    def test_full_initial_html_is_byte_identical(self):
        output = build_pages(ROOT)
        self.assertEqual(set(output), set(BASELINE_BLOBS))
        for slug, variant in ROUTES.items():
            with self.subTest(slug=slug):
                name = slug + ".html"
                original = (ROOT / name).read_text(encoding="utf-8")
                self.assertEqual(output[name], original)
                self.assertEqual(git_blob_sha(original), BASELINE_BLOBS[name])
                self.assertEqual(original.count('<h1 id="category-title">'), 1)
                self.assertIn(
                    '<link rel="canonical" href="https://ausmalwiese.de/'
                    + slug + '">', original,
                )
        self.assertEqual(
            output["herbst.html"].count('<article class="coloring-card">'), 6
        )

    def test_cli_check_is_read_only_and_passes(self):
        paths = [ROOT / name for name in BASELINE_BLOBS]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        check = subprocess.run(
            [sys.executable, "tools/render_landing_hero_sections.py", "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("match reviewed source", check.stdout)
        self.assertEqual(
            before, [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        )

    def test_approved_art_is_single_authority_not_duplicate_metadata(self):
        self.assertEqual(self.content["schema"], SCHEMA)
        self.assertEqual(set(self.content["pages"]), {"fahrzeuge", "herbst"})
        for slug, variant in ROUTES.items():
            section = render_section(
                slug, self.content["pages"][slug],
                self.art[variant["namespace"]][slug],
            )
            self.assertEqual(section.count("<img "), 1)
            self.assertIn(
                self.art[variant["namespace"]][slug]["image"], section
            )
            self.assertNotIn("canonical", section)
            self.assertEqual(section.count('<h1 id="category-title">'), 1)

    def test_invalid_or_unreviewed_metadata_fails_closed(self):
        self.assertIs(validate_sections_data(self.content), self.content)
        bad = []
        for mutation in (
            lambda d: d.update({"unreviewed": {}}),
            lambda d: d["pages"].update({"tanzen": {}}),
            lambda d: d["pages"]["fahrzeuge"].update({"namespace": "topics"}),
            lambda d: d["pages"]["herbst"].update({"heading": "<script>"}),
            lambda d: d["pages"]["herbst"].update({"intro": "x" * 421}),
            lambda d: d["pages"]["herbst"].update({"breadcrumbs": []}),
            lambda d: d["pages"]["herbst"]["breadcrumbs"][1].update(
                {"href": "javascript:alert(1)"}
            ),
            lambda d: d["pages"]["fahrzeuge"]["breadcrumbs"][-1].update(
                {"href": "/tanzen"}
            ),
            lambda d: d["pages"]["fahrzeuge"].update({"unexpected": True}),
            lambda d: d["pages"]["herbst"]["breadcrumbs"][0].update(
                {"label": "Elsewhere"}
            ),
        ):
            changed = deepcopy(self.content)
            mutation(changed)
            bad.append(changed)
        for changed in bad:
            with self.subTest(changed=changed), self.assertRaises(
                ManifestValidationError
            ):
                validate_sections_data(changed)
        raw = SOURCE.read_text(encoding="utf-8")
        duplicated = raw.replace('"schema":', '"schema": "bad", "schema":', 1)
        with self.assertRaises(ManifestValidationError):
            parse_manifest(duplicated)

    def test_stale_section_is_replaced_without_touching_other_html(self):
        for slug, variant in ROUTES.items():
            name = slug + ".html"
            original = (ROOT / name).read_text(encoding="utf-8")
            generated = render_section(
                slug, self.content["pages"][slug],
                self.art[variant["namespace"]][slug],
            )
            stale = original.replace(
                '<h1 id="category-title">',
                '<h1 id="category-title">Outdated ',
                1,
            )
            self.assertNotEqual(original, stale)
            self.assertEqual(replace_section(stale, slug, generated), original)
            for malformed in (
                original.replace('    <section class="category-hero', "", 1),
                original.replace('    <section class="category-hero',
                                 '    <section class="category-hero'
                                 '    <section class="category-hero', 1),
                original.replace('<h1 id="category-title">',
                                 '<h1 id="category-title"><h1 id="category-title">', 1),
            ):
                with self.assertRaises(ManifestValidationError):
                    replace_section(malformed, slug, generated)

    def test_no_new_routes_or_unreviewed_editorial_copy(self):
        self.assertEqual(set(self.content["pages"]), {"fahrzeuge", "herbst"})
        self.assertNotIn("tanzen", self.content["pages"])
        self.assertNotIn("bauernhof", self.content["pages"])
        self.assertEqual(
            self.content["pages"]["herbst"]["breadcrumbs"][1],
            {"href": "/jahreszeiten", "label": "Jahreszeiten & Feste"},
        )
        self.assertEqual(
            self.content["pages"]["fahrzeuge"]["heading"],
            "Kostenlose Fahrzeug-Ausmalbilder",
        )


if __name__ == "__main__":
    unittest.main()
