"""The provider seam. Every model call in the system goes through this interface.

Three roles, three methods. A provider implements what it can and declares the
rest unsupported, so a project can mix Gemini for vision with Anthropic for
judging without any stage knowing which is which.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from autotester.schema.run import ProviderUsage

ModelT = TypeVar("ModelT", bound=BaseModel)


class ProviderError(RuntimeError):
    """Any provider-side failure, normalised so stages handle one exception type."""


class Unsupported(ProviderError):
    """This provider does not serve this role."""


class Provider(ABC):
    """One model vendor, adapted to the three jobs AutoTester needs.

    Implementations must never receive raw secret values: callers pass prompts
    containing `{{SECRET:KEY}}` placeholders only.
    """

    id: str = "base"

    def __init__(self, **options: Any) -> None:
        self.options = options
        self.usage: list[ProviderUsage] = []

    # -- role: vision -------------------------------------------------------
    def see_video(self, path: Path, prompt: str, schema: type[ModelT]) -> ModelT:
        """Watch a video and return a structured reading of it."""
        raise Unsupported(f"{self.id} does not support video understanding")

    # -- role: agent --------------------------------------------------------
    def act(self, prompt: str, schema: type[ModelT] | None = None) -> Any:
        """Reason about browser state and decide the next action or script edit."""
        raise Unsupported(f"{self.id} does not support agent actions")

    # -- role: judge --------------------------------------------------------
    def judge(
        self, prompt: str, schema: type[ModelT], images: list[Path] | None = None
    ) -> ModelT:
        """Grade evidence against a rubric in a fresh context. `images`, when
        given, are real screenshot files the judge must actually see (not
        just their filenames in `prompt`) — AT-049: a judge that only ever
        reads evidence *descriptions* is grading blind, however plausible
        its reasoning about a filename sounds."""
        raise Unsupported(f"{self.id} does not support judging")

    # -- shared -------------------------------------------------------------
    @abstractmethod
    def available(self) -> bool:
        """True when credentials/binaries for this provider are present."""

    def record(self, role: str, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Accumulate usage so a run can report its cost."""
        for entry in self.usage:
            if entry.role == role:
                entry.calls += 1
                entry.input_tokens += input_tokens
                entry.output_tokens += output_tokens
                return
        self.usage.append(
            ProviderUsage(
                provider=self.id,
                role=role,
                calls=1,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        )
