"""Schema round-trip tests. If these break, the case-file protocol broke."""
import json
from pathlib import Path

from rlm_logger.schemas import CaseFile, GroundTruth

FIXTURE = Path(__file__).parent.parent / "examples" / "checkout-incident"


def test_checkout_fixture_case_file_roundtrips():
    raw = json.loads((FIXTURE / "incident.rlm.json").read_text())
    case = CaseFile.model_validate(raw)
    assert case.question.startswith("why did checkout")
    assert case.termination_reason == "submitted"
    assert case.report is not None
    assert len(case.report.evidence) == 5
    assert sum(1 for e in case.report.evidence if e.is_key) == 4


def test_checkout_fixture_ground_truth_parses():
    raw = json.loads((FIXTURE / "ground_truth.json").read_text())
    gt = GroundTruth.model_validate(raw)
    assert gt.incident_id == "checkout-401-2026-04-17"
    assert len(gt.evidence_event_ids) == 5
    assert len(gt.distractors) == 5
