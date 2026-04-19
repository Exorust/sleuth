"""End-to-end agent loop test using MockLM with a canned ideal trajectory."""
from pathlib import Path

import pytest

from sleuth.agent import Budget, run
from sleuth.ingest import ingest_paths
from sleuth.lm import MockLM
from sleuth.schemas import ModelInfo
from sleuth.store import open_store
from sleuth.ui.plain import PlainRenderer

FIXTURE = Path(__file__).parent.parent / "examples" / "checkout-incident"


IDEAL_TRAJECTORY = [
    "```python\nprint(schema())\n```",
    "```python\nprint(top_errors(limit=10))\n```",
    '```python\nprint(search("invalid_api_key_version", limit=5))\n```',
    '```python\nprint(around("2026-04-17T02:58:04Z", window_s=60))\n```',
    '```python\nprint(trace("tr_0003"))\n```',
    """```python
submit_incident_report({
    "root_cause": "checkout-worker kept signing with stripe_api_key v6 after vault rotated to v7; payment-gateway cut over instantly and rejected v6 as invalid_api_key_version",
    "blast_radius": "47 minutes, ~4120 sessions, ~612 failed orders, ~$58k",
    "evidence": [
        {"event_id": "vault-rotate-stripe-2026-04-17T02:58:04Z", "file": "logs/vault.log.jsonl", "line": 3, "ts": "2026-04-17T02:58:04Z", "service": "vault", "level": "info", "text_redacted": "secret rotated old_version=6 new_version=7", "why": "precipitating event", "is_key": True},
        {"event_id": "payment-gateway-reject-v6-2026-04-17T02:58:41Z", "file": "logs/payment-gateway.log.jsonl", "line": 5, "ts": "2026-04-17T02:58:41Z", "service": "payment-gateway", "level": "warn", "text_redacted": "auth rejected invalid_api_key_version presented=6 expected=7", "why": "first rejection of stale key", "is_key": True},
        {"event_id": "checkout-worker-first-401-2026-04-17T02:58:41Z", "file": "logs/checkout-worker.log.jsonl", "line": 5, "ts": "2026-04-17T02:58:41Z", "service": "checkout-worker", "level": "error", "text_redacted": "payment-gateway returned 401", "why": "caller side of 401", "is_key": True},
        {"event_id": "api-gateway-5xx-spike-2026-04-17T03:02:12Z", "file": "logs/api-gateway.log.jsonl", "line": 7, "ts": "2026-04-17T03:02:12Z", "service": "api-gateway", "level": "error", "text_redacted": "5xx rate 91.4%", "why": "user-visible, paged oncall", "is_key": True}
    ],
    "remediation": "rolling restart checkout-worker; add SIGHUP + vault rotation webhook subscription",
    "confidence": 0.92,
    "confidence_rationale": "causal chain fully covered by logs; only unknown is in-memory secret state",
    "unknowns": ["exact unique customer session count"]
})
```"""
]


@pytest.fixture
def conn_and_manifest():
    c = open_store(":memory:")
    m = ingest_paths(sorted((FIXTURE / "logs").glob("*.jsonl")), c)
    return c, m


def test_agent_solves_checkout_fixture_with_mock_lm(conn_and_manifest):
    conn, manifest = conn_and_manifest
    lm = MockLM(IDEAL_TRAJECTORY)
    import io
    renderer = PlainRenderer(stream=io.StringIO())

    case = run(
        question="why did checkout fail around 3am?",
        conn=conn,
        manifest=manifest,
        model=ModelInfo(provider="mock", name="ideal", temperature=0.0),
        lm=lm,
        observer=renderer,
    )

    assert case.termination_reason == "submitted"
    assert case.report is not None
    assert "stripe_api_key" in case.report.root_cause.lower() or "v6" in case.report.root_cause
    assert len(case.trajectory) == 6
    assert case.trajectory[0].tool == "schema"
    assert case.trajectory[-1].tool == "submit_incident_report"
    assert case.report.confidence >= 0.5
    assert sum(1 for e in case.report.evidence if e.is_key) >= 3


def test_agent_respects_max_iterations(conn_and_manifest):
    conn, manifest = conn_and_manifest
    # Give the LM an infinite loop of no-ops; budget should terminate.
    lm = MockLM(["```python\nprint('noop')\n```"] * 50)
    import io
    case = run(
        question="q",
        conn=conn,
        manifest=manifest,
        model=ModelInfo(provider="mock", name="noop"),
        lm=lm,
        observer=PlainRenderer(stream=io.StringIO()),
        budget=Budget(max_iterations=3, max_llm_calls=100, max_wall_clock_s=60),
    )
    assert case.termination_reason == "max_iterations"
    assert case.report is None
    assert len(case.trajectory) == 3


def test_agent_returns_partial_case_on_bad_report_schema(conn_and_manifest):
    """Regression: if the LLM submits a malformed report, we must NOT crash —
    we capture the error on the step and keep going (or terminate gracefully)."""
    conn, manifest = conn_and_manifest
    lm = MockLM([
        "```python\nprint(schema())\n```",
        '```python\nsubmit_incident_report({"root_cause": "oops"})\n```',  # missing required fields
        "```python\nprint('recovering')\n```",
    ])
    import io
    case = run(
        question="q",
        conn=conn,
        manifest=manifest,
        model=ModelInfo(provider="mock", name="bad"),
        lm=lm,
        observer=PlainRenderer(stream=io.StringIO()),
        budget=Budget(max_iterations=5),
    )
    # Either max_iterations or error; the key contract is: no crash, case file returned.
    assert case.termination_reason in ("max_iterations", "error", "submitted")
    assert case.question == "q"
    assert len(case.trajectory) >= 1
