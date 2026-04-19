"""sleuth CLI. Typer-based."""
from __future__ import annotations

import sys
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help="Sleuth: use an RLM to figure out your log files.")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural-language question about the logs."),
    logs: list[Path] = typer.Option(..., "--logs", help="Log files or directories to ingest."),
    out: Path = typer.Option(Path("incident.sleuth.json"), "--out", help="Where to write the case file."),
    model: str = typer.Option("anthropic/claude-sonnet-4-6", "--model", help="LiteLLM model id."),
    plain: bool = typer.Option(False, "--plain", help="Flat-scroll output, no live TUI."),
    max_iterations: int = typer.Option(20, "--max-iterations"),
    max_llm_calls: int = typer.Option(50, "--max-llm-calls"),
    max_wall_clock: float = typer.Option(180.0, "--max-wall-clock"),
) -> None:
    """Run the agent on a set of logs and write a case file."""
    from sleuth.agent import Budget, run
    from sleuth.case_file import dump
    from sleuth.ingest import ingest_paths
    from sleuth.lm import LiteLM
    from sleuth.schemas import ModelInfo
    from sleuth.store import open_store
    from sleuth.ui.plain import PlainRenderer

    files = _expand_log_paths(logs)
    if not files:
        typer.echo("no log files found", err=True)
        raise typer.Exit(code=1)

    conn = open_store(":memory:")
    typer.echo(f"ingesting {len(files)} file(s)…", err=True)
    manifest = ingest_paths(files, conn)
    typer.echo(f"  {manifest.total_rows} rows, {manifest.time_window.start} → {manifest.time_window.end}", err=True)

    provider, name = (model.split("/", 1) + ["", ""])[:2]
    lm = LiteLM(model=model, temperature=0.2)
    model_info = ModelInfo(provider=provider or "unknown", name=name or model, temperature=0.2)

    budget = Budget(max_iterations=max_iterations, max_llm_calls=max_llm_calls, max_wall_clock_s=max_wall_clock)

    if plain or not sys.stdout.isatty():
        case = run(question=question, conn=conn, manifest=manifest, model=model_info,
                   lm=lm, observer=PlainRenderer(), budget=budget)
    else:
        from sleuth.ui.live import LiveRenderer
        with LiveRenderer(question=question) as renderer:
            case = run(question=question, conn=conn, manifest=manifest, model=model_info,
                       lm=lm, observer=renderer, budget=budget)

    dump(case, out)
    typer.echo(f"\ncase file → {out}  (termination: {case.termination_reason})", err=True)
    raise typer.Exit(code=0 if case.termination_reason == "submitted" else 2)


@app.command()
def replay(
    case: Path = typer.Argument(..., help="Path to a .sleuth.json case file."),
) -> None:
    """Deterministically re-play a case file's trajectory in the terminal."""
    from sleuth.case_file import load
    from sleuth.ui.plain import PlainRenderer

    cf = load(case)
    r = PlainRenderer()
    typer.echo(f"# {cf.question}\n# model: {cf.model.provider}/{cf.model.name}\n")
    for step in cf.trajectory:
        r.render_step_start(step)
        if step.stdout_excerpt:
            r.render_step_stdout(step, step.stdout_excerpt)
        r.render_step_end(step)
    r.render_terminated(cf.termination_reason)
    if cf.report:
        typer.echo(f"\nroot cause: {cf.report.root_cause}")
        typer.echo(f"confidence: {cf.report.confidence:.0%} — {cf.report.confidence_rationale}")


def _expand_log_paths(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    exts = {".log", ".jsonl", ".ndjson", ".gz"}
    for p in paths:
        if p.is_dir():
            out.extend(sorted(q for q in p.rglob("*") if q.is_file() and q.suffix in exts))
        elif p.is_file():
            out.append(p)
    return out


def main() -> int:
    app()
    return 0


if __name__ == "__main__":
    sys.exit(main())
