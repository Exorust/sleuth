"""top_errors(limit=20) — most frequent error/warn messages, with counts."""
from __future__ import annotations

import duckdb


def top_errors(conn: duckdb.DuckDBPyConnection, limit: int = 20) -> str:
    """Group by normalized msg where level in ('error','warn'), order by count desc."""
    # TODO: GROUP BY msg + service, count desc, limit N. Render as text table.
    raise NotImplementedError
