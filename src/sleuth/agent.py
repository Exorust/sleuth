"""The RLM agent loop.

One iteration = one LLM call that emits Python code, executed in a
restricted REPL with the 5 tools + submit_incident_report + llm_query
in scope. Budgets: max_iterations=20, max_llm_calls=50, max_wall_clock=180s.

The loop ALWAYS returns a CaseFile, even on Ctrl-C, budget breach, or
exception. Partial trajectory + whatever report exists gets captured
into termination_reason.
"""
from __future__ import annotations

import io
import re
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from typing import Any

import duckdb

from sleuth.lm import LM, LMResponse
from sleuth.schemas import (
    CaseFile,
    IncidentReport,
    LogsManifest,
    ModelInfo,
    Step,
    TerminationReason,
    Usage,
)
from sleuth.tools import around as _around
from sleuth.tools import schema as _schema
from sleuth.tools import search as _search
from sleuth.tools import top_errors as _top_errors
from sleuth.tools import trace as _trace
from sleuth.ui.observer import StepObserver


@dataclass
class Budget:
    max_iterations: int = 20
    max_llm_calls: int = 50
    max_wall_clock_s: float = 180.0


SYSTEM_PROMPT = """You are an incident debugger. You have a DuckDB store of log
events and 5 read-only tools, plus an llm_query helper and a submit_incident_report
sink. Every reply MUST be a single ```python``` code block that calls tools and
optionally assigns to stdout-visible variables (print). When you have root cause
+ evidence + remediation, call submit_incident_report({...}) with a dict that
matches the IncidentReport schema, then stop.

Tools in scope:
  schema()                           -> str (services, levels, time window)
  top_errors(limit=20)               -> str (ranked error/warn msgs)
  search(pattern, limit=10)          -> str (substring match, redacted)
  around(ts, window_s=60, service=None) -> str (events near a timestamp)
  trace(trace_id)                    -> str (events sharing a correlation id)
  llm_query(question, context)       -> str (ask a side LLM for text analysis)
  submit_incident_report(report)     -> terminate with the given report

IncidentReport fields:
  root_cause: str
  blast_radius: str (free-form)
  evidence: list of {file, line, ts, service, level, text_redacted, why, is_key, event_id?}
  remediation: str
  confidence: float in [0,1]
  confidence_rationale: str
  unknowns: list of str

Work step by step. Think in the code block as comments. Be concise in prints."""


CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str:
    m = CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1)
    return text  # fall back: treat the whole reply as code


def _llm_query_factory(lm: LM, usage: Usage):
    def llm_query(question: str, context: str = "") -> str:
        resp = lm.complete(
            "You are a log-analysis side-oracle. Answer concisely.",
            [{"role": "user", "content": f"{question}\n\ncontext:\n{context}"}],
        )
        usage.llm_calls += 1
        usage.input_tokens += resp.input_tokens
        usage.output_tokens += resp.output_tokens
        return resp.text
    return llm_query


class _Submitted(Exception):
    def __init__(self, report: IncidentReport) -> None:
        self.report = report


def _submit_factory():
    def submit_incident_report(report: dict[str, Any] | IncidentReport) -> str:
        validated = report if isinstance(report, IncidentReport) else IncidentReport.model_validate(report)
        raise _Submitted(validated)
    return submit_incident_report


def run(
    question: str,
    conn: duckdb.DuckDBPyConnection,
    manifest: LogsManifest,
    model: ModelInfo,
    lm: LM,
    observer: StepObserver,
    budget: Budget = Budget(),
) -> CaseFile:
    start = time.monotonic()
    usage = Usage()
    trajectory: list[Step] = []
    report: IncidentReport | None = None
    termination: TerminationReason = "max_iterations"
    messages: list[dict[str, str]] = [
        {"role": "user", "content": f"Question: {question}\n\nBegin by calling schema()."}
    ]

    # Tools bound to this conn, plus the sinks.
    def _bind(fn):
        return lambda *a, **kw: fn(conn, *a, **kw)

    exec_globals: dict[str, Any] = {
        "schema": _bind(_schema),
        "top_errors": _bind(_top_errors),
        "search": _bind(_search),
        "around": _bind(_around),
        "trace": _bind(_trace),
        "llm_query": _llm_query_factory(lm, usage),
        "submit_incident_report": _submit_factory(),
        "print": print,
    }

    try:
        for step_n in range(1, budget.max_iterations + 1):
            if time.monotonic() - start > budget.max_wall_clock_s:
                termination = "max_wall_clock"
                break
            if usage.llm_calls >= budget.max_llm_calls:
                termination = "max_llm_calls"
                break

            resp: LMResponse = lm.complete(SYSTEM_PROMPT, messages)
            usage.llm_calls += 1
            usage.input_tokens += resp.input_tokens
            usage.output_tokens += resp.output_tokens

            code = _extract_code(resp.text)
            step = Step(step=step_n, tool="llm_query", args={"code_len": len(code)})  # refined below

            # Heuristic: derive a display tool name from the first real call in the code.
            tool_hint = _first_tool_call(code)
            if tool_hint:
                step = Step(step=step_n, tool=tool_hint, args={})

            observer.render_step_start(step)

            stdout, stderr = io.StringIO(), io.StringIO()
            t0 = time.monotonic()
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exec(compile(code, f"<step-{step_n}>", "exec"), exec_globals)
            except _Submitted as done:
                report = done.report
                step.elapsed_ms = int((time.monotonic() - t0) * 1000)
                step.tool = "submit_incident_report"
                step.stdout_excerpt = stdout.getvalue()[-4000:]
                observer.render_step_end(step)
                trajectory.append(step)
                usage.tool_calls += 1
                termination = "submitted"
                break
            except Exception:
                step.stderr_excerpt = (stderr.getvalue() + "\n" + traceback.format_exc())[-4000:]

            step.elapsed_ms = int((time.monotonic() - t0) * 1000)
            step.stdout_excerpt = stdout.getvalue()[-4000:]
            usage.tool_calls += 1
            observer.render_step_stdout(step, step.stdout_excerpt)
            observer.render_step_end(step)
            trajectory.append(step)

            # Feed the observed output back to the model.
            messages.append({"role": "assistant", "content": resp.text})
            observed = step.stdout_excerpt or step.stderr_excerpt or "(no output)"
            messages.append({"role": "user", "content": f"stdout:\n{observed}"})

    except KeyboardInterrupt:
        termination = "aborted"
    except Exception:
        termination = "error"

    usage.wall_clock_s = round(time.monotonic() - start, 2)
    observer.render_terminated(termination)

    return CaseFile(
        version="0.1",
        question=question,
        model=model,
        logs_manifest=manifest,
        trajectory=trajectory,
        report=report,
        termination_reason=termination,
        usage=usage,
    )


_TOOL_NAMES = {"schema", "top_errors", "search", "around", "trace", "submit_incident_report", "llm_query"}


def _first_tool_call(code: str) -> str | None:
    for name in _TOOL_NAMES:
        if re.search(rf"\b{name}\s*\(", code):
            return name
    return None
