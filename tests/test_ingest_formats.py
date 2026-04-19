"""Enterprise export format detection: Splunk, Datadog, New Relic, Honeycomb."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rlm_logger.ingest import ingest_paths
from rlm_logger.store import open_store


def _write(tmp_path: Path, name: str, lines: list[str]) -> Path:
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n")
    return p


def _write_json(tmp_path: Path, name: str, obj) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(obj))
    return p


def test_splunk_wrapped_result(tmp_path: Path):
    """Splunk ``Export → JSON`` with ``{"preview":..., "result":{...}}`` envelope."""
    lines = [
        json.dumps({
            "preview": False,
            "offset": 0,
            "result": {
                "_time": "2026-04-17T02:58:04.000+00:00",
                "_raw": "payment-gateway returned 401 invalid_api_key_version",
                "host": "prod-checkout-7",
                "source": "/var/log/checkout.log",
                "sourcetype": "checkout-worker",
                "level": "error",
            },
        }),
    ]
    path = _write(tmp_path, "splunk.jsonl", lines)
    conn = open_store(":memory:")
    manifest = ingest_paths([path], conn)
    assert manifest.total_rows == 1
    row = conn.execute("SELECT service, level, msg FROM events").fetchone()
    assert row[0] == "checkout-worker"
    assert row[1] == "error"
    assert "invalid_api_key_version" in row[2]


def test_splunk_flat_result(tmp_path: Path):
    """Splunk export variant where each line IS the result dict (no preview wrapper)."""
    lines = [
        json.dumps({
            "_time": "2026-04-17T02:58:04Z",
            "_raw": "secret rotated old_version=6 new_version=7",
            "sourcetype": "vault",
            "severity": "info",
        }),
    ]
    path = _write(tmp_path, "splunk-flat.jsonl", lines)
    conn = open_store(":memory:")
    ingest_paths([path], conn)
    row = conn.execute("SELECT service, level, msg FROM events").fetchone()
    assert row[0] == "vault"
    assert row[1] == "info"
    assert "new_version=7" in row[2]


def test_datadog_attributes_shape(tmp_path: Path):
    """Datadog NDJSON download: ``{"id":..., "attributes": {"timestamp":..., "service":..., ...}}``."""
    lines = [
        json.dumps({
            "id": "AQAAAXqPdJ-abc",
            "type": "log",
            "attributes": {
                "timestamp": "2026-04-17T02:58:04.123Z",
                "host": "prod-checkout-7",
                "service": "checkout-worker",
                "status": "error",
                "message": "payment-gateway returned 401",
                "tags": ["env:prod"],
                "attributes": {"trace_id": "tr_0003"},
            },
        }),
    ]
    path = _write(tmp_path, "dd.jsonl", lines)
    conn = open_store(":memory:")
    ingest_paths([path], conn)
    row = conn.execute("SELECT service, level, msg FROM events").fetchone()
    assert row[0] == "checkout-worker"
    assert row[1] == "error"
    assert "401" in row[2]


def test_datadog_content_legacy(tmp_path: Path):
    """Legacy Datadog ``content`` envelope."""
    lines = [
        json.dumps({
            "id": "x",
            "content": {
                "timestamp": "2026-04-17T02:58:04Z",
                "service": "api-gateway",
                "status": "warn",
                "message": "upstream slow",
            },
        }),
    ]
    path = _write(tmp_path, "dd-legacy.jsonl", lines)
    conn = open_store(":memory:")
    ingest_paths([path], conn)
    row = conn.execute("SELECT service, level FROM events").fetchone()
    assert row == ("api-gateway", "warn")


def test_newrelic_epoch_ms(tmp_path: Path):
    """New Relic NRQL export: ``timestamp`` as epoch ms + dotted keys."""
    ts_ms = 1713322684000  # 2024-04-17T02:58:04Z
    lines = [
        json.dumps({
            "timestamp": ts_ms,
            "service.name": "checkout",
            "log.level": "ERROR",
            "message": "401 from payment-gateway",
            "trace.id": "abc123",
        }),
    ]
    path = _write(tmp_path, "nr.jsonl", lines)
    conn = open_store(":memory:")
    ingest_paths([path], conn)
    row = conn.execute("SELECT service, level, msg FROM events").fetchone()
    assert row[0] == "checkout"
    assert row[1] == "error"
    assert "401" in row[2]


def test_honeycomb_events_shape(tmp_path: Path):
    """Honeycomb events API: ``{"time":..., "samplerate":..., "data":{...}}``."""
    lines = [
        json.dumps({
            "time": "2026-04-17T02:58:04Z",
            "samplerate": 1,
            "data": {
                "service.name": "payment-gateway",
                "level": "error",
                "error.message": "invalid_api_key_version",
                "trace.trace_id": "tr_0003",
            },
        }),
    ]
    path = _write(tmp_path, "hc.jsonl", lines)
    conn = open_store(":memory:")
    ingest_paths([path], conn)
    row = conn.execute("SELECT service, level, msg FROM events").fetchone()
    assert row[0] == "payment-gateway"
    assert row[1] == "error"
    assert "invalid_api_key_version" in row[2]


def test_json_array_unwrap(tmp_path: Path):
    """Files wrapped in ``[...]`` should flatten into a stream of events."""
    events = [
        {"ts": "2026-04-17T02:58:04Z", "service": "a", "level": "info", "msg": "one"},
        {"ts": "2026-04-17T02:58:05Z", "service": "b", "level": "warn", "msg": "two"},
    ]
    path = _write_json(tmp_path, "array.json", events)
    conn = open_store(":memory:")
    manifest = ingest_paths([path], conn)
    assert manifest.total_rows == 2


def test_datadog_data_wrapper_unwrap(tmp_path: Path):
    """Datadog REST response shape: ``{"data":[{"attributes":...}], "meta":...}``."""
    doc = {
        "data": [
            {
                "id": "a",
                "attributes": {
                    "timestamp": "2026-04-17T02:58:04Z",
                    "service": "checkout",
                    "status": "error",
                    "message": "boom",
                },
            },
            {
                "id": "b",
                "attributes": {
                    "timestamp": "2026-04-17T02:58:05Z",
                    "service": "checkout",
                    "status": "warn",
                    "message": "retry",
                },
            },
        ],
        "meta": {"page": {"after": "tok"}},
    }
    path = _write_json(tmp_path, "dd-api.json", doc)
    conn = open_store(":memory:")
    manifest = ingest_paths([path], conn)
    assert manifest.total_rows == 2
    rows = conn.execute("SELECT service, level FROM events ORDER BY ts").fetchall()
    assert rows[0] == ("checkout", "error")
    assert rows[1] == ("checkout", "warn")


def test_nrql_nested_results_events_unwrap(tmp_path: Path):
    """NRQL results wrapper: ``{"results":[{"events":[...]}]}``."""
    doc = {
        "results": [
            {
                "events": [
                    {"timestamp": 1713322684000, "service.name": "a", "log.level": "info", "message": "hi"},
                    {"timestamp": 1713322685000, "service.name": "b", "log.level": "warn", "message": "bye"},
                ]
            }
        ]
    }
    path = _write_json(tmp_path, "nrql.json", doc)
    conn = open_store(":memory:")
    manifest = ingest_paths([path], conn)
    assert manifest.total_rows == 2


def test_generic_json_still_works(tmp_path: Path):
    """Plain ``{"ts":..., "service":..., ...}`` should still parse through the fall-through path."""
    lines = [
        json.dumps({"ts": "2026-04-17T02:58:04Z", "service": "foo", "level": "info", "msg": "ok"}),
    ]
    path = _write(tmp_path, "generic.jsonl", lines)
    conn = open_store(":memory:")
    ingest_paths([path], conn)
    row = conn.execute("SELECT service, level, msg FROM events").fetchone()
    assert row == ("foo", "info", "ok")


@pytest.mark.parametrize("shape", ["splunk", "datadog", "newrelic", "honeycomb"])
def test_redaction_runs_on_all_formats(tmp_path: Path, shape: str):
    """Secret redactor must run regardless of which format adapter handled the line."""
    bearer = "Bearer ey4hG9vKpL2mNqR8sT3uVwX7yZaBcDeF"
    shapes = {
        "splunk": {"_time": "2026-04-17T02:58:04Z", "_raw": f"auth={bearer}", "sourcetype": "gw"},
        "datadog": {
            "id": "x",
            "attributes": {"timestamp": "2026-04-17T02:58:04Z", "service": "gw", "status": "info", "message": f"h {bearer}"},
        },
        "newrelic": {"timestamp": 1713322684000, "service.name": "gw", "log.level": "info", "message": f"h {bearer}"},
        "honeycomb": {
            "time": "2026-04-17T02:58:04Z",
            "samplerate": 1,
            "data": {"service.name": "gw", "level": "info", "message": f"h {bearer}"},
        },
    }
    path = _write(tmp_path, f"{shape}.jsonl", [json.dumps(shapes[shape])])
    conn = open_store(":memory:")
    ingest_paths([path], conn)
    row = conn.execute("SELECT msg, raw FROM events").fetchone()
    assert "ey4hG9vKpL2mNqR8" not in row[0]
    assert "ey4hG9vKpL2mNqR8" not in row[1]
    assert "[REDACTED_BEARER]" in row[0] or "[REDACTED_BEARER]" in row[1]
