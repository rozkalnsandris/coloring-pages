"""Regression contracts for UI/UX audit #511 finding 16 focus retention."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FocusRetention511Tests(unittest.TestCase):
    def test_category_topic_click_keeps_the_focused_chip_in_the_dom(self):
        source = (ROOT / "js" / "category.js").read_text(encoding="utf-8")
        match = re.search(
            r'button\.addEventListener\("click", \(\) => \{\n'
            r'\s+activeCategoryTopic = id;(?P<body>.*?)'
            r'\s+renderCategoryEntries\(categoryEntries, \{ resetLimit: true \}\);\n'
            r'\s+\}\);',
            source,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group("body")
        self.assertIn('strip.querySelectorAll("[data-category-topic]")', body)
        self.assertIn('"aria-pressed"', body)
        self.assertNotIn("ensureCategoryTopicFilter(categoryEntries)", body)

    def test_keyboard_load_more_focuses_the_first_new_card_after_render(self):
        source = (ROOT / "js" / "app.js").read_text(encoding="utf-8")
        start = source.index('loadMoreButton?.addEventListener("click", (event) => {')
        end = source.index("\n\ncategoryButtons.forEach", start)
        block = source[start:end]

        self.assertIn(
            'const previousVisibleCount = gallery?.querySelectorAll(".coloring-card").length || 0;',
            block,
        )
        self.assertIn("const shouldMoveFocus = event.detail === 0;", block)
        self.assertIn("if (shouldMoveFocus)", block)
        self.assertIn(
            'nextCards[previousVisibleCount]?.querySelector("a")?.focus({ preventScroll: true });',
            block,
        )
        self.assertLess(block.index("renderCatalog();"), block.index(".focus({ preventScroll: true })"))

    def test_final_page_can_hide_load_more_without_losing_keyboard_focus(self):
        source = (ROOT / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn(
            "loadMoreButton.hidden = visibleEntries.length >= matches.length;",
            source,
        )
        self.assertIn(
            'nextCards[previousVisibleCount]?.querySelector("a")?.focus({ preventScroll: true });',
            source,
        )


if __name__ == "__main__":
    unittest.main()
