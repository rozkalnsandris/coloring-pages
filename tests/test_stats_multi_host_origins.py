"""Exact same-origin browser writes for the three published Stats hostnames (#190)."""

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StatsMultiHostOriginTests(unittest.TestCase):
    def test_worker_checks_both_target_and_request_origin(self):
        worker = (ROOT / "cloudflare/stats-worker.js").read_text(encoding="utf-8")
        checks = r"""
const approved = [
  "https://coloring.rozkalns.net",
  "https://ausmalwiese.de",
  "https://www.ausmalwiese.de",
];
const env = { PUBLIC_ORIGIN: approved[0] };
function allowed(target, origin, site) {
  const headers = new Headers();
  if (origin !== null) headers.set("origin", origin);
  if (site !== null) headers.set("sec-fetch-site", site);
  return allowedWriteOrigin({url: target + "/api/stats/print", headers}, env);
}
function check(target, origin, site, expected) {
  const actual = allowed(target, origin, site);
  if (actual !== expected) throw Error(
    JSON.stringify({target, origin, site, expected, actual})
  );
}
for (const host of approved) {
  // Existing browsers and compatible clients keep their same-origin behavior.
  check(host, host, "same-origin", true);
  check(host, null, "same-origin", true);
  check(host, host, null, true);
  check(host, null, null, true);
  check(host, null, "none", true);

  // Allowed public hosts are NEVER cross-origin with each other.
  for (const differentHost of approved) {
    if (differentHost !== host) {
      check(host, differentHost, "same-origin", false);
    }
  }
  check(host, "https://attacker.example", "same-origin", false);
  check(host, "null", "same-origin", false);
  check(host, host, "cross-site", false);
  check(host, host, "same-site", false);
  check(host, null, "cross-site", false);
}
check("http://ausmalwiese.de", "http://ausmalwiese.de", "same-origin", false);
check("https://preview.ausmalwiese.de", "https://preview.ausmalwiese.de", "same-origin", false);
check("https://coloring.rozkalns.net.attacker.example",
      "https://coloring.rozkalns.net.attacker.example", "same-origin", false);
// A mistakenly configured PUBLIC_ORIGIN must not expand the fixed host allowlist.
check("https://unrelated.example", "https://unrelated.example", "same-origin", false);
"""
        result = subprocess.run(
            ["node", "--input-type=module"],
            input=worker + "\n" + checks,
            text=True, capture_output=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-1000:])

    def test_public_routes_remain_separately_owner_gated(self):
        worker = (ROOT / "cloudflare/stats-worker.js").read_text(encoding="utf-8")
        docs = (ROOT / "docs/CLOUDFLARE_STATS_V1.md").read_text(encoding="utf-8")
        self.assertIn('"https://ausmalwiese.de"', worker)
        self.assertIn('"https://www.ausmalwiese.de"', worker)
        self.assertIn("new URL(request.url).origin", worker)
        self.assertIn('url.hostname === PRINT_QR_HOST', worker)
        self.assertIn("ausmalwiese.de/api/stats/*", docs)
        self.assertIn("www.ausmalwiese.de/api/stats/*", docs)
        self.assertIn("separate explicit LIVE authorization", docs)


if __name__ == "__main__":
    unittest.main()
