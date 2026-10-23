"""GitHub-first policy: source-only Coloring Pages consumer conformance."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "4e89b75d7f496dfb43fd9c1eb10a995fad53fdd8"


def choose_route(case):
    if case["error"]:
        return "STOP"
    if case["github"]:
        return "GITHUB"
    if case["ci"]:
        return "GITHUB_ACTIONS"
    return "RDC_EXCEPTION" if case["host"] and case["authority"] else "STOP"


class GitHubFirstRdcPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / ".github/github-first-rdc-v1.json").read_text(encoding="utf-8"))
        cls.agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cls.doc = (ROOT / "docs/GITHUB_FIRST_RDC_ADOPTION_V1.md").read_text(encoding="utf-8")
        cls.deploy = (ROOT / ".github/workflows/simple-deploy.yml").read_text(encoding="utf-8")

    def test_immutable_source_and_local_identity(self):
        self.assertEqual(len(UPSTREAM), 40)
        self.assertEqual(self.policy["schema"], "rozkalns.github-first-rdc-fallback.consumer.v1")
        self.assertEqual(self.policy["repository"], "rozkalnsandris/coloring-pages")
        self.assertEqual(self.policy["upstream"]["revision"], UPSTREAM)
        self.assertIn(UPSTREAM, self.agents)
        self.assertIn(UPSTREAM, self.doc)

    def test_mandatory_selection(self):
        p = self.policy["selection"]
        for name in ("per_step", "github_equivalent_mandatory", "github_actions_when_equivalent"):
            self.assertIs(p[name], True)
        self.assertIs(p["rdc_for_convenience_allowed"], False)
        self.assertEqual(p["order"], ["GITHUB_CONNECTED_TOOLS",
            "GITHUB_HOSTED_CI_WHEN_APPLICABLE",
            "MINIMAL_AUTHORIZED_RDC_IF_GITHUB_INCAPABLE", "STOP"])

    def test_github_failures_stop_and_rdc_record(self):
        p = self.policy
        for group in ("fail_closed", "rdc_exception"):
            for key, val in p[group].items():
                if key != "evidence_fields":
                    self.assertIs(val, True, key)
        self.assertEqual(p["rdc_exception"]["evidence_fields"], [
            "STEP", "REPOSITORY_AND_TARGET", "GITHUB_CAPABILITY_CHECKED",
            "PRECISE_CAPABILITY_GAP", "GITHUB_CI_NOT_EQUIVALENT_REASON",
            "MINIMAL_RDC_OPERATION", "EXISTING_AUTHORIZATION",
            "GITHUB_RETURN_EVIDENCE"])

    def test_eight_allow_and_stop_scenarios(self):
        rows = self.policy["cases"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({x["name"] for x in rows}), len(rows))
        for row in rows:
            with self.subTest(row=row["name"]):
                self.assertEqual(choose_route(row), row["expected"])

    def test_coloring_pages_owner_and_content_safety(self):
        for key, value in self.policy["local_boundaries"].items():
            self.assertIs(value, True, key)
        self.assertIn("Production coloring-page image binaries must not be committed", self.agents)
        self.assertIn("MERGE coloring-pages #N", self.agents)
        self.assertIn("A fresh `PUBLISH` command approves", self.agents)
        self.assertIn("No merge, PUBLISH, RPi5 media store", self.agents)
        self.assertIn("GitHub -> minimal RDC -> GitHub", self.doc)

    def test_no_governance_triggered_live_deploy(self):
        d = self.policy["deploy_trigger"]
        self.assertIs(d["governance_only_activates_deploy"], False)
        self.assertIn("on:\n  push:\n", self.deploy)
        self.assertIn("    paths:\n", self.deploy)
        self.assertNotIn("paths-ignore:", self.deploy)
        for p in d["approved_paths"]:
            self.assertIn('"' + p + '"', self.deploy)
        governance_paths = [
            "AGENTS.md", ".github/github-first-rdc-v1.json",
            ".github/workflows/github-first-rdc-policy.yml",
            "docs/GITHUB_FIRST_RDC_ADOPTION_V1.md",
            "tests/test_github_first_rdc_v1.py"]
        for path in governance_paths:
            self.assertNotIn('"' + path + '"', self.deploy)
        self.assertFalse((ROOT / ".github/agent-bootstrap.json").exists())


if __name__ == "__main__":
    unittest.main()
