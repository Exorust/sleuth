"""around(ts|service, window_s=60) — events within ±window_s of a timestamp."""
from __future__ import annotations

from datetime import datetime

import duckdb


def around(
    conn: duckdb.DuckDBPyConnection,
    ts: datetime | str,
    window_s: int = 60,
    service: str | None = None,
) -> str:
    """WHERE ts BETWEEN ts - window_s AND ts + window_s, optionally filtered by service."""
    # TODO: order by ts asc; include line/file so the agent can cite.
    raise NotImplementedError
