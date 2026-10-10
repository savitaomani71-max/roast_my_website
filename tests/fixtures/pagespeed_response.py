"""Synthetic PageSpeed-shaped response; it is not a real website audit."""

SAMPLE_PAGESPEED_RESPONSE = {
    "lighthouseResult": {
        "requestedUrl": "https://example.org/",
        "finalUrl": "https://example.org/",
        "fetchTime": "2026-01-02T03:04:05.000Z",
        "lighthouseVersion": "12.0.0",
        "categories": {
            "performance": {
                "score": 0.58,
                "auditRefs": [
                    {"id": "slow-audit", "weight": 10},
                    {"id": "passed-audit", "weight": 0}
                ]
            },
            "accessibility": {
                "score": 0.84,
                "auditRefs": [
                    {"id": "not-applicable-audit", "weight": 0},
                    {"id": "missing-audit", "weight": 1}
                ]
            },
            "best-practices": {
                "score": 0.92,
                "auditRefs": [{"id": "manual-audit", "weight": 0}]
            },
            "seo": {"score": None, "auditRefs": []}
        },
        "audits": {
            "slow-audit": {
                "title": "Synthetic slow audit",
                "description": "A synthetic fixture description and recommendation.",
                "score": 0.2,
                "scoreDisplayMode": "numeric",
                "displayValue": "1,200 ms"
            },
            "passed-audit": {
                "title": "Synthetic passing audit",
                "score": 1,
                "scoreDisplayMode": "binary"
            },
            "not-applicable-audit": {
                "title": "Synthetic N/A audit",
                "score": None,
                "scoreDisplayMode": "notApplicable"
            },
            "manual-audit": {
                "title": "Synthetic manual audit",
                "score": None,
                "scoreDisplayMode": "manual"
            }
        }
    }
}
