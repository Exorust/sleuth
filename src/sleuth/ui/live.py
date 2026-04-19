"""Rich multi-panel live TUI.

Layout:
  ┌─ Question ──────────────────────────────────────────┐
  │ why did checkout fail around 3am?                   │
  ├─ Trajectory ─────────┬─ Step output ───────────────┤
  │ 1 ✓ schema           │ (live streaming)            │
  │ 2 ✓ top_errors       │                             │
  │ 3 ► search           │                             │
  ├─ Report (forming) ───┴─ Budget ─────────────────────┤
  │ root_cause: …          iter 3  calls 4  12s        │
  └─────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import time
from typing import Any

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sleuth.schemas import Step
from sleuth.ui.observer import StepObserver

_TOOL_COLOR = {
    "schema": "cyan",
    "top_errors": "red",
    "search": "magenta",
    "around": "yellow",
    "trace": "green",
    "submit_incident_report": "bold #ff6b3d",
    "llm_query": "dim",
}


class LiveRenderer(StepObserver):
    def __init__(self, question: str = "") -> None:
        self.question = question
        self.trajectory: list[tuple[Step, str]] = []  # (step, status: running|done|error)
        self.current_output = Text("")
        self.report_delta: dict[str, Any] = {}
        self.terminated: str | None = None
        self.started_at = time.monotonic()
        self._live: Live | None = None

    def __enter__(self) -> "LiveRenderer":
        self._live = Live(self._render(), refresh_per_second=10, transient=False)
        self._live.__enter__()
        return self

    def __exit__(self, *exc) -> None:
        if self._live:
            self._live.__exit__(*exc)

    def _tool_style(self, tool: str) -> str:
        return _TOOL_COLOR.get(tool, "white")

    def _render_trajectory(self) -> Panel:
        t = Table.grid(padding=(0, 1))
        t.add_column(justify="right", width=3, style="dim")
        t.add_column(width=2)
        t.add_column()
        for step, status in self.trajectory:
            icon = {"done": "✓", "running": "►", "error": "✗"}.get(status, "·")
            icon_style = {"done": "green", "running": "yellow", "error": "red"}.get(status, "dim")
            t.add_row(
                str(step.step),
                Text(icon, style=icon_style),
                Text(step.tool, style=self._tool_style(step.tool)),
            )
        return Panel(t, title="trajectory", title_align="left", border_style="#262a31")

    def _render_output(self) -> Panel:
        return Panel(
            self.current_output or Text("(waiting)", style="dim"),
            title="step output",
            title_align="left",
            border_style="#262a31",
        )

    def _render_report(self) -> Panel:
        if not self.report_delta:
            body = Text("(report forming…)", style="dim")
        else:
            body = Text()
            for k, v in self.report_delta.items():
                vs = str(v)
                if len(vs) > 120:
                    vs = vs[:120] + "…"
                body.append(f"{k}: ", style="bold")
                body.append(f"{vs}\n")
        return Panel(body, title="report", title_align="left", border_style="#262a31")

    def _render_budget(self) -> Panel:
        elapsed = time.monotonic() - self.started_at
        iters = len(self.trajectory)
        state = self.terminated or "running"
        txt = Text.assemble(
            ("iter ", "dim"), (f"{iters}", "bold"),
            ("  ", ""), ("elapsed ", "dim"), (f"{elapsed:.1f}s", "bold"),
            ("  ", ""), ("state ", "dim"),
            (state, "bold green" if state == "submitted" else ("bold yellow" if state == "running" else "bold red")),
        )
        return Panel(txt, title="budget", title_align="left", border_style="#262a31")

    def _render(self) -> Group:
        header = Panel(
            Text(self.question or "(no question)", style="bold"),
            title="question",
            title_align="left",
            border_style="#ff6b3d",
        )
        return Group(header, self._render_trajectory(), self._render_output(), self._render_report(), self._render_budget())

    def _refresh(self) -> None:
        if self._live:
            self._live.update(self._render())

    # StepObserver impl
    def render_step_start(self, step: Step) -> None:
        self.trajectory.append((step, "running"))
        self.current_output = Text("")
        self._refresh()

    def render_step_stdout(self, step: Step, chunk: str) -> None:
        self.current_output = Text(chunk[-2000:], style=self._tool_style(step.tool))
        self._refresh()

    def render_step_end(self, step: Step) -> None:
        # mutate the last entry to done/error
        if self.trajectory and self.trajectory[-1][0].step == step.step:
            status = "error" if step.stderr_excerpt else "done"
            self.trajectory[-1] = (step, status)
        self._refresh()

    def render_report_delta(self, delta: dict[str, Any]) -> None:
        self.report_delta.update(delta)
        self._refresh()

    def render_terminated(self, reason: str) -> None:
        self.terminated = reason
        self._refresh()
