"""top_errors(limit=20) — most frequent error/warn messages, with counts."""
from __future__ import annotations

import duckdb


def top_errors(conn: duckdb.DuckDBPyConnection, limit: int = 20) -> str:
    rows = conn.execute(
        """
        SELECT service, level, msg, COUNT(*) AS n
        FROM events
        WHERE level IN ('error', 'warn')
        GROUP BY service, level, msg
        ORDER BY n DESC, service
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    if not rows:
        return "no error/warn events found"
    lines = [f"{'count':>6}  {'level':<5}  {'service':<20}  msg"]
    lines.append("-" * 80)
    for service, level, msg, n in rows:
        msg_short = (msg[:60] + "…") if len(msg) > 60 else msg
        lines.append(f"{n:>6}  {level:<5}  {service:<20}  {msg_short}")
    return "\n".join(lines)
