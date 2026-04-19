"""search(pattern, limit=10) — substring match across redacted text."""
from __future__ import annotations

import duckdb


def search(conn: duckdb.DuckDBPyConnection, pattern: str, limit: int = 10) -> str:
    rows = conn.execute(
        """
        SELECT ts, service, level, msg, file, line
        FROM events
        WHERE msg ILIKE '%' || ? || '%' OR raw::VARCHAR ILIKE '%' || ? || '%'
        ORDER BY ts
        LIMIT ?
        """,
        [pattern, pattern, limit],
    ).fetchall()
    if not rows:
        return f"no matches for pattern: {pattern!r}"
    lines = [f"found {len(rows)} matches for {pattern!r} (capped at {limit}):"]
    for ts, service, level, msg, f, ln in rows:
        msg_short = (msg[:80] + "…") if len(msg) > 80 else msg
        lines.append(f"  [{ts.isoformat()}] {service:<18} {level:<5} {f}:{ln}  {msg_short}")
    return "\n".join(lines)
