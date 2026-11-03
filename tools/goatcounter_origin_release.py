#!/usr/bin/env python3
"""Build/prove once on ephemeral ARM64 CI; separately publish the same OCI bytes.

No RPi5 connection or activation. No credential value is accepted by this CLI.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BASE = "ghcr.io/rozkalnsandris/coloring-pages"
IMAGE = BASE + "-origin"
RECIPE = "8d0de541e03f2db1196fb89569d549fb2294abfb"
RPI = "ccd468de5ae6ea76cdc3dd009bd06812c20e6874"
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
INDEX = "application/vnd.oci.image.index.v1+json"
MANIFEST = "application/vnd.oci.image.manifest.v1+json"


def require(ok, reason="RELEASE_REFUSED"):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def file_hash(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def unique(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "DUPLICATE_JSON_KEY")
        obj[key] = value
    return obj


def decode(data):
    return json.loads(data, object_pairs_hook=unique)


def candidate(value):
    keys = {"schema", "application_source_sha", "recipe_source_sha", "rpi_source_sha",
            "shared_workflow_sha", "base_digest", "base_platform_digest"}
    require(type(value) is dict and set(value) == keys)
    require(value["schema"] == "rozkalns.origin-release-candidate.v1")
    for key in keys - {"schema", "base_digest", "base_platform_digest"}:
        require(type(value[key]) is str and SHA.fullmatch(value[key]) is not None)
    for key in ("base_digest", "base_platform_digest"):
        require(type(value[key]) is str and DIGEST.fullmatch(value[key]) is not None)
    require(value["recipe_source_sha"] == RECIPE and value["rpi_source_sha"] == RPI)
    return value


def run(*args, timeout=180):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout)
    # No automatic retries, credential-bearing output or raw exception commands.
    require(p.returncode == 0, "COMMAND_FAILED:" + args[0])
    return p.stdout


def registry(ref):
    return run("docker", "buildx", "imagetools", "inspect", ref, "--raw")


def validate_base(raw, config, contract, validator):
    require(sha(raw) == contract["base_digest"], "BASE_POINTER_DRIFT")
    index = decode(raw)
    require(index.get("schemaVersion") == 2 and index.get("mediaType") == INDEX)
    matches = [x for x in index.get("manifests", []) if x.get("platform", {}).get("os") == "linux"
               and x["platform"].get("architecture") == "arm64"
               and x["platform"].get("variant", "v8") == "v8"]
    require(len(matches) == 1 and matches[0]["digest"] == contract["base_platform_digest"])
    validator.sd.validate_origin_metadata(config, contract, contract["shared_workflow_sha"], derivative=False)


class Archive:
    """Read/hash without extracting. Reject links, traversal, duplicates and excess."""
    def __init__(self, path):
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2 * 1024**3)
        self.tar = tarfile.open(path, "r:")
        try:
            self.members = {}
            total = 0
            for member in self.tar:
                require(len(self.members) < 256)
                name = member.name
                require(not name.startswith("/") and ".." not in name.split("/"))
                if member.isdir():
                    require(name in {"blobs", "blobs/sha256"})
                    continue
                require(member.isfile() and name not in self.members)
                require(name in {"index.json", "oci-layout"} or
                        re.fullmatch(r"blobs/sha256/[0-9a-f]{64}", name) is not None)
                require(0 <= member.size <= 512 * 1024**2)
                total += member.size
                require(total <= 2 * 1024**3)
                self.members[name] = member
                if name.startswith("blobs/"):
                    with self.tar.extractfile(member) as stream:
                        require(hashlib.file_digest(stream, "sha256").hexdigest() == name.split("/")[-1],
                                "OCI_BLOB_HASH_MISMATCH")
            require(decode(self.read("oci-layout")) == {"imageLayoutVersion": "1.0.0"})
        except Exception:
            self.tar.close()
            raise

    def read(self, name):
        member = self.members[name]
        require(member.size <= 2 * 1024**2, "OCI_METADATA_TOO_LARGE")
        with self.tar.extractfile(member) as stream:
            return stream.read()

    def blob(self, descriptor):
        require(type(descriptor) is dict and DIGEST.fullmatch(descriptor.get("digest", "")) is not None)
        name = "blobs/sha256/" + descriptor["digest"][7:]
        require(type(descriptor.get("size")) is int and descriptor["size"] == self.members[name].size)
        return self.read(name)

    def close(self):
        self.tar.close()


def inspect_archive(path, contract, validator):
    archive = Archive(path)
    try:
        root = decode(archive.read("index.json"))
        require(root.get("schemaVersion") == 2 and len(root.get("manifests", [])) == 1)
        descriptor = root["manifests"][0]
        require(descriptor.get("mediaType") == INDEX)
        index_raw = archive.blob(descriptor)
        index = decode(index_raw)
        require(index.get("mediaType") == INDEX and index.get("schemaVersion") == 2)
        manifests = index.get("manifests", [])
        require(len(manifests) == 2)
        images = [x for x in manifests if x.get("platform", {}).get("os") == "linux"
                  and x["platform"].get("architecture") == "arm64"
                  and x["platform"].get("variant", "v8") == "v8"]
        require(len(images) == 1)
        image = images[0]
        require(image.get("mediaType") == MANIFEST)
        image_raw = archive.blob(image)
        manifest = decode(image_raw)
        config = decode(archive.blob(manifest["config"]))
        # Bind every runtime layer's size/digest, even though no extraction occurs here.
        for layer in manifest["layers"]:
            require(DIGEST.fullmatch(layer["digest"]) is not None)
            require(archive.members["blobs/sha256/" + layer["digest"][7:]].size == layer["size"])
        validator.sd.validate_origin_metadata(config, contract, contract["shared_workflow_sha"], derivative=True)
        attestation = next(x for x in manifests if x is not image)
        require(attestation.get("mediaType") == MANIFEST)
        require(attestation.get("platform") == {"architecture": "unknown", "os": "unknown"})
        require(attestation.get("annotations", {}).get("vnd.docker.reference.type") == "attestation-manifest")
        require(attestation["annotations"].get("vnd.docker.reference.digest") == image["digest"])
        att = decode(archive.blob(attestation))
        require(len(att["layers"]) == 1 and att["layers"][0]["mediaType"] == "application/vnd.in-toto+json")
        statement_raw = archive.blob(att["layers"][0])
        statement = decode(statement_raw)
        profile = {**contract, "derivative_digest": image["digest"],
                   "provenance_sha256": hashlib.sha256(canonical(statement)).hexdigest()}
        # Use the actual accepted RPi5 parser, not a second approximate implementation.
        validator.validate_provenance(statement, profile)
        return {"index_digest": descriptor["digest"], "derivative_digest": image["digest"],
                "config_digest": manifest["config"]["digest"],
                "provenance_sha256": profile["provenance_sha256"],
                "index_raw": index_raw, "image_raw": image_raw,
                "statement_raw": statement_raw, "config": config}
    finally:
        archive.close()


def hosted():
    require(os.environ.get("GITHUB_ACTIONS") == "true" and
            os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted", "GITHUB_HOSTED_ONLY")
    require(platform.machine() in {"aarch64", "arm64"}, "NATIVE_ARM64_REQUIRED")
    require(os.environ.get("GITHUB_REPOSITORY") == "rozkalnsandris/coloring-pages")
    require(os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "NO_AUTOMATIC_RETRY")


def authorize_publication(env, contract):
    source = env.get("GITHUB_SHA", "")
    require(SHA.fullmatch(source) is not None)
    expected = f"PUBLISH GOATCOUNTER-ORIGIN WORKFLOW={source} BASE={contract['base_digest']} RECIPE={RECIPE}"
    require(env.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and env.get("GITHUB_REF") == "refs/heads/main")
    require(env.get("GITHUB_ACTOR") == "rozkalnsandris" and env.get("GITHUB_TRIGGERING_ACTOR") == "rozkalnsandris")
    require(env.get("GITHUB_RUN_ATTEMPT") == "1")
    require(re.fullmatch(r"[1-9][0-9]*", env.get("GITHUB_RUN_ID", "")) is not None)
    require(env.get("EXPECTED_SOURCE_SHA") == source and env.get("PUBLICATION_AUTHORIZATION") == expected)


def load_validator():
    root = ROOT / ".rpi-release"
    require(run("git", "-C", str(root), "rev-parse", "HEAD").decode().strip() == RPI)
    spec = importlib.util.spec_from_file_location("rpi_origin_preparer", root / "scripts/prepare-goatcounter-origin-deploy-v1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prove(out, contract, validator):
    from goatcounter_origin_app_probe import application_fingerprint, verify_compose
    from goatcounter_origin_isolated_probe import probe
    out.mkdir()  # refuse stale artifacts, never overwrite a previous attempt
    raw = registry(BASE + ":production")
    config = decode(run("docker", "buildx", "imagetools", "inspect", BASE + "@" + contract["base_platform_digest"],
                        "--format", "{{json .Image}}"))
    validate_base(raw, config, contract, validator)
    (out / "base-manifest.raw.json").write_bytes(raw)
    (out / "base-config.json").write_bytes(canonical(config))
    run_id = os.environ["GITHUB_RUN_ID"]
    require(re.fullmatch(r"[1-9][0-9]*", run_id) is not None)
    tag = IMAGE + ":candidate-" + run_id
    archive = out / "candidate.tar"
    run("docker", "buildx", "build", "--platform=linux/arm64",
        "--file=deploy/Dockerfile.origin-counting", "--build-arg=APPLICATION_IMAGE=" + BASE + "@" + contract["base_digest"],
        "--label=io.rozkalns.origin.base-digest=" + contract["base_digest"],
        "--label=io.rozkalns.origin.recipe-revision=" + RECIPE,
        "--provenance=mode=max,version=v0.2", "--sbom=false", "--tag=" + tag,
        "--output=type=oci,dest=" + str(archive),
        "https://github.com/rozkalnsandris/coloring-pages.git#" + RECIPE, timeout=900)
    facts = inspect_archive(archive, contract, validator)
    run("skopeo", "--override-os=linux", "--override-arch=arm64", "copy",
        "oci-archive:" + str(archive), "docker-daemon:coloring-pages-origin-app:ci", timeout=300)
    loaded = decode(run("docker", "image", "inspect", "coloring-pages-origin-app:ci"))
    require(len(loaded) == 1 and loaded[0]["Id"] == facts["config_digest"], "LOADED_CONFIG_MISMATCH")
    run("docker", "pull", "--platform=linux/arm64", BASE + "@" + contract["base_platform_digest"], timeout=300)
    before = application_fingerprint(BASE + "@" + contract["base_platform_digest"])
    require(before and before == application_fingerprint("coloring-pages-origin-app:ci"), "APPLICATION_FILES_CHANGED")
    verify_compose(out)
    probe(application_image=True, platform="linux/arm64")
    for name, key in (("index.raw.json", "index_raw"), ("image.raw.json", "image_raw"), ("provenance.json", "statement_raw")):
        (out / name).write_bytes(facts[key])
    (out / "derivative-config.json").write_bytes(canonical(facts["config"]))
    receipt = {"schema": "rozkalns.origin-release-proof.v1", "result": "ARM64_PASS", "source_sha": os.environ["GITHUB_SHA"],
               "run_id": run_id, "contract": contract, "publication_performed": False,
               "activation_performed": False, "archive_sha256": file_hash(archive),
               "application_files": len(before), "application_fingerprint_sha256": hashlib.sha256(canonical(before)).hexdigest(),
               **{key: facts[key] for key in ("index_digest", "derivative_digest", "config_digest", "provenance_sha256")}}
    (out / "proof.json").write_bytes(canonical(receipt))
    print(json.dumps(receipt, sort_keys=True))


def publish(out, contract, validator):
    authorize_publication(os.environ, contract)
    receipt = decode((out / "proof.json").read_bytes())
    require(receipt.get("schema") == "rozkalns.origin-release-proof.v1")
    require(receipt.get("publication_performed") is False and receipt.get("activation_performed") is False)
    require(not (out / "publication.json").exists(), "ALREADY_PUBLISHED")
    require(receipt["result"] == "ARM64_PASS" and receipt["contract"] == contract)
    require(receipt["source_sha"] == os.environ["GITHUB_SHA"] and receipt["run_id"] == os.environ["GITHUB_RUN_ID"])
    archive = out / "candidate.tar"
    require(file_hash(archive) == receipt["archive_sha256"])
    facts = inspect_archive(archive, contract, validator)
    for key in ("index_digest", "derivative_digest", "config_digest", "provenance_sha256"):
        require(facts[key] == receipt[key])
    require(sha(registry(BASE + ":production")) == contract["base_digest"], "BASE_POINTER_DRIFT")
    tag = IMAGE + ":candidate-" + receipt["run_id"]
    # An existing tag or an ambiguous lookup is a refusal. No overwrite/retry.
    check = subprocess.run(["skopeo", "inspect", "--raw", "docker://" + tag], capture_output=True, timeout=60)
    require(check.returncode != 0 and (b"manifest unknown" in check.stderr.lower() or b"name unknown" in check.stderr.lower()),
            "PUBLICATION_TARGET_NOT_PROVEN_ABSENT")
    run("skopeo", "copy", "--all", "--preserve-digests", "--retry-times=0",
        "oci-archive:" + str(archive), "docker://" + tag, timeout=900)
    # Same immutable manifest/config/layer identities as the proven OCI artifact.
    require(sha(registry(IMAGE + "@" + facts["index_digest"])) == facts["index_digest"])
    require(sha(registry(IMAGE + "@" + facts["derivative_digest"])) == facts["derivative_digest"])
    require(sha(registry(BASE + ":production")) == contract["base_digest"], "BASE_POINTER_DRIFT_AFTER_PUBLICATION")
    receipt.update(publication_performed=True, published_tag=tag, result="PUBLISHED_VERIFIED")
    (out / "publication.json").write_bytes(canonical(receipt))
    print(json.dumps(receipt, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prove", "publish", "authorize"])
    args = parser.parse_args()
    hosted()
    contract = candidate(decode((ROOT / "deploy/goatcounter-origin-release.json").read_bytes()))
    if args.mode == "authorize":
        authorize_publication(os.environ, contract)
        return
    validator = load_validator()
    out = ROOT / "origin-release-artifact"
    (prove if args.mode == "prove" else publish)(out, contract, validator)


if __name__ == "__main__":
    main()
