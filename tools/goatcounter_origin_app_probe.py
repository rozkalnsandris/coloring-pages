#!/usr/bin/env python3
"""Build/test the opt-in application image on an ephemeral GitHub runner only.

No registry push, host service, production mount, credential or GoatCounter DB.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile

from goatcounter_origin_compose import override
from goatcounter_origin_isolated_probe import IMAGE, probe

ROOT = Path(__file__).resolve().parents[1]
BASE_IMAGE = "coloring-pages-origin-base:ci"
APP_IMAGE = "coloring-pages-origin-app:ci"
FIXTURE_DIGEST = "ghcr.io/rozkalnsandris/coloring-pages-origin@sha256:" + "a" * 64


def run(*args, timeout=180):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # Only public build output or synthetic fixture data exists in this job.
        raise RuntimeError((result.stdout + result.stderr)[-6000:])
    return result.stdout


def verify_compose(root):
    path = root / "origin.compose.json"
    path.write_text(json.dumps(override(FIXTURE_DIGEST, "1234")))
    def config(*files):
        args = ["docker", "compose", "--project-name", "origin-proof"]
        for file in files:
            args.extend(["-f", str(file)])
        return json.loads(run(*args, "config", "--format", "json"))
    base = config(ROOT / "deploy/docker-compose.simple.yml")
    combined = config(ROOT / "deploy/docker-compose.simple.yml", path)
    before = base["services"]["coloring-pages"]
    after = combined["services"]["coloring-pages"]
    assert len(after["volumes"]) == len(before["volumes"]) + 1
    socket = [v for v in after["volumes"] if v["target"] == "/run/ausmalwiese-pageview"]
    assert len(socket) == 1
    assert {k: v for k, v in socket[0].items() if k != "bind"} == {
        "type": "bind", "source": "/run/ausmalwiese-pageview",
        "target": "/run/ausmalwiese-pageview", "read_only": True}
    # Older compose-go omits false in normalized JSON; newer releases preserve
    # explicit false. Verify semantics against a permissive negative control,
    # rather than mistaking serialization differences for a bad mount.
    binding = socket[0].get("bind", {})
    assert set(binding) <= {"create_host_path"}
    assert binding.get("create_host_path", False) is False
    permissive = override(FIXTURE_DIGEST, "1234")
    permissive["services"]["coloring-pages"]["volumes"][0]["bind"]["create_host_path"] = True
    control = root / "permissive.compose.json"
    control.write_text(json.dumps(permissive))
    normalized_control = config(ROOT / "deploy/docker-compose.simple.yml", control)
    control_socket = [v for v in normalized_control["services"]["coloring-pages"]["volumes"]
                      if v["target"] == "/run/ausmalwiese-pageview"]
    assert control_socket != socket, "Compose must retain false/true bind distinction"
    assert after["image"] == FIXTURE_DIGEST
    assert after["platform"] == "linux/arm64" and after["group_add"] == ["1234"]
    rest = {k: v for k, v in after.items() if k not in ("image", "platform", "group_add", "volumes")}
    assert rest == {k: v for k, v in before.items() if k not in ("image", "volumes")}
    assert [v for v in after["volumes"] if v not in socket] == before["volumes"]
    assert not before.get("group_add")


def application_fingerprint(image):
    # Compare all built public assets and importer tools, not just fixture HTML.
    code = '''import hashlib,json,pathlib
roots=['/usr/share/nginx/html','/usr/local/bin','/usr/local/share/coloring-pages']
out={}
for root in roots:
    for path in sorted(pathlib.Path(root).rglob('*')):
        if path.is_file():
            out[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps(out,sort_keys=True))'''
    return json.loads(run("docker", "run", "--rm", "--network=none", "--read-only",
                          "--cap-drop=ALL", "--security-opt=no-new-privileges",
                          "--entrypoint=python3", image, "-c", code))


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted":
        raise RuntimeError("EPHEMERAL_GITHUB_RUNNER_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="origin-app-proof-") as tmp:
        root = Path(tmp)
        verify_compose(root)
        dockerfile = (ROOT / "Dockerfile").read_text()
        expected = "FROM nginxinc/nginx-unprivileged:1.29.1-alpine\n"
        assert dockerfile.startswith(expected), "review new application base before updating proof"
        pinned = root / "Dockerfile.base"
        pinned.write_text("FROM " + IMAGE + "\n" + dockerfile[len(expected):])
        run("docker", "build", "--platform=linux/amd64", "--pull=false", "-f", str(pinned),
            "-t", BASE_IMAGE, ".", timeout=300)
        run("docker", "build", "--platform=linux/amd64", "--pull=false",
            "--build-arg", "APPLICATION_IMAGE=" + BASE_IMAGE,
            "-f", "deploy/Dockerfile.origin-counting", "-t", APP_IMAGE, ".")
        original = application_fingerprint(BASE_IMAGE)
        assert original and original == application_fingerprint(APP_IMAGE)
        probe(application_image=True)
        print(json.dumps({"result": "APP_INTEGRATION_PASS", "compose_merge": True,
                          "unchanged_application_files": len(original),
                          "public_activation": False, "live_data": False}))


if __name__ == "__main__":
    main()
