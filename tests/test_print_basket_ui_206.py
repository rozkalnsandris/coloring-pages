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

    def test_zip_requires_explicit_visitor_download_and_print_remains_off(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn('panelButton("ZIP vorbereiten", "prepare-zip")', source)
        self.assertIn("stageBasketZipDownloadLink(zip)", source)
        self.assertIn("slot.replaceChildren(staged.link);", source)
        self.assertIn('note.textContent = "Alles drucken ist noch nicht verfügbar."', source)
        for forbidden in ("window.print", ".click()", "innerHTML", "window.open("):
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

    def test_header_indicator_uses_actual_menu_parent(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn('const actions = header.querySelector(".header-actions");', source)
        self.assertIn("if (menu) actions.insertBefore(root, menu);", source)
        self.assertIn("else actions.append(root);", source)
        self.assertNotIn("header.insertBefore(root, menu)", source)
        for name in PUBLIC:
            with self.subTest(page=name):
                html = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn('class="header-actions"', html)

    def test_gallery_observer_does_not_rewrite_toggle_labels(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        observer = source.split("observer = new MutationObserver(() => {", 1)[1].split("});", 1)[0]
        self.assertIn("enhanceCards();", observer)
        self.assertIn("enhanceDetail();", observer)
        self.assertNotIn("syncButtons();", observer)

    def test_pressed_toggle_keeps_stable_accessible_name(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        label = source.split('button.setAttribute(\n      "aria-label",', 1)[1].split("\n    );", 1)[0]
        self.assertIn('"Drucksammlung: " + entry.title', label)
        self.assertNotIn("selected", label)
        self.assertIn('button.setAttribute("aria-pressed", String(selected));', source)

    def test_basket_dialog_modal_and_focus(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            'root.setAttribute("aria-haspopup", "dialog")',
            'root.setAttribute("aria-controls", "basket-dialog")',
            'node.setAttribute("aria-labelledby", "basket-dialog-title")',
            'dialog.showModal();',
            'node.addEventListener("close", () => { resetZip(); summary?.focus(); });',
            'close.autofocus = true',
        ):
            self.assertIn(marker, source)

    def test_basket_dialog_reuses_atomic_selection_and_is_export_gated(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            "moveBasketActivity(basket.ids", "removeBasketActivity(basket.ids",
            "commitBasket(clearBasket()", "writeStoredBasketIds(next.ids)",
            "link.textContent = entry.title", "encodeURIComponent(id)",
            "Alles drucken ist noch nicht verfügbar.",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("innerHTML", source)
        css = (ROOT / "css" / "print-basket.css").read_text(encoding="utf-8")
        self.assertIn(".basket-dialog::backdrop", css)
        self.assertIn("max-height: calc(100dvh - 24px)", css)

    def test_basket_dialog_empty_state_and_boundary_controls(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn('empty.textContent = "Noch keine Malvorlagen ausgewählt."', source)
        self.assertIn('dialog.querySelector("[data-basket-empty]").hidden', source)
        self.assertIn('dialog.querySelector("[data-basket-clear]").disabled', source)
        self.assertIn('["Nach oben", "up", index === 0]', source)
        self.assertIn('["Nach unten", "down", index === basket.ids.length - 1]', source)
        self.assertIn('if (summary && typeof dialog.showModal === "function") summary.disabled = false;', source)

    def test_zip_refreshes_catalogue_and_revalidates_selection_before_fetch(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            'readStoredBasketIds()',
            'JSON.stringify(selectedIds) !== JSON.stringify(basket.ids)',
            'fetch("/catalog.json", {',
            'cache: "no-store", credentials: "omit", redirect: "error", signal: controller.signal',
            'expandBasketForExport(selectedIds, catalogFresh)',
            'pages.length !== basket.sheetCount',
            'page.printUrl !== basket.pages[index]?.printUrl',
            'prepareBasketPngZip(pages, {',
            'origin: window.location.origin, signal: controller.signal',
        ):
            self.assertIn(marker, source)

    def test_zip_cancels_and_releases_blob_on_selection_change_or_close(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        for marker in (
            'zipController?.abort();',
            'stagedZip.link.remove();',
            'stagedZip.dispose();',
            'node.addEventListener("close", () => { resetZip(); summary?.focus(); });',
            'window.addEventListener("pagehide", resetZip);',
            'if (action === "cancel-zip")',
            'if (epoch !== zipEpoch || controller.signal.aborted || !dialog.open) return;',
            'resetZip();\n  resetPreview();\n  basket = next;',
        ):
            self.assertIn(marker, source)
        self.assertNotIn("staged.link.click()", source)
        self.assertNotIn("setTimeout(", source)

    def test_zip_ready_link_is_accessible_and_empty_basket_blocks_prepare(self):
        source = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        self.assertIn('zipPrepare.disabled = true;', source)
        self.assertIn('zipPrepare.disabled = basket.ids.length === 0 || zipBusy || bookCover.enabled;', source)
        self.assertIn('zipStatus.setAttribute("role", "status");', source)
        self.assertIn('zipStatus.setAttribute("aria-live", "polite");', source)
        css = (ROOT / "css" / "print-basket.css").read_text(encoding="utf-8")
        self.assertIn(".basket-zip-download", css)
        self.assertIn("min-height: 48px;", css)

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
