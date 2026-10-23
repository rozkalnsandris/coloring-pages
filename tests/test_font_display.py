"""Self-hosted webfont loading regression: identical Baloo 2 / Nunito, no remote dependency."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "detail.html", "kita.html", "stats.html", "traffic.html", "print.html", "impressum.html", "datenschutz.html")


class LocalFontsTest(unittest.TestCase):
    def test_fonts_stylesheet_hash_and_preloads(self):
        css = (ROOT / "css/fonts.css").read_text(encoding="utf-8")
        css_hash = hashlib.sha256(css.encode("utf-8")).hexdigest()[:16]
        paths = re.findall(r'src: url\("\.\./(assets/fonts/[^"]+\.woff2)"\)', css)
        self.assertEqual(len(paths), 2)
        for path in paths:
            data = (ROOT / path).read_bytes()
            self.assertEqual(data[:4], b"wOF2")
            self.assertEqual(int.from_bytes(data[8:12], "big"), len(data))
            self.assertIn(hashlib.sha256(data).hexdigest()[:16], path)
        for html_name in PAGES:
            with self.subTest(page=html_name):
                page = (ROOT / html_name).read_text(encoding="utf-8")
                self.assertNotIn("fonts.googleapis.com", page)
                self.assertNotIn("fonts.gstatic.com", page)
                self.assertIn(f'css/fonts.css?v={css_hash}', page)
                self.assertLess(page.index("css/fonts.css?"), page.index("css/app.css?"))
                preload_paths = re.findall(
                    r'<link rel="preload" href="(assets/fonts/[^"]+\.woff2)" as="font" type="font/woff2" crossorigin>',
                    page,
                )
                self.assertEqual(preload_paths, paths if html_name != "print.html" else paths[1:])
        self.assertIn("font-display: optional", css)
        self.assertIn('font-family: "Baloo 2"', css)
        self.assertIn('font-family: "Nunito"', css)
        self.assertNotIn("data:font/", css)
        self.assertNotIn("fonts.googleapis.com", css)
        self.assertIn("max-age=31536000, immutable", (ROOT / "deploy/nginx.conf").read_text(encoding="utf-8"))

    def test_license_and_brand_preservation(self):
        for name in ("Baloo2", "Nunito"):
            license_text = (ROOT / f"assets/fonts/OFL-{name}.txt").read_text(encoding="utf-8-sig")
            self.assertIn("SIL OPEN FONT LICENSE", license_text)
        app = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn('--font-display: "Baloo 2"', app)
        self.assertIn('--font-body: "Nunito"', app)
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="hero-art"', home)
        self.assertIn('id="entdecken"', home)


if __name__ == "__main__":
    unittest.main()
