"""Validated server-side client for the Google PageSpeed Insights API."""

from __future__ import annotations

import ipaddress
import json
import math
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from audit.roasts import build_findings, build_priorities


API_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
API_TIMEOUT_SECONDS = 35
MAX_RESPONSE_BYTES = 10_000_000
CATEGORY_NAMES = {
    "performance": "Performance",
    "accessibility": "Accessibility",
    "best-practices": "Best Practices",
    "seo": "SEO",
}
ALLOWED_STRATEGIES = {"mobile", "desktop"}
AUTOMATED_SCORE_MODES = {"numeric", "binary"}


class AuditError(Exception):
    """An expected audit failure safe to describe to the user."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def validate_public_url(value: Any) -> str:
    """Return a normalized HTTP(S) URL, rejecting malformed and local hosts."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise AuditError("Enter a valid public website URL.", 400)
    if value != value.strip() or any(character.isspace() for character in value):
        raise AuditError("Enter a valid public website URL without spaces.", 400)

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise AuditError("Enter a valid public website URL.", 400) from error

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.netloc
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise AuditError("Use a public URL starting with http:// or https://.", 400)

    host = hostname.rstrip(".").lower()
    if not host or host == "localhost" or host.endswith(
        (".localhost", ".local", ".internal", ".test", ".example", ".invalid")
    ):
        raise AuditError("Local and example addresses cannot be audited.", 400)

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if "." not in host or host.startswith(".") or ".." in host:
            raise AuditError("Enter a fully qualified public website hostname.", 400)
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError as error:
            raise AuditError("Enter a valid public website hostname.", 400) from error
        if any(
            not label
            or len(label) > 63
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label, re.IGNORECASE)
            for label in ascii_host.split(".")
        ):
            raise AuditError("Enter a valid public website hostname.", 400)
    else:
        if not address.is_global:
            raise AuditError("Private and reserved IP addresses cannot be audited.", 400)

    netloc = host
    if ":" in host:
        netloc = f"[{host}]"
    if port is not None:
        netloc = f"{netloc}:{port}"

    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))


def _audit_status(audit: dict[str, Any] | None) -> str:
    if audit is None:
        return "unavailable"
    mode = audit.get("scoreDisplayMode")
    if mode == "notApplicable":
        return "not_applicable"
    if mode not in AUTOMATED_SCORE_MODES:
        return "unavailable"

    score = audit.get("score")
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0 <= score <= 1
    ):
        return "unavailable"
    return "passed" if score >= 1 else "failed"


def _is_rate_limit_error(error_payload: Any) -> bool:
    if not isinstance(error_payload, dict):
        return False
    error = error_payload.get("error")
    if not isinstance(error, dict):
        return False
    if error.get("code") == 429:
        return True

    reasons = error.get("errors")
    if not isinstance(reasons, list):
        return False
    rate_limit_reasons = {
        "rateLimitExceeded",
        "userRateLimitExceeded",
        "dailyLimitExceeded",
        "quotaExceeded",
    }
    return any(
        isinstance(reason, dict) and reason.get("reason") in rate_limit_reasons
        for reason in reasons
    )


def normalize_pagespeed_response(payload: Any, submitted_url: str, strategy: str) -> dict[str, Any]:
    """Extract only category scores and relevant Lighthouse audit evidence."""
    if not isinstance(payload, dict):
        raise AuditError("Google returned an invalid audit response.")
    if "error" in payload:
        if _is_rate_limit_error(payload):
            raise AuditError("Google PageSpeed is rate-limited right now. Please try again shortly.", 429)
        raise AuditError("Google PageSpeed could not complete this audit. Please try again later.")

    lighthouse = payload.get("lighthouseResult")
    if not isinstance(lighthouse, dict):
        raise AuditError("Google returned an incomplete audit response.")

    categories = lighthouse.get("categories")
    if not isinstance(categories, dict):
        raise AuditError("Google returned an incomplete audit response.")

    audits = lighthouse.get("audits")
    if not isinstance(audits, dict):
        audits = {}

    category_results = []
    audit_results = []
    audit_by_id: dict[str, dict[str, Any]] = {}

    for category_id, label in CATEGORY_NAMES.items():
        category = categories.get(category_id)
        category = category if isinstance(category, dict) else {}
        raw_score = category.get("score")
        if (
            isinstance(raw_score, bool)
            or not isinstance(raw_score, (int, float))
            or not math.isfinite(raw_score)
            or not 0 <= raw_score <= 1
        ):
            score = None
        else:
            score = round(raw_score * 100)

        category_results.append({
            "id": category_id,
            "label": label,
            "score": score,
            "status": "available" if score is not None else "unavailable",
        })

        references = category.get("auditRefs")
        if not isinstance(references, list):
            continue
        for reference in references:
            if not isinstance(reference, dict):
                continue
            audit_id = reference.get("id")
            if not isinstance(audit_id, str):
                continue
            existing = audit_by_id.get(audit_id)
            if existing is not None:
                if label not in existing["category"].split(" · "):
                    existing["category"] = f'{existing["category"]} · {label}'
                if not any(entry["id"] == category_id for entry in existing["categoryWeights"]):
                    existing["categoryWeights"].append({
                        "id": category_id,
                        "label": label,
                        "weight": _valid_weight(reference.get("weight")),
                    })
                else:
                    for entry in existing["categoryWeights"]:
                        if entry["id"] == category_id:
                            entry["weight"] = max(
                                entry["weight"],
                                _valid_weight(reference.get("weight")),
                            )
                continue

            source = audits.get(audit_id)
            source = source if isinstance(source, dict) else None
            status = _audit_status(source)
            if status == "failed":
                title = source.get("title")
                description = source.get("description")
                result = {
                    "id": audit_id,
                    "title": title if isinstance(title, str) else audit_id,
                    "description": description if isinstance(description, str) else "",
                    "displayValue": source.get("displayValue") if isinstance(source.get("displayValue"), str) else None,
                    "score": source.get("score"),
                    "scoreDisplayMode": source.get("scoreDisplayMode"),
                    "status": status,
                    "category": label,
                    "categoryWeights": [{
                        "id": category_id,
                        "label": label,
                        "weight": _valid_weight(reference.get("weight")),
                    }],
                }
            else:
                result = {
                    "id": audit_id,
                    "status": status,
                    "category": label,
                    "categoryWeights": [{
                        "id": category_id,
                        "label": label,
                        "weight": _valid_weight(reference.get("weight")),
                    }],
                }
            audit_results.append(result)
            audit_by_id[audit_id] = result

    status_counts = {
        status: sum(1 for audit in audit_results if audit["status"] == status)
        for status in ("failed", "passed", "not_applicable", "unavailable")
    }
    findings = build_findings(audit_results)
    priorities = build_priorities(category_results, findings)

    requested_url = lighthouse.get("requestedUrl")
    final_url = lighthouse.get("finalUrl")
    return {
        "source": "pagespeed-insights",
        "site": final_url if isinstance(final_url, str) else submitted_url,
        "requestedUrl": requested_url if isinstance(requested_url, str) else submitted_url,
        "finalUrl": final_url if isinstance(final_url, str) else submitted_url,
        "fetchTime": lighthouse.get("fetchTime") if isinstance(lighthouse.get("fetchTime"), str) else None,
        "lighthouseVersion": lighthouse.get("lighthouseVersion") if isinstance(lighthouse.get("lighthouseVersion"), str) else None,
        "strategy": strategy,
        "scores": category_results,
        "audits": audit_results,
        "findings": findings,
        "priorities": priorities,
        "auditStatusCounts": status_counts,
    }


def _valid_weight(value: Any) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        return 0.0
    return float(value)


def run_pagespeed_audit(url: Any, strategy: Any = "mobile") -> dict[str, Any]:
    """Call PageSpeed securely using the server's environment configuration."""
    normalized_url = validate_public_url(url)
    if not isinstance(strategy, str) or strategy not in ALLOWED_STRATEGIES:
        raise AuditError("Choose either the mobile or desktop audit strategy.", 400)

    api_key = os.environ.get("PAGESPEED_API_KEY", "").strip()
    if not api_key or api_key == "replace-with-your-google-pagespeed-api-key":
        raise AuditError("PageSpeed API is not configured on this server.", 503)

    parameters = [
        ("url", normalized_url),
        ("strategy", strategy),
        *[("category", category) for category in CATEGORY_NAMES],
        ("key", api_key),
    ]
    request_url = f"{API_ENDPOINT}?{urlencode(parameters)}"
    api_request = Request(request_url, headers={"User-Agent": "RoastMyWebsite/1.0"})

    try:
        with urlopen(api_request, timeout=API_TIMEOUT_SECONDS) as response:
            raw_body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        error_payload = None
        if error.code in {403, 429} and error.fp is not None:
            try:
                error_payload = json.loads(error.read(MAX_RESPONSE_BYTES))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                error_payload = None
        if error.code == 429 or _is_rate_limit_error(error_payload):
            raise AuditError("Google PageSpeed is rate-limited right now. Please try again shortly.", 429) from error
        if error.code == 400:
            raise AuditError("Google PageSpeed could not audit this URL. Check that the public page is accessible.", 422) from error
        if error.code in {401, 403}:
            raise AuditError("Google rejected the PageSpeed request. Check the server API key and API settings.", 502) from error
        raise AuditError("Google PageSpeed is temporarily unavailable. Please try again later.", 502) from error
    except TimeoutError as error:
        raise AuditError("The PageSpeed request timed out. Please try again.", 504) from error
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise AuditError("The PageSpeed request timed out. Please try again.", 504) from error
        raise AuditError("Could not reach Google PageSpeed. Check the connection and try again.", 502) from error

    if len(raw_body) > MAX_RESPONSE_BYTES:
        raise AuditError("Google returned an unexpectedly large audit response.")
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise AuditError("Google returned an unreadable audit response.") from error

    return normalize_pagespeed_response(payload, normalized_url, strategy)
