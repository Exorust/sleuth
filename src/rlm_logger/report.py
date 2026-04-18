"""submit_incident_report — the terminal tool that ends a run.

The LLM calls this once it believes it has root cause + evidence.
We validate the payload against IncidentReport, attach it to the
in-flight CaseFile, and signal the agent loop to stop.
"""
from __future__ import annotations

from rlm_logger.schemas import IncidentReport


def validate_report(payload: dict) -> IncidentReport:
    """Raises ValidationError if the LLM's report is malformed."""
    return IncidentReport.model_validate(payload)
