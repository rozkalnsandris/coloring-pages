"""Canonical read-only managed Topics v2 runtime registry (image v1 = seed only)."""
from __future__ import annotations

from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import unicodedata

SCHEMA = "rozkalns.coloring-pages.topics.v2"
SEED_SCHEMA = "rozkalns.coloring-pages.topics.v1"
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MAX_BYTES = 65536
MAX_TOPICS = 128
MAX_TERMS = 32


class RegistryError(ValueError):
    """Unsafe Topics must fail before publishing any content."""


def _text(value, maximum, field):
    if (type(value) is not str or not 1 <= len(value) <= maximum
            or value != value.strip() or unicodedata.normalize("NFC", value) != value
            or any(unicodedata.category(char)[0] == "C" for char in value)):
        raise RegistryError(f"topic {field} is invalid")


def _date(value):
    if type(value) is not str or not re.fullmatch(r"[0-9]{2}-[0-9]{2}", value):
        raise RegistryError("topic date must use MM-DD")
    month, day = map(int, value.split("-"))
    try:
        date(2024, month, day)  # 02-29 and wraparound intervals are valid
    except ValueError as exc:
        raise RegistryError("topic date is invalid") from exc


def validate_document(document):
    if type(document) is not dict or set(document) != {"schema", "revision", "topics"}:
        raise RegistryError("topic registry keys are invalid")
    if document["schema"] != SCHEMA:
        raise RegistryError("topic registry schema is invalid")
    revision = document["revision"]
    if type(revision) is not int or not 1 <= revision <= 2147483647:
        raise RegistryError("topic revision is invalid")
    topics = document["topics"]
    if type(topics) is not list or not 1 <= len(topics) <= MAX_TOPICS:
        raise RegistryError("topic count is invalid")
    ids = set()
    for topic in topics:
        if type(topic) is not dict or topic.get("kind") not in ("seasonal", "evergreen"):
            raise RegistryError("topic entry or kind is invalid")
        kind = topic["kind"]
        required = {"id", "label", "icon", "kind", "legacy_terms"}
        if kind == "seasonal":
            required |= {"active_from", "active_to"}
        if set(topic) != required:
            raise RegistryError("topic fields are invalid")
        ident = topic["id"]
        if type(ident) is not str or len(ident) > 48 or not ID_RE.fullmatch(ident):
            raise RegistryError("topic id is invalid")
        if ident in ids:
            raise RegistryError("duplicate topic id")
        ids.add(ident)
        _text(topic["label"], 80, "label")
        icon = topic["icon"]
        # Allow emoji ZWJ sequences, not markup/control or path fragments.
        if (type(icon) is not str or not 1 <= len(icon) <= 12
                or unicodedata.normalize("NFC", icon) != icon
                or any(char in "<>&" or (unicodedata.category(char)[0] == "C" and char != "\u200d")
                       for char in icon)):
            raise RegistryError("topic icon is invalid")
        terms = topic["legacy_terms"]
        if type(terms) is not list or len(terms) > MAX_TERMS:
            raise RegistryError("topic terms are invalid")
        for term in terms:
            _text(term, 64, "legacy term")
        if len(set(terms)) != len(terms):
            raise RegistryError("duplicate topic terms")
        if kind == "seasonal":
            _date(topic["active_from"])
            _date(topic["active_to"])
    return {topic["id"]: topic["kind"] for topic in topics}


def serialize_registry(document):
    validate_document(document)
    raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise RegistryError("topic registry exceeds size limit")
    return raw


def seed_from_source(path):
    """Construct a deterministic v2 seed without touching runtime state."""
    try:
        source = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise RegistryError("topic seed is unavailable") from exc
    if type(source) is not dict or set(source) != {"schema", "topics"} or source["schema"] != SEED_SCHEMA:
        raise RegistryError("topic seed schema is invalid")
    document = {"schema": SCHEMA, "revision": 1, "topics": source["topics"]}
    serialize_registry(document)
    return document


def read_registry(path):
    """Read bounded canonical runtime JSON plus SHA-256, with no fallback."""
    path = Path(path)
    if path.is_symlink() or path.parent.is_symlink():
        raise RegistryError("topic registry symlink is forbidden")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_BYTES
                    or info.st_mode & 0o022):
                raise RegistryError("topic registry type, mode or size is invalid")
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise RegistryError("topic registry exceeds size limit")
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        if isinstance(exc, RegistryError):
            raise
        raise RegistryError("runtime topic registry is missing or invalid") from exc
    if raw != serialize_registry(document):
        raise RegistryError("topic registry JSON is not canonical")
    return document, hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Read-only managed Topics v2 helper")
    parser.add_argument("command", choices=["seed", "validate"])
    parser.add_argument("--registry", type=Path,
                        default=Path("/srv/coloring-pages-content/public/topics.json"))
    args = parser.parse_args()
    try:
        if args.command == "seed":
            seed = Path("/usr/local/share/coloring-pages/topics.json")
            if not seed.is_file():
                seed = Path(__file__).resolve().parents[1] / "metadata/topics.json"
            print(serialize_registry(seed_from_source(seed)).decode("utf-8"), end="")
        else:
            document, sha = read_registry(args.registry)
            print(f"TOPICS_OK revision={document['revision']} sha256={sha}")
    except RegistryError as exc:
        parser.exit(1, f"TOPICS_ERROR: {exc}\n")
