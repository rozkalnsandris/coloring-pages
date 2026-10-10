import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RuntimeContractTests(unittest.TestCase):
    def test_home_hero_lcp_image_has_high_fetch_priority(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        marker = '<img src="assets/hero-illustration.png"'
        self.assertEqual(html.count(marker), 1)
        hero_img = html.split(marker, 1)[1].split(">", 1)[0]
        self.assertIn('width="1408"', hero_img)
        self.assertIn('height="736"', hero_img)
        self.assertIn('fetchpriority="high"', hero_img)
        self.assertNotIn('loading="lazy"', hero_img)

    def test_simple_deploy_contract_declares_read_only_content_bind(self):
        contract = json.loads((ROOT / ".simple-deploy.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "rozkalns.simple-deploy.consumer.v1")
        self.assertEqual(contract["repository"], "rozkalnsandris/coloring-pages")
        self.assertEqual(contract["image"], "ghcr.io/rozkalnsandris/coloring-pages")
        self.assertEqual(contract["build"]["architecture"], "linux/arm64")
        self.assertEqual(contract["target"]["runtime_class"], "rpi5-compose")
        self.assertEqual(contract["compose"]["file"], "deploy/docker-compose.simple.yml")
        self.assertEqual(contract["compose"]["service"], "coloring-pages")
        self.assertEqual(contract["health"]["liveness_path"], "/health")
        self.assertEqual(contract["health"]["readiness"]["path"], "/ready")
        self.assertEqual(
            contract["persistence"]["volumes"],
            ["coloring_pages_content"],
        )

    def test_compose_mounts_only_public_content_read_only(self):
        compose = (ROOT / "deploy/docker-compose.simple.yml").read_text(encoding="utf-8")
        for required in (
            "read_only: true",
            "no-new-privileges:true",
            "cap_drop:",
            "- ALL",
            "tmpfs:",
            "http://127.0.0.1:8080/ready",
            "coloring_pages_content:/var/lib/coloring-pages/public:ro",
            "volumes:",
            "coloring_pages_content:",
        ):
            self.assertIn(required, compose)
        self.assertNotIn("/srv/coloring-pages-content/public", compose)
        self.assertNotIn("/srv/coloring-pages-content/inbox", compose)
        self.assertNotIn("/srv/coloring-pages-content/originals", compose)
        self.assertNotIn("/srv/coloring-pages-content/state", compose)

    def test_nginx_serves_runtime_catalog_and_media(self):
        nginx = (ROOT / "deploy/nginx.conf").read_text(encoding="utf-8")
        self.assertIn("location = /catalog.json", nginx)
        self.assertIn("location /media/", nginx)
        self.assertIn("root /var/lib/coloring-pages/public", nginx)
        self.assertIn('Cache-Control "no-cache"', nginx)
        self.assertIn('Cache-Control "public, max-age=31536000, immutable"', nginx)
        css_js_block = nginx.split("location ~* \\.(?:css|js)$ {", 1)[1].split("}", 1)[0]
        self.assertIn('Cache-Control "no-cache"', css_js_block)
        self.assertNotIn("immutable", css_js_block)

    def test_html_uses_content_versioned_css_and_js(self):
        versions = {}
        for path in ("css/app.css", "js/app.js", "js/detail.js", "js/print.js"):
            versions[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:16]

        index = (ROOT / "index.html").read_text(encoding="utf-8")
        detail = (ROOT / "detail.html").read_text(encoding="utf-8")
        print_html = (ROOT / "print.html").read_text(encoding="utf-8")

        self.assertIn(f'href="css/app.css?v={versions["css/app.css"]}"', index)
        self.assertIn(f'src="js/app.js?v={versions["js/app.js"]}"', index)
        self.assertIn(f'href="css/app.css?v={versions["css/app.css"]}"', detail)
        self.assertIn(f'src="js/app.js?v={versions["js/app.js"]}"', detail)
        self.assertIn(f'src="js/detail.js?v={versions["js/detail.js"]}"', detail)
        self.assertIn(f'href="css/app.css?v={versions["css/app.css"]}"', print_html)
        self.assertIn(f'src="js/print.js?v={versions["js/print.js"]}"', print_html)

    def test_html_declares_branded_svg_favicon(self):
        favicon = ROOT / "assets/favicon.svg"
        self.assertTrue(favicon.is_file())
        svg = favicon.read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 64 64"', svg)
        self.assertIn("#ff776d", svg)
        self.assertNotIn("<rect", svg)
        self.assertNotIn("#f5f9ff", svg)

        favicon_version = hashlib.sha256(favicon.read_bytes()).hexdigest()[:16]
        favicon_link = (
            '<link rel="icon" type="image/svg+xml" '
            f'href="assets/favicon.svg?v={favicon_version}">'
        )
        for path in ("index.html", "detail.html", "print.html"):
            html = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn(favicon_link, html)

    def test_dockerfile_embeds_importer_runtime_without_media(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("nginxinc/nginx-unprivileged:1.29.1-alpine", dockerfile)
        self.assertIn("USER root", dockerfile)
        self.assertIn("apk add --no-cache python3 py3-pillow", dockerfile)
        self.assertIn(
            "COPY tools/coloring-pages-import /usr/local/bin/coloring-pages-import",
            dockerfile,
        )
        self.assertIn(
            "COPY metadata/categories.json /usr/local/share/coloring-pages/categories.json",
            dockerfile,
        )
        self.assertIn("chmod 0555 /usr/local/bin/coloring-pages-import", dockerfile)
        self.assertIn(
            "test -x /usr/local/bin/coloring-pages-regenerate-derivatives",
            dockerfile,
        )
        self.assertIn(
            "rozkalns.coloring-pages.existing-derivative-regeneration.v1",
            dockerfile,
        )
        self.assertIn('assert d["issue"] == 74', dockerfile)
        self.assertIn("USER 101", dockerfile)
        self.assertIn("COPY index.html detail.html print.html /usr/share/nginx/html/", dockerfile)
        self.assertNotIn("build_catalog.py", dockerfile)
        self.assertNotIn("build_media.py", dockerfile)
        self.assertNotIn("COPY originals", dockerfile)
        self.assertNotIn("COPY metadata /usr/share/nginx/html", dockerfile)

    def test_simple_deploy_release_gate_stays_narrow(self):
        workflow = (
            ROOT / ".github/workflows/simple-deploy.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('- "Dockerfile"', workflow)
        self.assertNotIn('tools/coloring-pages-regenerate-derivatives', workflow)
        self.assertNotIn('deploy/existing-derivative-regeneration-v1.json', workflow)

    def test_importer_runtime_contract_is_isolated_and_digest_bound(self):
        contract = json.loads(
            (ROOT / "deploy/importer-runtime.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            contract["schema"],
            "rozkalns.coloring-pages.importer-runtime.v1",
        )
        self.assertEqual(
            contract["image"],
            "ghcr.io/rozkalnsandris/coloring-pages",
        )
        self.assertEqual(
            contract["image_identity"],
            "immutable-digest-required-at-live",
        )
        self.assertEqual(
            contract["entrypoint"],
            "/usr/local/bin/coloring-pages-import",
        )
        self.assertEqual(
            contract["host_content_root"],
            "/srv/coloring-pages-content",
        )
        self.assertEqual(contract["network"], "none")
        self.assertTrue(contract["read_only_root"])
        self.assertEqual(contract["tmpfs"], ["/tmp"])
        self.assertEqual(contract["cap_drop"], ["ALL"])
        self.assertTrue(contract["no_new_privileges"])
        self.assertTrue(contract["run_as_host_operator"])
        self.assertEqual(contract["source_scope"], "direct-child-of-inbox")
        self.assertEqual(contract["content_mount"], "read-write")
        self.assertEqual(
            contract["category_registry"],
            "/usr/local/share/coloring-pages/categories.json",
        )
        self.assertTrue(contract["category_argument_required"])
        self.assertEqual(contract["host_dependencies"], ["docker"])
        self.assertEqual(
            contract["long_running_web_mount"],
            {
                "source_identity": "coloring_pages_content",
                "target": "/var/lib/coloring-pages/public",
                "mode": "read-only",
            },
        )
        self.assertIn("host-python-install", contract["forbidden"])
        self.assertIn("host-pillow-install", contract["forbidden"])
        self.assertIn("production-image-redeploy-per-import", contract["forbidden"])

    def test_category_registry_is_reflected_in_detail_ui_and_ingest_docs(self):
        registry = json.loads(
            (ROOT / "metadata/categories.json").read_text(encoding="utf-8")
        )
        detail_js = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        ingest_docs = (
            ROOT / "docs/CHAT_TO_DRIVE_INGESTION_V1.md"
        ).read_text(encoding="utf-8")

        for category in registry["categories"]:
            self.assertIn(
                f'{category["id"]}: "{category["label"]}"',
                detail_js,
            )
            self.assertIn(f'`{category["id"]}`', ingest_docs)

        self.assertNotIn('`rettungshunde`', ingest_docs)

    def test_detail_print_action_uses_embedded_html_print_view(self):
        detail_js = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        print_js = (ROOT / "js/print.js").read_text(encoding="utf-8")
        print_html = (ROOT / "print.html").read_text(encoding="utf-8")
        detail_html = (ROOT / "detail.html").read_text(encoding="utf-8")

        self.assertIn(
            'setAction(printLink, allPrintable ? `print.html?id=${encodeURIComponent(entry.id)}` : "");',
            detail_js,
        )
        self.assertIn('document.createElement("iframe")', detail_js)
        self.assertIn('printUrl.searchParams.set("embedded", "1")', detail_js)
        self.assertIn(
            'printWindow.addEventListener("afterprint", cleanup, { once: true })',
            detail_js,
        )
        self.assertIn("printWindow.print()", detail_js)
        self.assertIn("window.location.assign(href)", detail_js)
        self.assertIn("function entryPrintPages(entry)", print_js)
        self.assertIn("entry.pages", print_js)
        self.assertNotIn("PRINT_CLEAR_LUMA", print_js)
        self.assertNotIn("PRINT_SOLID_LUMA", print_js)
        self.assertIn("A4_PAGE_WIDTH_MM = 210", print_js)
        self.assertIn("A4_PAGE_HEIGHT_MM = 297", print_js)
        self.assertIn("function printOrientation(width, height)", print_js)
        self.assertIn("function isCanonicalA4Raster(width, height)", print_js)
        self.assertIn("function a4CanvasSize(width, height)", print_js)
        self.assertIn("width === 2480 && height === 3508", print_js)
        self.assertIn("width === 3508 && height === 2480", print_js)
        self.assertIn("if (isCanonicalA4Raster(width, height))", print_js)
        self.assertIn('return width > height ? "landscape" : "portrait"', print_js)
        self.assertIn('sheet.className = `print-sheet is-${orientation}`', print_js)
        self.assertIn("Math.ceil(width / a4Ratio)", print_js)
        self.assertIn("Math.ceil(height * a4Ratio)", print_js)
        self.assertIn("const offsetX = Math.floor", print_js)
        self.assertIn("const offsetY = Math.floor", print_js)
        self.assertNotIn("printCanvas.width = image.naturalWidth;", print_js)
        self.assertNotIn("printCanvas.height = image.naturalHeight;", print_js)
        self.assertNotIn("getImageData", print_js)
        self.assertNotIn("putImageData", print_js)
        self.assertIn("context.drawImage(", print_js)
        self.assertIn('document.querySelector("[data-print-pages]")', print_js)
        self.assertIn('document.createElement("canvas")', print_js)
        self.assertIn(
            'notifyParent("coloring-pages-print-ready", id)',
            print_js,
        )
        self.assertIn(
            'printButton?.addEventListener("click", () => window.print())',
            print_js,
        )
        self.assertIn('class="print-sheet"', print_html)
        self.assertIn("data-print-pages", print_html)
        self.assertNotIn("data-print-canvas", print_html)
        self.assertNotIn("<embed", print_html)
        self.assertNotIn("<object", print_html)
        self.assertIn("setAction(pngLink, page.print)", detail_js)
        self.assertIn("data-detail-page-switcher", detail_html)
        self.assertIn("data-detail-pages", detail_html)
        self.assertIn("data-action-png download", detail_html)
        self.assertIn("PNG herunterladen", detail_html)

        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn("break-after: page", css)
        self.assertIn("@page a4-portrait", css)
        self.assertIn("size: A4 portrait", css)
        self.assertIn("@page a4-landscape", css)
        self.assertIn("size: A4 landscape", css)
        self.assertIn("page: a4-portrait", css)
        self.assertIn("page: a4-landscape", css)

    def test_legacy_print_scale_keeps_historical_one_pixel_fit(self):
        migration = (
            ROOT / "tools/coloring-pages-migrate-legacy-print-scale"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "artwork_margin_px=print_master.OUTER_WHITE_BORDER",
            migration,
        )

    def test_home_catalog_renders_twenty_items_per_batch(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")

        self.assertIn('id="new-pages-gallery"', index)
        self.assertIn("data-load-more", index)
        self.assertIn("Mehr anzeigen", index)
        self.assertIn("const CATALOG_PAGE_SIZE = 20;", app)
        self.assertIn("matches.slice(0, visibleLimit)", app)
        self.assertIn("visibleLimit += CATALOG_PAGE_SIZE;", app)
        self.assertIn('image.loading = "lazy";', app)
        self.assertIn(".gallery-actions", css)

    def test_frontend_fetches_runtime_catalog(self):
        for path in ("js/app.js", "js/detail.js", "js/print.js"):
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn('fetch("catalog.json"', source)


if __name__ == "__main__":
    unittest.main()
