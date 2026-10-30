"""Small dependency-free tests for the #189 random published activity shortcut."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
const vm=require("node:vm"), fs=require("node:fs");
const f=JSON.parse(process.argv[1]);
const button={disabled:true,listeners:{},addEventListener(name,fn){this.listeners[name]=fn;}};
const status={hidden:true,textContent:""};
const gallery={cards:[],replaceChildren(...nodes){this.cards=nodes.flatMap(n=>n.children||[n]);}};
const selectors={"[data-surprise-button]":button,"[data-surprise-status]":status,"[data-gallery]":gallery};
const document={
 querySelector(name){return selectors[name]||null;},
 querySelectorAll(){return [];},
 createDocumentFragment(){return {children:[],append(item){this.children.push(item);}};},
 createElement(){return {
   dataset:{},children:[],classList:{add(){},remove(){},toggle(){}},
   append(...items){this.children.push(...items);},
   setAttribute(){},textContent:"",disabled:false
 };},
};
let navigated="",fetchCalls=0;
const location={search:f.campaign?"?campaign=dortmund-01":"",pathname:"/index.html"};
const window={location:{hash:"",assign(url){navigated=url;}},addEventListener(){}};
const pseudoMath=Object.create(Math);
pseudoMath.random=()=>f.random===undefined?0:f.random;
const context={window,location,document,URLSearchParams,Intl,Math:pseudoMath,
 fetch:async(url)=>{
   fetchCalls++;
   if(url==="/categories.json")return {ok:true,json:async()=>({
     schema:"rozkalns.coloring-pages.categories.v2", revision:1, categories:[
       {id:"tiere",label:"Tiere"},{id:"fahrzeuge",label:"Fahrzeuge"},
       {id:"alphabet",label:"Alphabet"},{id:"lernen",label:"Lernen"},
       {id:"figuren",label:"Figuren & Helden"},{id:"jahreszeiten",label:"Jahreszeiten & Feste"}
     ]})};
   if(url==="/topics.json")return {ok:true,json:async()=>({schema:"rozkalns.coloring-pages.topics.v1",topics:[]})};
   if(f.mode==="network")throw Error("offline");
   if(f.mode==="http")return {ok:false};
   return {ok:true,json:async()=>f.mode==="invalid"?{}:f.items};
 }};
vm.runInNewContext(fs.readFileSync("js/app.js","utf8"),context);
setImmediate(()=>{
  if(f.click!==false && !button.disabled)button.listeners.click();
  console.log(JSON.stringify({disabled:button.disabled,navigated,statusHidden:status.hidden,
    statusText:status.textContent,fetchCalls,cardCount:gallery.cards.length}));
});
"""

class SurpriseMeTests(unittest.TestCase):
    def run_case(self, items=None, **options):
        if not shutil.which("node"):
            self.skipTest("node required")
        fixture={"items": items if items is not None else [], **options}
        proc=subprocess.run(["node","-e",HARNESS,json.dumps(fixture)], cwd=ROOT,
                            capture_output=True,text=True,check=True)
        return json.loads(proc.stdout)

    def test_button_has_correct_mobile_accessible_markup_and_asset(self):
        html=(ROOT/"index.html").read_text(encoding="utf-8")
        css=(ROOT/"css/surprise.css").read_text(encoding="utf-8")
        self.assertIn('type="button" data-surprise-button',html)
        self.assertIn('aria-label="Zufällige Malvorlage öffnen"',html)
        self.assertIn('data-surprise-status role="status" hidden',html)
        self.assertIn('Überrasch mich!',html)
        self.assertIn('.surprise-button:focus-visible',css)
        self.assertIn('min-height: 44px',css)
        self.assertLess(html.index('data-search-form'),html.index('data-surprise-button'))
        self.assertLess(html.index('data-surprise-button'),html.index('id="kategorien"'))

    def test_one_activity_navigates_using_gallery_detail_contract(self):
        result=self.run_case([{"id":"3147286","title":"Ein Hund","thumb":"media/h.webp"}],random=0.99)
        self.assertFalse(result["disabled"])
        self.assertEqual(result["navigated"],"detail.html?id=3147286")
        self.assertEqual(result["fetchCalls"],3)
        self.assertEqual(result["cardCount"],1)

    def test_multi_page_set_is_one_activity_and_preserves_campaign(self):
        result=self.run_case([
            {"id":"1111111","title":"Erstes Bild","thumb":"media/1.webp"},
            {"id":"2222222","title":"Mehrseitig","thumb":"media/2.webp",
             "pages":[{"source":"one"},{"source":"two"}]},
        ],random=.99,campaign=True)
        self.assertEqual(result["navigated"],"detail.html?id=2222222&campaign=dortmund-01")
        self.assertEqual(result["fetchCalls"],3)
        self.assertEqual(result["cardCount"],2)

    def test_skips_invalid_items_before_random_selection(self):
        result=self.run_case([
            {"id":"","title":"Unveröffentlicht","thumb":"media/missing.webp"},
            {"id":"7078476","title":"Veröffentlicht","thumb":"media/real.webp"},
            {"id":"9999999","thumb":"media/empty.webp"},
        ],random=0)
        self.assertEqual(result["navigated"],"detail.html?id=7078476")
        self.assertEqual(result["cardCount"],1)

    def test_empty_and_unavailable_catalog_disable_button_without_navigation(self):
        for mode,items in [("normal",[]),("network",[]),("http",[]),("invalid",[])]:
            with self.subTest(mode=mode):
                result=self.run_case(items,mode=mode)
                self.assertTrue(result["disabled"])
                self.assertEqual(result["navigated"],"")
                self.assertFalse(result["statusHidden"])
                self.assertTrue(result["statusText"])
                self.assertEqual(result["fetchCalls"],3)
