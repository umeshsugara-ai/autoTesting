"""Deterministic provider for tests and dry runs. Never calls a network."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from autotester.providers.base import Provider, ProviderError

ModelT = TypeVar("ModelT", bound=BaseModel)


class MockProvider(Provider):
    """Returns pre-seeded responses keyed by role.

    Seed it with ready-made model instances; the mock records usage exactly like
    a real provider so cost-accounting tests are meaningful.
    """

    id = "mock"

    def __init__(self, **options: Any) -> None:
        super().__init__(**options)
        self.responses: dict[str, list[Any]] = options.get("responses", {})
        self.prompts: list[tuple[str, str]] = []

    def available(self) -> bool:
        return True

    def _next(self, role: str, prompt: str) -> Any:
        self.prompts.append((role, prompt))
        queue = self.responses.get(role) or []
        if not queue:
            raise ProviderError(f"mock provider has no queued response for role={role}")
        self.record(role, input_tokens=len(prompt) // 4, output_tokens=16)
        return queue.pop(0)

    def see_video(self, path: Path, prompt: str, schema: type[ModelT]) -> ModelT:
        return self._next("vision", f"{path}:{prompt}")

    def act(self, prompt: str, schema: type[ModelT] | None = None) -> Any:
        return self._next("agent", prompt)

    def judge(self, prompt: str, schema: type[ModelT]) -> ModelT:
        return self._next("judge", prompt)
