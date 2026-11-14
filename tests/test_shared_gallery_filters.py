"""Single filter renderer for every browse route: source and DOM contract."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = (
    "tiere.html", "fahrzeuge.html", "alphabet.html", "lernen.html",
    "figuren.html", "jahreszeiten.html", "essen-natur.html",
)
ROUTES = ("index.html", *CATEGORIES, "herbst.html")


class SharedGalleryFiltersTests(unittest.TestCase):
    def test_every_route_loads_exact_same_renderer_first(self):
        version = hashlib.sha256(
            (ROOT / "js/gallery-filter-panel.js").read_bytes()
        ).hexdigest()[:16]
        for filename in ROUTES:
            html = (ROOT / filename).read_text(encoding="utf-8")
            shared = "js/gallery-filter-panel.js?v=" + version
            controller = (
                "js/app.js?v=" if filename == "index.html" else
                "js/topic-landing.js?v=" if filename == "herbst.html" else
                "js/category.js?v="
            )
            self.assertEqual(html.count(shared), 1, filename)
            self.assertLess(html.index(shared), html.index(controller), filename)

    def test_one_topic_age_difficulty_count_reset_in_all_controllers(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        category = (ROOT / "js/category.js").read_text(encoding="utf-8")
        topic = (ROOT / "js/topic-landing.js").read_text(encoding="utf-8")
        self.assertEqual(homepage.count("data-gallery-filter-panel"), 1)
        self.assertEqual(homepage.count("data-reset-all-filters"), 1)
        self.assertIn("AusmalGalleryFilterPanel.mount", category)
        self.assertIn("AusmalGalleryFilterPanel.mount", topic)
        self.assertNotIn('className = "category-topic-filter"', category)
        self.assertNotIn("createMetadataSelect(", category)
        self.assertNotIn("category-topic-strip", category)
        self.assertIn("filterPanel?.setCount(filteredEntries.length)", category)
        self.assertIn("filterPanel?.setCount(filtered.length)", topic)
        for controller in (category, topic):
            self.assertIn('heading.querySelector(".catalog-total")?.remove()', controller)

    def test_mobile_css_and_no_repeated_footer_assets(self):
        css = "css/metadata-filters.css"
        version = hashlib.sha256((ROOT / css).read_bytes()).hexdigest()[:16]
        for filename in (*CATEGORIES, "herbst.html"):
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn(f"/css/metadata-filters.css?v={version}", html)
        herbst = (ROOT / "herbst.html").read_text(encoding="utf-8")
        self.assertEqual(herbst.count("social-footer.css?v="), 1)
        self.assertEqual(herbst.count("social-footer.js?v="), 1)

    def test_shared_renderer_behavior(self):
        if not shutil.which("node"):
            raise unittest.SkipTest("Node unavailable")
        script = r"""
const vm=require('node:vm'),fs=require('node:fs');
class Node {
  constructor(tag){
    this.tag=tag;this.children=[];this.dataset={};this.attrs={};
    this.value='';this.hidden=false;this.disabled=false;this.textContent='';
  }
  append(...nodes){this.children.push(...nodes)}
  replaceChildren(...nodes){this.children=nodes}
  setAttribute(name,value){this.attrs[name]=value}
}
const doc={createElement:tag=>new Node(tag),querySelector:()=>null};
const ctx={document:doc,globalThis:{}};
vm.runInNewContext(fs.readFileSync('js/gallery-filter-panel.js','utf8'),ctx);
const root=new Node('div'),panel=ctx.globalThis.AusmalGalleryFilterPanel.mount(root);
panel.setTopics([{id:'obst',label:'Obst'},{id:'herbst',label:'Herbst'}],'obst');
panel.setValues({age:'3-6',difficulty:'easy'});panel.setCount(2);
panel.setResetVisible(true);
const a={topic:panel.topic.value,age:panel.age.value,
  difficulty:panel.difficulty.value,count:panel.count.textContent,
  reset:panel.reset.hidden};
panel.setTopics([{id:'herbst',label:'Herbst'}],'herbst',true);
panel.setResetVisible(false);
const all=[];
function visit(node){all.push(node);node.children.forEach(visit)}
visit(root);
const count=key=>all.filter(n=>Object.prototype.hasOwnProperty.call(n.dataset,key)).length;
console.log(JSON.stringify({a,locked:panel.topic.disabled,topic:panel.topic.value,
reset:panel.reset.hidden,panels:count('galleryFilterPanel'),
topics:count('filterTopic'),ages:count('filterAge'),
difficulties:count('filterDifficulty'),counts:count('resultCount'),
resets:count('resetAllFilters'),labels:all.filter(n=>n.tag==='label').length}));
"""
        run = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True,
            capture_output=True, check=True, timeout=10,
        )
        result = json.loads(run.stdout)
        self.assertEqual(result["a"], {
            "topic": "obst", "age": "3-6", "difficulty": "easy",
            "count": "2 Malvorlagen", "reset": False,
        })
        self.assertTrue(result["locked"])
        self.assertEqual(result["topic"], "herbst")
        self.assertTrue(result["reset"])
        for item in ("panels", "topics", "ages", "difficulties", "counts", "resets"):
            self.assertEqual(result[item], 1, item)
        self.assertEqual(result["labels"], 3)


if __name__ == "__main__":
    unittest.main()
