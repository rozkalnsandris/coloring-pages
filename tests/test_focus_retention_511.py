"""Regression contracts for UI/UX audit #511 finding 16 focus retention."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FocusRetention511Tests(unittest.TestCase):
    def test_category_topic_change_keeps_the_native_select_mounted(self):
        source = (ROOT / "js" / "category.js").read_text(encoding="utf-8")
        start = source.index('filterPanel.topic.addEventListener("change", () => {')
        end = source.index("\\n  });", start)
        handler = source[start:end]
        self.assertIn("activeCategoryTopic = filterPanel.topic.value;", handler)
        self.assertIn(
            "renderCategoryEntries(categoryEntries, { resetLimit: true });",
            handler,
        )
        # The selected control must survive re-render; only cards are replaced.
        self.assertNotIn("ensureCategoryTopicFilter(", handler)
        self.assertNotIn("replaceChildren(", handler)
        self.assertIn("gallery.replaceChildren(fragment);", source)
        self.assertNotIn("filterPanel.root.replaceChildren", source)

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
