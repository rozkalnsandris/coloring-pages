"""#169: new preview derivatives carry a baked watermark; all other media stay clean."""
import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools/coloring-pages-import"
loader = importlib.machinery.SourceFileLoader("watermark_preview_importer", str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
importer = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(importer)


class PreviewWatermarkTests(unittest.TestCase):
    def test_render_is_preview_only_and_source_unchanged(self):
        for size in ((1055, 1491), (1536, 1024)):
            with self.subTest(size=size):
                original = Image.new("RGB", size, "white")
                original.putpixel((40, 40), (255, 32, 64))
                original_pixel = original.getpixel((40, 40))
                preview = importer.resized_copy(original, importer.PREVIEW_MAX_WIDTH)
                clean = preview.copy()
                branded = importer.watermark_preview(preview)
                self.assertEqual(preview.tobytes(), clean.tobytes())
                self.assertEqual(original.getpixel((40, 40)), original_pixel)
                self.assertEqual(branded.size, preview.size)
                self.assertIsNotNone(
                    ImageChops.difference(
                        branded.convert("RGB"), clean.convert("RGB"),
                    ).getbbox()
                )
                self.assertEqual(
                    branded.convert("RGB").getpixel((3, 3)),
                    clean.convert("RGB").getpixel((3, 3)),
                )
                self.assertEqual(importer.PREVIEW_WATERMARK_TEXT, "ausmalwiese.de")
                self.assertAlmostEqual(importer.PREVIEW_WATERMARK_OPACITY, 0.13)
                self.assertEqual(importer.PREVIEW_WATERMARK_ANGLE, 28)
                self.assertAlmostEqual(importer.PREVIEW_WATERMARK_WIDTH_RATIO, 0.46)

    def test_lossless_webp_has_baked_visible_pixels(self):
        with tempfile.TemporaryDirectory() as td:
            original = Image.new("RGB", (1000, 1450), "white")
            before = original.tobytes()
            target = Path(td) / "media"
            importer.build_derivatives([original], target)
            self.assertEqual(original.tobytes(), before)
            with Image.open(target / "thumb.webp") as thumb:
                self.assertEqual(thumb.convert("RGB").getpixel((thumb.width // 2, thumb.height // 2)), (255, 255, 255))
            with Image.open(target / "print.png") as printable:
                self.assertEqual(printable.size, original.size)
                self.assertEqual(printable.getpixel((500, 725)), (255, 255, 255))
            with Image.open(target / "preview.webp") as branded:
                rendered = branded.convert("RGB")
                different = ImageChops.difference(
                    rendered, Image.new("RGB", rendered.size, "white"),
                )
                self.assertIsNotNone(different.getbbox())
                lower = min(rendered.getchannel("R").getextrema())
                self.assertGreaterEqual(lower, 220)
                self.assertLessEqual(lower, 235)

    def test_multipage_uses_one_watermark_per_preview(self):
        with tempfile.TemporaryDirectory() as td:
            original = Image.new("RGB", (1100, 1500), "white")
            target = Path(td) / "media"
            importer.build_derivatives([original, original], target)
            self.assertEqual(
                {p.name for p in target.iterdir()},
                {"thumb.webp", "preview-1.webp", "preview-2.webp",
                 "print-1.png", "print-2.png"},
            )
            for i in (1, 2):
                with Image.open(target / f"preview-{i}.webp") as im:
                    self.assertNotEqual(im.convert("RGB").getpixel((im.width//2,im.height//2)), (0, 0, 0))
                    self.assertIsNotNone(ImageChops.difference(
                        im.convert("RGB"), Image.new("RGB", im.size, "white")
                    ).getbbox())
                with Image.open(target / f"print-{i}.png") as im:
                    self.assertEqual(im.getpixel((im.width//2,im.height//2)), (255,255,255))


if __name__ == "__main__":
    unittest.main()
