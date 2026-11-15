#!/usr/bin/env python3
"""Build the existing Topic Hero browser adapter from reviewed source metadata.

The reviewed source manifest owns artwork/copy. Protected /topics.json remains
authoritative for which managed Topic the client may actually render (#582).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from validate_landing_hero_manifest import (
    ManifestValidationError, ROOT, validate_manifest_text,
)

SOURCE = ROOT / "metadata/landing-hero.v1.json"
TARGET = ROOT / "js/topic-hero-content.js"
TEMPLATE = r"""/* Generated from reviewed Hero metadata by render_landing_hero_topic_js.py.
   Do not edit this browser adapter directly. The managed Topic registry is /topics.json. */
(() => {
  "use strict";
  const manifest = Object.freeze({
    schema: "rozkalns.ausmalwiese.topic-hero.v1",
    topics: Object.freeze({
@@TOPIC_ROWS@@
    })
  });

  function get(topicId) {
    if (typeof topicId !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(topicId)) return null;
    const entry = Object.prototype.hasOwnProperty.call(manifest.topics, topicId)
      ? manifest.topics[topicId] : null;
    if (!entry) return null;
    const intro = typeof entry.intro === "string" && entry.intro.length <= 300
      ? entry.intro : "";
    const image = entry.image;
    const safeImage = image && image.src === "/assets/" + topicId + "-topic-hero.webp" &&
      Number.isInteger(image.width) && image.width > 0 &&
      Number.isInteger(image.height) && image.height > 0 &&
      typeof image.alt === "string" && image.alt.length > 0 && image.alt.length <= 180 &&
      /^[a-f0-9]{64}$/.test(image.sha256)
      ? image : null;
    return { intro, image: safeImage };
  }

  globalThis.AusmalTopicHero = Object.freeze({ schema: manifest.schema, get });
})();
"""


def render(root: Path = ROOT) -> str:
    """Return deterministic JS; validate complete manifest and static art first."""
    root = Path(root)
    payload = validate_manifest_text(
        (root / "metadata/landing-hero.v1.json").read_text(encoding="utf-8"), root
    )
    blocks = []
    for slug, record in sorted(payload["topics"].items()):
        q = lambda value: json.dumps(value, ensure_ascii=True)
        blocks.append(
            f"      {q(slug)}: Object.freeze({{\n"
            f"        intro: {q(record.get('intro', ''))},\n"
            "        image: Object.freeze({\n"
            f"          src: {q(record['image'])},\n"
            f"          width: {record['width']},\n"
            f"          height: {record['height']},\n"
            f"          alt: {q(record['alt'])},\n"
            f"          sha256: {q(record['sha256'])},\n"
            f"          provenance: {q(record['provenance'])},\n"
            f"          approval_ref: {q(record['approval_ref'])}\n"
            "        })\n"
            "      })"
        )
    return TEMPLATE.replace("@@TOPIC_ROWS@@", ",\n".join(blocks))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Check that committed JS matches the approved source")
    args = parser.parse_args()
    try:
        generated = render()
        if args.check:
            if TARGET.read_text(encoding="utf-8") != generated:
                print("Topic Hero adapter is stale: regenerate from source", file=sys.stderr)
                return 1
            print("Topic Hero adapter matches reviewed manifest")
            return 0
        TARGET.write_text(generated, encoding="utf-8")
        print("Wrote validated Topic Hero adapter")
        return 0
    except (ManifestValidationError, OSError, UnicodeError) as exc:
        print("Topic Hero adapter generation failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
