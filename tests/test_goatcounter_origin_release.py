import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import goatcounter_origin_release as release
from goatcounter_origin_isolated_probe import probe

CONTRACT = json.loads((ROOT / "deploy/goatcounter-origin-release.json").read_text())
VALIDATOR = ROOT / ".rpi-release/scripts/prepare-goatcounter-origin-deploy-v1.py"


def environment():
    source = "a" * 40
    return {"GITHUB_SHA": source, "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
            "GITHUB_ACTOR": "rozkalnsandris", "GITHUB_TRIGGERING_ACTOR": "rozkalnsandris",
            "GITHUB_RUN_ATTEMPT": "1", "GITHUB_RUN_ID": "42", "EXPECTED_SOURCE_SHA": source,
            "PUBLICATION_AUTHORIZATION": f"PUBLISH GOATCOUNTER-ORIGIN WORKFLOW={source} BASE={CONTRACT['base_digest']} RECIPE={release.RECIPE}"}


def archive_fixture(path, *, config_change=None, statement_change=None, corrupt=False, extra=None, contract=CONTRACT):
    """Synthetic test data only; never a publication or production attestation."""
    files = {}

    def blob(value, media):
        raw = release.canonical(value)
        digest = release.sha(raw)
        files["blobs/sha256/" + digest[7:]] = raw
        return {"mediaType": media, "digest": digest, "size": len(raw)}

    config = {"os": "linux", "architecture": "arm64", "config": {
        "User": "101", "Entrypoint": ["nginx"], "Cmd": ["-c", "/etc/nginx/nginx-origin.conf", "-g", "daemon off;"],
        "Labels": {"org.opencontainers.image.revision": contract["application_source_sha"],
                   "io.rozkalns.simple-deploy.target": "coloring-pages-public-rpi5",
                   "io.rozkalns.simple-deploy.shared-revision": contract["shared_workflow_sha"],
                   "io.rozkalns.origin.base-digest": contract["base_digest"],
                   "io.rozkalns.origin.recipe-revision": release.RECIPE}}}
    if config_change:
        config_change(config)
    image = blob({"schemaVersion": 2, "mediaType": release.MANIFEST,
                  "config": blob(config, "application/vnd.oci.image.config.v1+json"), "layers": []}, release.MANIFEST)
    image["platform"] = {"os": "linux", "architecture": "arm64"}
    statement = {"_type": "https://in-toto.io/Statement/v0.1", "predicateType": "https://slsa.dev/provenance/v0.2",
                 "subject": [{"name": "pkg:docker/ghcr.io/rozkalnsandris/coloring-pages-origin@candidate-42?platform=linux%2Farm64",
                              "digest": {"sha256": image["digest"][7:]}}],
                 "predicate": {"buildType": "https://mobyproject.org/buildkit@v1", "invocation": {
                     "configSource": {"uri": "https://github.com/rozkalnsandris/coloring-pages.git#" + release.RECIPE,
                                      "digest": {"sha1": release.RECIPE}, "entryPoint": "deploy/Dockerfile.origin-counting"},
                     "parameters": {"args": {"build-arg:APPLICATION_IMAGE": release.BASE + "@" + contract["base_digest"]}}},
                     "materials": [{"uri": "pkg:docker/ghcr.io/rozkalnsandris/coloring-pages@" + contract["base_digest"].replace(":", "%3A") + "?platform=linux%2Farm64",
                                    "digest": {"sha256": contract["base_platform_digest"][7:]}}]}}
    if statement_change:
        statement_change(statement)
    att = blob({"schemaVersion": 2, "mediaType": release.MANIFEST,
                "layers": [blob(statement, "application/vnd.in-toto+json")]}, release.MANIFEST)
    att.update(platform={"architecture": "unknown", "os": "unknown"}, annotations={
        "vnd.docker.reference.type": "attestation-manifest", "vnd.docker.reference.digest": image["digest"]})
    index = blob({"schemaVersion": 2, "mediaType": release.INDEX, "manifests": [image, att]}, release.INDEX)
    files["index.json"] = release.canonical({"schemaVersion": 2, "manifests": [index]})
    files["oci-layout"] = release.canonical({"imageLayoutVersion": "1.0.0"})
    if corrupt:
        files[next(iter(files))] += b" "
    with tarfile.open(path, "w") as handle:
        for name, data in files.items():
            member = tarfile.TarInfo(name); member.size = len(data)
            handle.addfile(member, io.BytesIO(data))
        if extra:
            handle.addfile(extra)


class ReleaseBoundaryTests(unittest.TestCase):
    def test_reviewed_rpi_validator_pin_consistency(self):
        accepted = "ccd468de5ae6ea76cdc3dd009bd06812c20e6874"
        workflow = (ROOT / ".github/workflows/goatcounter-origin-release.yml").read_text()
        self.assertEqual(workflow.count("ref: " + accepted), 2)
        self.assertEqual(CONTRACT["rpi_source_sha"], accepted)
        self.assertEqual(release.RPI, accepted)

    def test_candidate_is_strict_and_immutable(self):
        self.assertEqual(release.candidate(copy.deepcopy(CONTRACT)), CONTRACT)
        for key, value in (("base_digest", "production"), ("recipe_source_sha", "b" * 40),
                           ("application_source_sha", "a" * 40 + "\n"), ("rpi_source_sha", None), ("extra", True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                release.candidate({**CONTRACT, key: value})

    def test_duplicate_json_is_refused(self):
        with self.assertRaises(ValueError):
            release.decode('{"schema":1,"schema":2}')

    def test_publication_requires_exact_owner_event_source_and_first_attempt(self):
        release.authorize_publication(environment(), CONTRACT)
        for key, value in (("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_REF", "refs/heads/feature"),
                           ("GITHUB_ACTOR", "another-owner"), ("GITHUB_TRIGGERING_ACTOR", "bot"),
                           ("GITHUB_RUN_ATTEMPT", "2"), ("GITHUB_RUN_ID", "../other"),
                           ("EXPECTED_SOURCE_SHA", "b" * 40), ("PUBLICATION_AUTHORIZATION", "publish")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                release.authorize_publication({**environment(), key: value}, CONTRACT)

    def test_wrong_authority_cannot_read_artifact_or_run_commands(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(release, "run") as run:
            with self.assertRaises(ValueError):
                release.publish(Path("/does-not-exist"), CONTRACT, None)
            run.assert_not_called()

    def test_native_hosted_runner_required(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            release.hosted()

    def test_platform_extension_does_not_change_pinned_raw_fixture(self):
        for kwargs in ({"platform": "linux/arm64"}, {"application_image": True, "platform": "arbitrary"}):
            with self.assertRaises(ValueError):
                probe(**kwargs)


@unittest.skipUnless(VALIDATOR.exists(), "pinned RPi validator is provided by the ARM64 release job")
class ReleaseArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("release_test_rpi_validator", VALIDATOR)
        cls.validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.validator)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.archive = self.out / "candidate.tar"

    def test_valid_archive_uses_real_rpi_parser(self):
        archive_fixture(self.archive)
        facts = release.inspect_archive(self.archive, CONTRACT, self.validator)
        self.assertEqual(release.sha(facts["index_raw"]), facts["index_digest"])
        self.assertEqual(release.sha(facts["image_raw"]), facts["derivative_digest"])
        self.assertNotEqual(facts["index_digest"], facts["derivative_digest"])

    def test_architecture_and_runtime_command_rejected(self):
        for mutate in (lambda c: c.update(architecture="amd64"), lambda c: c["config"].update(User="0"),
                       lambda c: c["config"].update(Cmd=["nginx"]), lambda c: c["config"]["Labels"].clear()):
            archive_fixture(self.archive, config_change=mutate)
            with self.assertRaises(self.validator.sd.SimpleDeployError):
                release.inspect_archive(self.archive, CONTRACT, self.validator)

    def test_subject_recipe_base_and_schema_tampering_rejected(self):
        mutations = [lambda s: s["subject"][0]["digest"].update(sha256="0" * 64),
                     lambda s: s["predicate"]["invocation"]["configSource"].update(uri="https://example.invalid/main"),
                     lambda s: s["predicate"]["materials"][0]["digest"].update(sha256="0" * 64),
                     lambda s: s.update(predicateType="https://slsa.dev/provenance/v1")]
        for mutate in mutations:
            archive_fixture(self.archive, statement_change=mutate)
            with self.assertRaises(ValueError):
                release.inspect_archive(self.archive, CONTRACT, self.validator)

    def test_blob_corruption_refused_without_extraction(self):
        archive_fixture(self.archive, corrupt=True)
        with self.assertRaisesRegex(ValueError, "OCI_BLOB_HASH"):
            release.Archive(self.archive)

    def test_archive_path_link_duplicate_and_unknown_member_refusals(self):
        for name, kind in (("../outside", tarfile.REGTYPE), ("index.json", tarfile.REGTYPE),
                           ("blobs/link", tarfile.SYMTYPE), ("arbitrary", tarfile.REGTYPE)):
            member = tarfile.TarInfo(name); member.type = kind; member.linkname = "/outside"
            archive_fixture(self.archive, extra=member)
            with self.assertRaises(ValueError):
                release.Archive(self.archive)
        self.assertFalse((self.out.parent / "outside").exists())

    def test_changed_production_pointer_stops_before_registry_copy(self):
        archive_fixture(self.archive)
        facts = release.inspect_archive(self.archive, CONTRACT, self.validator)
        receipt = {"schema": "rozkalns.origin-release-proof.v1", "result": "ARM64_PASS", "contract": CONTRACT,
                   "source_sha": "a" * 40, "run_id": "42", "publication_performed": False,
                   "activation_performed": False, "archive_sha256": release.file_hash(self.archive),
                   **{k: facts[k] for k in ("index_digest", "derivative_digest", "config_digest", "provenance_sha256")}}
        (self.out / "proof.json").write_bytes(release.canonical(receipt))
        with patch.dict(os.environ, environment(), clear=True), patch.object(release, "registry", return_value=b"drift"), \
                patch.object(release, "run") as run, self.assertRaisesRegex(ValueError, "BASE_POINTER_DRIFT"):
            release.publish(self.out, CONTRACT, self.validator)
        run.assert_not_called()

    def test_publish_copies_same_archive_once_and_never_promotes_production(self):
        raw = b'synthetic ordinary pointer'
        contract = {**CONTRACT, 'base_digest': release.sha(raw)}
        archive_fixture(self.archive, contract=contract)
        facts = release.inspect_archive(self.archive, contract, self.validator)
        receipt = {'schema': 'rozkalns.origin-release-proof.v1', 'result': 'ARM64_PASS', 'contract': contract,
                   'source_sha': 'a' * 40, 'run_id': '42', 'publication_performed': False,
                   'activation_performed': False, 'archive_sha256': release.file_hash(self.archive),
                   **{k: facts[k] for k in ('index_digest', 'derivative_digest', 'config_digest', 'provenance_sha256')}}
        (self.out / 'proof.json').write_bytes(release.canonical(receipt))
        env = environment()
        env['PUBLICATION_AUTHORIZATION'] = env['PUBLICATION_AUTHORIZATION'].replace(CONTRACT['base_digest'], contract['base_digest'])
        refs = {release.BASE + ':production': raw,
                release.IMAGE + '@' + facts['index_digest']: facts['index_raw'],
                release.IMAGE + '@' + facts['derivative_digest']: facts['image_raw']}
        absent = subprocess.CompletedProcess([], 1, b'', b'manifest unknown')
        with patch.dict(os.environ, env, clear=True), patch.object(release, 'registry', side_effect=refs.__getitem__), \
                patch.object(release.subprocess, 'run', return_value=absent), patch.object(release, 'run') as run:
            release.publish(self.out, contract, self.validator)
            run.assert_called_once_with('skopeo', 'copy', '--all', '--preserve-digests', '--retry-times=0',
                                        'oci-archive:' + str(self.archive),
                                        'docker://' + release.IMAGE + ':candidate-42', timeout=900)
            with self.assertRaisesRegex(ValueError, 'ALREADY_PUBLISHED'):
                release.publish(self.out, contract, self.validator)
            self.assertEqual(run.call_count, 1)
        result = json.loads((self.out / 'publication.json').read_bytes())
        self.assertEqual(result['result'], 'PUBLISHED_VERIFIED')
        self.assertFalse(result['activation_performed'])


if __name__ == "__main__":
    unittest.main()
