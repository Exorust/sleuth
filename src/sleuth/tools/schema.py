"""schema() — describe the event store: distinct services, levels, time range."""
from __future__ import annotations

import duckdb


def schema(conn: duckdb.DuckDBPyConnection) -> str:
    services = [r[0] for r in conn.execute("SELECT DISTINCT service FROM events ORDER BY service").fetchall()]
    levels = [r[0] for r in conn.execute("SELECT DISTINCT level FROM events ORDER BY level").fetchall()]
    row = conn.execute("SELECT MIN(ts), MAX(ts), COUNT(*) FROM events").fetchone()
    ts_min, ts_max, n = row
    return (
        f"events table: {n} rows\n"
        f"services: {', '.join(services)}\n"
        f"levels: {', '.join(levels)}\n"
        f"time window: {ts_min.isoformat()} → {ts_max.isoformat()}\n"
        f"columns: ts, service, level, msg, raw (json), file, line"
    )
