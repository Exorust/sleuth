"""trace(trace_id | request_id) — pull all events sharing a correlation ID."""
from __future__ import annotations

import duckdb


def trace(conn: duckdb.DuckDBPyConnection, trace_id: str) -> str:
    """Match trace_id or request_id in the raw JSON, order by ts."""
    # TODO: json_extract(raw, '$.trace_id') = trace_id OR json_extract(raw, '$.request_id') = trace_id.
    raise NotImplementedError
