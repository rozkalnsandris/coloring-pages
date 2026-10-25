"""Disconnected tests for the opt-in GoatCounter synthetic process harness.

No GoatCounter binary is required. No subprocess is started or HTTP call made.
Tests cannot prove the real upstream binary or German privacy compliance.
"""
import contextlib
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

    def test_digest_verified_for_only_explicit_regular_binary(self):
        path = self.root / "test-bin"
        path.write_bytes(b"synthetic-goatcounter-binary")
        os.chmod(path, 0o700)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(runner._verified_binary(str(path), digest), path)
        with self.assertRaisesRegex(
            runner.RuntimeStop, "^BINARY_DIGEST_MISMATCH$"
        ):
            runner._verified_binary(str(path), "0" * 64)

    def test_symlinked_binary_rejected(self):
        path = self.root / "test-bin"
        path.write_bytes(b"synthetic")
        os.chmod(path, 0o700)
        link = self.root / "bin-link"
        link.symlink_to(path)
        with self.assertRaisesRegex(
            runner.RuntimeStop, "^BINARY_INPUT_INVALID$"
        ):
            runner._verified_binary(str(link), "0" * 64)

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

    def test_invalid_version_stops_before_creating_site(self):
        process = mock.Mock(returncode=0, stdout=b'{"version":"v2.8.0"}')
        with mock.patch.object(
            runner.subprocess, "run", return_value=process
        ) as called:
            with self.assertRaisesRegex(
                runner.RuntimeStop, "^WRONG_GOATCOUNTER_VERSION$"
            ):
                runner._version(Path("/nonexistent/synthetic"), self.root, {})
        called.assert_called_once()

    def test_cli_failure_does_not_leak_stdout(self):
        stream = io.StringIO()
        with mock.patch(
            "sys.argv",
            ["goatcounter-probe", "--binary", "/nonexistent",
             "--expected-binary-sha256", "0" * 64],
        ), contextlib.redirect_stdout(stream), mock.patch.object(
            runner.platform, "node", return_value="isolated-ci"
        ), mock.patch.object(runner.os, "geteuid", return_value=1000):
            result = runner.main()
        self.assertEqual(result, 2)
        self.assertEqual(
            stream.getvalue().strip(),
            "GOATCOUNTER_ISOLATED=STOP CODE=BINARY_INPUT_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
