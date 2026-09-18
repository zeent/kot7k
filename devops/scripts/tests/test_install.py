import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("installer", Path(__file__).resolve().parents[1] / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_domain_validation(self):
        self.assertEqual(installer.domain_name("IDP.ABAQUA.CAT"), "idp.abaqua.cat")
        for value in ["https://example.com", "example.com;include x", "../foo", "localhost",
                      "example.com:443", "127.0.0.1", "-bad.example.com", "example..com"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                installer.domain_name(value)

    def test_checkout_isolation(self):
        first = installer.instance_id(Path("/opt/kot7k"))
        second = installer.instance_id(Path("/opt/kot7k-alt"))
        self.assertNotEqual(first, second)
        self.assertEqual(first, installer.instance_id(Path("/opt/kot7k")))
        config = installer.unit(Path("/opt/kot7k-alt"), "serviceuser", second)
        self.assertIn("WorkingDirectory=/opt/kot7k-alt/api", config)
        self.assertIn(f"unix:/run/{second}/app.sock", config)
        self.assertNotIn("192.168.", config)

    def test_nginx_tls_and_bootstrap(self):
        root = Path("/opt/kot7k-alt")
        bootstrap = installer.nginx_config(root, "auth.example.com", "test")
        self.assertNotIn("ssl_certificate", bootstrap)
        self.assertIn("return 503", bootstrap)
        self.assertIn("/.well-known/acme-challenge/", bootstrap)
        final = installer.nginx_config(root, "auth.example.com", "test", tls=True)
        self.assertIn("return 301 https://auth.example.com$request_uri", final)
        self.assertIn("proxy_set_header X-Forwarded-Proto $scheme", final)
        self.assertIn("alias /opt/kot7k-alt/api/static_dist/", final)
        self.assertIn("/run/test/app.sock", final)
        self.assertNotIn("X-Frame-Options", final)

    def test_atomic_private_state(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "state.json"
            installer.write_atomic(file, "first", 0o600)
            installer.write_atomic(file, "second", 0o600)
            self.assertEqual(file.read_text(), "second")
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
            self.assertFalse(file.with_name("state.json.install-tmp").exists())

    def test_non_linux_is_rejected_before_mutations(self):
        with patch.object(installer.sys, "platform", "darwin"), patch.object(installer, "run") as run:
            with self.assertRaises(RuntimeError):
                installer.main()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class NginxInstallTests(unittest.TestCase):
    def test_failed_validation_restores_old_site(self):
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            site = root / "available/site"
            enabled = root / "enabled"
            enabled.mkdir()
            installer.write_atomic(site, installer.MARKER + "\nold")
            (enabled / "site").symlink_to(site)
            with patch.object(installer, "run", side_effect=subprocess.CalledProcessError(1, ["nginx", "-t"])), self.assertRaises(subprocess.CalledProcessError):
                installer.install_nginx(site, installer.MARKER + "\nnew", enabled)
            self.assertEqual(site.read_text(), installer.MARKER + "\nold")
            self.assertTrue((enabled / "site").is_symlink())

    def test_failed_new_site_leaves_no_broken_link(self):
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            site = root / "available/site"
            enabled = root / "enabled"
            enabled.mkdir()
            with patch.object(installer, "run", side_effect=subprocess.CalledProcessError(1, ["nginx", "-t"])), self.assertRaises(subprocess.CalledProcessError):
                installer.install_nginx(site, installer.MARKER + "\nnew", enabled)
            self.assertFalse(site.exists())
            self.assertFalse((enabled / "site").is_symlink())

    def test_unmanaged_site_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder) / "site"
            site.write_text("existing config")
            with self.assertRaises(RuntimeError):
                installer.install_nginx(site, "new config", Path(folder))
            self.assertEqual(site.read_text(), "existing config")
