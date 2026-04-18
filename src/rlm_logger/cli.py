"""rlm CLI. Typer-based."""
from __future__ import annotations

import sys
from pathlib import Path

import typer

app = typer.Typer(add_completion=False, help="Recursive-LM incident debugger for logs.")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural-language question about the logs."),
    logs: list[Path] = typer.Option(..., "--logs", help="Log files or directories to ingest."),
    out: Path = typer.Option(Path("incident.rlm.json"), "--out", help="Where to write the case file."),
    model: str = typer.Option("anthropic/claude-sonnet-4-6", "--model", help="LiteLLM model id."),
    plain: bool = typer.Option(False, "--plain", help="Flat-scroll output, no live TUI."),
) -> None:
    """Run the agent on a set of logs and write a case file."""
    # TODO: wire ingest → store → agent.run(..., observer=Live|Plain) → case_file.dump
    typer.echo("stub: implement ask()", err=True)
    raise typer.Exit(code=1)


@app.command()
def replay(
    case: Path = typer.Argument(..., help="Path to a .rlm.json case file."),
) -> None:
    """Deterministically re-play a case file's trajectory in the terminal."""
    # TODO: load case_file, stream Steps through PlainRenderer, no LLM calls.
    typer.echo("stub: implement replay()", err=True)
    raise typer.Exit(code=1)


def main() -> int:
    app()
    return 0


if __name__ == "__main__":
    sys.exit(main())
