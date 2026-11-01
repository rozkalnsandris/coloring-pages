#!/usr/bin/env python3
"""Emit a NEW opt-in Compose override; never inspect or change runtime state.

JSON is valid Compose input. The default application does not load this file.
The image must be a separately built, reviewed origin-counting derivative.
The supplementary group is the explicitly verified container-visible group
mapping to the host socket group; it is not the primary SO_PEERCRED identity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

IMAGE_RE = r"ghcr\.io/rozkalnsandris/coloring-pages-origin@sha256:[0-9a-f]{64}"
SOCKET_DIRECTORY = "/run/ausmalwiese-pageview"


def override(image: str, socket_group: str) -> dict:
    if not isinstance(image, str) or not re.fullmatch(IMAGE_RE, image):
        raise ValueError("IMMUTABLE_ORIGIN_IMAGE_REQUIRED")
    if (not isinstance(socket_group, str)
            or not re.fullmatch(r"[1-9][0-9]{0,9}", socket_group)
            or int(socket_group) > 4294967294):
        raise ValueError("EXPLICIT_NONROOT_SOCKET_GROUP_REQUIRED")
    return {"services": {"coloring-pages": {
        "image": image,
        "platform": "linux/arm64",
        "group_add": [socket_group],
        "volumes": [{
            "type": "bind",
            "source": SOCKET_DIRECTORY,
            "target": SOCKET_DIRECTORY,
            "read_only": True,
            "bind": {"create_host_path": False},
        }],
    }}}


def write_override(output: Path, image: str, socket_group: str) -> None:
    text = json.dumps(override(image, socket_group), indent=2) + "\n"
    with output.open("x", encoding="utf-8") as handle:
        handle.write(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--socket-group", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_override(args.output, args.image, args.socket_group)


if __name__ == "__main__":
    main()
