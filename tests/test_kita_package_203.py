"""Kita Herbst package source contract for issue #203."""
import hashlib
import json
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = ["7297970", "8611574", "4089571", "1481910", "2472924"]


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.urls.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.urls.append(attrs["href"])


def catalog_entry(activity_id):
    root = f"/media/{activity_id}"
    return {
        "id": activity_id,
        "title": f"Title {activity_id}",
        "thumb": f"{root}/thumb.webp",
        "preview": f"{root}/preview.webp",
        "print": f"{root}/print.png",
    }


class KitaPackage203Tests(unittest.TestCase):
    def test_hub_and_detail_route_are_source_backed(self):
        hub = (ROOT / "kita.html").read_text(encoding="utf-8")
        detail = (ROOT / "kita-herbst.html").read_text(encoding="utf-8")
        docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        nginx = (ROOT / "deploy/nginx.conf").read_text(encoding="utf-8")

        self.assertIn('id="pakete"', hub)
        self.assertIn('href="/kita/herbst"', hub)
        self.assertIn("Herbst – 5 Aktivitäten", hub)
        self.assertIn('<link rel="canonical" href="https://ausmalwiese.de/kita/herbst">', detail)
        self.assertIn('data-kita-package-slug="herbst"', detail)
        self.assertIn("COPY kita-herbst.html /usr/share/nginx/html/", docker)
        self.assertIn("location = /kita/herbst {", nginx)
        self.assertIn("try_files /kita-herbst.html =404;", nginx)

    def test_detail_assets_are_content_hashed(self):
        parser = Assets()
        parser.feed((ROOT / "kita-herbst.html").read_text(encoding="utf-8"))
        checked = 0
        for url in parser.urls:
            if url.startswith("https:") or "?v=" not in url:
                continue
            path, version = url.lstrip("/").split("?v=", 1)
            if path == "js/stats.js":
                continue
            file_path = ROOT / path
            self.assertTrue(file_path.is_file(), path)
            self.assertEqual(version, hashlib.sha256(file_path.read_bytes()).hexdigest()[:16], path)
            checked += 1
        self.assertGreaterEqual(checked, 7)

    def run_resolver(self, catalog):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js required")
        script = """
import { getKitaPackage, resolveKitaPackage } from './js/kita-packages.mjs';
const catalog = JSON.parse(process.argv[1]);
const definition = getKitaPackage('herbst');
const resolved = resolveKitaPackage(definition, catalog);
console.log(JSON.stringify({
  ids: definition.activityIds,
  expectedSheets: definition.expectedSheets,
  complete: resolved.complete,
  sheetCount: resolved.sheetCount,
  missingIds: resolved.missingIds,
  resolvedIds: resolved.activities.map((item) => item.entry.id),
}));
"""
        result = subprocess.run(
            [node, "--input-type=module", "-e", script, json.dumps(catalog)],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=20,
        )
        return json.loads(result.stdout)

    def test_registry_resolves_exact_reviewed_order_to_five_sheets(self):
        result = self.run_resolver([catalog_entry(activity_id) for activity_id in EXPECTED_IDS])
        self.assertEqual(result["ids"], EXPECTED_IDS)
        self.assertEqual(result["resolvedIds"], EXPECTED_IDS)
        self.assertEqual(result["expectedSheets"], 5)
        self.assertEqual(result["sheetCount"], 5)
        self.assertTrue(result["complete"])
        self.assertEqual(result["missingIds"], [])

    def test_missing_or_extra_sheet_member_fails_closed(self):
        missing = self.run_resolver([catalog_entry(activity_id) for activity_id in EXPECTED_IDS[:-1]])
        self.assertFalse(missing["complete"])
        self.assertIn(EXPECTED_IDS[-1], missing["missingIds"])

        catalog = [catalog_entry(activity_id) for activity_id in EXPECTED_IDS]
        catalog[-1]["pages"] = [
            {"print": f"/media/{EXPECTED_IDS[-1]}/print-1.png"},
            {"print": f"/media/{EXPECTED_IDS[-1]}/print-2.png"},
        ]
        extra = self.run_resolver(catalog)
        self.assertFalse(extra["complete"])
        self.assertNotEqual(extra["sheetCount"], 5)

    def test_mjs_modules_use_javascript_mime_and_no_cache(self):
        nginx = (ROOT / "deploy/nginx.conf").read_text(encoding="utf-8")
        module_route = nginx.split("location ~* \\.mjs$ {", 1)[1].split("}", 1)[0]
        self.assertIn("default_type application/javascript;", module_route)
        self.assertIn('Cache-Control "no-cache"', module_route)
        self.assertIn("try_files $uri =404;", module_route)

    def test_package_activity_previews_use_bounded_card_column(self):
        css = (ROOT / "css" / "kita.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns: minmax(220px, 320px) minmax(0, 1fr);", css)
        self.assertIn('"card instruction"', css)
        self.assertIn('grid-template-areas: "step" "card" "instruction";', css)
        self.assertIn("width: min(100%, 360px);", css)

    def test_package_reuses_shared_basket_and_keeps_combined_print_gate_closed(self):
        detail = (ROOT / "kita-herbst.html").read_text(encoding="utf-8")
        package_js = (ROOT / "js" / "kita-package.mjs").read_text(encoding="utf-8")
        registry = (ROOT / "js" / "kita-packages.mjs").read_text(encoding="utf-8")
        basket = (ROOT / "js" / "print-basket-ui.mjs").read_text(encoding="utf-8")
        gate = (ROOT / "js" / "book-output-release-gate.mjs").read_text(encoding="utf-8")

        self.assertIn("print-basket-ui.mjs", detail)
        self.assertIn("ausmalwiese:print-basket-replace", package_js)
        self.assertIn("reconcileBasket", registry)
        self.assertIn("CURATED_BASKET_EVENT", basket)
        self.assertIn("reconcileBasket(request.ids, catalog)", basket)
        self.assertIn("bookCover = createBookCoverState();", basket)
        self.assertIn("combinedPrint: false", gate)
        self.assertNotIn("Ganzes Paket drucken", detail)

    def test_package_copy_discloses_replacement_and_missing_state(self):
        detail = (ROOT / "kita-herbst.html").read_text(encoding="utf-8")
        package_js = (ROOT / "js" / "kita-package.mjs").read_text(encoding="utf-8")
        self.assertIn("ersetzt deine aktuelle Drucksammlung", detail)
        self.assertIn("unvollständig", package_js)
        self.assertIn("disabled", detail)
        self.assertNotIn("PDF", detail)


if __name__ == "__main__":
    unittest.main()
