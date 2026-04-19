"""LM abstraction. Real model via LiteLLM; mock model for deterministic tests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class LM(Protocol):
    def complete(self, system: str, messages: list[dict[str, str]]) -> LMResponse: ...


class LiteLM:
    """Real LLM via litellm. Model string follows litellm conventions
    (e.g. 'anthropic/claude-sonnet-4-6', 'openai/gpt-5', 'ollama/llama3.2')."""

    def __init__(self, model: str, temperature: float = 0.2) -> None:
        self.model = model
        self.temperature = temperature

    def complete(self, system: str, messages: list[dict[str, str]]) -> LMResponse:
        import litellm

        resp = litellm.completion(
            model=self.model,
            messages=[{"role": "system", "content": system}, *messages],
            temperature=self.temperature,
        )
        choice = resp.choices[0]
        text = choice.message.content or ""
        usage = getattr(resp, "usage", None)
        return LMResponse(
            text=text,
            input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
        )


class MockLM:
    """Replays a canned list of responses. Used for eval + unit tests."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._i = 0

    def complete(self, system: str, messages: list[dict[str, str]]) -> LMResponse:
        if self._i >= len(self._responses):
            raise RuntimeError("MockLM exhausted — test expected more LLM calls than provided")
        text = self._responses[self._i]
        self._i += 1
        return LMResponse(text=text, input_tokens=100, output_tokens=50)
