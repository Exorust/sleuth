"""Redaction regression tests. Any new pattern in redact.py gets a case here.

Secret-shaped strings are assembled at runtime so this file is safe for
repo-level secret scanning. None of these are real credentials.
"""
from sleuth.redact import redact

# Assemble secret-shaped tokens from parts so the raw file never contains
# a full match for common scanners (GitHub push protection, TruffleHog, etc.).
FAKE_STRIPE = "sk_" + "live_" + "A" * 24
FAKE_STRIPE_TEST = "sk_" + "test_" + "B" * 24
FAKE_AWS = "AKIA" + "IOSFODNN7EXAMPLE"[:16]
FAKE_JWT = (
    "eyJ" + "hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    + "." + "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ"
    + "." + "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)
FAKE_BEARER_OPAQUE = "ey4hG9vKpL2mNqR8sT3uVwX7yZaBcDeF"


def test_bearer_token_redacted():
    out = redact(f'auth_header: "Bearer {FAKE_BEARER_OPAQUE}"')
    assert FAKE_BEARER_OPAQUE not in out
    assert "[REDACTED_BEARER]" in out


def test_stripe_live_key_redacted():
    out = redact(f"key={FAKE_STRIPE}")
    assert FAKE_STRIPE not in out
    assert "[REDACTED_STRIPE_KEY]" in out


def test_stripe_test_key_redacted():
    out = redact(f"key={FAKE_STRIPE_TEST}")
    assert FAKE_STRIPE_TEST not in out


def test_aws_access_key_redacted():
    out = redact(f"AWS_ACCESS_KEY_ID={FAKE_AWS}")
    assert FAKE_AWS not in out


def test_jwt_redacted():
    out = redact(f"token={FAKE_JWT}")
    assert FAKE_JWT not in out


def test_benign_text_unchanged():
    s = "user submitted order ord_88121 for $42.00"
    assert redact(s) == s
