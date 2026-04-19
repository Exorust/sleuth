# Sleuth

**Use an RLM to figure out your log files.** Git bisect for production incidents.
Point it at your logs, ask a natural-language question, get a signed case file you
can share in a Slack channel or link in a PR.

```bash
pip install sleuth-rlm
sleuth ask "why did checkout fail around 3am?" --logs ./logs/
```

## What it is

A Python library and CLI that wraps a DSPy-style recursive-LM agent around your log
files. The agent has 5 read-only tools over a DuckDB event store, can call a side LLM
for judgement, and terminates by writing an `IncidentReport` with evidence citations
and a confidence score.

## What it isn't

- A hosted SaaS. Runs entirely locally. Your logs never leave your box.
- A log aggregator. Bring your own logs (`.log`, `.jsonl`, `.ndjson`, `.gz`).
- Tied to any model vendor. BYO model via LiteLLM (OpenAI, Anthropic, Bedrock, Ollama).

## The case file

Every run produces one `.sleuth.json` file: question + trajectory + report + evidence +
ground truth (optional). The file is the product. It's deterministic to replay
(`sleuth replay case.sleuth.json`), renders in [the browser viewer](viewer/),
and is small enough to paste into a GitHub issue.

## Works with your log platform

Auto-detects exports from Splunk, Datadog, New Relic, and Honeycomb. Click Export
in your platform of choice, hand Sleuth the file, ask a question. No connectors,
no API keys, no platform credentials.

- [Splunk](integrations/splunk.md)
- [Datadog](integrations/datadog.md)
- [New Relic](integrations/newrelic.md)
- [Honeycomb](integrations/honeycomb.md)

## Next

- [Quickstart](quickstart.md) — 90-second tour
- [Case File Protocol](case-file.md) — the v0.1 schema
- [Tools](tools.md) — what the agent can call
- [BYO Model](models.md) — provider configuration
- [Eval Harness](eval.md) — how to grade a run against ground truth
