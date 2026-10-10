import unittest
from unittest.mock import patch

from app import app
from audit.pagespeed import AuditError


class AuditRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_rejects_non_json_request(self):
        response = self.client.post("/api/audit", data="url=https://example.org")
        self.assertEqual(response.status_code, 415)
        self.assertIn("error", response.get_json())

    def test_homepage_serves_application_not_a_placeholder(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Roast My Website", response.data)
        self.assertIn(b"/static/js/screenshot.js", response.data)
        self.assertIn(b"visual analysis is not included", response.data)
        response.close()

    def test_static_assets_are_served(self):
        for path in (
            "/static/js/app.js",
            "/static/js/screenshot.js",
            "/static/css/styles.css",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_rejects_invalid_json_shape(self):
        response = self.client.post("/api/audit", json=["https://example.org"])
        self.assertEqual(response.status_code, 400)

    @patch(
        "app.run_pagespeed_audit",
        side_effect=AuditError("PageSpeed API is not configured on this server.", 503),
    )
    def test_returns_explicit_server_configuration_error(self, _audit):
        response = self.client.post("/api/audit", json={"url": "https://example.org"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["error"], "PageSpeed API is not configured on this server.")

    @patch("app.run_pagespeed_audit")
    def test_returns_audit_data_without_exposing_request_secrets(self, audit):
        audit.return_value = {
            "source": "pagespeed-insights",
            "site": "https://example.org/",
            "scores": [],
            "audits": [],
            "auditStatusCounts": {},
        }
        response = self.client.post(
            "/api/audit",
            json={"url": "https://example.org/", "strategy": "desktop"},
        )
        self.assertEqual(response.status_code, 200)
        audit.assert_called_once_with("https://example.org/", "desktop")
        self.assertEqual(response.get_json()["source"], "pagespeed-insights")


if __name__ == "__main__":
    unittest.main()
