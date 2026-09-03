"""Anthropic provider: the `agent` and `judge` roles via the Messages API.

Structured output uses Anthropic's tool-use mechanism: the caller's Pydantic
schema becomes the input schema of a single forced tool call, and that tool
call's input is the answer. `see_video` is not implemented here — that role
belongs to a vision-capable provider (Gemini).
"""

from __future__ import annotations

import os
from typing import Any, TypeVar

from pydantic import BaseModel

from autotester.providers.base import Provider, ProviderError

ModelT = TypeVar("ModelT", bound=BaseModel)

DEFAULT_MODEL = "claude-sonnet-5"
_TOOL_NAME = "answer"


class AnthropicProvider(Provider):
    """Wraps `anthropic.Anthropic`. Never receives a raw secret — callers pass
    prompts containing `{{SECRET:KEY}}` placeholders only, per the base contract."""

    id = "anthropic"

    def __init__(self, **options: Any) -> None:
        super().__init__(**options)
        self._api_key = options.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        self._model = options.get("model", DEFAULT_MODEL)

    def available(self) -> bool:
        return bool(self._api_key)

    def act(self, prompt: str, schema: type[ModelT] | None = None) -> Any:
        return self._structured(prompt, schema, role="agent")

    def judge(self, prompt: str, schema: type[ModelT]) -> ModelT:
        return self._structured(prompt, schema, role="judge")

    def _structured(self, prompt: str, schema: type[ModelT] | None, *, role: str) -> ModelT:
        if not self.available():
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        if schema is None:
            raise ProviderError(f"{self.id} requires a schema for structured output (role={role})")
        from anthropic import Anthropic

        client = Anthropic(api_key=self._api_key)
        tool = {
            "name": _TOOL_NAME,
            "description": "Return the structured answer for this request.",
            "input_schema": schema.model_json_schema(),
        }
        response = client.messages.create(
            model=self._model,
            max_tokens=2048,
            tools=[tool],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": prompt}],
        )
        block = next((b for b in response.content if b.type == "tool_use"), None)
        if block is None:
            raise ProviderError(f"{self.id}: no tool_use block in response for role={role}")
        self.record(
            role,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return schema.model_validate(block.input)
