"""Secret redaction. Regex pre-pass applied at ingest time; any text that
reaches the LLM or the case file has already been through here."""
from __future__ import annotations

import re

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_.~+/=]{16,}"), "Bearer [REDACTED_BEARER]"),
    (re.compile(r"sk_live_[A-Za-z0-9]{16,}"), "[REDACTED_STRIPE_KEY]"),
    (re.compile(r"sk_test_[A-Za-z0-9]{16,}"), "[REDACTED_STRIPE_TEST_KEY]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_ACCESS_KEY]"),
    (re.compile(r"eyJ[A-Za-z0-9\-_=]{10,}\.[A-Za-z0-9\-_=]{10,}\.[A-Za-z0-9\-_.+/=]{10,}"), "[REDACTED_JWT]"),
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "[REDACTED_SLACK_TOKEN]"),
]


def redact(text: str) -> str:
    """Apply all redaction patterns. Called once per log line at ingest."""
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text
