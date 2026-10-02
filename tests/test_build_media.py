import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

MODULE_PATH = TOOLS / "build_media.py"
SPEC = importlib.util.spec_from_file_location("build_media", MODULE_PATH)
build_media = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(build_media)


class BuildMediaTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.metadata = self.root / "metadata"
        self.originals = self.root / "originals" / "rettungshunde"
        self.output = self.root / "dist"
        self.metadata.mkdir(parents=True)
        self.originals.mkdir(parents=True)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_record(self, original="originals/rettungshunde/ben-001.png"):
        record = {
            "id": "ben-001",
            "title": "Ben hilft einem Kind",
            "character": "Ben",
            "category": "rettungshunde",
            "age": "3-6",
            "difficulty": "easy",
            "language": "de",
            "original": original,
        }
        (self.metadata / "ben-001.json").write_text(
            json.dumps(record), encoding="utf-8"
        )
        return record

    def write_master(self, size=(1240, 1754)):
        image = Image.new("L", size, color=255)
        for x in range(100, min(size[0] - 100, 400)):
            image.putpixel((x, 150), 0)
        path = self.originals / "ben-001.png"
        image.save(path, format="PNG", dpi=(300, 300))
        return path

    def test_normalize_a4_has_exact_print_dimensions(self):
        master = Image.new("L", (1000, 1000), color=255)
        normalized = build_media.normalize_a4(master)
        self.assertEqual(normalized.size, (2480, 3508))
        self.assertEqual(normalized.mode, "L")

    def test_build_generates_expected_derivatives(self):
        self.write_master()
        record = self.write_record()

        paths = build_media.build_record_media(record, self.root, self.output)

        self.assertEqual(
            paths["thumb"],
            self.output / "media" / "ben-001" / "ben-001-thumb.webp",
        )
        self.assertEqual(
            paths["preview"],
            self.output / "media" / "ben-001" / "ben-001-preview.webp",
        )
        self.assertEqual(
            paths["print"],
            self.output / "media" / "ben-001" / "ben-001.png",
        )
        self.assertEqual(
            paths["pdf"],
            self.output / "media" / "ben-001" / "ben-001.pdf",
        )

        for path in paths.values():
            self.assertTrue(path.is_file(), path)

        with Image.open(paths["print"]) as printable:
            self.assertEqual(printable.size, (2480, 3508))
            dpi = printable.info.get("dpi")
            self.assertIsNotNone(dpi)
            self.assertAlmostEqual(dpi[0], 300, delta=0.1)
            self.assertAlmostEqual(dpi[1], 300, delta=0.1)

        with Image.open(paths["thumb"]) as thumb:
            self.assertEqual(thumb.width, 400)
            self.assertLessEqual(thumb.height, 566)

        with Image.open(paths["preview"]) as preview:
            self.assertEqual(preview.width, 1000)
            self.assertLessEqual(preview.height, 1415)

        self.assertTrue(paths["pdf"].read_bytes().startswith(b"%PDF"))

    def test_invalid_image_fails_closed(self):
        self.write_record()
        (self.originals / "ben-001.png").write_bytes(b"not-an-image")

        with self.assertRaisesRegex(build_media.MediaError, "decodable image"):
            build_media.build_all(self.metadata, self.root, self.output)

    def test_non_png_original_fails_closed(self):
        self.write_record()
        image = Image.new("RGB", (100, 100), color="white")
        image.save(self.originals / "ben-001.png", format="JPEG")

        with self.assertRaisesRegex(build_media.MediaError, "must be PNG"):
            build_media.build_all(self.metadata, self.root, self.output)

    def test_empty_catalogue_generates_nothing(self):
        count = build_media.build_all(self.metadata, self.root, self.output)
        self.assertEqual(count, 0)
        self.assertFalse((self.output / "media").exists())


if __name__ == "__main__":
    unittest.main()
