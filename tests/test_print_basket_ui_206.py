"""Public basket selection UI integration for issue #206."""
import hashlib
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (
    "index.html", "detail.html", "tiere.html", "fahrzeuge.html",
    "alphabet.html", "lernen.html", "figuren.html", "jahreszeiten.html",
    "essen-natur.html",
)


class PrintBasketUi206Tests(unittest.TestCase):
    def test_public_browse_surfaces_load_hashed_assets(self):
        css = ROOT / "css" / "print-basket.css"
        js = ROOT / "js" / "print-basket-ui.mjs"
        css_version = hashlib.sha256(css.read_bytes()).hexdigest()[:16]
        js_version = hashlib.sha256(js.read_bytes()).hexdigest()[:16]
        for name in PUBLIC:
            with self.subTest(page=name):
                html = (ROOT / name).read_text(encoding="utf-8")
                self.assertEqual(html.count(f'css/print-basket.css?v={css_version}'), 1)
                self.assertEqual(
                    html.count(f'<script type="module" src="js/print-basket-ui.mjs?v={js_version}"></script>'),
                    1,
                )

    def test_module_reuses_existing_selection_and_session_storage_models(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn('from "./print-basket-selection.mjs"', source)
        self.assertIn('from "./print-basket-storage.mjs"', source)
        self.assertIn("addBasketActivity", source)
        self.assertIn("removeBasketActivity", source)
        self.assertIn("restoreStoredBasket", source)
        self.assertIn("writeStoredBasketIds", source)
        self.assertIn('fetch("/catalog.json"', source)
        self.assertIn("MutationObserver", source)

    def test_copy_and_accessibility_cover_add_remove_limit_and_counter(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            "Meine Drucksammlung",
            "Hinzufügen",
            "Entfernen",
            "Maximal 5 Druckseiten",
            'button.setAttribute("aria-pressed"',
            'node.setAttribute("role", "status")',
            'node.setAttribute("aria-live", "polite")',
        ):
            self.assertIn(marker, source)

    def test_slice_does_not_activate_zip_or_cross_activity_print(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for forbidden in (
            "prepareBasketPngZip",
            "stageBasketZipDownloadLink",
            "window.print",
            ".click()",
            "print-basket-zip-fetch",
            "print-basket-zip-link",
        ):
            self.assertNotIn(forbidden, source)
        for name in ("print.html", "stats.html", "traffic.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("print-basket-ui", html)
            self.assertNotIn("print-basket.css", html)

    def test_mobile_controls_keep_touch_targets(self):
        css = (ROOT / "css" / "print-basket.css").read_text(encoding="utf-8")
        self.assertIn(".basket-summary", css)
        self.assertIn(".basket-toggle", css)
        self.assertIn("min-height: 44px", css)
        self.assertIn("@media (max-width: 720px)", css)
        self.assertIn("min-height: 48px", css)

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
            f"Basket UI module syntax failed:\n{completed.stdout}\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
