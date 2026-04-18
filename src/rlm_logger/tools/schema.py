"""schema() — describe the event store: distinct services, levels, time range."""
from __future__ import annotations

import duckdb


def schema(conn: duckdb.DuckDBPyConnection) -> str:
    """Return a one-paragraph description of what's in the event store."""
    # TODO: SELECT DISTINCT service, SELECT DISTINCT level, MIN/MAX(ts), COUNT(*).
    raise NotImplementedError
