import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings
from django.urls import resolve


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class StaticUITests(SimpleTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        override = override_settings(UI_DIST_ROOT=self.root)
        override.enable()
        self.addCleanup(override.disable)
        for name in ["index.html", "authentication/login.html", "authentication/login.txt",
                     "authentication/front-channel-logout", "authentication/signed-out",
                     "_next/static/app.js", ".secret", ".nginx/logout.conf"]:
            file = self.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(name)
        self.headers = {"cache-control": "no-store", "referrer-policy": "no-referrer",
                        "content-security-policy": "default-src 'none'; frame-ancestors https://login.microsoftonline.com"}
        (self.root / ".ui-headers.json").write_text(json.dumps({
            "authentication/front-channel-logout": self.headers,
            "authentication/signed-out": {**self.headers, "content-security-policy": "frame-ancestors 'none'"},
        }))

    def test_pages_assets_and_head(self):
        for url, name in [("/", "index.html"), ("/authentication/login", "authentication/login.html"),
                          ("/authentication/login/", "authentication/login.html"),
                          ("/authentication/login.txt?_rsc=abc", "authentication/login.txt"),
                          ("/_next/static/app.js", "_next/static/app.js")]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b"".join(response.streaming_content), name.encode())
                response.close()
        response = self.client.head("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"")
        response.close()

    def test_logout_headers(self):
        response = self.client.get("/authentication/front-channel-logout?ticket=abc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        for key, value in self.headers.items():
            self.assertEqual(response[key], value)
        self.assertNotIn("X-Frame-Options", response)
        response.close()
        response = self.client.get("/authentication/signed-out")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        response.close()
        (self.root / ".ui-headers.json").unlink()
        self.assertEqual(self.client.get("/authentication/front-channel-logout").status_code, 503)

    def test_missing_private_and_traversal_paths(self):
        (self.root / "escape").symlink_to(Path(__file__).parent)
        for url in ["/missing", "/_next/missing.js", "/.secret", "/.nginx/logout.conf",
                    "/.ui-headers.json", "/%2e%2e/config/settings.py", "/escape/settings.py",
                    "/api/unknown", "/oauth/unknown", "/static/missing.css", "/media/missing"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post("/").status_code, 405)

    def test_backend_routing_and_slash_redirect(self):
        for url in ["/oauth/authorize/", "/admin/", "/.well-known/jwks.json"]:
            self.assertNotEqual(resolve(url).url_name, "ui")
        self.assertEqual(self.client.get("/admin").status_code, 301)
