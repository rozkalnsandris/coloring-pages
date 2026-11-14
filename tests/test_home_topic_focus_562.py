"""Regression for focused managed Topic gallery views (#562)."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HomeTopicFocus562(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "css/home-discovery.css").read_text(encoding="utf-8")

    def test_progressive_enhancement_and_navigation(self):
        self.assertIn('id="kategorien"', self.html)
        self.assertIn('data-category-ids="figuren"', self.html)
        self.assertIn('href="/herbst"', self.html)
        self.assertIn('data-gallery-topic-actions hidden', self.html)
        self.assertIn('data-show-categories aria-controls="kategorien" aria-expanded="false"', self.html)
        self.assertIn('data-clear-active-topic', self.html)
        self.assertIn('id="category-heading" tabindex="-1"', self.html)
        self.assertIn('#kategorien[hidden]', self.css)
        self.assertIn('.metadata-filter-field[hidden]', self.css)
        self.assertIn('min-height: 44px;', self.css)

    def test_url_and_accessibility_wiring(self):
        for term in (
            'categoriesExpanded = window.location.hash === "#kategorien"',
            'if (activeTopic && (hash === "#kategorien" || hash === "#neu"))',
            'syncCatalogFilterUrl();',
            'readTopicFilterFromUrl();',
            'syncFocusedTopicView();',
            'document.querySelector("#category-heading")?.focus({ preventScroll: true })',
            'galleryHeading?.focus({ preventScroll: true })',
            'selectTopic("", { toggle: false, moveFocus: false })',
        ):
            self.assertIn(term, self.app)
        subprocess.run(["node", "--check", str(ROOT / "js/app.js")], check=True, timeout=15)

    def test_managed_topic_display_behaviour(self):
        # Execute the real view function with light DOM doubles, not a
        # reimplementation, covering known/unknown/expanded Topics and focus.
        harness = r"""
const fs = require("node:fs"), vm = require("node:vm");
const source = fs.readFileSync("js/app.js", "utf8");
const match = source.match(/function syncFocusedTopicView\(\) \{[\s\S]*?\n\}/);
if (!match) throw new Error("function missing");
const run = (id, expanded, focusKind = "") => {
  const focusCalls = [];
  const section = {hidden:false, contains: target => target === "category"};
  const actions = {hidden:true};
  const field = {hidden:false, contains: target => target === "topic"};
  const heading = {textContent:"Malvorlagen", focus: () => focusCalls.push("heading")};
  const reveal = {setAttribute(k,v){this[k] = v}};
  const clear = {textContent:"", setAttribute(k,v){this[k] = v},
    focus: () => focusCalls.push("clear")};
  const ctx = {
    topicRegistry:[{id:"ostern", label:"Ostern"}, {id:"tanzen", label:"Tanzen"}],
    activeTopic:id, categoriesExpanded:expanded, categoriesSection:section,
    galleryTopicActions:actions, topicField:field, galleryHeading:heading,
    showCategoriesButton:reveal, clearTopicButton:clear,
    document:{activeElement:focusKind},
  };
  vm.runInNewContext(match[0] + "\nsyncFocusedTopicView();", ctx);
  return {hidden:section.hidden, actionsHidden:actions.hidden,
    topicFieldHidden:field.hidden, heading:heading.textContent,
    expanded:reveal["aria-expanded"], clearLabel:clear["aria-label"],
    focusCalls};
};
console.log(JSON.stringify([
  run("ostern",false), run("tanzen",false),
  run("ostern",true), run("unknown",false),
  run("",false), run("ostern",false,"topic"), run("ostern",false,"category")
]));
"""
        result = subprocess.run(
            ["node", "-e", harness], cwd=ROOT, check=True, text=True,
            capture_output=True, timeout=20,
        )
        ostern, tanzen, expanded, unknown, empty, topic_focus, category_focus = json.loads(result.stdout)
        self.assertEqual(ostern["heading"], "Ostern Ausmalbilder")
        self.assertTrue(ostern["hidden"])
        self.assertTrue(ostern["topicFieldHidden"])
        self.assertFalse(ostern["actionsHidden"])
        self.assertEqual(ostern["expanded"], "false")
        self.assertEqual(ostern["clearLabel"], "Thema Ostern entfernen")
        self.assertEqual(tanzen["heading"], "Tanzen Ausmalbilder")
        self.assertTrue(tanzen["hidden"])
        self.assertFalse(expanded["hidden"])
        self.assertEqual(expanded["expanded"], "true")
        for no_filter in (unknown, empty):
            self.assertFalse(no_filter["hidden"])
            self.assertFalse(no_filter["topicFieldHidden"])
            self.assertTrue(no_filter["actionsHidden"])
            self.assertEqual(no_filter["heading"], "Malvorlagen")
        self.assertEqual(topic_focus["focusCalls"], ["clear"])
        self.assertEqual(category_focus["focusCalls"], ["heading"])


if __name__ == "__main__":
    unittest.main()
