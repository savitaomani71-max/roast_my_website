"""Deterministic explanations for known Lighthouse findings.

Roasts are keyed to exact Lighthouse audit IDs and are only attached to failed
audits. Unknown checks retain their official Lighthouse guidance without a
generated joke or an inferred recommendation.
"""

from __future__ import annotations

from typing import Any


FINDING_EXPLANATIONS: dict[str, dict[str, str]] = {
    "render-blocking-resources": {
        "impact": "Stylesheets or scripts are delaying the browser from showing the page's first content.",
        "roast": "Your first impression is stuck in traffic behind files it did not ask to meet.",
        "fix": "Inline only the critical CSS needed for the first view, and defer or asynchronously load non-critical scripts.",
    },
    "unused-javascript": {
        "impact": "The page downloads JavaScript that is not needed for its initial content.",
        "roast": "The browser packed its whole toolbox just to turn on one light.",
        "fix": "Remove unused code, split JavaScript by route or feature, and load non-critical bundles only when needed.",
    },
    "unused-css-rules": {
        "impact": "The page sends CSS rules that are not used by the current page.",
        "roast": "Your stylesheet brought the entire wardrobe for one outfit.",
        "fix": "Remove unused CSS and split styles so each page loads only the rules it needs.",
    },
    "uses-optimized-images": {
        "impact": "Some images can be delivered with fewer bytes while preserving their visual content.",
        "roast": "That image showed up in full resolution for a job that needed a preview.",
        "fix": "Compress the flagged images and serve them at dimensions close to their rendered size.",
    },
    "modern-image-formats": {
        "impact": "Some images could use a more efficient image format supported by modern browsers.",
        "roast": "Those pixels took the scenic route when a faster format was available.",
        "fix": "Convert eligible images to WebP or AVIF, and keep a compatible fallback where needed.",
    },
    "uses-responsive-images": {
        "impact": "Some images are larger than the rendered size and may transfer more data than necessary.",
        "roast": "Your phone got the desktop-sized photo package. Generous, but unnecessary.",
        "fix": "Generate appropriately sized image variants and use srcset and sizes so browsers can choose a suitable source.",
    },
    "offscreen-images": {
        "impact": "Images below the initial viewport are being loaded before they are needed.",
        "roast": "The page is unpacking images for rooms visitors have not reached yet.",
        "fix": "Lazy-load below-the-fold images, while keeping the main above-the-fold image eager.",
    },
    "color-contrast": {
        "impact": "Some text and background color combinations may be difficult for people to distinguish.",
        "roast": "The text is playing hide-and-seek with the background. Let the text win this round.",
        "fix": "Adjust the flagged foreground or background colors to meet the applicable WCAG contrast ratio.",
    },
    "image-alt": {
        "impact": "Some images do not have text alternatives for people using assistive technology.",
        "roast": "A screen reader met an image and got the conversational equivalent of a shrug.",
        "fix": "Add concise alt text that conveys each informative image's purpose; use empty alt text for decorative images.",
    },
    "button-name": {
        "impact": "Some buttons do not expose a clear accessible name to assistive technology.",
        "roast": "That button is keeping its job title to itself.",
        "fix": "Give each button a concise accessible name using visible text or an appropriate aria-label.",
    },
    "link-name": {
        "impact": "Some links do not expose a clear accessible name to assistive technology.",
        "roast": "The link knows where it goes; its name forgot to come along.",
        "fix": "Provide descriptive link text or an accessible name that explains the link's destination or purpose.",
    },
    "label": {
        "impact": "Some form controls may not have labels that assistive technology can identify.",
        "roast": "The form is asking questions but forgot to label the blanks.",
        "fix": "Associate every form control with a visible label, or provide a suitable accessible name when a visible label is not possible.",
    },
    "document-title": {
        "impact": "The page may not have a useful title for browser tabs, bookmarks, and assistive technology.",
        "roast": "Your browser tab is trying to introduce the page and has no name to use.",
        "fix": "Add a concise, descriptive title element that identifies the page.",
    },
    "meta-description": {
        "impact": "Search engines may not have a concise page summary to use in search results.",
        "roast": "The search result was asked for a summary and got left on read.",
        "fix": "Write a unique, accurate meta description that summarizes the page; search engines may choose a different snippet.",
    },
    "crawlable-anchors": {
        "impact": "Some links may not expose destinations that search crawlers can reliably follow.",
        "roast": "A few links point with confidence, but not in a direction a crawler can follow.",
        "fix": "Use anchor elements with a valid href for navigation, and ensure each destination is crawlable.",
    },
    "uses-text-compression": {
        "impact": "Text-based responses could be transferred in a compressed form to reduce their size.",
        "roast": "The text files are traveling at full size with no suitcase compression.",
        "fix": "Enable Brotli or gzip compression for text responses on the web server or CDN.",
    },
    "server-response-time": {
        "impact": "The server took longer than Lighthouse's recommended threshold to begin responding.",
        "roast": "The server took a moment to collect its thoughts before saying hello.",
        "fix": "Investigate backend processing, caching, database work, and hosting latency to reduce the initial response time.",
    },
    "uses-long-cache-ttl": {
        "impact": "Some static resources may need to be downloaded again sooner than necessary.",
        "roast": "The browser keeps being reintroduced to files it has already met.",
        "fix": "Set an appropriate long-lived cache policy for versioned static assets, and use cache-busting filenames when they change.",
    },
    "font-display": {
        "impact": "Text may remain invisible while a web font is loading.",
        "roast": "The words arrived, but the font is still deciding whether to make an entrance.",
        "fix": "Use font-display: swap or an appropriate alternative so fallback text can appear while the font loads.",
    },
    "errors-in-console": {
        "impact": "The browser console reported errors while loading or running the page.",
        "roast": "The browser console is filing bug reports during the visit.",
        "fix": "Inspect the reported console errors, reproduce them, and fix the underlying scripts or failing requests.",
    },
}


def _finding_evidence(audit: dict[str, Any]) -> str:
    value = audit.get("displayValue")
    if isinstance(value, str) and value.strip():
        return f"Lighthouse reported: {value.strip()}."
    score = audit.get("score")
    if isinstance(score, (int, float)) and not isinstance(score, bool):
        return f"Lighthouse audit score: {round(score * 100)}%."
    return "Lighthouse marked this automatically scored audit as failed."


def build_finding(audit: dict[str, Any]) -> dict[str, Any]:
    """Create a finding from an actual failed audit, using only known recipes."""
    if audit.get("status") != "failed":
        raise ValueError("Only failed Lighthouse audits can become findings.")

    explanation = FINDING_EXPLANATIONS.get(audit["id"])
    official_description = audit.get("description")
    if not isinstance(official_description, str):
        official_description = ""
    guidance = official_description.strip()
    recommendation = explanation["fix"] if explanation else guidance

    return {
        "id": audit["id"],
        "title": audit["title"],
        "category": audit["category"],
        "evidence": _finding_evidence(audit),
        "officialGuidance": guidance,
        "impact": explanation["impact"] if explanation else None,
        "roast": explanation["roast"] if explanation else None,
        "fix": recommendation or None,
        "source": "lighthouse-audit-id" if explanation else "lighthouse-description",
        "score": audit.get("score"),
        "displayValue": audit.get("displayValue"),
        "categoryWeights": audit.get("categoryWeights", []),
    }


def build_findings(audits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build findings only from failed Lighthouse audits."""
    return [
        build_finding(audit)
        for audit in audits
        if audit.get("status") == "failed"
    ]


def build_priorities(
    scores: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Order categories by actual score, then findings by category-local weight."""
    category_order = {score["id"]: index for index, score in enumerate(scores)}
    categories = sorted(
        scores,
        key=lambda score: (
            score["score"] is None,
            score["score"] if score["score"] is not None else 101,
            category_order[score["id"]],
        ),
    )
    priorities = []
    for category in categories:
        category_findings = []
        for finding in findings:
            weight = next(
                (
                    entry["weight"]
                    for entry in finding["categoryWeights"]
                    if entry["id"] == category["id"]
                ),
                None,
            )
            if weight is not None:
                category_findings.append((weight, finding))
        category_findings.sort(key=lambda entry: -entry[0])
        if not category_findings:
            continue

        priorities.append({
            "categoryId": category["id"],
            "category": category["label"],
            "categoryScore": category["score"],
            "findings": [
                {
                    "id": finding["id"],
                    "title": finding["title"],
                    "weight": weight,
                }
                for weight, finding in category_findings
            ],
        })
    return priorities
