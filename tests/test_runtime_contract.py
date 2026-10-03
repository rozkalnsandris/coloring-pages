import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RuntimeContractTests(unittest.TestCase):
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

    def test_html_uses_content_versioned_css_and_js(self):
        versions = {}
        for path in ("css/app.css", "js/app.js", "js/detail.js", "js/print.js"):
            versions[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12]

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

    def test_dockerfile_is_application_only(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("nginxinc/nginx-unprivileged:1.29.1-alpine", dockerfile)
        self.assertNotIn("build_catalog.py", dockerfile)
        self.assertNotIn("build_media.py", dockerfile)
        self.assertNotIn("COPY originals", dockerfile)
        self.assertNotIn("COPY metadata", dockerfile)

    def test_frontend_fetches_runtime_catalog(self):
        for path in ("js/app.js", "js/detail.js", "js/print.js"):
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn('fetch("catalog.json"', source)


if __name__ == "__main__":
    unittest.main()
