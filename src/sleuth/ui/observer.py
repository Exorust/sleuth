"""StepObserver protocol.

The agent loop depends on this protocol, not the concrete renderer.
LiveRenderer (Rich multi-panel) is for interactive TTYs; PlainRenderer
(flat scroll) is for --plain and CI. Add a third impl without touching
agent.py.
"""
from __future__ import annotations

from typing import Any, Protocol

from sleuth.schemas import Step


class StepObserver(Protocol):
    def render_step_start(self, step: Step) -> None: ...
    def render_step_stdout(self, step: Step, chunk: str) -> None: ...
    def render_step_end(self, step: Step) -> None: ...
    def render_report_delta(self, delta: dict[str, Any]) -> None: ...
    def render_terminated(self, reason: str) -> None: ...
