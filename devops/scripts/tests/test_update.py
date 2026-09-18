import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("updater", SCRIPTS / "update.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class GitUpdateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        self.remote, self.source, self.checkout = [root / name for name in ("remote", "source", "checkout")]
        self.git("init", "--bare", str(self.remote), cwd=root)
        self.git("clone", str(self.remote), str(self.source), cwd=root)
        self.configure(self.source)
        (self.source / "app").write_text("v1")
        self.git("add", ".", cwd=self.source)
        self.git("commit", "-m", "initial", cwd=self.source)
        self.git("push", "-u", "origin", "HEAD", cwd=self.source)
        self.git("clone", str(self.remote), str(self.checkout), cwd=root)
        self.configure(self.checkout)

    def git(self, *args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)

    def configure(self, root):
        self.git("config", "user.email", "test@example.com", cwd=root)
        self.git("config", "user.name", "Test", cwd=root)

    def app(self, *args, **kwargs):
        return subprocess.run(args, check=True, **kwargs)

    def test_fast_forward_and_repeat(self):
        (self.source / "app").write_text("v2")
        self.git("commit", "-am", "update", cwd=self.source)
        self.git("push", cwd=self.source)
        before, after = updater.update_git(self.app, self.checkout)
        self.assertNotEqual(before, after)
        self.assertEqual((self.checkout / "app").read_text(), "v2")
        self.assertEqual(updater.update_git(self.app, self.checkout), (after, after))

    def test_local_changes_are_preserved(self):
        (self.checkout / "app").write_text("local")
        with self.assertRaises(RuntimeError):
            updater.update_git(self.app, self.checkout)
        self.assertEqual((self.checkout / "app").read_text(), "local")

    def test_local_commits_are_not_reset(self):
        (self.checkout / "app").write_text("local commit")
        self.git("commit", "-am", "local", cwd=self.checkout)
        before = self.git("rev-parse", "HEAD", cwd=self.checkout).stdout
        with self.assertRaises(RuntimeError):
            updater.update_git(self.app, self.checkout)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=self.checkout).stdout, before)

    def test_detached_head_is_rejected(self):
        self.git("checkout", "--detach", cwd=self.checkout)
        with self.assertRaises(RuntimeError):
            updater.update_git(self.app, self.checkout)


class DeploymentTests(unittest.TestCase):
    def test_build_failure_recovers_services_and_does_not_migrate(self):
        calls = []
        def app(*args, **kwargs):
            calls.append(args)
            if "build" in args:
                raise RuntimeError("failed build")
        with patch.object(updater, "run"), patch.object(updater.subprocess, "run") as recovery:
            recovery.return_value.returncode = 0
            with self.assertRaises(RuntimeError):
                updater.deploy(app, Path("/opt/example"), "kot7k-test", "auth.example.com")
            self.assertEqual(recovery.call_count, 2)
            self.assertFalse(any("migrate" in args for args in calls))

    def test_success_checks_services_and_http(self):
        with patch.object(updater, "run") as run, patch.object(updater.subprocess, "run") as recovery, patch.object(updater, "verify_http") as health:
            recovery.return_value.returncode = 0
            updater.deploy(lambda *args, **kwargs: None, Path("/opt/example"), "kot7k-test", "auth.example.com")
            health.assert_called_once_with("auth.example.com", "kot7k-test", configure_tls=True)
            checked = [call.args[-1] for call in run.call_args_list if "is-active" in call.args]
            self.assertEqual(len(checked), 5)
            self.assertIn("certbot.timer", checked)

    def test_https_error_is_not_reported_as_success(self):
        response = subprocess.CompletedProcess([], 0, '[]', '')
        with patch.object(updater.subprocess, "run", return_value=response), patch.object(updater, "run", return_value=subprocess.CompletedProcess([], 0, '302', '')):
            with self.assertRaises(RuntimeError):
                updater.verify_http("auth.example.com", "kot7k-test")


class ExternalProxyUpdateTests(unittest.TestCase):
    def test_update_does_not_require_certbot(self):
        with patch.object(updater, "run") as run, patch.object(updater.subprocess, "run") as recovery, patch.object(updater, "verify_http") as health:
            recovery.return_value.returncode = 0
            updater.deploy(lambda *args, **kwargs: None, Path("/opt/example"), "kot7k-test", "auth.example.com", configure_tls=False)
            self.assertFalse(any("certbot.timer" in call.args for call in run.call_args_list))
            health.assert_called_once_with("auth.example.com", "kot7k-test", configure_tls=False)

    def test_proxy_health_uses_http_and_host_without_dns(self):
        with patch.object(updater.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '[]', '')), patch.object(updater, "run", return_value=subprocess.CompletedProcess([], 0, '200', '')) as run:
            updater.verify_http("auth.example.com", "kot7k-test", configure_tls=False)
            self.assertEqual(run.call_count, 3)
            for call in run.call_args_list:
                self.assertIn("Host: auth.example.com", call.args)
                self.assertNotIn("--resolve", call.args)
