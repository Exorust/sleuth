# rlm-logger

**Git bisect for production incidents.** Point it at your logs, ask a question in English, get back a signed case file with a root cause, cited evidence, and a confidence score.

```bash
pip install rlm-logger
export ANTHROPIC_API_KEY=...
rlm ask "why did checkout fail around 3am?" --logs ./logs/
```

## Why

When an incident hits, you don't need a dashboard. You need an answer. `rlm-logger` is a [DSPy RLM](https://github.com/stanfordnlp/dspy)-style agent that writes Python, runs it inside a sandboxed REPL over your logs, and recursively narrows down the cause. It stops when it can submit a structured `IncidentReport` or when it runs out of budget.

Every run produces a **case file**: one self-contained JSON document with the question, the full trajectory, the evidence cited (with ±3 lines of context), and the termination reason. Share it. Replay it. Grade it.

## What the agent can do

Five read-only query primitives plus two side channels, all sandboxed:

- `schema()` — services, levels, time window, row count
- `top_errors(limit=20)` — loudest failure modes
- `search(pattern, limit=10)` — substring across `msg` and `raw`
- `around(ts, window_s=60, service=None)` — what happened next to this timestamp
- `trace(trace_id)` — follow one request across services
- `llm_query(question, context="")` — ask a secondary LLM a judgement question
- `submit_incident_report(report)` — terminal, validated against schema

The loop is: LLM emits a python code block → we exec it → feed stdout back → repeat until `submit_incident_report` or budget exhaustion.

## Works with your log platform

Auto-detects exports from **Splunk**, **Datadog**, **New Relic**, and **Honeycomb** out of the box. Click Export in the tool you already pay for, point rlm-logger at the file, ask a question. No connectors, no API keys. See the [integration docs](https://exorust.github.io/rlm-logger/quickstart/#bring-your-own-logs).

## BYO model

Anything LiteLLM supports:

```bash
rlm ask "..." --logs ./logs --model anthropic/claude-sonnet-4-6
rlm ask "..." --logs ./logs --model openai/gpt-5
rlm ask "..." --logs ./logs --model ollama/llama3.2
rlm ask "..." --logs ./logs --model bedrock/anthropic.claude-sonnet-4-6-v1:0
```

## Reference fixture

`examples/checkout-incident/` is a 72-row, 5-service fixture: a Stripe API key rotation that cascades into 5xx errors on the checkout worker. It ships with:

- 5 ground-truth events (the causal chain)
- 5 distractors (plausible-but-unrelated events: redis blip, db pool pressure, feature flag reload, subscription retry, unrelated 429)
- An ideal trajectory any decent agent should match

Run the eval:

```bash
pytest eval/test_checkout_fixture.py -v
```

The eval enforces two gates: **evidence overlap ≥ 0.5** (cited the right events) and **distractor hits == 0** (didn't chase red herrings).

## Case file viewer

`viewer/` is an Astro site that renders any case file: trajectory with per-step tool badges, evidence cards with redacted context lines, confidence dial, ground-truth diff.

```bash
cd viewer && npm install && npm run dev
```

## Safety

Every log line passes through a secret redactor at ingest time: Bearer tokens, Stripe/AWS/GitHub/Slack keys, JWTs, and SSH private keys are stripped before anything touches the agent. Case files never carry raw secrets.

## Docs

Full docs at [exorust.github.io/rlm-logger](https://exorust.github.io/rlm-logger/).

## License

Apache-2.0.
