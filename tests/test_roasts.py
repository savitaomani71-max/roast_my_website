import unittest

from audit.roasts import build_finding, build_findings, build_priorities


def make_audit(audit_id, category, weight, status="failed"):
    return {
        "id": audit_id,
        "title": audit_id.replace("-", " ").title(),
        "description": f"Official description for {audit_id}.",
        "displayValue": "Synthetic evidence value",
        "score": 0.5 if status == "failed" else 1,
        "status": status,
        "category": category,
        "categoryWeights": [{"id": category, "label": category, "weight": weight}],
    }


class FindingGenerationTests(unittest.TestCase):
    def test_known_failed_audit_gets_id_matched_roast_and_actionable_fix(self):
        finding = build_finding(make_audit("color-contrast", "accessibility", 7))

        self.assertIn("distinguish", finding["impact"].lower())
        self.assertTrue(finding["roast"])
        self.assertIn("WCAG", finding["fix"])
        self.assertEqual(finding["source"], "lighthouse-audit-id")
        self.assertIn("Synthetic evidence value", finding["evidence"])

    def test_unknown_failed_audit_uses_official_guidance_without_a_joke(self):
        finding = build_finding(make_audit("unknown-audit", "performance", 2))

        self.assertIsNone(finding["impact"])
        self.assertIsNone(finding["roast"])
        self.assertEqual(finding["fix"], "Official description for unknown-audit.")
        self.assertEqual(finding["source"], "lighthouse-description")

    def test_passed_audits_are_never_roasted_or_recommended(self):
        with self.assertRaises(ValueError):
            build_finding(make_audit("color-contrast", "accessibility", 7, status="passed"))

        self.assertEqual(build_findings([
            make_audit("color-contrast", "accessibility", 7, status="passed")
        ]), [])

    def test_priorities_sort_categories_by_score_and_findings_by_local_weight(self):
        scores = [
            {"id": "performance", "label": "Performance", "score": 75},
            {"id": "accessibility", "label": "Accessibility", "score": 48},
        ]
        findings = build_findings([
            make_audit("render-blocking-resources", "performance", 5),
            make_audit("unused-javascript", "performance", 10),
            make_audit("color-contrast", "accessibility", 2),
            make_audit("image-alt", "accessibility", 8),
        ])

        priorities = build_priorities(scores, findings)

        self.assertEqual([group["categoryId"] for group in priorities], [
            "accessibility",
            "performance",
        ])
        self.assertEqual([finding["weight"] for finding in priorities[0]["findings"]], [8, 2])
        self.assertEqual([finding["weight"] for finding in priorities[1]["findings"]], [10, 5])


if __name__ == "__main__":
    unittest.main()
