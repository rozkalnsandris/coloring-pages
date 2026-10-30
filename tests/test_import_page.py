import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "coloring-pages-import"
LOADER = importlib.machinery.SourceFileLoader("coloring_pages_import", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
importer = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(importer)


class ImportPageTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.content = self.root / "content"
        for relative in ("inbox", "originals", "public/media", "state"):
            (self.content / relative).mkdir(parents=True, exist_ok=True)
        (self.content / "public/catalog.json").write_text("[]\n", encoding="utf-8")
        from coloring_pages_categories import seed_from_source, serialize_registry
        (self.content / "public/categories.json").write_bytes(
            serialize_registry(seed_from_source(ROOT / "metadata/categories.json"))
        )
        self.source = self.content / "inbox/fire-pup-001.png"
        self.write_source()

    def tearDown(self):
        self.tempdir.cleanup()

    def write_source(self, size=(1055, 1491), fmt="PNG", path=None):
        target = path or self.source
        image = Image.new("L", size, color=255)
        for x in range(150, min(size[0] - 150, 700)):
            image.putpixel((x, min(300, size[1] - 1)), 0)
        image.save(target, format=fmt)

    def metadata(self, **overrides):
        value = {
            "id": "fire-pup-001",
            "title": "Fire Pup 001",
            "character": "",
            "category": "tiere",
            "age": "3-6",
            "difficulty": "easy",
            "language": "de",
        }
        value.update(overrides)
        return value

    def test_success_preserves_source_and_generates_derivatives(self):
        original_bytes = self.source.read_bytes()
        entry = importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(entry["id"], "fire-pup-001")
        original = self.content / "originals/fire-pup-001/source.png"
        media = self.content / "public/media/fire-pup-001"
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertFalse((media / "source.png").exists())
        self.assertTrue((media / "thumb.webp").is_file())
        self.assertTrue((media / "preview.webp").is_file())
        self.assertTrue((media / "print.png").is_file())
        self.assertEqual(
            {path.name for path in media.iterdir()},
            {"thumb.webp", "preview.webp", "print.png"},
        )

        with Image.open(media / "print.png") as print_image:
            self.assertEqual(print_image.mode, "RGB")
            self.assertEqual(print_image.size, (1055, 1491))
            self.assertEqual(print_image.getpixel((0, 0)), (255, 255, 255))
            self.assertEqual(print_image.getpixel((150, 300)), (0, 0, 0))

        catalog = json.loads(
            (self.content / "public/catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog, [entry])
        self.assertEqual(entry["thumb"], "/media/fire-pup-001/thumb.webp")
        self.assertEqual(entry["preview"], "/media/fire-pup-001/preview.webp")
        self.assertEqual(entry["print"], "/media/fire-pup-001/print.png")
        self.assertEqual(
            (self.content / "public/catalog.json").stat().st_mode & 0o777,
            0o644,
        )

    def test_import_stamps_new_utc_publication_time_preserving_legacy_entries(self):
        from datetime import datetime, timezone
        existing = [{"id": "legacy-001", "title": "Old", "thumb": "/media/legacy-001/thumb.webp"}]
        catalog_path = self.content / "public/catalog.json"
        catalog_path.write_text(json.dumps(existing) + "\n", encoding="utf-8")
        before = datetime.now(timezone.utc)
        entry = importer.import_page(self.source, self.content, self.metadata())
        after = datetime.now(timezone.utc)

        published = entry.get("published_at", "")
        self.assertRegex(published, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        moment = datetime.fromisoformat(published.replace("Z", "+00:00"))
        self.assertLessEqual(before.replace(microsecond=0), moment)
        self.assertLessEqual(moment, after)
        catalogue = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(catalogue[0], entry)
        self.assertEqual(catalogue[1], existing[0])
        self.assertNotIn("published_at", catalogue[1])

    def test_print_preserves_source_dpi_metadata_when_present(self):
        Image.new("RGB", (1055, 1491), "white").save(
            self.source, format="PNG", dpi=(300, 300)
        )

        importer.import_page(self.source, self.content, self.metadata())

        with Image.open(self.content / "public/media/fire-pup-001/print.png") as print_image:
            self.assertEqual(print_image.mode, "RGB")
            dpi = print_image.info.get("dpi")
            self.assertIsNotNone(dpi)
            self.assertAlmostEqual(dpi[0], 300.0, delta=1.0)
            self.assertAlmostEqual(dpi[1], 300.0, delta=1.0)

    def test_new_import_is_first_and_existing_order_is_preserved(self):
        existing = [{"id": "z-old"}, {"id": "a-older"}]
        catalog_path = self.content / "public/catalog.json"
        catalog_path.write_text(
            json.dumps(existing) + "\n",
            encoding="utf-8",
        )

        entry = importer.import_page(self.source, self.content, self.metadata())

        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["id"] for item in catalog],
            [entry["id"], "z-old", "a-older"],
        )

    def test_multi_category_one_activity_and_legacy_remain_unchanged(self):
        existing = [{"id": "previous-001", "category": "tiere"}]
        (self.content / "public/catalog.json").write_text(
            json.dumps(existing) + "\n", encoding="utf-8"
        )
        source_bytes = self.source.read_bytes()
        entry = importer.import_page(
            self.source, self.content,
            self.metadata(categories=["tiere", "jahreszeiten"]),
        )
        self.assertEqual(entry["category"], "tiere")
        self.assertEqual(entry["categories"], ["tiere", "jahreszeiten"])
        self.assertEqual((self.content / "originals/fire-pup-001/source.png").read_bytes(), source_bytes)
        catalog = json.loads((self.content / "public/catalog.json").read_text())
        self.assertEqual(len(catalog), 2)
        self.assertEqual(catalog[0], entry)
        self.assertEqual(catalog[1], existing[0])
        self.assertNotIn("categories", catalog[1])
        self.assertEqual(len(list((self.content / "public/media").iterdir())), 1)

    def test_malformed_multi_categories_fail_before_any_content_mutation(self):
        original = (self.content / "public/catalog.json").read_bytes()
        invalid = [[], ["jahreszeiten", "tiere"], ["tiere", "tiere"],
                   ["tiere", "unknown"], ["tiere", ""], ["tiere", 1],
                   ["tiere", None], "tiere", None, {"tiere": True},
                   ["tiere"] * 7]
        for categories in invalid:
            with self.subTest(categories=categories):
                with self.assertRaises(importer.ImportError):
                    importer.import_page(
                        self.source, self.content, self.metadata(categories=categories)
                    )
                self.assertEqual((self.content / "public/catalog.json").read_bytes(), original)
                self.assertFalse((self.content / "originals/fire-pup-001").exists())
                self.assertFalse((self.content / "public/media/fire-pup-001").exists())

    def test_secondary_category_permits_matching_explicit_topic(self):
        entry = importer.import_page(
            self.source, self.content,
            self.metadata(category="tiere", categories=["tiere", "jahreszeiten"],
                          topic="weihnachten"),
        )
        self.assertEqual(entry["topics"], ["weihnachten"])
        self.assertEqual(entry["categories"], ["tiere", "jahreszeiten"])

    def test_cli_repeated_additional_categories_and_duplicate_rejection(self):
        base = [sys.executable, str(MODULE_PATH), str(self.source),
                "--content-root", str(self.content), "--id", "fire-pup-001",
                "--category", "tiere"]
        bad = subprocess.run(
            [*base, "--additional-category", "lernen",
             "--additional-category", "lernen"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(bad.returncode, 0)
        self.assertEqual((self.content / "public/catalog.json").read_text(), "[]\n")
        good = subprocess.run(
            [*base, "--additional-category", "lernen",
             "--additional-category", "jahreszeiten"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        published = json.loads((self.content / "public/catalog.json").read_text())
        self.assertEqual(published[0]["categories"], ["tiere", "lernen", "jahreszeiten"])
        self.assertEqual(published[0]["category"], "tiere")

    def test_explicit_topic_persists_without_changing_legacy_entries(self):
        existing = [{"id": "previous-001", "title": "Original", "category": "tiere"}]
        (self.content / "public/catalog.json").write_text(
            json.dumps(existing) + "\n", encoding="utf-8"
        )
        metadata = self.metadata(category="jahreszeiten", topic="weihnachten")
        entry = importer.import_page(self.source, self.content, metadata)
        self.assertEqual(entry["topics"], ["weihnachten"])
        catalog = json.loads((self.content / "public/catalog.json").read_text())
        self.assertEqual(catalog[0]["topics"], ["weihnachten"])
        self.assertEqual(catalog[1], existing[0])

    def test_multiple_topics_persist_in_order_on_one_activity(self):
        before = self.source.read_bytes()
        entry = importer.import_page(
            self.source, self.content,
            self.metadata(category="tiere", categories=["tiere", "jahreszeiten"],
                          topics=["bauernhof", "weihnachten", "blumen"]),
        )
        self.assertEqual(entry["topics"], ["bauernhof", "weihnachten", "blumen"])
        self.assertEqual(entry["categories"], ["tiere", "jahreszeiten"])
        self.assertEqual((self.content / "originals/fire-pup-001/source.png").read_bytes(), before)
        self.assertTrue((self.content / "public/media/fire-pup-001/print.png").is_file())
        self.assertEqual(json.loads((self.content / "public/catalog.json").read_text())[0], entry)

    def test_one_item_topics_array_and_legacy_single_topic_are_compatible(self):
        entry = importer.import_page(
            self.source, self.content, self.metadata(topics=["bauernhof"]),
        )
        self.assertEqual(entry["topics"], ["bauernhof"])

    def test_repeated_additional_topics_cli_and_duplicate_rejection(self):
        base = [
            sys.executable, str(MODULE_PATH), str(self.source),
            "--content-root", str(self.content), "--id", "fire-pup-001",
            "--category", "tiere", "--additional-category", "jahreszeiten",
        ]
        bad_cases = [
            ["--additional-topic", "bauernhof"],
            ["--topic", "bauernhof", "--additional-topic", "bauernhof"],
            ["--topic", "bauernhof", "--additional-topic", "not-registered"],
        ]
        for extra in bad_cases:
            with self.subTest(extra=extra):
                bad = subprocess.run([*base, *extra], capture_output=True, text=True, check=False)
                self.assertNotEqual(bad.returncode, 0)
                self.assertEqual((self.content / "public/catalog.json").read_text(), "[]\n")
                self.assertFalse((self.content / "originals/fire-pup-001").exists())
        good = subprocess.run(
            [*base, "--topic", "bauernhof", "--additional-topic", "weihnachten",
             "--additional-topic", "blumen"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        published = json.loads((self.content / "public/catalog.json").read_text())
        self.assertEqual(published[0]["topics"], ["bauernhof", "weihnachten", "blumen"])

    def test_invalid_topic_sets_fail_before_content_writes(self):
        before = (self.content / "public/catalog.json").read_bytes()
        invalid = [
            [], ["bauernhof", "bauernhof"], ["bauernhof", "not-registered"],
            ["bauernhof", ""], ["bauernhof", 1], ["bauernhof", None],
            "bauernhof", None, {"topic": "bauernhof"}, ["bauernhof"] * 22,
            ["weihnachten"], ["bauernhof", "weihnachten"],
        ]
        for topics in invalid:
            with self.subTest(topics=topics):
                with self.assertRaises(importer.ImportError):
                    importer.import_page(self.source, self.content, self.metadata(topics=topics))
                self.assertEqual((self.content / "public/catalog.json").read_bytes(), before)
                self.assertFalse((self.content / "originals/fire-pup-001").exists())
                self.assertFalse((self.content / "public/media/fire-pup-001").exists())
        with self.assertRaisesRegex(importer.ImportError, "primary topic"):
            importer.import_page(
                self.source, self.content,
                self.metadata(topic="bauernhof", topics=["blumen", "bauernhof"]),
            )
        self.assertEqual((self.content / "public/catalog.json").read_bytes(), before)

    def test_multiple_seasonal_topics_require_seasonal_category(self):
        entry = importer.import_page(
            self.source, self.content,
            self.metadata(category="jahreszeiten", topics=["weihnachten", "winter"]),
        )
        self.assertEqual(entry["topics"], ["weihnachten", "winter"])

    def test_optional_topic_is_not_synthesized_for_legacy_import(self):
        entry = importer.import_page(self.source, self.content, self.metadata())
        self.assertNotIn("topics", entry)

    def test_unknown_topic_rejected_before_content_writes(self):
        before = (self.content / "public/catalog.json").read_bytes()
        with self.assertRaisesRegex(importer.ImportError, "canonical topic registry"):
            importer.import_page(self.source, self.content, self.metadata(topic="not-registered"))
        self.assertEqual((self.content / "public/catalog.json").read_bytes(), before)
        self.assertFalse((self.content / "originals/fire-pup-001").exists())
        self.assertFalse((self.content / "public/media/fire-pup-001").exists())

    def test_topic_category_kind_and_invalid_selection_rejected(self):
        for topic, category in [
            ("weihnachten", "tiere"),
            ("obst", "jahreszeiten"),
            ("", "jahreszeiten"),
            ("../../etc", "jahreszeiten"),
        ]:
            with self.subTest(topic=topic, category=category):
                with self.assertRaises(importer.ImportError):
                    importer.import_page(self.source, self.content, self.metadata(category=category, topic=topic))
                self.assertFalse((self.content / "originals/fire-pup-001").exists())
        self.assertEqual((self.content / "public/catalog.json").read_text(), "[]\n")

    def test_topics_registry_validation_fail_closed_before_writes(self):
        from unittest.mock import patch
        path = self.root / "topics.json"
        original = json.loads((ROOT / "metadata/topics.json").read_text(encoding="utf-8"))
        with patch.object(importer, "topic_registry_path", return_value=path):
            for invalid in [
                {"schema": "wrong", "topics": original["topics"]},
                {"schema": original["schema"], "topics": [original["topics"][0]] * 2},
                {"schema": original["schema"], "topics": [{"id": "test", "label": "Test", "kind": "broken"}]},
            ]:
                with self.subTest(invalid=invalid):
                    path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaises(importer.ImportError):
                        importer.import_page(
                            self.source, self.content,
                            self.metadata(category="jahreszeiten", topic="weihnachten")
                        )
        self.assertEqual((self.content / "public/catalog.json").read_text(), "[]\n")
        self.assertFalse((self.content / "originals/fire-pup-001").exists())

    def test_cli_accepts_exact_topic_and_persists_it(self):
        run = subprocess.run(
            [sys.executable, str(MODULE_PATH), str(self.source),
             "--content-root", str(self.content), "--id", "fire-pup-001",
             "--category", "jahreszeiten", "--topic", "weihnachten"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("IMPORTED=fire-pup-001 PAGES=1", run.stdout)
        catalog = json.loads((self.content / "public/catalog.json").read_text())
        self.assertEqual(catalog[0]["topics"], ["weihnachten"])

    def test_unknown_category_rejected_before_publication(self):
        with self.assertRaisesRegex(importer.ImportError, "category must be one of"):
            importer.import_page(
                self.source,
                self.content,
                self.metadata(category="berufe"),
            )

    def test_category_registry_contains_current_public_filters(self):
        self.assertEqual(
            importer.load_allowed_categories(),
            frozenset(
                {
                    "tiere",
                    "fahrzeuge",
                    "alphabet",
                    "lernen",
                    "figuren",
                    "jahreszeiten",
                }
            ),
        )

    def test_non_png_rejected(self):
        Image.new("RGB", (1055, 1491), "white").save(self.source, format="JPEG")
        with self.assertRaisesRegex(importer.ImportError, "source must be PNG"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_two_by_three_source_is_accepted_and_preserved(self):
        self.write_source(size=(1024, 1536))
        original_bytes = self.source.read_bytes()

        importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(
            (self.content / "originals/fire-pup-001/source.png").read_bytes(),
            original_bytes,
        )
        self.assertFalse(
            (self.content / "public/media/fire-pup-001/source.png").exists()
        )
        self.assertTrue(
            (self.content / "public/media/fire-pup-001/print.png").is_file()
        )

    def test_landscape_source_is_accepted_and_preserved(self):
        self.write_source(size=(1536, 1024))
        original_bytes = self.source.read_bytes()

        importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(
            (self.content / "originals/fire-pup-001/source.png").read_bytes(),
            original_bytes,
        )
        media = self.content / "public/media/fire-pup-001"
        with Image.open(media / "print.png") as print_image:
            self.assertEqual(print_image.size, (1536, 1024))
        with Image.open(media / "preview.webp") as preview:
            self.assertGreater(preview.width, preview.height)

    def test_print_image_preserves_colors_and_composites_alpha_on_white(self):
        image = Image.new("RGBA", (3, 1), color=(255, 255, 255, 255))
        image.putpixel((1, 0), (255, 32, 64, 255))
        image.putpixel((2, 0), (32, 96, 255, 128))

        result = importer.build_print_image(image)

        self.assertEqual(result.mode, "RGB")
        self.assertEqual(
            list(result.getdata()),
            [(255, 255, 255), (255, 32, 64), (143, 175, 255)],
        )

    def test_color_source_stays_color_in_preview_and_print(self):
        image = Image.new("RGB", (900, 1350), color="white")
        image.putpixel((40, 40), (255, 32, 64))
        image.save(self.source, format="PNG")

        importer.import_page(self.source, self.content, self.metadata())

        media = self.content / "public/media/fire-pup-001"
        with Image.open(media / "preview.webp") as preview:
            self.assertEqual(preview.convert("RGB").getpixel((40, 40)), (255, 32, 64))
        with Image.open(media / "print.png") as print_image:
            self.assertEqual(print_image.getpixel((40, 40)), (255, 32, 64))

    def test_importer_has_no_fixed_2480_by_3508_upscale(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("2480", source)
        self.assertNotIn("3508", source)
        self.assertNotIn("PRINT_DPI", source)

    def test_webp_derivatives_use_balanced_encoder_method(self):
        calls = []
        original_save = Image.Image.save

        def capture_save(image, fp, format=None, **params):
            calls.append((Path(fp).name, format, dict(params)))
            return original_save(image, fp, format=format, **params)

        target = self.root / "derivatives"
        image = Image.new("RGB", (1024, 1536), "white")
        with mock.patch.object(Image.Image, "save", new=capture_save):
            importer.build_derivatives([image], target)

        webp_calls = [call for call in calls if call[1] == "WEBP"]
        self.assertEqual(len(webp_calls), 2)
        for _, _, params in webp_calls:
            self.assertTrue(params["lossless"])
            self.assertEqual(params["quality"], 100)
            self.assertEqual(params["method"], 4)

    def test_invalid_aspect_rejected(self):
        Image.new("L", (1200, 1200), 255).save(self.source, format="PNG")
        with self.assertRaisesRegex(importer.ImportError, "portrait or landscape orientation"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_too_narrow_portrait_ratio_rejected(self):
        Image.new("L", (900, 1500), 255).save(self.source, format="PNG")
        with self.assertRaisesRegex(importer.ImportError, "approximately A4/2:3"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_duplicate_id_rejected(self):
        importer.import_page(self.source, self.content, self.metadata())
        with self.assertRaisesRegex(importer.ImportError, "duplicate page id"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_failure_keeps_published_catalog_unchanged(self):
        sentinel = [{"id": "existing-001"}]
        catalog = self.content / "public/catalog.json"
        catalog.write_text(json.dumps(sentinel) + "\n", encoding="utf-8")

        Image.new("L", (1200, 1200), 255).save(self.source, format="PNG")
        before = catalog.read_bytes()
        with self.assertRaises(importer.ImportError):
            importer.import_page(self.source, self.content, self.metadata())

        self.assertEqual(catalog.read_bytes(), before)

    def test_source_outside_inbox_is_rejected(self):
        outside = self.root / "outside.png"
        self.write_source(path=outside)
        with self.assertRaisesRegex(importer.ImportError, "inside the content inbox"):
            importer.import_page(outside, self.content, self.metadata())

    def test_nested_inbox_source_is_rejected(self):
        nested_dir = self.content / "inbox/nested"
        nested_dir.mkdir()
        nested = nested_dir / "fire-pup-001.png"
        self.write_source(path=nested)
        with self.assertRaisesRegex(importer.ImportError, "direct child"):
            importer.import_page(nested, self.content, self.metadata())

    def test_missing_bootstrap_layout_is_rejected(self):
        (self.content / "state").rmdir()
        with self.assertRaisesRegex(importer.ImportError, "required content directory"):
            importer.import_page(self.source, self.content, self.metadata())

    def test_filename_defaults_are_stable(self):
        path = self.root / "Water Rescue Pup 001.png"
        Image.new("L", (1055, 1491), 255).save(path, format="PNG")
        self.assertEqual(importer.slug_from_path(path), "water-rescue-pup-001")
        self.assertEqual(
            importer.default_title("water-rescue-pup-001"),
            "Water Rescue Pup 001",
        )

    def test_multi_page_activity_preserves_order_and_generates_page_media(self):
        second = self.content / "inbox/fire-pup-001-2.png"
        self.write_source(path=second)
        first_bytes = self.source.read_bytes()
        second_bytes = second.read_bytes()

        entry = importer.import_activity(
            [self.source, second],
            self.content,
            self.metadata(),
        )

        originals = self.content / "originals/fire-pup-001"
        media = self.content / "public/media/fire-pup-001"
        self.assertEqual((originals / "source-1.png").read_bytes(), first_bytes)
        self.assertEqual((originals / "source-2.png").read_bytes(), second_bytes)
        self.assertEqual(
            {path.name for path in originals.iterdir()},
            {"source-1.png", "source-2.png"},
        )
        self.assertEqual(
            {path.name for path in media.iterdir()},
            {
                "thumb.webp",
                "preview-1.webp",
                "preview-2.webp",
                "print-1.png",
                "print-2.png",
            },
        )
        self.assertEqual(
            entry["pages"],
            [
                {
                    "preview": "/media/fire-pup-001/preview-1.webp",
                    "print": "/media/fire-pup-001/print-1.png",
                },
                {
                    "preview": "/media/fire-pup-001/preview-2.webp",
                    "print": "/media/fire-pup-001/print-2.png",
                },
            ],
        )
        self.assertEqual(entry["preview"], entry["pages"][0]["preview"])
        self.assertEqual(entry["print"], entry["pages"][0]["print"])

    def test_multi_page_explicit_topic_is_one_activity_topic(self):
        second = self.content / "inbox/fire-pup-001-2.png"
        self.write_source(path=second)
        entry = importer.import_activity(
            [self.source, second], self.content,
            self.metadata(category="jahreszeiten", topic="halloween"),
        )
        self.assertEqual(entry["topics"], ["halloween"])
        self.assertEqual(len(entry["pages"]), 2)

    def test_multi_page_multiple_topics_stay_on_one_activity(self):
        second = self.content / "inbox/fire-pup-001-2.png"
        self.write_source(path=second)
        entry = importer.import_activity(
            [self.source, second], self.content,
            self.metadata(category="tiere", categories=["tiere", "jahreszeiten"],
                          topics=["bauernhof", "weihnachten"]),
        )
        self.assertEqual(entry["topics"], ["bauernhof", "weihnachten"])
        self.assertEqual(len(entry["pages"]), 2)
        self.assertEqual(len(json.loads((self.content / "public/catalog.json").read_text())), 1)

    def test_multi_page_duplicate_source_is_rejected(self):
        with self.assertRaisesRegex(importer.ImportError, "listed more than once"):
            importer.import_activity(
                [self.source, self.source],
                self.content,
                self.metadata(),
            )

    def test_multi_page_source_outside_inbox_is_rejected(self):
        outside = self.root / "outside-2.png"
        self.write_source(path=outside)
        with self.assertRaisesRegex(importer.ImportError, "inside the content inbox"):
            importer.import_activity(
                [self.source, outside],
                self.content,
                self.metadata(),
            )


if __name__ == "__main__":
    unittest.main()
