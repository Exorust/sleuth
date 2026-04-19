"""Format detection and streaming ingest.

Autodetect by extension:
  .jsonl / .ndjson   → one JSON object per line
  .log / other       → heuristic: try json, else treat as plaintext with
                       a best-effort timestamp parse (ISO 8601 prefix or
                       [bracketed] prefix; falls back to now + line order).
  .gz                → transparently decompress, then re-dispatch.

Enterprise export formats detected per-line (no extension hint needed):
  Splunk       — ``{"result": {...}}`` or flat with ``_time``/``_raw``
  Datadog      — ``{"attributes": {"timestamp": ..., ...}}`` or legacy ``content``
  New Relic    — flat object with numeric epoch-ms ``timestamp`` + dotted keys
  Honeycomb    — ``{"time": ..., "data": {"service.name": ..., ...}}``

Wrapped JSON-doc files (``[...]``, ``{"data":[...]}``, ``{"results":[{"events":[...]}]}``)
are flattened into a per-event stream before line parsing.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

import duckdb

from rlm_logger.redact import redact
from rlm_logger.schemas import LogFileEntry, LogsManifest, TimeWindow

MAX_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB
MAX_ROWS = 50_000_000
BATCH = 5_000

ISO_TS = re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)")

ParsedLine = tuple[datetime, str, str, str, str]


class IngestCapExceeded(Exception):
    """Raised when ingest exceeds 2 GiB or 50M rows."""


def _open_text(path: Path) -> Iterator[str]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            yield from f
    else:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            yield from f


def _peek(path: Path, n: int = 4096) -> str:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            return f.read(n)
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.read(n)


def _read_all(path: Path) -> str:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            return f.read()
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _parse_ts(raw: str, fallback: datetime) -> datetime:
    m = ISO_TS.search(raw)
    if m:
        try:
            s = m.group(1).replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except ValueError:
            pass
    return fallback


def _parse_splunk(obj: dict, fallback: datetime) -> ParsedLine | None:
    """Splunk ``Export → JSON``: ``{"preview":..., "result":{...}}`` or flat with ``_time``/``_raw``."""
    r = obj.get("result") if isinstance(obj.get("result"), dict) else obj
    if "_time" not in r and "_raw" not in r:
        return None
    ts_raw = r.get("_time")
    ts = _parse_ts(str(ts_raw), fallback) if ts_raw else fallback
    service = str(r.get("sourcetype") or r.get("source") or r.get("host") or "splunk")
    level = str(r.get("level") or r.get("severity") or r.get("log_level") or "info").lower()
    msg = str(r.get("_raw") or r.get("message") or "")
    return ts, service, level, redact(msg)[:500], redact(json.dumps(r))


def _parse_datadog(obj: dict, fallback: datetime) -> ParsedLine | None:
    """Datadog logs: ``{"id":..., "attributes": {"timestamp":..., "service":..., ...}}`` or legacy ``content``."""
    attrs = obj.get("attributes") or obj.get("content")
    if not isinstance(attrs, dict) or "timestamp" not in attrs:
        return None
    ts_raw = attrs.get("timestamp")
    ts = _parse_ts(str(ts_raw), fallback) if ts_raw else fallback
    service = str(attrs.get("service") or "datadog")
    level = str(attrs.get("status") or attrs.get("level") or "info").lower()
    nested = attrs.get("attributes") if isinstance(attrs.get("attributes"), dict) else {}
    msg = str(attrs.get("message") or nested.get("message") or "")
    return ts, service, level, redact(msg)[:500], redact(json.dumps(attrs))


def _parse_newrelic(obj: dict, fallback: datetime) -> ParsedLine | None:
    """New Relic NRQL/logs: flat object with numeric epoch-ms ``timestamp`` and dotted field names."""
    ts_raw = obj.get("timestamp")
    if not isinstance(ts_raw, (int, float)):
        return None
    has_dotted = any(
        isinstance(k, str) and ("." in k and k.split(".", 1)[0] in ("service", "log", "trace", "entity", "host"))
        for k in obj
    )
    if not has_dotted:
        return None
    try:
        ts = datetime.fromtimestamp(ts_raw / 1000.0, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        ts = fallback
    service = str(obj.get("service.name") or obj.get("entity.name") or "newrelic")
    level = str(obj.get("log.level") or obj.get("level") or "info").lower()
    msg = str(obj.get("message") or "")
    return ts, service, level, redact(msg)[:500], redact(json.dumps(obj))


def _parse_honeycomb(obj: dict, fallback: datetime) -> ParsedLine | None:
    """Honeycomb events: ``{"time":..., "samplerate":N, "data": {"service.name":..., ...}}``."""
    if "time" not in obj or not isinstance(obj.get("data"), dict):
        return None
    d = obj["data"]
    dotted = any(
        isinstance(k, str) and k.split(".", 1)[0] in ("service", "trace", "app", "request", "error")
        for k in d
    )
    if "samplerate" not in obj and not dotted:
        return None
    ts_raw = obj.get("time")
    ts = _parse_ts(str(ts_raw), fallback) if ts_raw else fallback
    service = str(d.get("service.name") or d.get("service") or "honeycomb")
    level = str(d.get("level") or d.get("log.level") or "info").lower()
    msg = str(d.get("message") or d.get("error.message") or d.get("name") or "")
    return ts, service, level, redact(msg)[:500], redact(json.dumps(d))


_DETECTORS: tuple[Callable[[dict, datetime], ParsedLine | None], ...] = (
    _parse_splunk,
    _parse_datadog,
    _parse_newrelic,
    _parse_honeycomb,
)


def _parse_line(line: str, fallback_ts: datetime) -> ParsedLine:
    """Return (ts, service, level, msg, raw_json_string) for a single log line."""
    line = line.rstrip("\n")
    try:
        obj = json.loads(line)
        if isinstance(obj, dict):
            for detector in _DETECTORS:
                result = detector(obj, fallback_ts)
                if result is not None:
                    return result
            ts_raw = obj.get("ts") or obj.get("timestamp") or obj.get("time")
            ts = _parse_ts(str(ts_raw), fallback_ts) if ts_raw else fallback_ts
            service = str(obj.get("service") or obj.get("svc") or "unknown")
            level = str(obj.get("level") or obj.get("severity") or "info").lower()
            msg = str(obj.get("msg") or obj.get("message") or "")
            return ts, service, level, redact(msg), redact(json.dumps(obj))
    except json.JSONDecodeError:
        pass
    ts = _parse_ts(line, fallback_ts)
    redacted = redact(line)
    return ts, "unknown", "info", redacted[:500], json.dumps({"text": redacted})


def _unwrap_events(doc: Any) -> list | None:
    """Flatten common platform wrapper shapes into a flat event list. Return None if no wrapper recognized."""
    if isinstance(doc, list):
        return doc
    if not isinstance(doc, dict):
        return None
    # Datadog v2 REST: {"data":[{"id":..., "attributes":...}], "meta":...}
    if isinstance(doc.get("data"), list):
        return doc["data"]
    # New Relic NRQL: {"results":[{"events":[...]}]}
    results = doc.get("results")
    if isinstance(results, list) and results:
        r0 = results[0]
        if isinstance(r0, dict) and isinstance(r0.get("events"), list):
            return r0["events"]
        if isinstance(r0, dict):
            return results
    # Honeycomb query: {"events":[...]}
    if isinstance(doc.get("events"), list):
        return doc["events"]
    return None


def _iter_events(path: Path) -> Iterator[str]:
    """Yield one JSON-serialized event per iteration.

    For NDJSON files (the common case), yields lines as-is.
    For single-document JSON files wrapped in ``[...]``, ``{"data":[...]}``, or
    ``{"results":[{"events":[...]}]}``, flattens and re-serializes each event.
    """
    peek = _peek(path).lstrip()
    if peek.startswith("[") or peek.startswith("{"):
        # Might be a whole-file JSON doc. Try to parse it.
        full = _read_all(path)
        try:
            doc = json.loads(full)
        except json.JSONDecodeError:
            yield from _open_text(path)
            return
        events = _unwrap_events(doc)
        if events is not None and not (isinstance(doc, dict) and _looks_like_single_event(doc)):
            for item in events:
                yield json.dumps(item) if not isinstance(item, str) else item
            return
    yield from _open_text(path)


def _looks_like_single_event(doc: dict) -> bool:
    """Guard so a single-event NDJSON line (e.g. a Splunk result dict) isn't mis-unwrapped."""
    event_markers = ("_time", "_raw", "ts", "timestamp", "time", "msg", "message")
    return any(k in doc for k in event_markers) and not any(
        isinstance(doc.get(k), list) for k in ("data", "events", "results")
    )


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

        for line_no, raw_line in enumerate(_iter_events(p), start=1):
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
