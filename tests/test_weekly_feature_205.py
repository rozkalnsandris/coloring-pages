"""Owner-curated weekly highlight uses only already-fetched published catalogue entries."""
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
const instant=new Date(fixture.instant||'2026-10-22T08:00:00Z');
const week=api.isoWeekInBerlin(instant);
const shown=fixture.default
  ? api.render(fixture.catalog||[],undefined,instant)
  : api.render(fixture.catalog||[],fixture.schedule||{},instant);
console.log(JSON.stringify({
  week,shown,hidden:section.hidden,
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


class WeeklyFeatureTests(unittest.TestCase):
    def test_berlin_iso_week_year_and_local_midnight(self):
        self.assertEqual(run_weekly(instant="2020-12-31T22:30:00Z")["week"], "2020-W53")
        self.assertEqual(run_weekly(instant="2020-12-31T23:30:00Z")["week"], "2020-W53")
        self.assertEqual(run_weekly(instant="2021-01-03T23:15:00Z")["week"], "2021-W01")
        self.assertEqual(run_weekly(instant="2026-10-25T22:30:00Z")["week"], "2026-W44")

    def test_no_owner_curated_id_means_hidden_not_guessed(self):
        catalog = [{"id":"1234567","title":"Eule","thumb":"/media/1234567/preview.webp"}]
        result = run_weekly(default=True, catalog=catalog)
        self.assertFalse(result["shown"])
        self.assertTrue(result["hidden"])
        self.assertEqual(result["href"], "")

    def test_only_explicit_existing_catalogue_id_can_be_featured(self):
        catalog = [{"id":"1234567","title":"Eule","thumb":"/media/1234567/preview.webp"}]
        for schedule in ({}, {"2026-W43":"1234567"}, {"2026-W43":"1111111"},
                         {"2026-W43":"bad-id"}):
            with self.subTest(schedule=schedule):
                result = run_weekly(instant="2026-10-22T08:00:00Z",
                                    catalog=catalog, schedule=schedule)
                self.assertFalse(result["shown"])
                self.assertTrue(result["hidden"])
        # Week 43/2026, approved ID exists in the fixture catalogue.
        result = run_weekly(instant="2026-10-22T08:00:00Z", catalog=catalog,
                            schedule={"2026-W43":"1234567"}, search="?campaign=dortmund-01")
        self.assertTrue(result["shown"])
        self.assertFalse(result["hidden"])
        self.assertEqual(result["href"], "detail.html?id=1234567&campaign=dortmund-01")
        self.assertEqual(result["action"], result["href"])
        self.assertEqual(result["title"], "Eule")
        self.assertEqual(result["alt"], "Eule")
        self.assertEqual(result["image"], "/media/1234567/preview.webp")

    def test_incomplete_or_missing_catalogue_is_not_featured(self):
        for catalog in ([], [{"id":"1234567","title":"","thumb":"/media/1234567/p.webp"}],
                        [{"id":"1234567","title":"Eule","thumb":""}]):
            self.assertTrue(run_weekly(catalog=catalog,
                schedule={"2026-W43":"1234567"})["hidden"])

    def test_static_page_mount_and_single_catalogue_fetch(self):
        html=(ROOT/"index.html").read_text(encoding="utf-8")
        js=(ROOT/"js/app.js").read_text(encoding="utf-8")
        weekly=(ROOT/"js/weekly-feature.js").read_text(encoding="utf-8")
        css=(ROOT/"css/weekly-feature.css").read_text(encoding="utf-8")
        self.assertIn('data-weekly-feature', html)
        self.assertIn('aria-labelledby="weekly-title"', html)
        self.assertLess(html.index('js/weekly-feature.js'), html.index('js/app.js'))
        self.assertIn("window.AusmalWeekly?.render(catalogEntries)",js)
        self.assertIn('fetch("catalog.json"',js)
        self.assertNotIn("fetch(",weekly)
        self.assertNotIn("setInterval",weekly)
        self.assertIn("max-width: 500px",css)
        self.assertIn(":root", (ROOT/"css/app.css").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
