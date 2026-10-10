"""Routing/asset contracts and the small Kita controller (Node, no npm packages)."""
import hashlib
import json
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.urls.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.urls.append(attrs['href'])


class KitaTests(unittest.TestCase):
    def test_packaged_route_and_versioned_assets(self):
        docker = (ROOT / 'Dockerfile').read_text()
        self.assertIn('COPY stats.html traffic.html kita.html /usr/share/nginx/html/', docker)
        nginx = (ROOT / 'deploy/nginx.conf').read_text()
        route = nginx.split('location = /kita {')[1].split('}')[0]
        self.assertIn('try_files /kita.html =404;', route)
        self.assertIn('Cache-Control "no-cache"', route)
        self.assertIn('return 308 /kita$is_args$args;', nginx)
        assets = Assets()
        assets.feed((ROOT / 'kita.html').read_text())
        for url in assets.urls:
            if url.startswith('https:'):
                continue
            path, version = url.split('?v=')
            self.assertTrue((ROOT / path).is_file())
            if path == 'js/stats.js':
                self.assertEqual(version, 'privacy-v1')
            elif path == 'css/fonts.css':
                self.assertEqual(version, 'privacy-ofl-v1')
            else:
                self.assertEqual(version, hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:16])
        self.assertLess(assets.urls.index(next(x for x in assets.urls if x.startswith('js/app.js'))),
                        assets.urls.index(next(x for x in assets.urls if x.startswith('js/kita.js'))))

    def test_kita_trailing_slash_redirect_is_relative_and_query_preserving(self):
        nginx = (ROOT / 'deploy/nginx.conf').read_text()
        redirect = nginx.split('location = /kita/ {', 1)[1].split('}', 1)[0]
        self.assertIn('absolute_redirect off;', redirect)
        self.assertIn('return 308 /kita$is_args$args;', redirect)
        # Keep this setting local to the Kita slash route.
        self.assertEqual(nginx.count('absolute_redirect off;'), 1)

    def run_controller(self, catalog, campaign='dortmund-01', ok=True):
        if not shutil.which('node'):
            self.skipTest('Node is needed for the dependency-free browser-controller check')
        harness = r'''
const vm = require('node:vm');
const fs = require('node:fs');
const fixture = JSON.parse(process.argv[1]);
const links = [
  {href:'http://site.test/index.html#neu'},
  {href:'http://site.test/detail.html?id=3147286'},
  {href:'http://elsewhere.test/index.html'},
  {href:'http://site.test/kita#beispiele'},
];
let cards = [], visits = 0, fetches = [];
const status = {hidden:false, textContent:'Loading'};
const target = {replaceChildren: (...items) => cards = items, querySelectorAll: () => []};
const context = {
  URL, URLSearchParams,
  location: {search:'?campaign='+encodeURIComponent(fixture.campaign),
    href:'http://site.test/kita', origin:'http://site.test'},
  document: {querySelector: (selector) => selector === '[data-kita-examples]' ? target : status,
    querySelectorAll: () => links},
  window: {ColoringStats:{trackVisit: () => visits++}},
  fetch: async (url, options) => {fetches.push({url, options});
    return {ok:fixture.ok, json:async () => fixture.catalog};},
  createCatalogCard: (entry) => ({id:entry.id, title:entry.title, thumb:entry.thumb}),
};
vm.runInNewContext(fs.readFileSync('js/kita.js','utf8'), context);
setImmediate(() => console.log(JSON.stringify({cards, status, visits, links, fetches})));
'''
        result = subprocess.run(['node', '-e', harness, json.dumps({
            'catalog': catalog, 'campaign': campaign, 'ok': ok,
        })], cwd=ROOT, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_only_reviewed_ids_use_current_catalog_content(self):
        result = self.run_controller([
            {'id': 'unreviewed', 'title': 'Dino', 'thumb': '/other.webp', 'category': 'tiere'},
            {'id': '7078476', 'title': 'Current fire engine title', 'thumb': '/new-fire.webp'},
            {'id': '3147286', 'title': 'Current dinosaur title', 'thumb': '/new-dino.webp'},
            None,
        ])
        self.assertEqual([x['id'] for x in result['cards']], ['3147286', '7078476'])
        self.assertEqual(result['cards'][0]['thumb'], '/new-dino.webp')
        self.assertEqual(result['cards'][1]['title'], 'Current fire engine title')
        self.assertTrue(result['status']['hidden'])
        self.assertEqual(result['visits'], 1)
        self.assertEqual(result['fetches'], [{'url': 'catalog.json', 'options': {'cache': 'no-store'}}])

    def test_empty_invalid_and_failed_catalog_keep_fallback(self):
        for catalog, ok in [([], True), ({'error': 'invalid'}, True), ([], False)]:
            with self.subTest(catalog=catalog, ok=ok):
                result = self.run_controller(catalog, ok=ok)
                self.assertFalse(result['status']['hidden'])
                self.assertEqual(result['cards'], [])
                self.assertIn('nicht verfügbar', result['status']['textContent'])

    def test_campaign_is_allowlisted_and_only_added_to_catalog_and_detail(self):
        result = self.run_controller([])
        self.assertEqual(result['links'][0]['href'], 'http://site.test/index.html?campaign=dortmund-01#neu')
        self.assertEqual(result['links'][1]['href'], 'http://site.test/detail.html?id=3147286&campaign=dortmund-01')
        self.assertEqual(result['links'][2]['href'], 'http://elsewhere.test/index.html')
        self.assertEqual(result['links'][3]['href'], 'http://site.test/kita#beispiele')
        result = self.run_controller([], campaign='recipient@example.com')
        self.assertEqual(result['links'][0]['href'], 'http://site.test/index.html#neu')


if __name__ == '__main__':
    unittest.main()
