import io
import json
import os
import socket
import unittest
from copy import deepcopy
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from audit.pagespeed import (
    AuditError,
    normalize_pagespeed_response,
    run_pagespeed_audit,
    validate_public_url,
)
from tests.fixtures.pagespeed_response import SAMPLE_PAGESPEED_RESPONSE


class ValidatePublicUrlTests(unittest.TestCase):
    def test_normalizes_public_http_url_and_drops_fragment(self):
        self.assertEqual(
            validate_public_url("HTTPS://Example.org/path?q=1#section"),
            "https://example.org/path?q=1",
        )

    def test_rejects_local_private_and_non_http_urls(self):
        for url in (
            "http://localhost/",
            "http://127.0.0.1/",
            "http://192.168.1.5/",
            "http://site.local/",
            "file:///C:/private.txt",
            "https://user:pass@example.org/",
            "https://example.org:invalid/",
        ):
            with self.subTest(url=url), self.assertRaises(AuditError):
                validate_public_url(url)

    def test_rejects_malformed_and_non_string_urls(self):
        for url in (None, "", "example.org", "https://bad_host.example.org", "https://bad..org"):
            with self.subTest(url=url), self.assertRaises(AuditError):
                validate_public_url(url)


class NormalizePageSpeedResponseTests(unittest.TestCase):
    def test_maps_realistic_scores_and_all_audit_statuses_without_zero_fallbacks(self):
        result = normalize_pagespeed_response(
            SAMPLE_PAGESPEED_RESPONSE,
            "https://example.org/",
            "mobile",
        )

        self.assertEqual([category["score"] for category in result["scores"]], [58, 84, 92, None])
        self.assertEqual(result["scores"][3]["status"], "unavailable")
        self.assertEqual(result["source"], "pagespeed-insights")
        self.assertEqual(result["auditStatusCounts"], {
            "failed": 1,
            "passed": 1,
            "not_applicable": 1,
            "unavailable": 2,
        })
        failed = result["audits"][0]
        self.assertEqual(failed["id"], "slow-audit")
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["description"], "A synthetic fixture description and recommendation.")
        self.assertEqual(failed["displayValue"], "1,200 ms")
        finding = result["findings"][0]
        self.assertIsNone(finding["roast"])
        self.assertEqual(finding["fix"], "A synthetic fixture description and recommendation.")
        self.assertEqual(finding["source"], "lighthouse-description")
        self.assertEqual(result["priorities"][0]["category"], "Performance")
        self.assertEqual(result["priorities"][0]["findings"][0]["weight"], 10)

    def test_rejects_malformed_response_shapes(self):
        with self.assertRaises(AuditError):
            normalize_pagespeed_response({}, "https://example.org/", "mobile")

    def test_deduplicates_audit_references_and_preserves_all_categories(self):
        response = deepcopy(SAMPLE_PAGESPEED_RESPONSE)
        response["lighthouseResult"]["categories"]["seo"] = {
            "score": 0.76,
            "auditRefs": [{"id": "slow-audit", "weight": 2}],
        }

        result = normalize_pagespeed_response(response, "https://example.org/", "mobile")
        failed = [audit for audit in result["audits"] if audit["status"] == "failed"]

        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["category"], "Performance · SEO")
        priority_by_id = {
            group["categoryId"]: [finding["id"] for finding in group["findings"]]
            for group in result["priorities"]
        }
        self.assertIn("slow-audit", priority_by_id["performance"])
        self.assertIn("slow-audit", priority_by_id["seo"])

    def test_surfaces_provider_rate_limit(self):
        response = {"error": {"code": 429, "message": "synthetic rate limit"}}
        with self.assertRaises(AuditError) as context:
            normalize_pagespeed_response(response, "https://example.org/", "mobile")
        self.assertEqual(context.exception.status_code, 429)

    def test_surfaces_google_quota_error_response(self):
        response = {
            "error": {
                "code": 403,
                "errors": [{"reason": "userRateLimitExceeded"}],
            }
        }
        with self.assertRaises(AuditError) as context:
            normalize_pagespeed_response(response, "https://example.org/", "mobile")
        self.assertEqual(context.exception.status_code, 429)


class RunPageSpeedAuditTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_requires_server_api_key(self):
        with self.assertRaises(AuditError) as context:
            run_pagespeed_audit("https://example.org/")
        self.assertEqual(context.exception.status_code, 503)

    @patch.dict(
        os.environ,
        {"PAGESPEED_API_KEY": "replace-with-your-google-pagespeed-api-key"},
    )
    def test_rejects_unreplaced_example_api_key(self):
        with self.assertRaises(AuditError) as context:
            run_pagespeed_audit("https://example.org/")
        self.assertEqual(context.exception.status_code, 503)

    @patch.dict(os.environ, {"PAGESPEED_API_KEY": "test-only-key"})
    @patch("audit.pagespeed.urlopen")
    def test_requests_all_categories_and_does_not_return_the_api_key(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(
            SAMPLE_PAGESPEED_RESPONSE
        ).encode()

        result = run_pagespeed_audit("https://example.org/", "desktop")

        request = urlopen.call_args.args[0]
        self.assertIn("key=test-only-key", request.full_url)
        self.assertIn("strategy=desktop", request.full_url)
        for category in ("performance", "accessibility", "best-practices", "seo"):
            self.assertIn(f"category={category}", request.full_url)
        self.assertNotIn("test-only-key", json.dumps(result))
        self.assertEqual(result["strategy"], "desktop")

    @patch.dict(os.environ, {"PAGESPEED_API_KEY": "test-only-key"})
    @patch("audit.pagespeed.urlopen", side_effect=URLError("network unavailable"))
    def test_reports_network_failure(self, _urlopen):
        with self.assertRaises(AuditError) as context:
            run_pagespeed_audit("https://example.org/")
        self.assertEqual(context.exception.status_code, 502)

    @patch.dict(os.environ, {"PAGESPEED_API_KEY": "test-only-key"})
    @patch(
        "audit.pagespeed.urlopen",
        side_effect=HTTPError("https://googleapis.example/", 429, "limited", {}, io.BytesIO()),
    )
    def test_reports_upstream_rate_limit(self, _urlopen):
        with self.assertRaises(AuditError) as context:
            run_pagespeed_audit("https://example.org/")
        self.assertEqual(context.exception.status_code, 429)
        context.exception.__cause__.close()

    @patch.dict(os.environ, {"PAGESPEED_API_KEY": "test-only-key"})
    @patch("audit.pagespeed.urlopen", side_effect=socket.timeout())
    def test_reports_timeout(self, _urlopen):
        with self.assertRaises(AuditError) as context:
            run_pagespeed_audit("https://example.org/")
        self.assertEqual(context.exception.status_code, 504)

    @patch.dict(os.environ, {"PAGESPEED_API_KEY": "test-only-key"})
    @patch(
        "audit.pagespeed.urlopen",
        side_effect=HTTPError(
            "https://googleapis.example/",
            403,
            "quota",
            {},
            io.BytesIO(
                b'{"error":{"code":403,"errors":[{"reason":"quotaExceeded"}]}}'
            ),
        ),
    )
    def test_maps_google_403_quota_error_to_rate_limit(self, _urlopen):
        with self.assertRaises(AuditError) as context:
            run_pagespeed_audit("https://example.org/")
        self.assertEqual(context.exception.status_code, 429)
        context.exception.__cause__.close()

    @patch.dict(os.environ, {"PAGESPEED_API_KEY": "test-only-key"})
    @patch("audit.pagespeed.urlopen")
    def test_rejects_malformed_json_response(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b"not json"
        with self.assertRaises(AuditError):
            run_pagespeed_audit("https://example.org/")


if __name__ == "__main__":
    unittest.main()
