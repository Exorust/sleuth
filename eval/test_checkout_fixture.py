"""End-to-end eval: run the agent against the checkout-401 fixture.

Gates:
  - evidence_overlap  >= 0.5  (jaccard of report.evidence event_ids vs ground_truth.evidence_event_ids)
  - distractor_hits   == 0    (any distractor cited as is_key=True fails the run)
  - judge_correctness >= 3.0  (LLM-judge score 1-5 on root_cause match)

These thresholds are from the approved design doc.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="eval harness pending — agent.run() is a stub")


def test_agent_solves_checkout_401():
    # TODO: ingest examples/checkout-incident/logs, run agent, load ground_truth,
    # compute evidence_overlap + distractor_hits + judge_correctness, assert gates.
    ...
