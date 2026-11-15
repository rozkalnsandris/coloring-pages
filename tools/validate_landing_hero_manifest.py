#!/usr/bin/env python3
"""Validate source-reviewed Hero art metadata without changing runtime state.

This is a source-only foundation (#578), NOT a runtime Topic registry or renderer.
Approval references are assertions reviewed with the source PR; they are not proof
that a remote GitHub approval exists. Runtime managed IDs come from /topics.json.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "rozkalns.ausmalwiese.landing-hero.v1"
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
APPROVAL = re.compile(r"coloring-pages#[1-9][0-9]*\Z")
PROVENANCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./:# -]{4,159}\Z")
BASE_FIELDS = frozenset({
    "image", "width", "height", "bytes", "sha256", "alt",
    "provenance", "approval_ref",
})


class ManifestValidationError(ValueError):
    """Invalid or unsupported landing Hero source data."""


def fail(reason: str) -> None:
    raise ManifestValidationError(reason)


def unique_pairs(pairs):
    """Fail on duplicate keys at every JSON object depth."""
    output = {}
    for key, value in pairs:
        if key in output:
            fail("duplicate JSON key: " + key)
        output[key] = value
    return output


def parse_manifest(text: str):
    try:
        return json.loads(
            text,
            object_pairs_hook=unique_pairs,
            parse_constant=lambda value: fail("nonfinite JSON value: " + value),
        )
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, ManifestValidationError):
            raise
        fail("invalid JSON: " + str(exc))


def exact_keys(value, expected, label):
    if type(value) is not dict or set(value) != set(expected):
        fail(label + ": required keys differ from allowed keys")


def printable_text(value, label, limit=180):
    if type(value) is not str or not (1 <= len(value) <= limit):
        fail(label + ": empty, oversized or non-string text")
    if value != value.strip() or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        fail(label + ": whitespace/control characters")
    if any(ch in value for ch in "<>&\""):
        fail(label + ": HTML markup/entity special character")


def webp_size(data: bytes):
    """Read image dimensions from RIFF WebP VP8, VP8L or VP8X headers."""
    if (len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP"
            or int.from_bytes(data[4:8], "little") != len(data) - 8):
        fail("invalid RIFF/WebP envelope")
    kind = data[12:16]
    chunk_size = int.from_bytes(data[16:20], "little")
    if chunk_size <= 0 or 20 + chunk_size > len(data):
        fail("truncated WebP chunk")
    if kind == b"VP8 ":
        if chunk_size < 10 or data[23:26] != bytes((0x9d, 0x01, 0x2a)):
            fail("invalid VP8 keyframe")
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
    elif kind == b"VP8L":
        if chunk_size < 5 or data[20] != 0x2F:
            fail("invalid VP8L header")
        bits = int.from_bytes(data[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
    elif kind == b"VP8X":
        if chunk_size < 10:
            fail("invalid VP8X header")
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
    else:
        fail("unsupported WebP first chunk")
    if width <= 0 or height <= 0:
        fail("invalid WebP dimensions")
    return width, height


class HeroImages(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.images = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "section":
            if self.depth:
                self.depth += 1
            elif "page-hero" in data.get("class", "").split():
                self.depth = 1
        elif tag == "img" and self.depth:
            self.images.append(data)

    def handle_endtag(self, tag):
        if tag == "section" and self.depth:
            self.depth -= 1


def validate_html(record, slug, path: Path):
    if not path.is_file() or path.is_symlink():
        fail("static Hero page missing: " + path.name)
    try:
        markup = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail("cannot read static Hero page: " + str(exc))
    found = HeroImages()
    found.feed(markup)
    images = [attrs for attrs in found.images if attrs.get("src") == record["image"]]
    if len(images) != 1 or markup.count('src="' + record["image"] + '"') != 1:
        fail(slug + ": missing, duplicate or misplaced static Hero image")
    attrs = images[0]
    if (attrs.get("alt") != record["alt"]
            or attrs.get("width") != str(record["width"])
            or attrs.get("height") != str(record["height"])):
        fail(slug + ": existing static Hero HTML differs from manifest")


def validate_record(record, slug, namespace, root: Path):
    fields = BASE_FIELDS | ({"intro"} if namespace == "topics" and "intro" in record else set())
    exact_keys(record, fields, namespace + "." + slug)
    if type(slug) is not str or not ID.fullmatch(slug):
        fail("invalid Hero ID")
    if type(record["image"]) is not str or record["image"] != "/assets/" + slug + "-topic-hero.webp":
        fail(slug + ": asset path must match the reviewed slug convention")
    if (type(record["width"]) is not int or type(record["height"]) is not int
            or record["width"] <= 0 or record["height"] <= 0
            or record["width"] > 8192 or record["height"] > 8192):
        fail(slug + ": invalid dimensions")
    if type(record["bytes"]) is not int or not (1 <= record["bytes"] <= 2_000_000):
        fail(slug + ": invalid byte count")
    if type(record["sha256"]) is not str or not SHA256.fullmatch(record["sha256"]):
        fail(slug + ": invalid digest")
    printable_text(record["alt"], slug + ".alt")
    if "intro" in record:
        printable_text(record["intro"], slug + ".intro", 300)
    if (type(record["provenance"]) is not str
            or not PROVENANCE.fullmatch(record["provenance"])
            or ".." in record["provenance"]):
        fail(slug + ": invalid provenance")
    if type(record["approval_ref"]) is not str or not APPROVAL.fullmatch(record["approval_ref"]):
        fail(slug + ": missing source-reviewed approval reference")

    assets = (root / "assets").resolve()
    filename = record["image"].removeprefix("/assets/")
    candidate = root / "assets" / filename
    if candidate.is_symlink() or not candidate.is_file() or candidate.resolve().parent != assets:
        fail(slug + ": missing or unsafe local asset")
    try:
        data = candidate.read_bytes()
    except OSError as exc:
        fail(slug + ": cannot read asset: " + str(exc))
    if len(data) != record["bytes"]:
        fail(slug + ": asset bytes differ")
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        fail(slug + ": asset SHA-256 differs")
    if webp_size(data) != (record["width"], record["height"]):
        fail(slug + ": native WebP dimensions differ")
    validate_html(record, slug, root / (slug + ".html"))


def validate_data(data, root: Path = ROOT):
    exact_keys(data, {"schema", "categories", "topics"}, "manifest")
    if data["schema"] != SCHEMA:
        fail("unsupported Hero manifest schema")
    root = Path(root)
    for namespace in ("categories", "topics"):
        records = data[namespace]
        if type(records) is not dict:
            fail(namespace + " must be an object")
        if namespace == "categories":
            category_file = root / "metadata" / "categories.json"
            try:
                categories = json.loads(category_file.read_text(encoding="utf-8"))
                if (categories.get("schema") != "rozkalns.coloring-pages.categories.v1"
                        or not isinstance(categories.get("categories"), list)):
                    fail("invalid source category seed")
                ids = {entry["id"] for entry in categories["categories"]}
            except (ValueError, KeyError, TypeError, OSError) as exc:
                fail("invalid source category seed: " + str(exc))
        for slug, record in records.items():
            if type(slug) is not str or not ID.fullmatch(slug):
                fail("invalid namespace ID")
            if namespace == "categories" and slug not in ids:
                fail("unknown source category ID: " + slug)
            # Topic IDs are NOT validated against metadata/topics.json: it is
            # a source seed, not the canonical managed /topics.json in LIVE.
            validate_record(record, slug, namespace, root)
    return data


def validate_manifest_text(text: str, root: Path = ROOT):
    return validate_data(parse_manifest(text), root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "metadata/landing-hero.v1.json")
    args = parser.parse_args()
    try:
        validate_manifest_text(args.manifest.read_text(encoding="utf-8"))
    except (ManifestValidationError, OSError, UnicodeError) as exc:
        print("Hero manifest INVALID: " + str(exc), file=sys.stderr)
        return 1
    print("Hero manifest valid (source-only, no runtime registry mutation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
