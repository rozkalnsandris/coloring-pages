"""Regression checks for detail-page related coloring discovery (#363)."""

import hashlib
import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


RELATED_HARNESS = r"""
const fs = require("node:fs");
const vm = require("node:vm");
const fixture = JSON.parse(process.argv[1]);
const source = fs.readFileSync("js/detail.js", "utf8");
const start = source.indexOf("function relatedTopicIds(");
const end = source.indexOf("function relatedDetailHref(", start);
if (start < 0 || end < 0) throw new Error("related selection segment absent");
const context = {
  entryPages(entry) {
    if (Array.isArray(entry?.pages) && entry.pages.length > 0) return entry.pages;
    if (entry?.preview || entry?.print) return [{preview:entry.preview || "", print:entry.print || ""}];
    return [];
  },
};
vm.runInNewContext(source.slice(start, end), context);
const selected = context.selectRelatedEntries(
  fixture.current,
  fixture.catalog,
  fixture.limit
);
console.log(JSON.stringify(selected.map((entry) => String(entry.id))));
"""


def related_ids(current, catalog, limit=6):
    if not shutil.which("node"):
        raise unittest.SkipTest("Node is needed for related-detail behavior tests")
    result = subprocess.run(
        ["node", "-e", RELATED_HARNESS, json.dumps({
            "current": current,
            "catalog": catalog,
            "limit": limit,
        })],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def entry(entry_id, category="tiere", topics=None, **extra):
    value = {
        "id": entry_id,
        "title": f"Motiv {entry_id}",
        "category": category,
        "topics": topics or [],
        "thumb": f"/media/{entry_id}-thumb.webp",
        "preview": f"/media/{entry_id}-preview.webp",
        "print": f"/media/{entry_id}-print.png",
    }
    value.update(extra)
    return value


class DetailRelatedTests(unittest.TestCase):
    def test_topics_outrank_same_category_and_invalid_items_are_excluded(self):
        current = entry("current", topics=["wald", "hase"])
        catalog = [
            current,
            entry("topic-one", category="fahrzeuge", topics=["wald"]),
            entry("same-category", topics=["meer"]),
            entry("topic-two", topics=["wald", "hase"]),
            entry("duplicate", topics=[]),
            entry("duplicate", topics=[]),
            entry("hidden", topics=["wald"], hidden=True),
            entry("invisible", topics=["wald"], visible=False),
            {**entry("no-thumb", topics=["wald"]), "thumb": ""},
            entry("unrelated", category="lernen", topics=["alphabet"]),
        ]
        self.assertEqual(
            related_ids(current, catalog),
            ["topic-two", "topic-one", "same-category", "duplicate"],
        )

    def test_same_category_is_deterministic_fallback_when_topics_are_missing(self):
        current = entry("current", topics=[])
        catalog = [
            current,
            entry("first", topics=[]),
            entry("other", category="lernen", topics=[]),
            entry("second", topics=[]),
        ]
        self.assertEqual(related_ids(current, catalog), ["first", "second"])

    def test_no_genuine_relation_hides_general_discovery_instead_of_mislabeling_it(self):
        current = entry("current", category="tiere", topics=["wald"])
        catalog = [
            current,
            entry("alphabet", category="lernen", topics=["alphabet"]),
            entry("vehicle", category="fahrzeuge", topics=["autos"]),
        ]
        self.assertEqual(related_ids(current, catalog), [])

    def test_limit_is_enforced_after_relevance_ranking(self):
        current = entry("current", topics=["wald"])
        catalog = [current] + [
            entry(f"topic-{index}", category="lernen", topics=["wald"])
            for index in range(8)
        ]
        self.assertEqual(
            related_ids(current, catalog, limit=6),
            [f"topic-{index}" for index in range(6)],
        )

    def test_detail_markup_and_css_are_accessible_mobile_first(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        css = (ROOT / "css" / "detail-related.css").read_text(encoding="utf-8")
        self.assertIn('class="detail-related" data-related-section', html)
        self.assertIn('aria-labelledby="related-title" hidden', html)
        self.assertIn('<h2 id="related-title">Ähnliche Ausmalbilder</h2>', html)
        self.assertIn('data-related-grid', html)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", css)
        self.assertIn("@media (min-width: 760px)", css)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", css)
        self.assertIn("object-fit: contain", css)
        self.assertIn("focus-visible", css)

    def test_related_cards_use_only_catalog_thumbnails_and_lazy_loading(self):
        source = (ROOT / "js" / "detail.js").read_text(encoding="utf-8")
        start = source.index("function renderRelatedEntries(")
        end = source.index("\nfunction selectPage(", start)
        render = source[start:end]
        self.assertIn("image.src = entry.thumb", render)
        self.assertIn('image.loading = "lazy"', render)
        self.assertIn('image.decoding = "async"', render)
        self.assertNotIn("entry.preview", render)
        self.assertNotIn("entry.print", render)
        self.assertIn("renderRelatedEntries(entry, catalog);", source)
        self.assertIn("if (relatedSection) relatedSection.hidden = true;", source)

    def test_detail_asset_versions_match_content_hashes(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        for filename in ("js/detail.js", "css/detail-related.css"):
            version = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()[:16]
            self.assertIn(f"{filename}?v={version}", html)

    def test_existing_print_and_download_actions_remain_in_detail_markup(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertIn("data-action-print", html)
        self.assertIn("A4 drucken", html)
        self.assertIn("data-action-png", html)
        self.assertIn("PNG herunterladen", html)


if __name__ == "__main__":
    unittest.main()
