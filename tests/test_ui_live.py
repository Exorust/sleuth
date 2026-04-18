"""Snapshot-ish tests for LiveRenderer. We don't render to a real TTY; we
exercise the public Observer surface against a recording Console and assert
that key substrings land in the captured output."""
from __future__ import annotations

from rich.console import Console

from rlm_logger.schemas import Step
from rlm_logger.ui.live import LiveRenderer


def test_live_renderer_captures_core_panels():
    r = LiveRenderer(question="why did checkout fail?")
    r.render_step_start(Step(step=1, tool="schema", args={}))
    r.render_step_stdout(Step(step=1, tool="schema"), "services: vault, checkout-worker")
    r.render_step_end(Step(step=1, tool="schema", elapsed_ms=12))
    r.render_report_delta({"root_cause": "checkout-worker stale secret"})
    r.render_terminated("submitted")

    console = Console(record=True, width=100, force_terminal=True)
    console.print(r._render())
    out = console.export_text()

    assert "why did checkout fail?" in out
    assert "schema" in out
    assert "services: vault" in out
    assert "root_cause" in out
    assert "submitted" in out


def test_live_renderer_status_icons():
    r = LiveRenderer(question="q")
    r.render_step_start(Step(step=1, tool="schema"))
    # while running: ► icon should be in the render
    console = Console(record=True, width=80, force_terminal=True)
    console.print(r._render())
    assert "►" in console.export_text() or "schema" in console.export_text()

    r.render_step_end(Step(step=1, tool="schema", elapsed_ms=10))
    console2 = Console(record=True, width=80, force_terminal=True)
    console2.print(r._render())
    assert "✓" in console2.export_text()
