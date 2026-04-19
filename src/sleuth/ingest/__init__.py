"""Log ingestion: file → redact → DuckDB.

Supported formats: .log, .jsonl, .ndjson, .gz (autodetect by extension).
Caps: 2 GiB total, 50M rows. Breaches raise IngestCapExceeded.
"""
from sleuth.ingest.formats import IngestCapExceeded, ingest_paths

__all__ = ["ingest_paths", "IngestCapExceeded"]
