"""around(ts, window_s=60, service=None) — events within ±window_s of a timestamp."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import duckdb


def around(
    conn: duckdb.DuckDBPyConnection,
    ts: datetime | str,
    window_s: int = 60,
    service: str | None = None,
) -> str:
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    lo = ts - timedelta(seconds=window_s)
    hi = ts + timedelta(seconds=window_s)
    sql = """
        SELECT ts, service, level, msg, file, line
        FROM events
        WHERE ts BETWEEN ? AND ?
    """
    params: list = [lo, hi]
    if service:
        sql += " AND service = ?"
        params.append(service)
    sql += " ORDER BY ts"
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        return f"no events within ±{window_s}s of {ts.isoformat()}"
    svc_note = f" in service={service}" if service else ""
    lines = [f"{len(rows)} events around {ts.isoformat()} (±{window_s}s){svc_note}:"]
    for t, svc, lvl, msg, f, ln in rows:
        msg_short = (msg[:80] + "…") if len(msg) > 80 else msg
        lines.append(f"  [{t.isoformat()}] {svc:<18} {lvl:<5} {f}:{ln}  {msg_short}")
    return "\n".join(lines)
