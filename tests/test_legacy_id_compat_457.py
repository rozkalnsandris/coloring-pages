import json, re, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALIASES=ROOT/"metadata"/"legacy-id-aliases.json"; TOOL=ROOT/"tools"/"coloring-pages-legacy-id-compat"; NGINX=ROOT/"deploy"/"nginx.conf"; DOCKER=ROOT/"Dockerfile"; DETAIL=ROOT/"js"/"detail.js"
class LegacyIdCompatibility457Tests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads(ALIASES.read_text(encoding="utf-8")); self.nginx=NGINX.read_text(encoding="utf-8"); self.docker=DOCKER.read_text(encoding="utf-8")
        self.rendered=subprocess.run([str(TOOL),"--aliases",str(ALIASES),"--render-nginx"],check=True,text=True,capture_output=True).stdout
    def test_frozen_manifest_identity_and_30_exact_aliases(self):
        self.assertEqual(self.doc["source_catalog_sha256"],"efa6a736839657f849606f665b09bd51dff1165a1c9c2038e9d5b7e720cc7ba9"); self.assertEqual(self.doc["source_catalog_count"],477); self.assertEqual(self.doc["source_legacy_count"],30)
        self.assertEqual(self.doc["source_plan_manifest_sha256"],"80538dd2bda9755212c599d1b75a106673e1eb5c774cebc47f4192e0478fad9c"); self.assertEqual(self.doc["aliases_sha256"],"24cf6ec46ba2ad2b1791c8aff8975937bb9b0e629076d0d34b828ee30d6308b5")
        self.assertEqual(len(self.doc["aliases"]),30); old=[x["old_id"] for x in self.doc["aliases"]]; new=[x["new_id"] for x in self.doc["aliases"]]; self.assertEqual(len(set(old)),30); self.assertEqual(len(set(new)),30); self.assertTrue(all(re.fullmatch(r"[0-9]{7}",x) for x in new)); self.assertIn("0921115",new)
    def test_one_source_drives_activity_and_media_maps(self):
        for x in self.doc["aliases"]:
            self.assertIn(f'"{x["old_id"]}" "{x["new_id"]}";',self.rendered); self.assertIn(f'"/media/{x["new_id"]}/$1";',self.rendered)
        self.assertIn('default "";',self.rendered); self.assertNotIn("rewrite ",self.rendered); self.assertNotIn("proxy_pass",self.rendered)
    def test_redirects_are_latent_until_exact_marker(self):
        self.assertIn(".legacy-id-aliases-"+self.doc["source_plan_manifest_sha256"]+".active",self.rendered); self.assertIn("if (-f $legacy_id_activation_marker)",self.nginx)
        self.assertIn("return 308 /detail.html?id=$legacy_detail_target_id$legacy_campaign_suffix;",self.nginx); self.assertIn("return 308 /print.html?id=$legacy_print_target_id$legacy_embedded_suffix;",self.nginx); self.assertIn("try_files $uri @legacy_media_missing;",self.nginx); self.assertIn('if ($legacy_media_target != "")',self.nginx); self.assertIn("return 404;",self.nginx)
    def test_alias_json_hidden_before_cutover(self):
        block=self.nginx.split("location = /legacy-id-aliases.json",1)[1].split("location",1)[0]; self.assertIn('Cache-Control "no-store"',block); self.assertIn("if (!-f $legacy_id_activation_marker)",block); self.assertIn("return 404;",block)
    def test_new_detail_canonical_is_catalogue_id(self):
        detail=DETAIL.read_text(encoding="utf-8"); self.assertIn("addVerifiedDetailCanonical(entry.id)",detail); self.assertIn("https://ausmalwiese.de/detail.html?id=",detail)
    def test_image_build_uses_same_alias_json(self):
        self.assertIn("COPY metadata/legacy-id-aliases.json /usr/local/share/coloring-pages/legacy-id-aliases.json",self.docker); self.assertIn("coloring-pages-legacy-id-compat --aliases /usr/local/share/coloring-pages/legacy-id-aliases.json --render-nginx",self.docker); self.assertIn("COPY metadata/legacy-id-aliases.json /usr/share/nginx/html/legacy-id-aliases.json",self.docker); self.assertIn("include /etc/nginx/legacy-id-aliases.conf;",self.nginx)
    def test_malformed_source_fails_closed(self):
        duplicate=json.loads(json.dumps(self.doc)); duplicate["aliases"][1]["new_id"]=duplicate["aliases"][0]["new_id"]; wrong=json.loads(json.dumps(self.doc)); wrong["source_legacy_count"]=29; bad=json.loads(json.dumps(self.doc)); bad["aliases_sha256"]="0"*64
        for doc in [duplicate,wrong,bad]:
            with tempfile.NamedTemporaryFile("w",encoding="utf-8",suffix=".json") as h:
                json.dump(doc,h); h.flush(); proc=subprocess.run([str(TOOL),"--aliases",h.name,"--render-nginx"],text=True,capture_output=True)
            self.assertNotEqual(proc.returncode,0); self.assertEqual(proc.stdout,""); self.assertIn("LEGACY_ID_COMPAT_ERROR",proc.stderr)
if __name__=="__main__": unittest.main()
