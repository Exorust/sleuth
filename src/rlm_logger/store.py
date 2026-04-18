"""DuckDB event store. One table: events(ts, service, level, msg, raw, file, line)."""
from __future__ import annotations

from pathlib import Path

import duckdb

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    ts         TIMESTAMP NOT NULL,
    service    VARCHAR NOT NULL,
    level      VARCHAR NOT NULL,
    msg        VARCHAR NOT NULL,
    raw        JSON,
    file       VARCHAR NOT NULL,
    line       INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_service ON events(service);
CREATE INDEX IF NOT EXISTS idx_events_level ON events(level);
"""


def open_store(path: Path | str = ":memory:") -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(path))
    conn.execute(SCHEMA)
    return conn
