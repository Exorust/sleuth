"""search(pattern, limit=10) — substring or regex match across redacted text."""
from __future__ import annotations

import duckdb


def search(conn: duckdb.DuckDBPyConnection, pattern: str, limit: int = 10) -> str:
    """WHERE msg ~ pattern OR raw::VARCHAR ~ pattern. Return redacted excerpts."""
    # TODO: use regexp_matches; sort by ts; cap result size to avoid blowing the LLM context.
    raise NotImplementedError
