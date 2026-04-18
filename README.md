# rlm-logger

**Git bisect for production incidents.** Point it at your logs, ask a question, get a signed case file.

```bash
pip install rlm-logger
rlm ask "why did checkout fail around 3am?" --logs ./logs/
```

Status: pre-0.1. Design doc approved, fixture landed, implementation in progress.

Weekend scope. BYO-model (OpenAI, Anthropic, Ollama, Bedrock via LiteLLM). Deterministic replay of any case file. Open source Apache-2.0.

See `examples/checkout-incident/` for the reference fixture.
