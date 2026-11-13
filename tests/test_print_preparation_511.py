"""Regression coverage for UI/UX audit #511 finding 17 print preparation recovery."""

import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PrintPreparation511Tests(unittest.TestCase):
    def test_detail_has_visible_print_preparation_and_manual_fallback(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertIn('data-print-status role="status" aria-live="polite"', html)
        self.assertIn('data-print-fallback-wrap hidden', html)
        self.assertIn('data-print-fallback', html)
        self.assertIn('Druckansicht öffnen', html)

    def test_print_preparation_is_bounded_and_never_auto_redirects_on_error(self):
        source = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        self.assertIn("const PRINT_PREP_TIMEOUT_MS=8000;", source)
        self.assertIn('setPrintFeedback("Druckansicht wird vorbereitet …")', source)
        self.assertIn("window.setTimeout(() => {", source)
        self.assertIn("}, PRINT_PREP_TIMEOUT_MS);", source)
        self.assertIn('event.data.type === "coloring-pages-print-error"', source)
        self.assertIn("showFallback(", source)
        self.assertNotIn("window.location.assign(href)", source)

    def test_print_cancel_or_completion_restores_primary_action(self):
        source = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        self.assertIn('printWindow.addEventListener("afterprint", cleanup, { once: true })', source)
        self.assertIn("setPrintBusy(false);", source)
        self.assertIn("if (!preserveFeedback) setPrintFeedback();", source)
        self.assertIn('printLink.getAttribute("aria-disabled")==="true"', source)

    def test_detail_js_content_hash_is_current(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        digest = hashlib.sha256((ROOT / "js/detail.js").read_bytes()).hexdigest()[:16]
        self.assertIn(f"js/detail.js?v={digest}", html)


if __name__ == "__main__":
    unittest.main()
