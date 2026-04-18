"""Rich multi-panel live TUI.

Layout (rich.Layout):

    ┌─ Question ──────────────────────────────────────────┐
    │ why did checkout fail around 3am?                   │
    ├─ Trajectory ─────────┬─ Step output ───────────────┤
    │ 1 ✓ schema           │ services: vault, checkout…  │
    │ 2 ✓ top_errors       │                             │
    │ 3 ► search           │ (stream)                    │
    ├─ Report (live) ──────┴─ Budget ─────────────────────┤
    │ root_cause: (forming)   iter 3/20  llm 4/50  12s    │
    └─────────────────────────────────────────────────────┘
"""
from __future__ import annotations

from typing import Any

from rlm_logger.schemas import Step
from rlm_logger.ui.observer import StepObserver


class LiveRenderer(StepObserver):
    def __init__(self) -> None:
        # TODO: build rich.Live + rich.Layout with panels: question,
        # trajectory (list of Steps), step_output (streaming), report (live
        # forming), budget (iter/llm/wall). Keep refresh_per_second=10.
        ...

    def render_step_start(self, step: Step) -> None:
        raise NotImplementedError

    def render_step_stdout(self, step: Step, chunk: str) -> None:
        raise NotImplementedError

    def render_step_end(self, step: Step) -> None:
        raise NotImplementedError

    def render_report_delta(self, delta: dict[str, Any]) -> None:
        raise NotImplementedError

    def render_terminated(self, reason: str) -> None:
        raise NotImplementedError
