"""Regression coverage for privacy-friendly, shared social follow footer."""
import hashlib
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (
    "index.html", "detail.html", "tiere.html", "fahrzeuge.html",
    "alphabet.html", "lernen.html", "figuren.html", "jahreszeiten.html",
    "essen-natur.html", "kalender.html", "kita.html",
)


class SocialFollowFooterTests(unittest.TestCase):
    def test_all_public_pages_use_same_assets(self):
        css_version = hashlib.sha256((ROOT / "css/social-footer.css").read_bytes()).hexdigest()[:16]
        js_version = hashlib.sha256((ROOT / "js/social-footer.js").read_bytes()).hexdigest()[:16]
        for name in PUBLIC:
            with self.subTest(page=name):
                page = (ROOT / name).read_text(encoding="utf-8")
                self.assertEqual(page.count(f'href="css/social-footer.css?v={css_version}"'), 1)
                self.assertEqual(page.count(f'src="js/social-footer.js?v={js_version}"'), 1)

    def test_print_and_dashboards_unchanged(self):
        for name in ("print.html", "stats.html", "traffic.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("social-footer.css", html)
            self.assertNotIn("social-footer.js", html)

    def test_owner_provided_destinations_and_safe_external_navigation(self):
        js = (ROOT / "js/social-footer.js").read_text(encoding="utf-8")
        self.assertIn('instagram: "https://www.instagram.com/ausmalwiese/"', js)
        self.assertIn('facebook: "https://www.facebook.com/share/1F6tVwJ7QK/"', js)
        self.assertIn('url.href === "https://www.facebook.com/share/1F6tVwJ7QK/"', js)
        self.assertIn('platform.key === "facebook"', js)
        self.assertIn("if (!links.length) return;", js)
        self.assertIn('url.protocol !== "https:"', js)
        self.assertIn("platform.hosts.includes(url.hostname)", js)
        self.assertIn('link.rel = "noopener noreferrer"', js)
        self.assertIn('link.target = "_blank"', js)
        self.assertIn('heading.textContent = "Folge uns"', js)
        self.assertNotIn("facebook.com/ausmalwiese", js)
        self.assertNotIn("facebook.com/sharer.php", js)
        self.assertNotIn("connect.facebook.net", js)


    def test_browser_logic_accepts_only_exact_owner_share_url(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js unavailable")
        harness = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');

function render(code) {
  function element(tag) {
    return {
      tag, children: [], attrs: {},
      append(...items) { this.children.push(...items); },
      setAttribute(key, val) { this.attrs[key] = val; }
    };
  }
  const body = element('body');
  vm.runInNewContext(code, { document: { body, createElement: element }, URL });
  assert.equal(body.children.length, 1);
  const footer = body.children[0];
  assert.equal(footer.tag, 'footer');
  const inner = footer.children[0];
  assert.equal(inner.children[0].textContent, 'Folge uns');
  return inner.children[1].children.map(a => ({
    href: a.href, target: a.target, rel: a.rel, label: a.attrs['aria-label']
  }));
}

const links = render(source);
assert.deepEqual(links.map(a => a.href), [
  'https://www.instagram.com/ausmalwiese/',
  'https://www.facebook.com/share/1F6tVwJ7QK/'
]);
for (const link of links) {
  assert.equal(link.target, '_blank');
  assert.equal(link.rel, 'noopener noreferrer');
  assert.match(link.label, /neuer Tab/);
}
const original = 'facebook: "https://www.facebook.com/share/1F6tVwJ7QK/"';
for (const candidate of [
  'https://www.facebook.com/share/not-approved/',
  'https://www.facebook.com/share/1F6tVwJ7QK/?ref=tracking',
  'https://www.facebook.com.evil.test/share/1F6tVwJ7QK/',
  'http://www.facebook.com/share/1F6tVwJ7QK/'
]) {
  const modified = source.replace(original, 'facebook: "' + candidate + '"');
  assert.notEqual(modified, source);
  assert.deepEqual(render(modified).map(a => a.href), [
    'https://www.instagram.com/ausmalwiese/'
  ]);
}
'''
        result = subprocess.run(
            [node, "-e", harness, str(ROOT / "js/social-footer.js")],
            cwd=ROOT, text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accessible_responsive_and_print_safe(self):
        css = (ROOT / "css/social-footer.css").read_text(encoding="utf-8")
        self.assertIn("min-height: 44px;", css)
        self.assertIn(".site-footer-link:focus-visible", css)
        self.assertIn("@media print", css)
        js = (ROOT / "js/social-footer.js").read_text(encoding="utf-8")
        self.assertIn('nav.setAttribute("aria-label"', js)
        self.assertIn('link.setAttribute("aria-label"', js)


if __name__ == "__main__":
    unittest.main()
