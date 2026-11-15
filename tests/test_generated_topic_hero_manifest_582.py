"""#582: source-manifest generated Topic Hero adapter, no runtime Topic invention."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from render_landing_hero_topic_js import render  # noqa: E402


class GeneratedTopicHero582Tests(unittest.TestCase):
    def test_generated_file_is_exact_reviewed_manifest_projection(self):
        js = (ROOT / "js/topic-hero-content.js").read_text(encoding="utf-8")
        self.assertEqual(js, render(ROOT))
        self.assertEqual(js.count("image: Object.freeze("), 1)
        self.assertIn("Object.prototype.hasOwnProperty.call", js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("landing-hero.v1.json", js)

    def test_check_mode_is_read_only_and_successful(self):
        target = ROOT / "js/topic-hero-content.js"
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        check = subprocess.run(
            [sys.executable, "tools/render_landing_hero_topic_js.py", "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), before)

    def test_runtime_approved_herbst_and_safe_unknown_fallback(self):
        source = ROOT / "js/topic-hero-content.js"
        subprocess.run(["node", "--check", str(source)], cwd=ROOT, check=True, timeout=15)
        script = r"""
const fs = require("node:fs");
const vm = require("node:vm");
const context = {globalThis: {}};
vm.runInNewContext(fs.readFileSync("js/topic-hero-content.js", "utf8"), context);
const api = context.globalThis.AusmalTopicHero;
console.log(JSON.stringify({
  schema: api.schema,
  herbst: api.get("herbst"),
  bauernhof: api.get("bauernhof"),
  ostern: api.get("ostern"),
  tanzen: api.get("tanzen"),
  invalid: api.get("../herbst"),
  prototype: api.get("constructor"),
}));
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, capture_output=True,
            text=True, timeout=20, check=True,
        )
        payload = json.loads(result.stdout)
        manifest = json.loads((ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8"))
        expected = manifest["topics"]["herbst"]
        self.assertEqual(payload["schema"], "rozkalns.ausmalwiese.topic-hero.v1")
        self.assertEqual(payload["herbst"]["intro"], expected["intro"])
        self.assertEqual(payload["herbst"]["image"]["src"], expected["image"])
        for key in ("width", "height", "alt", "sha256", "provenance", "approval_ref"):
            self.assertEqual(payload["herbst"]["image"][key], expected[key])
        for key in ("bauernhof", "ostern", "tanzen", "invalid", "prototype"):
            self.assertIsNone(payload[key])

    def test_versioned_single_script_and_initial_html_preserved(self):
        js = (ROOT / "js/topic-hero-content.js").read_bytes()
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        digest = hashlib.sha256(js).hexdigest()[:16]
        self.assertIn(f'js/topic-hero-content.js?v={digest}', home)
        self.assertEqual(home.count('src="js/topic-hero-content.js?v='), 1)
        for route, art in (("herbst", "herbst"), ("fahrzeuge", "fahrzeuge")):
            html = (ROOT / (route + ".html")).read_text(encoding="utf-8")
            self.assertIn(f'src="/assets/{art}-topic-hero.webp"', html)
            self.assertIn(f'canonical" href="https://ausmalwiese.de/{route}"', html)
            self.assertEqual(html.count('<h1 id="category-title">'), 1)


if __name__ == "__main__":
    unittest.main()
