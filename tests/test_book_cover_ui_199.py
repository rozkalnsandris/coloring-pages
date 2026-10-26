"""In-memory optional cover UI privacy and capacity contract for issue #199."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BookCoverUi199Tests(unittest.TestCase):
    def test_cover_fields_are_literal_in_memory_only(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            'coverTitleInput.dataset.basketCoverTitle = "";',
            'coverNameInput.dataset.basketCoverName = "";',
            'coverPrivacy.textContent = "Titel und Name werden nicht gespeichert.";',
            'bookCover = updateBookCoverText(bookCover, { title: control.value });',
            'bookCover = updateBookCoverText(bookCover, { name: control.value });',
            'coverTitle.textContent = display.content.title;',
        ):
            self.assertIn(marker, source)
        cover_code = source.split('const coverControls = document.createElement("section");', 1)[1].split('const previewOpen = panelButton("Vorschau", "preview");', 1)[0]
        for forbidden in ("sessionStorage", "localStorage", "URLSearchParams", "fetch(", "analytics", "innerHTML"):
            self.assertNotIn(forbidden, cover_code)

    def test_cover_counts_as_one_sheet_and_blocks_overflow(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn("return basket.sheetCount + (bookCover.enabled ? 1 : 0);", source)
        self.assertIn("setBookCoverEnabled(bookCover, true, next.ids, catalog);", source)
        self.assertIn("Maximal 5 A4-Druckseiten. Diese Malvorlage passt mit Deckblatt nicht mehr in deine Auswahl.", source)
        self.assertIn("Das Deckblatt zählt als eine von 5 A4-Druckseiten.", source)

    def test_cover_zip_is_held_until_conformant_renderer(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn("basket.ids.length === 0 || zipBusy || bookCover.enabled", source)
        self.assertIn("ZIP mit Deckblatt ist noch nicht verfügbar.", source)
        self.assertIn('printAction.disabled = true;', source)
        self.assertNotIn("window.print(", source)

    def test_clear_resets_transient_cover_draft(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        clear = source.split('if (action === "clear") {', 1)[1].split("\n    }", 1)[0]
        self.assertIn("bookCover = createBookCoverState();", clear)
        self.assertIn("commitBasket(clearBasket()", clear)


if __name__ == "__main__":
    unittest.main()
