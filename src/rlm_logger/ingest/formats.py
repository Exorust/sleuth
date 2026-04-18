"""Format detection and streaming ingest."""
from __future__ import annotations

from pathlib import Path

import duckdb

from rlm_logger.schemas import LogsManifest

MAX_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB
MAX_ROWS = 50_000_000


class IngestCapExceeded(Exception):
    """Raised when ingest exceeds 2 GiB or 50M rows."""


def ingest_paths(paths: list[Path], conn: duckdb.DuckDBPyConnection) -> LogsManifest:
    """Stream-ingest a list of log files into the DuckDB `events` table.
    Returns a manifest with per-file byte/row/sha256 + overall time window.
    """
    # TODO: implement. Flow:
    # 1. For each path, autodetect format (.jsonl/.ndjson = line-per-json,
    #    .log = heuristic parse, .gz = gzip wrapper).
    # 2. Stream lines, redact via rlm_logger.redact.redact(), extract
    #    ts/service/level/msg, insert to DuckDB in batches of 10_000.
    # 3. Track sha256 per file, running byte/row totals.
    # 4. Raise IngestCapExceeded if caps breached.
    # 5. Return LogsManifest(files, time_window=min/max(ts), total_rows).
    raise NotImplementedError("ingest_paths: stub — see eval/test_checkout_fixture.py for expected behavior")
