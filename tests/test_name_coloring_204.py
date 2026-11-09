"""Source/privacy/PNG-contract tests for client-only name coloring page #204."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NameColoring204Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "name.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "css/name-coloring.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "js/name-coloring.js").read_text(encoding="utf-8")
        cls.fonts = (ROOT / "css/fonts.css").read_text(encoding="utf-8")
        cls.license = (ROOT / "assets/fonts/OFL-Baloo2.txt").read_text(encoding="utf-8-sig")

    def test_page_is_local_only_and_not_catalog_route(self):
        self.assertIn('meta name="robots" content="noindex"', self.html)
        self.assertNotIn("catalog.json", self.html + self.js)
        self.assertNotIn("stats.js", self.html)
        self.assertNotIn("goat", (self.html + self.js).lower())
        self.assertNotIn("fetch(", self.js)
        self.assertNotIn("XMLHttpRequest", self.js)
        self.assertNotIn("localStorage", self.js)
        self.assertNotIn("sessionStorage", self.js)
        self.assertNotRegex(self.js, r"URLSearchParams|location\.search|location\.hash")
        self.assertIn('anchor.download = "mein-name-a4.png"', self.js)
        self.assertNotIn("input.value", re.sub(r"input\.value\s*=", "", self.js).split("anchor.download", 1)[1] if "anchor.download" in self.js else "")

    def test_accessible_input_and_actions(self):
        self.assertIn('<label for="name-input">Name oder kurzes Wort</label>', self.html)
        self.assertIn('aria-describedby="name-hint name-error"', self.html)
        self.assertIn('role="status"', self.html)
        self.assertIn("Vorschau anzeigen", self.html)
        self.assertIn("Als PNG speichern", self.html)
        self.assertIn("A4 drucken", self.html)
        self.assertIn("Eingabe löschen", self.html)
        self.assertIn("autocomplete="off"", self.html)
        self.assertIn("spellcheck="false"", self.html)

    def test_validation_contract(self):
        self.assertIn("ÄÖÜäöüß", self.js)
        self.assertIn("normalize("NFC")", self.js)
        self.assertIn("count > 18", self.js)
        self.assertIn("höchstens ein Leerzeichen oder Bindestrich", self.js)
        self.assertIn("maxlength="20"", self.html)

    def test_existing_ofl_baloo_is_used(self):
        self.assertIn('font-family: "Baloo 2"', self.fonts)
        self.assertIn("baloo2-latin-vf-26fb4610d4bc976d.woff2", self.fonts)
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", self.license)
        self.assertIn('const FONT = '"Baloo 2"';', self.js)
        self.assertIn("document.fonts.load", self.js)
        self.assertIn("document.fonts.check", self.js)

    def test_a4_rgb_png_contract(self):
        self.assertIn("const WIDTH = 2480;", self.js)
        self.assertIn("const HEIGHT = 3508;", self.js)
        self.assertIn("const SAFE = 177;", self.js)
        self.assertIn("const PX_PER_METRE = 11811;", self.js)
        self.assertIn('new CompressionStream("deflate")', self.js)
        self.assertIn('chunk("IHDR", ihdr)', self.js)
        self.assertIn('chunk("pHYs", phys)', self.js)
        self.assertIn('chunk("IDAT", compressed)', self.js)
        self.assertIn('chunk("IEND", new Uint8Array())', self.js)
        self.assertIn("bytes[dataStart + 9] !== 2", self.js)
        self.assertIn("PNG_CRC", self.js)
        self.assertIn('new Blob([bytes], { type: "image/png" })', self.js)

    def test_print_is_one_a4_page(self):
        self.assertIn("@page { size: A4 portrait; margin: 0; }", self.css)
        self.assertIn("width: 210mm", self.css)
        self.assertIn("height: 297mm", self.css)
        self.assertIn("window.print()", self.js)

    def test_export_fails_closed_without_compressionstream(self):
        self.assertIn('throw new Error("COMPRESSION_STREAM_UNAVAILABLE")', self.js)
        self.assertIn("downloadButton.disabled = true", self.js)
        self.assertIn("PNG-Speichern ist auf diesem Gerät nicht verfügbar", self.js)

if __name__ == "__main__":
    unittest.main()
