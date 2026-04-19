"""Pydantic v2 schemas for the case-file protocol.

These types define the portable, shareable artifact a run produces.
The Astro viewer at rlm.sh binds directly to this shape, so any change
here is a breaking change to the protocol.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    name: str
    temperature: float = 0.2


class LogFileEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    bytes: int
    rows: int
    sha256: str


class TimeWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: datetime
    end: datetime


class LogsManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    files: list[LogFileEntry]
    time_window: TimeWindow
    total_rows: int


class EvidenceLine(BaseModel):
    """A single log line cited in the report. Carries ±3 lines of context
    so the viewer can render surrounding events without re-reading source."""
    model_config = ConfigDict(extra="forbid")
    event_id: str | None = None
    file: str
    line: int
    ts: datetime
    service: str
    level: str
    text_redacted: str
    context_before: list[str] = Field(default_factory=list, max_length=3)
    context_after: list[str] = Field(default_factory=list, max_length=3)
    why: str
    is_key: bool = False


class BlastRadius(BaseModel):
    model_config = ConfigDict(extra="allow")  # schema varies per incident
    duration_minutes: int | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None


class IncidentReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root_cause: str
    blast_radius: str | BlastRadius
    evidence: list[EvidenceLine]
    remediation: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_rationale: str
    unknowns: list[str] = Field(default_factory=list)


class Step(BaseModel):
    """One iteration of the agent loop: a tool call and its outcome."""
    model_config = ConfigDict(extra="forbid")
    step: int
    tool: Literal["schema", "top_errors", "search", "around", "trace", "submit_incident_report", "llm_query"]
    args: dict[str, Any] = Field(default_factory=dict)
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    elapsed_ms: int = 0
    report_delta: dict[str, Any] | None = None


class Usage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    llm_calls: int = 0
    tool_calls: int = 0
    wall_clock_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


class GroundTruth(BaseModel):
    """Optional expected answer, for eval grading."""
    model_config = ConfigDict(extra="allow")
    incident_id: str | None = None
    root_cause: str
    evidence_event_ids: list[str] = Field(default_factory=list)
    blast_radius: dict[str, Any] | str | None = None
    remediation: dict[str, Any] | str | None = None
    distractors: list[dict[str, Any]] = Field(default_factory=list)


TerminationReason = Literal["submitted", "max_iterations", "max_llm_calls", "max_wall_clock", "aborted", "error"]


class CaseFile(BaseModel):
    """Top-level artifact. One run = one case file."""
    model_config = ConfigDict(extra="forbid")
    version: Literal["0.1"] = "0.1"
    question: str
    model: ModelInfo
    logs_manifest: LogsManifest
    trajectory: list[Step]
    report: IncidentReport | None = None
    termination_reason: TerminationReason
    usage: Usage = Field(default_factory=Usage)
    ground_truth: GroundTruth | None = None
