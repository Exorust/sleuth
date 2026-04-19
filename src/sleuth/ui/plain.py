"""Flat scroll renderer. Used for --plain, CI, pipes, snapshot tests."""
from __future__ import annotations

import sys
from typing import Any

from sleuth.schemas import Step
from sleuth.ui.observer import StepObserver


class PlainRenderer(StepObserver):
    def __init__(self, stream=sys.stdout) -> None:
        self.stream = stream

    def render_step_start(self, step: Step) -> None:
        self.stream.write(f"[{step.step}] {step.tool}({step.args})\n")
        self.stream.flush()

    def render_step_stdout(self, step: Step, chunk: str) -> None:
        self.stream.write(chunk)
        self.stream.flush()

    def render_step_end(self, step: Step) -> None:
        self.stream.write(f"[{step.step}] ✓ {step.elapsed_ms}ms\n\n")
        self.stream.flush()

    def render_report_delta(self, delta: dict[str, Any]) -> None:
        self.stream.write(f"  report δ: {list(delta)}\n")
        self.stream.flush()

    def render_terminated(self, reason: str) -> None:
        self.stream.write(f"\n--- terminated: {reason} ---\n")
        self.stream.flush()
