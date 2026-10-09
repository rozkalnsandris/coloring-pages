"""Dependency-free Node UI regression checks and a conservative SEO preflight."""

import hashlib
import json
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def node_check(source, fixture):
    if not shutil.which("node"):
        raise unittest.SkipTest("Node is needed for dependency-free UI behavior tests")
    result = subprocess.run(
        ["node", "-e", source, json.dumps(fixture)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


HOME_HARNESS = r"""
const vm = require('node:vm');
const fs = require('node:fs');
const f = JSON.parse(process.argv[1]);
const empty = {hidden: true, textContent: 'Keine passenden Malvorlagen gefunden.'};
const count = {textContent: ''};
const total = {textContent: ''};
const gallery = {cards: [{demo:true}], replaceChildren(...nodes) {
  this.cards = nodes.flatMap(n => n.children || [n]);
}};
const selectors = {
  '[data-gallery]':gallery, '[data-empty-state]':empty,
  '[data-result-count]':count, '[data-total-count]':total,
};
const document = {
  querySelector:s => selectors[s] || null,
  querySelectorAll:() => [],
  createDocumentFragment:() => ({children:[], append(v){this.children.push(v)}}),
  createElement:tag => ({
    tag, dataset:{}, children:[],
    append(...items){this.children.push(...items)},
    setAttribute(){}, classList:{add(){}, remove(){}, toggle(){}},
  }),
};
const location = {search:''};
const window = {location:{hash:''}, addEventListener(){}};
const ctx = {window, document, location, URLSearchParams, Intl,
  fetch: async () => {
    if (f.mode === 'network') throw new Error('offline');
    return {ok:f.mode !== 'http', json: async () => f.catalog};
  },
};
vm.runInNewContext(fs.readFileSync('js/app.js','utf8'),ctx);
setImmediate(() => console.log(JSON.stringify({
  cards:gallery.cards.map(c => ({demo:!!c.demo, title:c.dataset?.title || ''})),
  message:empty.textContent, hidden:empty.hidden,
  count:count.textContent, total:total.textContent,
})));
"""


LIKE_HARNESS = r"""
const vm = require('node:vm');
const fs = require('node:fs');
const f = JSON.parse(process.argv[1]);
const handlers = {};
const attrs = {};
const likeStatus = {textContent:'', hidden:true};
const likeLabel = {textContent:''};
const likeCount = {textContent:'0'};
const heart = {textContent:'♡'};
const likeButton = {
  disabled:false, classList:{toggle(){},remove(){}},
  setAttribute(name,value){attrs[name]=value},
  querySelector:() => heart,
  addEventListener(name,cb){handlers[name]=cb},
};
const window = {ColoringStats:{
  toggleLike: async () => {
    if (f.fail) throw new Error('api unavailable');
    return {liked:true,like_count:1};
  },
}};
const code = fs.readFileSync('js/detail.js','utf8');
const section = code.slice(code.indexOf('function renderLikeState('),
                           code.indexOf('async function loadDetail()'));
vm.runInNewContext('let loadedEntryId="sample";\n'+section, {
  likeStatus, likeButton, likeLabel, likeCount, window,
});
Promise.resolve(handlers.click()).then(() => console.log(JSON.stringify({
  disabled:likeButton.disabled, text:likeStatus.textContent,
  hidden:likeStatus.hidden, pressed:attrs['aria-pressed'],
})));
"""


class UIErrorStateTests(unittest.TestCase):
    def test_catalog_http_network_and_invalid_json_are_not_demo_cards(self):
        for mode, catalog in [
            ("http", []), ("network", []), ("ok", {"error":"bad"})
        ]:
            with self.subTest(mode=mode):
                state = node_check(HOME_HARNESS, {"mode":mode,"catalog":catalog})
                self.assertEqual(state["cards"], [])
                self.assertFalse(state["hidden"])
                self.assertIn("konnten nicht geladen", state["message"])
                self.assertEqual(state["total"], "0")

    def test_empty_catalog_and_published_catalog(self):
        empty = node_check(HOME_HARNESS, {"mode":"ok","catalog":[]})
        self.assertEqual(empty["cards"], [])
        self.assertIn("keine Malvorlagen verfügbar", empty["message"])
        loaded = node_check(HOME_HARNESS, {"mode":"ok","catalog":[
            {"id":"1234567","title":"Dino","thumb":"/media/dino.webp",
             "age":"3-6","difficulty":"easy","category":"tiere"}
        ]})
        self.assertEqual(loaded["cards"], [{"demo":False,"title":"Dino"}])
        self.assertTrue(loaded["hidden"])
        self.assertEqual(loaded["total"], "1")

    def test_like_failure_is_visible_and_reenables_button(self):
        failed = node_check(LIKE_HARNESS, {"fail":True})
        self.assertFalse(failed["disabled"])
        self.assertFalse(failed["hidden"])
        self.assertIn("nicht gespeichert", failed["text"])
        good = node_check(LIKE_HARNESS, {"fail":False})
        self.assertFalse(good["disabled"])
        self.assertTrue(good["hidden"])
        self.assertEqual(good["pressed"], "true")


class PageHead(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = False
        self.description = False
        self.robots = ""
        self.canonicals = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "title":
            self.title = True
        if tag == "meta":
            if attrs.get("name") == "description" and attrs.get("content"):
                self.description = True
            if attrs.get("name") == "robots":
                self.robots = attrs.get("content", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))


class SEOPreflightTests(unittest.TestCase):
    def test_initial_public_heads_and_admin_noindex(self):
        for page in ("index.html", "detail.html", "kita.html"):
            parser = PageHead()
            parser.feed((ROOT / page).read_text(encoding="utf-8"))
            self.assertTrue(parser.title, page)
            self.assertTrue(parser.description, page)
            self.assertFalse(parser.canonicals,
                             "Do not introduce unverified canonical before LIVE route preflight")
        for page in ("stats.html", "traffic.html"):
            parser = PageHead()
            parser.feed((ROOT / page).read_text(encoding="utf-8"))
            self.assertIn("noindex", parser.robots)

    def test_preflight_is_not_a_fake_sitemap(self):
        document = (ROOT / "docs/SEO_PREFLIGHT_V1.md").read_text(encoding="utf-8")
        self.assertIn("production catalogue", document)
        self.assertIn("HTTP 200", document)
        self.assertIn("Cloudflare Access", document)
        self.assertFalse((ROOT / "sitemap.xml").exists())

    def test_error_status_is_in_initial_markup_and_versions_match(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        detail = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertIn('data-empty-state role="status" aria-live="polite"', index)
        self.assertIn('data-like-status role="status" aria-live="polite"', detail)
        for filename, pages in (
            ("js/app.js", ("index.html","detail.html","kita.html")),
            ("js/detail.js", ("detail.html",)),
        ):
            version = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()[:16]
            for page in pages:
                html = (ROOT / page).read_text(encoding="utf-8")
                self.assertIn(filename+"?v="+version, html, page)


if __name__ == "__main__":
    unittest.main()
