"""Format detection and streaming ingest.

Autodetect by extension:
  .jsonl / .ndjson   → one JSON object per line
  .log / other       → heuristic: try json, else treat as plaintext with
                       a best-effort timestamp parse (ISO 8601 prefix or
                       [bracketed] prefix; falls back to now + line order).
  .gz                → transparently decompress, then re-dispatch.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import duckdb

from rlm_logger.redact import redact
from rlm_logger.schemas import LogFileEntry, LogsManifest, TimeWindow

MAX_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB
MAX_ROWS = 50_000_000
BATCH = 5_000

ISO_TS = re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)")


class IngestCapExceeded(Exception):
    """Raised when ingest exceeds 2 GiB or 50M rows."""


def _open_text(path: Path) -> Iterator[str]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            yield from f
    else:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            yield from f


def _parse_ts(raw: str, fallback: datetime) -> datetime:
    m = ISO_TS.search(raw)
    if m:
        try:
            s = m.group(1).replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except ValueError:
            pass
    return fallback


def _parse_line(line: str, fallback_ts: datetime) -> tuple[datetime, str, str, str, str]:
    """Return (ts, service, level, msg, raw_json_string) for a single log line."""
    line = line.rstrip("\n")
    try:
        obj = json.loads(line)
        if isinstance(obj, dict):
            ts_raw = obj.get("ts") or obj.get("timestamp") or obj.get("time")
            ts = _parse_ts(str(ts_raw), fallback_ts) if ts_raw else fallback_ts
            service = str(obj.get("service") or obj.get("svc") or "unknown")
            level = str(obj.get("level") or obj.get("severity") or "info").lower()
            msg = str(obj.get("msg") or obj.get("message") or "")
            redacted = redact(json.dumps(obj))
            return ts, service, level, redact(msg), redacted
    except json.JSONDecodeError:
        pass
    ts = _parse_ts(line, fallback_ts)
    redacted = redact(line)
    return ts, "unknown", "info", redacted[:500], json.dumps({"text": redacted})


def ingest_paths(paths: list[Path], conn: duckdb.DuckDBPyConnection) -> LogsManifest:
    files: list[LogFileEntry] = []
    total_rows = 0
    total_bytes = 0
    min_ts: datetime | None = None
    max_ts: datetime | None = None

    for p in paths:
        if not p.exists():
            raise FileNotFoundError(p)
        size = p.stat().st_size
        total_bytes += size
        if total_bytes > MAX_BYTES:
            raise IngestCapExceeded(f"byte cap exceeded at {p}: {total_bytes} > {MAX_BYTES}")

        sha = hashlib.sha256()
        rows_in_file = 0
        batch: list[tuple[datetime, str, str, str, str, str, int]] = []
        fallback_ts = datetime.now(tz=timezone.utc)

        for line_no, raw_line in enumerate(_open_text(p), start=1):
            sha.update(raw_line.encode("utf-8", errors="replace"))
            if not raw_line.strip():
                continue
            ts, service, level, msg, raw_json = _parse_line(raw_line, fallback_ts)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if min_ts is None or ts < min_ts:
                min_ts = ts
            if max_ts is None or ts > max_ts:
                max_ts = ts
            batch.append((ts, service, level, msg, raw_json, str(p), line_no))
            rows_in_file += 1
            total_rows += 1
            if total_rows > MAX_ROWS:
                raise IngestCapExceeded(f"row cap exceeded: {total_rows} > {MAX_ROWS}")
            if len(batch) >= BATCH:
                conn.executemany(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)", batch
                )
                batch.clear()

        if batch:
            conn.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)", batch)

        files.append(LogFileEntry(path=str(p), bytes=size, rows=rows_in_file, sha256=sha.hexdigest()))

    assert min_ts is not None and max_ts is not None, "no rows ingested"
    return LogsManifest(
        files=files,
        time_window=TimeWindow(start=min_ts, end=max_ts),
        total_rows=total_rows,
    )
