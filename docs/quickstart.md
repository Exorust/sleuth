# Quickstart

## Install

```bash
pip install sleuth-rlm
```

Python 3.11+. DuckDB + pydantic + typer + rich + litellm + dspy are the core deps.

## Configure a model

```bash
export ANTHROPIC_API_KEY=...     # or
export OPENAI_API_KEY=...        # or
# local ollama: export OLLAMA_API_BASE=http://localhost:11434
```

## Run on the reference fixture

```bash
git clone https://github.com/Exorust/sleuth && cd sleuth
sleuth ask "why did checkout fail around 3am?" \
  --logs examples/checkout-incident/logs/ \
  --model anthropic/claude-sonnet-4-6 \
  --out case.sleuth.json
```

You'll see a live Rich TUI: the trajectory column tracks each tool call, the step-
output panel streams stdout, and the report panel fills in as the agent forms its
conclusion. When it calls `submit_incident_report`, the run ends and `case.sleuth.json`
is written.

## Replay a case file

```bash
sleuth replay case.sleuth.json
```

Deterministic, no LLM calls. Useful for sharing: the case file is self-contained.

## View in the browser

Drop `case.sleuth.json` on [rlm.sh](https://rlm.sh) or append `?url=<public-url>` to load
a remote file. The viewer renders trajectory, evidence (with context ±3 lines),
confidence dial, and a ground-truth diff if present.

## Bring your own logs

Sleuth auto-detects exports from the major log platforms. No flags, no config.

- [Splunk](integrations/splunk.md) — Export → JSON
- [Datadog](integrations/datadog.md) — Log Explorer → Download as JSON
- [New Relic](integrations/newrelic.md) — NRQL → Export → JSON
- [Honeycomb](integrations/honeycomb.md) — Query → Download as JSON

Plain `.jsonl`, `.ndjson`, `.log`, and `.gz` also work out of the box.
