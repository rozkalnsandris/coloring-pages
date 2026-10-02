#!/usr/bin/env python3
"""Generate deterministic web and print media derivatives from canonical PNG originals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

from build_catalog import CatalogError, validate_record


PRINT_SIZE = (2480, 3508)
PRINT_DPI = (300, 300)
THUMB_MAX_WIDTH = 400
PREVIEW_MAX_WIDTH = 1000


class MediaError(ValueError):
    """Raised when canonical media cannot be normalized safely."""


def _load_records(metadata_dir: Path, repo_root: Path) -> list[dict[str, str]]:
    if not metadata_dir.is_dir():
        raise MediaError(f"metadata directory does not exist: {metadata_dir}")

    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for source in sorted(metadata_dir.glob("*.json")):
        try:
            raw: Any = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MediaError(f"{source}: invalid JSON: {exc.msg}") from exc

        try:
            record = validate_record(raw, source, repo_root)
        except CatalogError as exc:
            raise MediaError(str(exc)) from exc

        page_id = record["id"]
        if page_id in seen_ids:
            raise MediaError(f"{source}: duplicate id: {page_id}")
        seen_ids.add(page_id)
        records.append(record)

    return records


def _open_master(path: Path) -> Image.Image:
    try:
        with Image.open(path) as source:
            source.load()
            if source.format != "PNG":
                raise MediaError(f"{path}: original must be PNG")
            return ImageOps.exif_transpose(source).convert("L")
    except UnidentifiedImageError as exc:
        raise MediaError(f"{path}: original is not a decodable image") from exc
    except OSError as exc:
        raise MediaError(f"{path}: failed to decode original: {exc}") from exc


def validate_master_size(path: Path, master: Image.Image) -> None:
    """Require canonical masters to already match the print-quality contract."""
    if master.size != PRINT_SIZE:
        raise MediaError(
            f"{path}: original must be exactly "
            f"{PRINT_SIZE[0]}x{PRINT_SIZE[1]} pixels; "
            f"got {master.width}x{master.height}"
        )


def normalize_a4(master: Image.Image) -> Image.Image:
    """Fit source onto a white A4 portrait canvas without stretching."""
    if master.width <= 0 or master.height <= 0:
        raise MediaError("original has invalid dimensions")

    fitted = ImageOps.contain(master, PRINT_SIZE, method=Image.Resampling.LANCZOS)
    canvas = Image.new("L", PRINT_SIZE, color=255)
    x = (PRINT_SIZE[0] - fitted.width) // 2
    y = (PRINT_SIZE[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def resized_copy(image: Image.Image, max_width: int) -> Image.Image:
    if image.width <= max_width:
        return image.copy()

    height = round(image.height * (max_width / image.width))
    return image.resize((max_width, height), Image.Resampling.LANCZOS)


def build_record_media(record: dict[str, str], repo_root: Path, output_root: Path) -> dict[str, Path]:
    page_id = record["id"]
    master_path = repo_root / record["original"]

    master = _open_master(master_path)
    validate_master_size(master_path, master)
    printable = normalize_a4(master)

    target_dir = output_root / "media" / page_id
    target_dir.mkdir(parents=True, exist_ok=True)

    print_path = target_dir / f"{page_id}.png"
    thumb_path = target_dir / f"{page_id}-thumb.webp"
    preview_path = target_dir / f"{page_id}-preview.webp"
    pdf_path = target_dir / f"{page_id}.pdf"

    printable.save(
        print_path,
        format="PNG",
        dpi=PRINT_DPI,
        optimize=False,
        compress_level=9,
    )

    thumb = resized_copy(printable, THUMB_MAX_WIDTH)
    preview = resized_copy(printable, PREVIEW_MAX_WIDTH)
    thumb.save(
        thumb_path,
        format="WEBP",
        lossless=True,
        quality=100,
        method=6,
    )
    preview.save(
        preview_path,
        format="WEBP",
        lossless=True,
        quality=100,
        method=6,
    )

    printable.convert("RGB").save(
        pdf_path,
        format="PDF",
        resolution=PRINT_DPI[0],
    )

    return {
        "thumb": thumb_path,
        "preview": preview_path,
        "print": print_path,
        "pdf": pdf_path,
    }


def build_all(metadata_dir: Path, repo_root: Path, output_root: Path) -> int:
    records = _load_records(metadata_dir, repo_root)
    for record in records:
        build_record_media(record, repo_root, output_root)
    return len(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-dir", type=Path, default=Path("metadata"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output-root", type=Path, default=Path("dist"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    metadata_dir = (
        args.metadata_dir
        if args.metadata_dir.is_absolute()
        else repo_root / args.metadata_dir
    )
    output_root = (
        args.output_root
        if args.output_root.is_absolute()
        else repo_root / args.output_root
    )

    try:
        count = build_all(metadata_dir, repo_root, output_root)
    except MediaError as exc:
        print(f"MEDIA_ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MEDIA_GENERATED={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
