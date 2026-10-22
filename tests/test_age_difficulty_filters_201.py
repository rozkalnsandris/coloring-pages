"""Homepage metadata filter contract #201: exact catalogue labels, not guesses."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r"""
const vm = require("node:vm"), fs = require("node:fs");
const sample = JSON.parse(process.argv[1]);
const callbacks = {};
const makeControl = () => ({value: "", callbacks: {}, addEventListener(name, fn) { this.callbacks[name] = fn; }});
const age = makeControl(), difficulty = makeControl();
const search = {value: sample.q || ""};
const selectors = {
  "[data-filter-age]": age,
  "[data-filter-difficulty]": difficulty,
  "#site-search": search
};
const document = {
  querySelector(key) { return selectors[key] || null; },
  querySelectorAll() { return []; }
};
const location = {
  href: "https://ausmalwiese.de/index.html" + (sample.url || ""),
  pathname: "/index.html", search: new URL("https://ausmalwiese.de/index.html" + (sample.url || "")).search,
  hash: new URL("https://ausmalwiese.de/index.html" + (sample.url || "")).hash
};
let pushed = "";
const history = { pushState(_a, _b, target) {
  pushed = target;
  const next = new URL(target, "https://ausmalwiese.de");
  location.href = next.href; location.search = next.search; location.hash = next.hash;
}};
const window = { location: {hash: ""}, addEventListener(name, cb) { callbacks[name] = cb; } };
const context = vm.createContext({document, window, location, history, URL, URLSearchParams, Intl});
vm.runInContext(fs.readFileSync("js/app.js", "utf8"), context);
function matches(entry) {
  return vm.runInContext("matchesFilters(" + JSON.stringify(entry.title) + "," +
    JSON.stringify(entry.category) + ", [], " +
    JSON.stringify(entry.age) + "," + JSON.stringify(entry.difficulty) + ")", context);
}
const before = sample.entries.map(matches);
if (sample.change) {
  if ("age" in sample.change) age.value = sample.change.age;
  if ("difficulty" in sample.change) difficulty.value = sample.change.difficulty;
  (sample.change.age !== undefined ? age : difficulty).callbacks.change();
}
const changed = sample.entries.map(matches);
if (sample.back) {
  const next = new URL("https://ausmalwiese.de/index.html" + sample.back);
  location.href = next.href; location.search = next.search; location.hash = next.hash;
  callbacks.popstate();
}
console.log(JSON.stringify({before, changed, after:sample.entries.map(matches),
  age:age.value, difficulty:difficulty.value, pushed, url:location.search, hash:location.hash}));
"""

def evaluate(fixture):
    result = subprocess.run(
        ["node", "-e", HARNESS, json.dumps(fixture)], cwd=ROOT,
        check=True, text=True, capture_output=True
    )
    return json.loads(result.stdout)


@unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
class MetadataFiltersTests(unittest.TestCase):
    def setUp(self):
        self.entries = [
            {"title": "Hund", "category": "tiere", "age": "3-6", "difficulty": "easy"},
            {"title": "Katze", "category": "tiere", "age": "4-8", "difficulty": "normal"},
            {"title": "Dino", "category": "tiere", "age": None, "difficulty": "detailed"},
            {"title": "Blume", "category": "tiere", "age": "3-6", "difficulty": None},
            {"title": "Stern", "category": "tiere", "age": "3-4", "difficulty": "easy"},
        ]

    def test_empty_facets_do_not_hide_legacy_or_unknown_entries(self):
        self.assertEqual(evaluate({"entries": self.entries})["before"], [True] * 5)

    def test_exact_age_and_difficulty_intersection(self):
        result = evaluate({"url": "?age=3-6&difficulty=easy", "entries": self.entries})
        self.assertEqual(result["before"], [True, False, False, False, False])
        self.assertEqual((result["age"], result["difficulty"]), ("3-6", "easy"))

    def test_difficulty_and_multi_page_use_activity_metadata_only(self):
        entries = [
            {"title": "Bastelset", "category": "lernen", "age": "4-8", "difficulty": "detailed"},
            {"title": "Alt", "category": "lernen", "age": None, "difficulty": "detailed"},
        ]
        result = evaluate({"url": "?difficulty=detailed", "entries": entries})
        self.assertEqual(result["before"], [True, True])
        result = evaluate({"url": "?age=4-8&difficulty=detailed", "entries": entries})
        self.assertEqual(result["before"], [True, False])

    def test_allowlist_and_back_forward_restore(self):
        result = evaluate({
            "url": "?age=3-4&difficulty=hard&campaign=dortmund-01#neu",
            "entries": self.entries,
            "change": {"age": "4-8"}, "back": "?age=3-6&difficulty=easy#neu"
        })
        self.assertEqual(result["before"], [True] * 5)
        self.assertIn("campaign=dortmund-01", result["pushed"])
        self.assertIn("age=4-8", result["pushed"])
        self.assertEqual(result["after"], [True, False, False, False, False])
        self.assertEqual(result["hash"], "#neu")

    def test_search_still_intersects_with_age(self):
        result = evaluate({"url": "?age=3-6", "q": "Hund", "entries": self.entries})
        self.assertEqual(result["before"], [True, False, False, False, False])


class FilterSourceContractTests(unittest.TestCase):
    def test_accessible_native_controls_and_reset(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "js/app.js").read_text(encoding="utf-8")
        css = (ROOT / "css/metadata-filters.css").read_text(encoding="utf-8")
        self.assertEqual(html.count('data-filter-age'), 1)
        self.assertEqual(html.count('data-filter-difficulty'), 1)
        for value in ('"3-6"', '"4-8"', '"easy"', '"normal"', '"detailed"'):
            self.assertIn(value, html)
        self.assertIn('for="filter-age"', html)
        self.assertIn('for="filter-difficulty"', html)
        self.assertIn("syncMetadataFilterUrl();", js)
        self.assertIn('window.addEventListener("popstate"', js)
        self.assertIn("min-height: 44px", css)
        self.assertIn("focus-visible", css)

    def test_importer_vocabulary_is_exact_and_unmodified(self):
        importer = (ROOT / "tools/coloring-pages-import").read_text(encoding="utf-8")
        self.assertIn('ALLOWED_AGES = {"3-6", "4-8"}', importer)
        self.assertIn('ALLOWED_DIFFICULTIES = {"easy", "normal", "detailed"}', importer)


if __name__ == "__main__":
    unittest.main()
