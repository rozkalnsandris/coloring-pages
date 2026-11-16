"""#586: real managed Topic Hero integration, including new label-only Topics."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManagedTopicHeroFallback586Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        harness = r"""
const fs = require("node:fs");
const vm = require("node:vm");
const app = fs.readFileSync("js/app.js", "utf8");

function extract(name) {
  const match = app.match(new RegExp("function " + name + "\\([^)]*\\) \\{[\\s\\S]*?\\n\\}"));
  if (!match) throw new Error("missing real app function: " + name);
  return match[0];
}
const artClasses = new Set();
const navLink = {href: "#hero"};
const art = {
  hidden: true, children: [],
  replaceChildren(...nodes) { this.children = nodes; },
  append(node) { this.children.push(node); }
};
const context = {
  topicRegistry: [{id:"herbst",label:"Herbst"},{id:"tanzen",label:"Tanzen"}],
  activeTopic: "", categoriesExpanded: false,
  categoriesSection: {hidden:false, contains() {return false;}},
  galleryTopicActions: {hidden:true},
  topicField: {hidden:false},
  galleryHeading: {textContent:"Malvorlagen"},
  showCategoriesButton: {setAttribute(key, value) {this[key] = value;}},
  homeHero: {hidden:false},
  focusedTopicHero: {
    hidden:true,
    classList: {
      toggle(name, enabled) {
        if (enabled) artClasses.add(name); else artClasses.delete(name);
      },
      remove(name) {artClasses.delete(name);}
    }
  },
  focusedTopicTitle: {textContent:""},
  focusedTopicBreadcrumb: {textContent:""},
  focusedTopicIntro: {textContent:"", hidden:true},
  focusedTopicArt: art,
  homeSearchLink: {href:"#hero"},
  document: {
    activeElement: null,
    querySelectorAll() {return [navLink];},
    createElement(tag) {
      if (tag !== "img") throw new Error("unexpected element");
      return {tag};
    }
  }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync("js/topic-hero-content.js", "utf8"), context);
vm.runInContext(
  extract("syncTopicLandingHero") + "\n" + extract("syncFocusedTopicView"),
  context
);
function snapshot() {
  const image = art.children[0];
  return {
    homeHidden: context.homeHero.hidden,
    heroHidden: context.focusedTopicHero.hidden,
    title: context.focusedTopicTitle.textContent,
    breadcrumb: context.focusedTopicBreadcrumb.textContent,
    intro: context.focusedTopicIntro.textContent,
    introHidden: context.focusedTopicIntro.hidden,
    artHidden: art.hidden,
    hasArt: artClasses.has("topic-landing-hero--with-art"),
    image: image ? {
      src:image.src, alt:image.alt, width:image.width, height:image.height
    } : null,
    count: art.children.length,
    categoriesHidden: context.categoriesSection.hidden,
    actionsHidden: context.galleryTopicActions.hidden,
    selectorHidden: context.topicField.hidden,
    galleryHeading: context.galleryHeading.textContent,
    header: context.homeSearchLink.href, nav: navLink.href
  };
}
function select(id) {
  context.activeTopic = id;
  context.syncFocusedTopicView();
  return snapshot();
}
const herbst = select("herbst");
const tanzen = select("tanzen");
// New valid managed Topic appears at runtime: no Hero/CSS/route code edit.
context.topicRegistry.push({id:"maerchen-abenteuer",label:"Märchen & Abenteuer"});
const newTopic = select("maerchen-abenteuer");
const missing = select("unknown-topic");
const restored = select("herbst");
const empty = select("");
console.log(JSON.stringify({herbst,tanzen,newTopic,missing,restored,empty}));
"""
        result = subprocess.run(
            ["node", "-e", harness], cwd=ROOT, text=True,
            capture_output=True, timeout=20, check=True,
        )
        cls.states = json.loads(result.stdout)
        cls.manifest = json.loads(
            (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
        )

    def test_reviewed_herbst_uses_exact_existing_art_and_intro(self):
        state = self.states["herbst"]
        source = self.manifest["topics"]["herbst"]
        self.assertTrue(state["homeHidden"])
        self.assertFalse(state["heroHidden"])
        self.assertEqual(state["title"], "Herbst Ausmalbilder")
        self.assertEqual(state["breadcrumb"], "Herbst")
        self.assertEqual(state["intro"], source["intro"])
        self.assertFalse(state["introHidden"])
        self.assertTrue(state["hasArt"])
        self.assertFalse(state["artHidden"])
        self.assertEqual(state["count"], 1)
        self.assertEqual(state["image"], {
            "src": source["image"], "alt": source["alt"],
            "width": source["width"], "height": source["height"],
        })

    def test_managed_new_topics_are_safe_label_only(self):
        for id_, label in (("tanzen", "Tanzen"),
                           ("newTopic", "Märchen & Abenteuer")):
            key = id_ if id_ == "tanzen" else "newTopic"
            with self.subTest(topic=id_):
                state = self.states[key]
                self.assertTrue(state["homeHidden"])
                self.assertFalse(state["heroHidden"])
                self.assertEqual(state["title"], label + " Ausmalbilder")
                self.assertEqual(state["breadcrumb"], label)
                self.assertEqual(state["intro"], "")
                self.assertTrue(state["introHidden"])
                self.assertIsNone(state["image"])
                self.assertEqual(state["count"], 0)
                self.assertTrue(state["artHidden"])
                self.assertFalse(state["hasArt"])
                self.assertTrue(state["categoriesHidden"])
                self.assertFalse(state["actionsHidden"])
                self.assertFalse(state["selectorHidden"])
                self.assertEqual(state["galleryHeading"], "Passende Malvorlagen entdecken")
                self.assertEqual(state["nav"], "/#hero")
                self.assertEqual(state["header"], "/#hero")

    def test_unknown_and_unfiltered_restore_home_and_clear_art(self):
        for key in ("missing", "empty"):
            state = self.states[key]
            self.assertFalse(state["homeHidden"])
            self.assertTrue(state["heroHidden"])
            self.assertIsNone(state["image"])
            self.assertEqual(state["count"], 0)
            self.assertTrue(state["artHidden"])
            self.assertFalse(state["hasArt"])
            self.assertFalse(state["actionsHidden"] is False)
            self.assertEqual(state["nav"], "#hero")
            self.assertEqual(state["header"], "#hero")
        self.assertEqual(self.states["restored"]["image"], self.states["herbst"]["image"])

    def test_no_new_indexed_route_or_approved_art_source(self):
        self.assertEqual(set(self.manifest["topics"]), {"herbst", "bauernhof", "weihnachten"})
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("data-focused-topic-hero", html)
        self.assertFalse((ROOT / "bauernhof.html").exists())
        self.assertFalse((ROOT / "weihnachten.html").exists())
        self.assertNotIn('href="/maerchen-abenteuer"', html)
        self.assertNotIn('rel="canonical" href="https://ausmalwiese.de/maerchen-abenteuer"', html)


if __name__ == "__main__":
    unittest.main()
