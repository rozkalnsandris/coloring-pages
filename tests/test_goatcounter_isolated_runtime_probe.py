"""Disconnected tests for the opt-in GoatCounter synthetic process harness.

No GoatCounter binary is required. No subprocess is started or HTTP call made.
Tests cannot prove the real upstream binary or German privacy compliance.
"""
import contextlib
import gzip
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import goatcounter_isolated_runtime_probe as runner  # noqa: E402


class FakeResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n):
        return b'{"ok":true}'


class RuntimeProbeContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="goatcounter-offline-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_reject_local_root_even_if_binary_exists(self):
        with mock.patch.object(runner.platform, "node", return_value="host.example"):
            with mock.patch.object(runner.os, "geteuid", return_value=0):
                with self.assertRaisesRegex(
                    runner.RuntimeStop, "^UNSAFE_HOST_OR_ROOT$"
                ):
                    runner._host_guard()

    def test_reject_rpi5_host(self):
        with mock.patch.object(runner.platform, "node", return_value="rpi5.local"):
            with mock.patch.object(runner.os, "geteuid", return_value=1000):
                with self.assertRaisesRegex(
                    runner.RuntimeStop, "^UNSAFE_HOST_OR_ROOT$"
                ):
                    runner._host_guard()

    def test_mock_non_root_non_rpi5_allowed(self):
        with mock.patch.object(runner.platform, "node", return_value="isolated-ci"):
            with mock.patch.object(runner.os, "geteuid", return_value=1000):
                runner._host_guard()

    def test_isolated_environment_has_no_proxy_or_credentials(self):
        env = runner._isolated_env(self.root)
        self.assertEqual(env["HOME"], str(self.root))
        self.assertEqual(env["TMPDIR"], str(self.root))
        self.assertNotIn("HTTP_PROXY", env)
        self.assertNotIn("HTTPS_PROXY", env)
        self.assertNotIn("GOATCOUNTER_DB", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)

    def _synthetic_release_archive(self):
        payload = b"synthetic-goatcounter-binary"
        path = self.root / "goatcounter-v2.7.0-linux-amd64.gz"
        with gzip.open(path, "wb") as f:
            f.write(payload)
        asset = {
            "name": path.name,
            "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        return path, payload, asset

    def test_official_release_asset_metadata_is_pinned(self):
        self.assertEqual(
            runner.RELEASE_ASSETS["amd64"],
            {
                "name": "goatcounter-v2.7.0-linux-amd64.gz",
                "size": 13935060,
                "sha256": "98d221cb9c8ef2bf76d8daa9cca647839f8d8b0bb5bc7400ff9337c5da834511",
            },
        )
        self.assertEqual(
            runner.RELEASE_ASSETS["arm64"],
            {
                "name": "goatcounter-v2.7.0-linux-arm64.gz",
                "size": 12770791,
                "sha256": "ff5b2670b858bbe48802dfdc74130b6dcde2de9f5c1229b838eb9132769307dd",
            },
        )

    def test_pinned_release_archive_is_verified_before_extraction(self):
        path, payload, asset = self._synthetic_release_archive()
        with mock.patch.object(
            runner, "_release_asset_for_host", return_value=asset
        ):
            binary = runner._verified_release_archive(str(path), self.root)
        self.assertEqual(binary, self.root / "goatcounter")
        self.assertEqual(binary.read_bytes(), payload)
        self.assertTrue(os.access(binary, os.X_OK))

    def test_release_archive_digest_mismatch_stops(self):
        path, _payload, asset = self._synthetic_release_archive()
        asset = dict(asset, sha256="0" * 64)
        with mock.patch.object(
            runner, "_release_asset_for_host", return_value=asset
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^RELEASE_ARCHIVE_DIGEST_MISMATCH$"
            ):
                runner._verified_release_archive(str(path), self.root)

    def test_release_archive_size_mismatch_stops_before_extraction(self):
        path, _payload, asset = self._synthetic_release_archive()
        asset = dict(asset, size=asset["size"] + 1)
        with mock.patch.object(
            runner, "_release_asset_for_host", return_value=asset
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^RELEASE_ARCHIVE_SIZE_MISMATCH$"
            ):
                runner._verified_release_archive(str(path), self.root)

    def test_symlinked_release_archive_rejected(self):
        path, _payload, asset = self._synthetic_release_archive()
        link = self.root / "release-link.gz"
        link.symlink_to(path)
        asset = dict(asset, name=link.name)
        with mock.patch.object(
            runner, "_release_asset_for_host", return_value=asset
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^RELEASE_ARCHIVE_INPUT_INVALID$"
            ):
                runner._verified_release_archive(str(link), self.root)

    def test_setup_command_rejection_identifies_stage_without_leaking(self):
        for stage in ("DB_NEWDB", "DB_SITE_CREATE", "DB_TOKEN_CREATE"):
            with self.subTest(stage=stage):
                with mock.patch.object(
                    runner.subprocess, "run",
                    return_value=mock.Mock(
                        returncode=2,
                        stdout=b"synthetic-secret-in-stdout",
                        stderr=b"synthetic-secret-in-stderr",
                    ),
                ) as invoked:
                    with self.assertRaises(runner.RuntimeStop) as caught:
                        runner._run(
                            self.root / "goatcounter", self.root, {},
                            "db", "synthetic", "-password=synthetic-secret",
                            stage=stage,
                        )
                self.assertEqual(str(caught.exception), stage + "_REJECTED")
                self.assertNotIn("synthetic-secret", str(caught.exception))
                invoked.assert_called_once()
                self.assertIs(invoked.call_args.kwargs["stdin"], runner.subprocess.DEVNULL)
                self.assertIs(invoked.call_args.kwargs["stdout"], runner.subprocess.DEVNULL)
                self.assertIs(invoked.call_args.kwargs["stderr"], runner.subprocess.DEVNULL)

    def test_setup_command_launch_errors_are_stage_specific(self):
        for stage in ("DB_NEWDB", "DB_SITE_CREATE", "DB_TOKEN_CREATE"):
            for error in (
                OSError("synthetic-secret"),
                runner.subprocess.TimeoutExpired("synthetic-secret", timeout=20),
            ):
                with self.subTest(stage=stage, error=type(error).__name__):
                    with mock.patch.object(
                        runner.subprocess, "run", side_effect=error,
                    ) as invoked:
                        with self.assertRaises(runner.RuntimeStop) as caught:
                            runner._run(
                                self.root / "goatcounter", self.root, {},
                                "db", "synthetic", stage=stage,
                            )
                    self.assertEqual(
                        str(caught.exception), stage + "_LAUNCH_ERROR",
                    )
                    self.assertNotIn("synthetic-secret", str(caught.exception))
                    invoked.assert_called_once()

    def test_unknown_setup_command_stage_stops_before_subprocess(self):
        with mock.patch.object(runner.subprocess, "run") as invoked:
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^BINARY_COMMAND_STAGE_INVALID$"
            ):
                runner._run(
                    self.root / "goatcounter", self.root, {},
                    "db", "synthetic", stage="db passwords in logs",
                )
        invoked.assert_not_called()

    def test_exact_outbound_schema_and_proxy_bypass(self):
        opener = mock.Mock()
        opener.open.return_value = FakeResponse()
        with mock.patch.object(
            runner.urllib.request, "build_opener", return_value=opener
        ) as make:
            runner._count_once(48721, "synthetic-key")
        make.assert_called_once()
        self.assertEqual(len(make.call_args.args), 2)
        self.assertIsInstance(
            make.call_args.args[0], runner.urllib.request.ProxyHandler
        )
        self.assertIsInstance(
            make.call_args.args[1], runner._RejectRedirects
        )
        # ProxyHandler({}) has no active proxy handlers.
        self.assertEqual(make.call_args.args[0].proxies, {})
        # OpenerDirector defaults to Python-urllib/<version> if unset;
        # this must be cleared to avoid an implicit outbound User-Agent.
        self.assertEqual(opener.addheaders, [])
        opener.open.assert_called_once()
        request = opener.open.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.full_url, "http://127.0.0.1:48721/api/v0/count")
        self.assertEqual(request.get_header("Host"), runner.HOST)
        self.assertNotIn("User-agent", request.headers)
        self.assertNotIn("Referer", request.headers)
        self.assertEqual(
            json.loads(request.data),
            {"no_sessions": True, "hits": [{"path": "/coloring-page/0427183"}]},
        )
        self.assertEqual(len(json.loads(request.data)["hits"]), 1)
        for term in (b'"ip"', b'"ref"', b'"user_agent"', b'"session"',
                     b'"query"', b'"bot"'):
            self.assertNotIn(term, request.data)

    def test_redirect_handler_never_forwards_bearer_credentials(self):
        request = runner.urllib.request.Request(
            "http://127.0.0.1:48123/api/v0/count",
            data=b"{}",
            headers={"Authorization": "Bearer synthetic-secret"},
        )
        handler = runner._RejectRedirects()
        self.assertIsNone(
            handler.redirect_request(
                request, None, 302, "Found", {},
                "https://destination.example.invalid/",
            )
        )

    def test_redirect_response_is_not_followed_or_retried(self):
        opener = mock.Mock()
        response = FakeResponse()
        response.status = 302
        opener.open.return_value = response
        with mock.patch.object(
            runner.urllib.request, "build_opener", return_value=opener
        ) as make:
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^BACKEND_NOT_ACCEPTED$"
            ):
                runner._count_once(48721, "synthetic-key")
        self.assertIsInstance(make.call_args.args[1], runner._RejectRedirects)
        opener.open.assert_called_once()

    def test_ambiguous_http_result_not_retried(self):
        opener = mock.Mock()
        opener.open.side_effect = OSError("synthetic-timeout")
        with mock.patch.object(
            runner.urllib.request, "build_opener", return_value=opener
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^BACKEND_RESPONSE_UNCERTAIN$"
            ):
                runner._count_once(48721, "synthetic-key")
        opener.open.assert_called_once()

    def test_non_202_stops(self):
        opener = mock.Mock()
        response = FakeResponse()
        response.status = 200
        opener.open.return_value = response
        with mock.patch.object(
            runner.urllib.request, "build_opener", return_value=opener
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^BACKEND_NOT_ACCEPTED$"
            ):
                runner._count_once(48721, "synthetic-key")

    def test_clean_sigint_wait_is_required_for_success(self):
        process = mock.Mock()
        process.poll.return_value = None
        process.wait.return_value = 0
        runner._stop_server(process)
        process.send_signal.assert_called_once_with(runner.signal.SIGINT)
        process.wait.assert_called_once_with(timeout=12)
        process.kill.assert_not_called()

    def test_nonzero_exit_after_sigint_must_not_pass(self):
        process = mock.Mock()
        process.poll.return_value = None
        process.wait.return_value = 3
        with self.assertRaisesRegex(
            runner.RuntimeStop, "^SERVER_UNCLEAN_EXIT$"
        ):
            runner._stop_server(process)
        process.send_signal.assert_called_once_with(runner.signal.SIGINT)

    def test_already_crashed_process_cannot_pass_sqlite_gate(self):
        process = mock.Mock()
        process.poll.return_value = 42
        process.returncode = 42
        with self.assertRaisesRegex(
            runner.RuntimeStop, "^SERVER_UNCLEAN_EXIT$"
        ):
            runner._stop_server(process)
        process.wait.assert_not_called()
        process.send_signal.assert_not_called()

    def test_shutdown_timeout_kills_process_and_fails(self):
        process = mock.Mock()
        process.poll.return_value = None
        process.wait.side_effect = [
            runner.subprocess.TimeoutExpired(cmd="synthetic", timeout=12),
            -9,
        ]
        with self.assertRaisesRegex(
            runner.RuntimeStop, "^SERVER_SHUTDOWN_TIMEOUT$"
        ):
            runner._stop_server(process)
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)

    @staticmethod
    def _version_json(**overrides):
        data = {
            "version": "v2.7.0",
            "go": "go1.23.2",
            "GOOS": "linux",
            "GOARCH": "amd64",
            "race": False,
            "cgo": True,
        }
        data.update(overrides)
        return json.dumps(data).encode("ascii")

    def test_exact_release_profile_accepted_on_matching_amd64_host(self):
        process = mock.Mock(returncode=0, stdout=self._version_json())
        with mock.patch.object(
            runner.subprocess, "run", return_value=process
        ), mock.patch.object(
            runner.platform, "system", return_value="Linux"
        ), mock.patch.object(
            runner.platform, "machine", return_value="x86_64"
        ):
            runner._version(Path("/nonexistent/synthetic"), self.root, {})

    def test_invalid_version_stops_before_creating_site(self):
        process = mock.Mock(
            returncode=0, stdout=self._version_json(version="v2.8.0")
        )
        with mock.patch.object(
            runner.subprocess, "run", return_value=process
        ) as called:
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^WRONG_GOATCOUNTER_VERSION$"
            ):
                runner._version(Path("/nonexistent/synthetic"), self.root, {})
        called.assert_called_once()

    def test_release_profile_rejects_non_linux_binary(self):
        process = mock.Mock(
            returncode=0, stdout=self._version_json(GOOS="darwin")
        )
        with mock.patch.object(
            runner.subprocess, "run", return_value=process
        ), mock.patch.object(
            runner.platform, "system", return_value="Linux"
        ), mock.patch.object(
            runner.platform, "machine", return_value="x86_64"
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^RELEASE_BUILD_PROFILE_MISMATCH$"
            ):
                runner._version(Path("/nonexistent/synthetic"), self.root, {})

    def test_release_profile_rejects_wrong_arch_for_host(self):
        process = mock.Mock(
            returncode=0, stdout=self._version_json(GOARCH="arm64")
        )
        with mock.patch.object(
            runner.subprocess, "run", return_value=process
        ), mock.patch.object(
            runner.platform, "system", return_value="Linux"
        ), mock.patch.object(
            runner.platform, "machine", return_value="x86_64"
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^RELEASE_BUILD_PROFILE_MISMATCH$"
            ):
                runner._version(Path("/nonexistent/synthetic"), self.root, {})

    def test_release_profile_rejects_cgo_disabled_or_race_build(self):
        for overrides in ({"cgo": False}, {"race": True}):
            with self.subTest(overrides=overrides):
                process = mock.Mock(
                    returncode=0, stdout=self._version_json(**overrides)
                )
                with mock.patch.object(
                    runner.subprocess, "run", return_value=process
                ), mock.patch.object(
                    runner.platform, "system", return_value="Linux"
                ), mock.patch.object(
                    runner.platform, "machine", return_value="x86_64"
                ):
                    with self.assertRaisesRegex(
                        runner.RuntimeStop,
                        "^RELEASE_BUILD_PROFILE_MISMATCH$",
                    ):
                        runner._version(
                            Path("/nonexistent/synthetic"), self.root, {}
                        )

    def test_release_profile_rejects_unexpected_json_field(self):
        process = mock.Mock(
            returncode=0, stdout=self._version_json(commit="synthetic")
        )
        with mock.patch.object(
            runner.subprocess, "run", return_value=process
        ), mock.patch.object(
            runner.platform, "system", return_value="Linux"
        ), mock.patch.object(
            runner.platform, "machine", return_value="x86_64"
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^RELEASE_BUILD_PROFILE_MISMATCH$"
            ):
                runner._version(Path("/nonexistent/synthetic"), self.root, {})

    def test_release_profile_rejects_unsupported_test_host_arch(self):
        process = mock.Mock(returncode=0, stdout=self._version_json())
        with mock.patch.object(
            runner.subprocess, "run", return_value=process
        ), mock.patch.object(
            runner.platform, "system", return_value="Linux"
        ), mock.patch.object(
            runner.platform, "machine", return_value="riscv64"
        ):
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^UNSUPPORTED_RELEASE_HOST$"
            ):
                runner._version(Path("/nonexistent/synthetic"), self.root, {})

    def test_cli_failure_does_not_leak_stdout(self):
        stream = io.StringIO()
        with mock.patch(
            "sys.argv",
            ["goatcounter-probe", "--release-archive",
             "/nonexistent/goatcounter-v2.7.0-linux-amd64.gz"],
        ), contextlib.redirect_stdout(stream), mock.patch.object(
            runner.platform, "node", return_value="isolated-ci"
        ), mock.patch.object(runner.os, "geteuid", return_value=1000):
            result = runner.main()
        self.assertEqual(result, 2)
        self.assertEqual(
            stream.getvalue().strip(),
            "GOATCOUNTER_ISOLATED=STOP CODE=RELEASE_ARCHIVE_INPUT_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
