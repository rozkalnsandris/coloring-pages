import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import goatcounter_origin_compose as compose

IMAGE = "ghcr.io/rozkalnsandris/coloring-pages-origin@sha256:" + "a" * 64


class OriginAppTests(unittest.TestCase):
    def test_narrow_explicit_mount_and_group(self):
        service = compose.override(IMAGE, "1234")["services"]["coloring-pages"]
        self.assertEqual(service, {
            "image": IMAGE, "platform": "linux/arm64", "group_add": ["1234"],
            "volumes": [{"type": "bind", "source": "/run/ausmalwiese-pageview",
                         "target": "/run/ausmalwiese-pageview", "read_only": True,
                         "bind": {"create_host_path": False}}]})

    def test_mutable_or_wrong_image_is_rejected(self):
        for image in [IMAGE.replace("@sha256:", ":"), IMAGE[:-1], IMAGE + "\n",
                      IMAGE.upper(), IMAGE.replace("-origin", ""), "nginx:latest",
                      "${IMAGE}", IMAGE.replace("ghcr.io", "example.invalid")]:
            with self.subTest(image=image), self.assertRaises(ValueError):
                compose.override(image, "1234")

    def test_group_cannot_be_root_name_expression_or_invalid_number(self):
        for group in ["0", "root", "0123", "-1", "+1", "1\n", "${GID}", "1:2",
                      "4294967295", "99999999999999", "", 1234, None]:
            with self.subTest(group=group), self.assertRaises(ValueError):
                compose.override(IMAGE, group)
        self.assertEqual(compose.override(IMAGE, "4294967294")["services"]
                         ["coloring-pages"]["group_add"], ["4294967294"])

    def test_no_overwrite_or_symlink_and_validation_before_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "override.json"
            with self.assertRaises(ValueError):
                compose.write_override(path, "mutable:tag", "1234")
            self.assertFalse(path.exists())
            compose.write_override(path, IMAGE, "1234")
            original = path.read_bytes()
            self.assertEqual(json.loads(original), compose.override(IMAGE, "1234"))
            with self.assertRaises(FileExistsError):
                compose.write_override(path, IMAGE, "2345")
            self.assertEqual(path.read_bytes(), original)
            link = Path(tmp) / "link.json"
            link.symlink_to(path)
            with self.assertRaises(FileExistsError):
                compose.write_override(link, IMAGE, "2345")
            self.assertEqual(path.read_bytes(), original)

    def test_default_build_and_deploy_do_not_select_origin_variant(self):
        for path in ("Dockerfile", "deploy/docker-compose.simple.yml",
                     ".simple-deploy.json", ".github/workflows/simple-deploy.yml"):
            source = (ROOT / path).read_text()
            self.assertNotIn("nginx-origin.conf", source)
            self.assertNotIn("Dockerfile.origin-counting", source)
            self.assertNotIn("/run/ausmalwiese-pageview", source)
        self.assertEqual(json.loads((ROOT / ".simple-deploy.json").read_text())
                         ["build"]["dockerfile"], "Dockerfile")


if __name__ == "__main__":
    unittest.main()
