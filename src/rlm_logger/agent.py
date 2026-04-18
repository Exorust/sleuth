"""The DSPy RLM agent loop.

One iteration = one LLM call that emits Python code, executed in a
sandboxed REPL with the 5 tools + submit_incident_report in scope.
Budgets: max_iterations=20, max_llm_calls=50, max_wall_clock=180s.
"""
from __future__ import annotations

from dataclasses import dataclass

import duckdb

from rlm_logger.schemas import CaseFile, LogsManifest, ModelInfo
from rlm_logger.ui.observer import StepObserver


@dataclass
class Budget:
    max_iterations: int = 20
    max_llm_calls: int = 50
    max_wall_clock_s: float = 180.0


def run(
    question: str,
    conn: duckdb.DuckDBPyConnection,
    manifest: LogsManifest,
    model: ModelInfo,
    observer: StepObserver,
    budget: Budget = Budget(),
) -> CaseFile:
    """Run the RLM loop until the model calls submit_incident_report or a budget is breached.

    Always returns a CaseFile, even on Ctrl-C or budget breach. Partial
    trajectory + whatever report we have goes into termination_reason.
    """
    # TODO:
    # 1. Build DSPy RLM module with [schema, top_errors, search, around, trace,
    #    submit_incident_report, llm_query] bound to `conn`.
    # 2. Loop: call LLM → observer.render_step_start(step) → exec tool code
    #    in sandbox → observer.render_step_stdout(chunk) → observer.render_step_end(step).
    # 3. If report delta emitted, observer.render_report_delta(delta).
    # 4. On submit_incident_report call: termination_reason="submitted", break.
    # 5. On budget breach or exception: termination_reason=<reason>, still return CaseFile.
    # 6. Always: assemble CaseFile with the full trajectory captured so far.
    raise NotImplementedError
