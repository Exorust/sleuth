# BYO Model

Sleuth uses [LiteLLM](https://github.com/BerriAI/litellm) under the hood, so any
model LiteLLM supports, we support. Set the appropriate API key and pass the model id.

## Anthropic

```bash
export ANTHROPIC_API_KEY=...
sleuth ask "..." --logs ./logs --model anthropic/claude-sonnet-4-6
```

Recommended for v0.1. Good at code synthesis, strong at following the `submit_incident_report`
protocol.

## OpenAI

```bash
export OPENAI_API_KEY=...
sleuth ask "..." --logs ./logs --model openai/gpt-5
```

## Local (Ollama)

```bash
ollama pull llama3.2
sleuth ask "..." --logs ./logs --model ollama/llama3.2
```

Works. Slower and less reliable at terminating via `submit_incident_report` than frontier
models. You may need to raise `--max-iterations`.

## AWS Bedrock

```bash
export AWS_REGION=us-west-2
sleuth ask "..." --logs ./logs --model bedrock/anthropic.claude-sonnet-4-6-v1:0
```

## Model capability floor

The agent is a DSPy-RLM-style loop: it writes Python code, we execute it in a sandbox.
Models below ~GPT-4-class generally can't maintain the code-block discipline or the
JSON-dict shape of the final `submit_incident_report`. If you're seeing `max_iterations`
terminations with no report, try a stronger model first.
