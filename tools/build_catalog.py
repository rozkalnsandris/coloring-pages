#!/usr/bin/env python3
"""Validate canonical coloring-page metadata and generate dist/catalog.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_AGES = {"3-6", "4-8"}
ALLOWED_DIFFICULTIES = {"easy", "normal", "detailed"}
ALLOWED_LANGUAGES = {"de"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "character",
    "category",
    "age",
    "difficulty",
    "language",
    "original",
}


class CatalogError(ValueError):
    """Raised when canonical catalogue metadata is invalid."""


def _require_string(record: dict[str, Any], key: str, source: Path) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{source}: {key} must be a non-empty string")
    return value.strip()


def validate_record(record: Any, source: Path, repo_root: Path) -> dict[str, str]:
    if not isinstance(record, dict):
        raise CatalogError(f"{source}: top-level JSON value must be an object")

    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        raise CatalogError(f"{source}: missing required fields: {', '.join(missing)}")

    unexpected = sorted(set(record) - REQUIRED_FIELDS)
    if unexpected:
        raise CatalogError(f"{source}: unexpected fields: {', '.join(unexpected)}")

    normalized = {key: _require_string(record, key, source) for key in REQUIRED_FIELDS}

    page_id = normalized["id"]
    if not ID_PATTERN.fullmatch(page_id):
        raise CatalogError(f"{source}: id must match {ID_PATTERN.pattern}")

    if normalized["age"] not in ALLOWED_AGES:
        raise CatalogError(
            f"{source}: age must be one of {', '.join(sorted(ALLOWED_AGES))}"
        )

    if normalized["difficulty"] not in ALLOWED_DIFFICULTIES:
        raise CatalogError(
            f"{source}: difficulty must be one of "
            f"{', '.join(sorted(ALLOWED_DIFFICULTIES))}"
        )

    if normalized["language"] not in ALLOWED_LANGUAGES:
        raise CatalogError(
            f"{source}: language must be one of {', '.join(sorted(ALLOWED_LANGUAGES))}"
        )

    original = Path(normalized["original"])
    if original.is_absolute() or ".." in original.parts:
        raise CatalogError(f"{source}: original must be a safe repository-relative path")

    if not original.parts or original.parts[0] != "originals":
        raise CatalogError(f"{source}: original must be below originals/")

    original_path = (repo_root / original).resolve()
    originals_root = (repo_root / "originals").resolve()
    try:
        original_path.relative_to(originals_root)
    except ValueError as exc:
        raise CatalogError(f"{source}: original escapes originals/") from exc

    if not original_path.is_file():
        raise CatalogError(f"{source}: original does not exist: {normalized['original']}")

    return normalized


def build_entry(record: dict[str, str]) -> dict[str, str]:
    page_id = record["id"]
    media_root = f"/media/{page_id}"
    return {
        "id": page_id,
        "title": record["title"],
        "character": record["character"],
        "category": record["category"],
        "age": record["age"],
        "difficulty": record["difficulty"],
        "language": record["language"],
        "thumb": f"{media_root}/{page_id}-thumb.webp",
        "preview": f"{media_root}/{page_id}-preview.webp",
        "print": f"{media_root}/{page_id}.png",
        "pdf": f"{media_root}/{page_id}.pdf",
    }


def load_catalog(metadata_dir: Path, repo_root: Path) -> list[dict[str, str]]:
    if not metadata_dir.is_dir():
        raise CatalogError(f"metadata directory does not exist: {metadata_dir}")

    entries: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for source in sorted(metadata_dir.glob("*.json")):
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CatalogError(f"{source}: invalid JSON: {exc.msg}") from exc

        record = validate_record(raw, source, repo_root)
        page_id = record["id"]
        if page_id in seen_ids:
            raise CatalogError(f"{source}: duplicate id: {page_id}")
        seen_ids.add(page_id)
        entries.append(build_entry(record))

    return sorted(entries, key=lambda item: item["id"])


def write_catalog(entries: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    output.write_text(payload, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-dir", type=Path, default=Path("metadata"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("dist/catalog.json"))
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate metadata without writing dist/catalog.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    metadata_dir = (
        args.metadata_dir
        if args.metadata_dir.is_absolute()
        else repo_root / args.metadata_dir
    )
    output = args.output if args.output.is_absolute() else repo_root / args.output

    try:
        entries = load_catalog(metadata_dir, repo_root)
        if not args.check:
            write_catalog(entries, output)
    except CatalogError as exc:
        print(f"CATALOG_ERROR: {exc}", file=sys.stderr)
        return 1

    mode = "validated" if args.check else "generated"
    print(f"CATALOG_{mode.upper()}={len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
