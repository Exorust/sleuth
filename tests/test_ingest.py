"""Ingest correctness against the checkout-401 fixture."""
from pathlib import Path

from rlm_logger.ingest import ingest_paths
from rlm_logger.store import open_store

FIXTURE = Path(__file__).parent.parent / "examples" / "checkout-incident"


def test_ingest_checkout_fixture():
    conn = open_store(":memory:")
    logs = sorted((FIXTURE / "logs").glob("*.jsonl"))
    manifest = ingest_paths(logs, conn)
    assert manifest.total_rows == 72
    assert len(manifest.files) == 5
    row_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert row_count == 72


def test_ingest_redacts_bearer_tokens():
    conn = open_store(":memory:")
    logs = sorted((FIXTURE / "logs").glob("*.jsonl"))
    ingest_paths(logs, conn)
    # No raw opaque bearer should survive into the store.
    bad = conn.execute(
        "SELECT COUNT(*) FROM events WHERE raw::VARCHAR LIKE '%ey4hG9vKpL2mNqR8%'"
    ).fetchone()[0]
    assert bad == 0
    redacted = conn.execute(
        "SELECT COUNT(*) FROM events WHERE raw::VARCHAR LIKE '%[REDACTED_BEARER]%'"
    ).fetchone()[0]
    assert redacted >= 2  # payment-gateway + checkout-worker lines


def test_ingest_time_window():
    conn = open_store(":memory:")
    logs = sorted((FIXTURE / "logs").glob("*.jsonl"))
    manifest = ingest_paths(logs, conn)
    assert manifest.time_window.start.isoformat().startswith("2026-04-17T02:55:00")
    assert manifest.time_window.end.isoformat().startswith("2026-04-17T04:10:00")
