"""Visitor-facing coverless book preview UI contract for issue #199."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BookPreviewUi199Tests(unittest.TestCase):
    def test_ui_reuses_reviewed_preview_models_without_new_storage_or_fetch(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            'from "./book-cover-state.mjs"',
            'from "./book-preview-plan.mjs"',
            'from "./book-preview-navigation.mjs"',
            'from "./book-preview-media.mjs"',
            "buildBookPreviewPlan(basket.ids, catalog, bookCover)",
            "createBookPreviewCursor(previewPlan)",
            "moveBookPreviewCursor(previewPlan, previewCursor, direction)",
            "buildBookPreviewDisplay(previewPlan, previewCursor, catalog)",
        ):
            self.assertIn(marker, source)
        preview = source.split("function resetPreview() {", 1)[1].split("\nfunction resetZip() {", 1)[0]
        self.assertNotIn("fetch(", preview)
        self.assertNotIn("sessionStorage", preview)
        self.assertNotIn("localStorage", preview)
        self.assertNotIn("writeStoredBasketIds", preview)

    def test_dialog_exposes_accessible_artwork_preview_navigation(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            'panelButton("Vorschau", "preview")',
            'preview.setAttribute("aria-labelledby", "basket-preview-title")',
            'previewPage.setAttribute("role", "status")',
            'previewPage.setAttribute("aria-live", "polite")',
            'panelButton("Zurück", "preview-previous")',
            'panelButton("Weiter", "preview-next")',
            'image.src = display.content.previewUrl',
            'panel.hidden = false',
        ):
            self.assertIn(marker, source)
        self.assertNotIn("innerHTML", source)

    def test_preview_supports_in_memory_cover_without_enabling_export_or_print(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        preview = source.split("function resetPreview() {", 1)[1].split("\nfunction resetZip() {", 1)[0]
        self.assertIn("let bookCover = createBookCoverState();", source)
        self.assertIn("setBookCoverEnabled", source)
        self.assertIn("updateBookCoverText", source)
        self.assertIn("buildBookPreviewPlan(basket.ids, catalog, bookCover)", preview)
        self.assertIn("coverTitle.textContent = display.content.title", preview)
        self.assertIn('coverName.textContent = display.content.name ? "Für " + display.content.name : "";', preview)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("window.print(", source)
        self.assertIn('printAction.disabled = true;', source)
        self.assertIn("basket.ids.length === 0 || zipBusy || bookCover.enabled", source)
        self.assertNotIn("prepareBasketPngZip", preview)

    def test_preview_resets_when_selection_changes_or_dialog_closes(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn('node.addEventListener("close", () => { resetPreview(); });', source)
        self.assertIn("resetZip();\n  resetPreview();\n  basket = next;", source)

    def test_mobile_preview_media_is_bounded(self):
        css = (ROOT / "css" / "print-basket.css").read_text(encoding="utf-8")
        for marker in (
            ".basket-book-preview",
            ".basket-preview-frame img",
            "max-width: 100%;",
            "max-height: min(58dvh, 640px);",
            ".basket-preview-controls",
            "@media (max-width: 480px)",
        ):
            self.assertIn(marker, css)

    def test_module_parses_with_node(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js required for module syntax check")
        completed = subprocess.run(
            [node, "--check", "js/print-basket-ui.mjs"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"Book preview UI module syntax failed:\n{completed.stdout}\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
