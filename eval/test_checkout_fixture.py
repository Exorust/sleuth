"""End-to-end eval: run the agent against the checkout-401 fixture with a
deterministic MockLM, then assert the design-doc grading gates.

Gates (from the approved plan):
  - evidence_overlap  >= 0.5  (jaccard of report event_ids vs ground_truth.evidence_event_ids)
  - distractor_hits   == 0    (any distractor cited with is_key=True is a fail)
  - confidence        >= 0.5  (proxy for judge_correctness when no real judge is wired)

The real judge-LLM version lives behind an env flag (RLM_EVAL_REAL) and is
not run in CI to keep the tests hermetic + free.
"""
from __future__ import annotations

import io
from pathlib import Path

from sleuth.agent import Budget, run
from sleuth.ingest import ingest_paths
from sleuth.lm import MockLM
from sleuth.schemas import GroundTruth, ModelInfo
from sleuth.store import open_store
from sleuth.ui.plain import PlainRenderer

FIXTURE = Path(__file__).parent.parent / "examples" / "checkout-incident"

# Same ideal trajectory as tests/test_agent.py. If the real agent drifts
# from this path, we'll grade its actual trajectory against the same gates.
from tests.test_agent import IDEAL_TRAJECTORY  # noqa: E402


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def test_agent_solves_checkout_401():
    conn = open_store(":memory:")
    manifest = ingest_paths(sorted((FIXTURE / "logs").glob("*.jsonl")), conn)
    lm = MockLM(IDEAL_TRAJECTORY)

    case = run(
        question="why did checkout fail around 3am?",
        conn=conn,
        manifest=manifest,
        model=ModelInfo(provider="mock", name="ideal"),
        lm=lm,
        observer=PlainRenderer(stream=io.StringIO()),
        budget=Budget(),
    )

    assert case.termination_reason == "submitted", f"expected submitted, got {case.termination_reason}"
    assert case.report is not None

    import json
    gt = GroundTruth.model_validate(json.loads((FIXTURE / "ground_truth.json").read_text()))

    report_ids = {e.event_id for e in case.report.evidence if e.event_id}
    gt_ids = set(gt.evidence_event_ids)

    overlap = _jaccard(report_ids & gt_ids, gt_ids)
    assert overlap >= 0.5, f"evidence_overlap {overlap:.2f} < 0.5 gate"

    distractor_events = {d.get("event", "") for d in gt.distractors}
    key_evidence_ids = {e.event_id for e in case.report.evidence if e.is_key and e.event_id}
    distractor_hits = key_evidence_ids & distractor_events
    assert not distractor_hits, f"distractor cited as key: {distractor_hits}"

    assert case.report.confidence >= 0.5, f"confidence {case.report.confidence:.2f} < 0.5"

    print(f"\nEVAL PASS: overlap={overlap:.2f} distractors=0 confidence={case.report.confidence:.2f} "
          f"iters={len(case.trajectory)} wall={case.usage.wall_clock_s}s")
