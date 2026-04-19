"""Tool smoke tests against the ingested checkout-401 fixture."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sleuth.ingest import ingest_paths
from sleuth.store import open_store
from sleuth.tools import around, schema, search, top_errors, trace

FIXTURE = Path(__file__).parent.parent / "examples" / "checkout-incident"


@pytest.fixture(scope="module")
def conn():
    c = open_store(":memory:")
    ingest_paths(sorted((FIXTURE / "logs").glob("*.jsonl")), c)
    return c


def test_schema_lists_all_five_services(conn):
    out = schema(conn)
    for s in ["vault", "payment-gateway", "checkout-worker", "api-gateway", "redis"]:
        assert s in out
    assert "72 rows" in out


def test_top_errors_surfaces_401s(conn):
    out = top_errors(conn, limit=5)
    assert "payment-gateway returned 401" in out or "auth rejected" in out


def test_search_finds_the_rotation(conn):
    out = search(conn, "invalid_api_key_version", limit=5)
    assert "payment-gateway" in out
    assert "checkout-worker" in out


def test_around_vault_rotation(conn):
    ts = datetime(2026, 4, 17, 2, 58, 4, tzinfo=timezone.utc)
    out = around(conn, ts, window_s=30)
    assert "vault" in out
    assert "secret rotated" in out or "rotated" in out


def test_trace_ties_services_by_trace_id(conn):
    out = trace(conn, "tr_0003")
    assert "checkout-worker" in out
    assert "api-gateway" in out or "payment-gateway" in out
