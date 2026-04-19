"""trace(trace_id) — pull all events sharing a correlation ID (trace_id or request_id)."""
from __future__ import annotations

import duckdb


def trace(conn: duckdb.DuckDBPyConnection, trace_id: str) -> str:
    rows = conn.execute(
        """
        SELECT ts, service, level, msg, file, line
        FROM events
        WHERE json_extract_string(raw, '$.trace_id') = ?
           OR json_extract_string(raw, '$.request_id') = ?
        ORDER BY ts
        """,
        [trace_id, trace_id],
    ).fetchall()
    if not rows:
        return f"no events with trace_id or request_id = {trace_id!r}"
    lines = [f"{len(rows)} events for {trace_id!r}:"]
    for t, svc, lvl, msg, f, ln in rows:
        msg_short = (msg[:100] + "…") if len(msg) > 100 else msg
        lines.append(f"  [{t.isoformat()}] {svc:<18} {lvl:<5} {f}:{ln}  {msg_short}")
    return "\n".join(lines)
