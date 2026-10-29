"""Run pure JavaScript basket model cases in ordinary Python unittest CI.

Node is available on the GitHub-hosted Ubuntu runner; use no npm install,
browser, network access or external test library.
"""

from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BasketSelectionJavaScriptTests(unittest.TestCase):
    def test_pure_model_node_cases(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js required to exercise the basket model")
        completed = subprocess.run(
            [
                node,
                "--test",
                "tests/test_print_basket_selection.mjs",
                "tests/test_book_cover_capacity_199.mjs",
                "tests/test_book_cover_state_199.mjs",
                "tests/test_book_cover_a4_contract_199.mjs",
                "tests/test_book_cover_png_parser_199.mjs",
                "tests/test_book_cover_rgb_safe_frame_199.mjs",
                "tests/test_book_cover_rgb_png_encoder_199.mjs",
                "tests/test_book_cover_png_decoded_verify_199.mjs",
                "tests/test_book_cover_font_preflight_199.mjs",
                "tests/test_book_cover_text_layout_199.mjs",
                "tests/test_book_cover_canvas_render_199.mjs",
                "tests/test_book_cover_canvas_rgb_199.mjs",
                "tests/test_book_cover_png_pipeline_199.mjs",
                "tests/test_book_export_plan_199.mjs",
                "tests/test_book_output_bundle_199.mjs",
                "tests/test_book_output_session_199.mjs",
                "tests/test_book_output_release_gate_199.mjs",
                "tests/test_book_print_media_199.mjs",
                "tests/test_book_print_document_199.mjs",
                "tests/test_book_preview_plan_199.mjs",
                "tests/test_book_preview_navigation_199.mjs",
                "tests/test_book_preview_labels_199.mjs",
                "tests/test_book_preview_view_199.mjs",
                "tests/test_book_preview_media_199.mjs",
                "tests/test_print_basket_storage.mjs",
                "tests/test_print_zip_store.mjs",
                "tests/test_print_basket_zip_fetch.mjs",
                "tests/test_print_basket_zip_link.mjs",
                "tests/test_print_basket_print_plan.mjs",
                "tests/test_print_basket_print_media.mjs",
                "tests/test_print_basket_print_canvas.mjs",
                "tests/test_print_basket_print_footer.mjs",
                "tests/test_print_basket_print_staged_document.mjs",
                "tests/test_print_basket_print_session.mjs",
                "tests/test_print_basket_print_lifecycle.mjs",
                "tests/test_print_basket_print_host_199.mjs",
                "tests/test_print_basket_real_media_qa_199.mjs",
                "tests/test_print_basket_ui_print_gate.mjs",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"Node basket-model tests failed:\n{completed.stdout}\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
