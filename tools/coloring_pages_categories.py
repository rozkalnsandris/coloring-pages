"""Bounded, read-only runtime taxonomy shared by nginx, ADMIN, and importer.

A v1 source registry seeds the v2 live file under a separately authorized
RPi5 operation. Importer never falls back to the image on a missing live file.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import unicodedata

SCHEMA = "rozkalns.coloring-pages.categories.v2"
SEED_SCHEMA = "rozkalns.coloring-pages.categories.v1"
CORE_IDS = ("tiere", "fahrzeuge", "alphabet", "lernen", "figuren", "jahreszeiten")
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MAX_BYTES = 16384
MAX_CATEGORIES = 64
# Reserved virtual collection/legacy aliases must not become canonical IDs.
RESERVED_IDS = frozenset({"essen-natur", "seasonal"})


class RegistryError(ValueError):
    """Missing, stale or unsafe taxonomy must prevent content publication."""


def validate_document(document):
    if type(document) is not dict or set(document) != {"schema", "revision", "categories"}:
        raise RegistryError("category registry has unexpected keys")
    if document["schema"] != SCHEMA:
        raise RegistryError("category registry schema is invalid")
    revision = document["revision"]
    if type(revision) is not int or not 1 <= revision <= 2147483647:
        raise RegistryError("category registry revision is invalid")
    categories = document["categories"]
    if type(categories) is not list or not 6 <= len(categories) <= MAX_CATEGORIES:
        raise RegistryError("category registry category count is invalid")
    ids = []
    for item in categories:
        if type(item) is not dict or set(item) != {"id", "label"}:
            raise RegistryError("category registry entry keys are invalid")
        identifier, label = item["id"], item["label"]
        if (type(identifier) is not str or len(identifier) > 48
                or not ID_RE.fullmatch(identifier) or identifier in RESERVED_IDS):
            raise RegistryError("category registry id is invalid")
        if (type(label) is not str or not 1 <= len(label) <= 80
                or label != label.strip() or unicodedata.normalize("NFC", label) != label
                or any(unicodedata.category(c)[0] == "C" for c in label)):
            raise RegistryError("category registry label is invalid")
        ids.append(identifier)
    if tuple(ids[:len(CORE_IDS)]) != CORE_IDS:
        raise RegistryError("structural categories may not be removed or reordered")
    if len(ids) != len(set(ids)):
        raise RegistryError("category registry contains duplicate ids")
    return frozenset(ids)


def serialize_registry(document):
    validate_document(document)
    data = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(data) > MAX_BYTES:
        raise RegistryError("category registry exceeds size limit")
    return data


def seed_from_source(seed_path):
    """Return exact first-deploy seed bytes without touching runtime state."""
    try:
        seed = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise RegistryError("category seed is unavailable") from exc
    if type(seed) is not dict or set(seed) != {"schema", "categories"} or seed["schema"] != SEED_SCHEMA:
        raise RegistryError("category seed schema is invalid")
    doc = {"schema": SCHEMA, "revision": 1, "categories": seed["categories"]}
    serialize_registry(doc)
    return doc


def read_registry(path):
    """(document, canonical SHA-256) from a fixed trusted filesystem path."""
    path = Path(path)
    if path.parent.is_symlink() or path.is_symlink():
        raise RegistryError("category registry symlink is forbidden")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        with os.fdopen(fd, "rb") as source:
            info = os.fstat(source.fileno())
            if (not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_BYTES
                    or (info.st_mode & 0o022)):
                raise RegistryError("category registry file type, mode or size is invalid")
            data = source.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise RegistryError("category registry exceeds size limit")
        document = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        if isinstance(exc, RegistryError):
            raise
        raise RegistryError("runtime category registry is missing or invalid") from exc
    validate_document(document)
    if data != serialize_registry(document):
        raise RegistryError("category registry is not canonical serialized JSON")
    return document, hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Read-only managed taxonomy helper")
    parser.add_argument("command", choices=["seed", "validate"])
    parser.add_argument("--registry", type=Path,
                        default=Path("/srv/coloring-pages-content/public/categories.json"))
    args = parser.parse_args()
    try:
        if args.command == "seed":
            source = Path("/usr/local/share/coloring-pages/categories.json")
            if not source.is_file():
                source = Path(__file__).resolve().parents[1] / "metadata/categories.json"
            print(serialize_registry(seed_from_source(source)).decode("utf-8"), end="")
        else:
            doc, digest = read_registry(args.registry)
            print(f"REGISTRY_OK revision={doc['revision']} sha256={digest}")
    except RegistryError as exc:
        parser.exit(1, f"REGISTRY_ERROR: {exc}\n")
