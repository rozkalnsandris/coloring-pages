"""No-cron, deterministic weekly highlight contract for Berlin Monday 00:10."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
const fs=require('node:fs'),vm=require('node:vm');
const fixture=JSON.parse(process.argv[1]);
const section={hidden:true},preview={href:'',label:'',setAttribute(_k,v){this.label=v;}};
const image={src:'',alt:''},title={href:'',textContent:''},action={href:''};
const refs=new Map([
  ['[data-weekly-feature]',section],['[data-weekly-preview]',preview],
  ['[data-weekly-image]',image],['[data-weekly-title]',title],
  ['[data-weekly-action]',action],
]);
const ctx={
  window:{},document:{querySelector(s){return refs.get(s)||null;}},
  location:{search:fixture.search||''},
  Intl,Date,URLSearchParams,Object,Number,String,
};
vm.runInNewContext(fs.readFileSync('js/weekly-feature.js','utf8'),ctx);
const api=ctx.window.AusmalWeekly;
const instant=new Date(fixture.instant||'2026-10-25T23:10:00Z');
const week=api.isoWeekInBerlin(instant);
const selected=api.chooseEntry(fixture.catalog||[],instant);
const shown=api.render(fixture.catalog||[],instant);
console.log(JSON.stringify({
  week,selectedId:selected?.id||null,
  shown,hidden:section.hidden,
  href:preview.href,image:image.src,alt:image.alt,
  title:title.textContent,action:action.href,label:preview.label,
}));
"""


def run_weekly(**fixture):
    result = subprocess.run(
        ["node", "-e", HARNESS, json.dumps(fixture)],
        cwd=ROOT, capture_output=True, text=True, timeout=10,
    )
    if result.returncode:
        raise AssertionError(result.stderr[-2000:])
    return json.loads(result.stdout)


def row(page_id, published_at, title="Malvorlage"):
    return {
        "id": page_id, "title": title,
        "thumb": f"/media/{page_id}/thumb.webp",
        "published_at": published_at,
    }


class WeeklyFeatureTests(unittest.TestCase):
    def test_monday_cutover_across_berlin_fall_dst(self):
        first = run_weekly(instant="2026-10-25T23:09:59Z")
        second = run_weekly(instant="2026-10-25T23:10:00Z")
        self.assertEqual(first["week"], "2026-W43")
        self.assertEqual(second["week"], "2026-W44")

    def test_spring_dst_cutover_and_year_rollover(self):
        self.assertEqual(run_weekly(instant="2027-03-28T22:09:59Z")["week"], "2027-W12")
        self.assertEqual(run_weekly(instant="2027-03-28T22:10:00Z")["week"], "2027-W13")
        self.assertEqual(run_weekly(instant="2027-01-03T23:09:59Z")["week"], "2026-W53")
        self.assertEqual(run_weekly(instant="2027-01-03T23:10:00Z")["week"], "2027-W01")

    def test_new_items_change_only_on_following_monday_cutover(self):
        older = row("3398005", "2026-10-20T08:00:00Z", "Fröhliches Auto")
        fresh = row("0662291", "2026-10-23T10:00:00Z", "Einhorn")
        late = row("2468053", "2026-10-25T23:11:00Z", "Mumie")
        just_before = run_weekly(
            instant="2026-10-25T23:09:59Z", catalog=[older, fresh, late])
        just_after = run_weekly(
            instant="2026-10-25T23:10:00Z", catalog=[older, fresh, late])
        self.assertEqual(just_before["selectedId"], "3398005")
        self.assertEqual(just_after["selectedId"], "0662291")
        # Once Monday's choice is fixed, newly-published pages cannot change it.
        later = run_weekly(instant="2026-10-28T12:00:00Z",
                           catalog=[late, fresh, older])
        self.assertEqual(later["selectedId"], "0662291")
        next_week = run_weekly(instant="2026-11-01T23:10:00Z",
                               catalog=[late, fresh, older])
        self.assertEqual(next_week["selectedId"], "2468053")

    def test_weekly_picked_item_uses_same_catalogue_title_thumb_and_detail(self):
        first = row("0662291", "2026-10-23T10:00:00Z", "Einhorn")
        result = run_weekly(instant="2026-10-27T12:00:00Z",
                            catalog=[first], search="?campaign=dortmund-01")
        self.assertTrue(result["shown"])
        self.assertFalse(result["hidden"])
        self.assertEqual(result["href"], "detail.html?id=0662291&campaign=dortmund-01")
        self.assertEqual(result["action"], result["href"])
        self.assertEqual(result["title"], "Einhorn")
        self.assertEqual(result["image"], "/media/0662291/thumb.webp")

    def test_unknown_legacy_invalid_future_and_damaged_records_fail_closed(self):
        entries = [
            row("1111111", "2026-02-31T12:00:00Z"),
            row("2222222", "2026-10-25T23:10:01Z"),
            row("3333333", "bad timestamp"),
            {key: val for key, val in row("4444444", "2026-10-24T10:00:00Z").items()
             if key != "published_at"},
            {"id": "bad", "title": "unknown",
             "thumb": "/media/bad/thumb.webp", "published_at": "2026-10-24T10:00:00Z"},
            {"id": "5555555", "title": "",
             "thumb": "/media/5555555/thumb.webp", "published_at": "2026-10-24T10:00:00Z"},
        ]
        result = run_weekly(instant="2026-10-25T23:10:00Z", catalog=entries)
        self.assertIsNone(result["selectedId"])
        self.assertTrue(result["hidden"])

    def test_without_fresh_publications_uses_older_known_date(self):
        catalog = [
            row("1111111", "2026-10-03T12:00:00Z"),
            row("2222222", "2026-10-10T12:00:00Z"),
        ]
        before = run_weekly(instant="2026-11-02T00:00:00Z", catalog=catalog)
        after = run_weekly(instant="2026-11-02T00:00:00Z", catalog=list(reversed(catalog)))
        self.assertIsNotNone(before["selectedId"])
        self.assertEqual(before["selectedId"], after["selectedId"])
        previous = run_weekly(instant="2026-10-27T12:00:00Z", catalog=catalog)
        self.assertNotEqual(previous["selectedId"], before["selectedId"])

    def test_unchanged_homepage_catalogue_contract_and_exact_content_versions(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        weekly = (ROOT / "js/weekly-feature.js").read_text(encoding="utf-8")
        css = (ROOT / "css/weekly-feature.css").read_text(encoding="utf-8")
        self.assertIn("data-weekly-feature", html)
        self.assertIn('aria-labelledby="weekly-title"', html)
        self.assertLess(html.index("js/weekly-feature.js"), html.index("js/app.js"))
        self.assertIn("window.AusmalWeekly?.render(catalogEntries)", app)
        self.assertIn('fetch("catalog.json"', app)
        self.assertNotIn("fetch(", weekly)
        self.assertNotIn("setInterval", weekly)
        self.assertNotIn("localStorage", weekly)
        self.assertNotIn("CURATED_WEEKS", weekly)
        self.assertIn("max-width: 500px", css)
        for filename in ("js/weekly-feature.js", "css/weekly-feature.css"):
            digest = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()[:16]
            self.assertIn(filename + "?v=" + digest, html)


if __name__ == "__main__":
    unittest.main()
