"""Read/write case files. One run = one signed JSON artifact."""
from __future__ import annotations

from pathlib import Path

import orjson

from rlm_logger.schemas import CaseFile


def dump(case: CaseFile, path: Path) -> None:
    path.write_bytes(orjson.dumps(case.model_dump(mode="json"), option=orjson.OPT_INDENT_2))


def load(path: Path) -> CaseFile:
    return CaseFile.model_validate_json(path.read_bytes())
