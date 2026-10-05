import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/coloring-pages-print-master"


class PrintMasterTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def run_tool(self, *args):
        return subprocess.run(
            [sys.executable, str(TOOL), *map(str, args)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_prepare_creates_valid_a4_png_without_mutating_draft(self):
        source = self.root / "draft.png"
        output = self.root / "print.png"

        image = Image.new("RGB", (1024, 1536), (253, 254, 253))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((180, 250, 844, 1280), radius=100, fill=(255, 128, 16))
        image.save(source, format="PNG")
        before = source.read_bytes()

        result = self.run_tool("prepare", source, output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UPSCALE_PRINT=PASS", result.stdout)
        self.assertEqual(source.read_bytes(), before)

        with Image.open(output) as prepared:
            prepared.load()
            self.assertEqual(prepared.format, "PNG")
            self.assertEqual(prepared.size, (2480, 3508))
            self.assertEqual(prepared.mode, "RGB")
            dpi = prepared.info["dpi"]
            self.assertAlmostEqual(dpi[0], 300, delta=1)
            self.assertAlmostEqual(dpi[1], 300, delta=1)
            self.assertEqual(prepared.getpixel((0, 0)), (255, 255, 255))
            self.assertEqual(prepared.getpixel((2479, 3507)), (255, 255, 255))
            self.assertNotEqual(prepared.getpixel((1240, 1754)), (255, 255, 255))

        validated = self.run_tool("validate", output)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertIn("VALIDATE_PRINT=PASS", validated.stdout)
        self.assertIn("WIDTH=2480", validated.stdout)
        self.assertIn("HEIGHT=3508", validated.stdout)
        self.assertIn("SHA256=", validated.stdout)

    def test_prepare_accepts_landscape_and_creates_landscape_a4_master(self):
        source = self.root / "landscape.png"
        output = self.root / "landscape-print.png"

        image = Image.new("RGB", (1536, 1024), "white")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((240, 180, 1296, 844), radius=100, fill=(40, 120, 220))
        image.save(source, format="PNG")

        result = self.run_tool("prepare", source, output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UPSCALE_PRINT=PASS", result.stdout)
        self.assertIn("WIDTH=3508", result.stdout)
        self.assertIn("HEIGHT=2480", result.stdout)
        self.assertIn("ORIENTATION=landscape", result.stdout)

        with Image.open(output) as prepared:
            prepared.load()
            self.assertEqual(prepared.size, (3508, 2480))
            self.assertEqual(prepared.mode, "RGB")
            self.assertEqual(prepared.getpixel((0, 0)), (255, 255, 255))
            self.assertEqual(prepared.getpixel((3507, 2479)), (255, 255, 255))

        validated = self.run_tool("validate", output)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertIn("VALIDATE_PRINT=PASS", validated.stdout)
        self.assertIn("ORIENTATION=landscape", validated.stdout)

    def test_prepare_reserves_white_border_when_source_art_reaches_page_edge(self):
        source = self.root / "edge-art.png"
        output = self.root / "edge-art-print.png"

        image = Image.new("RGB", (1055, 1491), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 100, 14, 1390), fill="black")
        draw.rectangle((1040, 100, 1054, 1390), fill="black")
        image.save(source, format="PNG")

        result = self.run_tool("prepare", source, output)
        self.assertEqual(result.returncode, 0, result.stderr)

        with Image.open(output) as prepared:
            prepared.load()
            self.assertEqual(prepared.size, (2480, 3508))
            self.assertEqual(prepared.mode, "RGB")
            width, height = prepared.size
            self.assertTrue(
                all(prepared.getpixel((x, 0)) == (255, 255, 255) for x in range(width))
            )
            self.assertTrue(
                all(
                    prepared.getpixel((x, height - 1)) == (255, 255, 255)
                    for x in range(width)
                )
            )
            self.assertTrue(
                all(prepared.getpixel((0, y)) == (255, 255, 255) for y in range(height))
            )
            self.assertTrue(
                all(
                    prepared.getpixel((width - 1, y)) == (255, 255, 255)
                    for y in range(height)
                )
            )
            self.assertNotEqual(
                prepared.getpixel((1, height // 2)),
                (255, 255, 255),
            )

        validated = self.run_tool("validate", output)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertIn("VALIDATE_PRINT=PASS", validated.stdout)

    def test_validate_rejects_off_white_outer_border(self):
        path = self.root / "bad-border.png"
        Image.new("RGB", (2480, 3508), (254, 254, 254)).save(
            path, format="PNG", dpi=(300, 300)
        )

        result = self.run_tool("validate", path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outer border must be exact #FFFFFF", result.stderr)

    def test_prepare_rejects_jpeg_and_never_relabels_it_as_png(self):
        source = self.root / "fake.png"
        output = self.root / "print.png"
        Image.new("RGB", (1024, 1536), "white").save(source, format="JPEG")

        result = self.run_tool("prepare", source, output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("draft must be PNG", result.stderr)
        self.assertFalse(output.exists())

    def test_prepare_refuses_to_overwrite_draft(self):
        source = self.root / "draft.png"
        Image.new("RGB", (1024, 1536), "white").save(source, format="PNG")

        result = self.run_tool("prepare", source, source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not overwrite", result.stderr)


if __name__ == "__main__":
    unittest.main()
