"""Gemini provider: the `vision` role (video understanding), plus `agent`/`judge`
via the same structured-output mechanism.

Uses the `google-genai` SDK directly (not LangChain) because video upload is a
vision-specific operation `providers.base.Provider.see_video` needs regardless
of which text model ends up judging/acting — this provider exists primarily to
serve ingest.py's need to watch a video, not to compete with
`LangChainFallbackProvider` for the judge/agent roles (though it can serve
those too, standalone, like `AnthropicProvider` can).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from autotester.providers.base import Provider, ProviderError

ModelT = TypeVar("ModelT", bound=BaseModel)

DEFAULT_MODEL = "gemini-3.6-flash"


class GeminiProvider(Provider):
    """Wraps `google.genai.Client`. Never receives a raw secret — callers pass
    prompts containing `{{SECRET:KEY}}` placeholders only, per the base contract."""

    id = "gemini"

    def __init__(self, **options: Any) -> None:
        super().__init__(**options)
        self._api_key = (
            options.get("api_key")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        self._model = options.get("model", DEFAULT_MODEL)

    def available(self) -> bool:
        return bool(self._api_key)

    def see_video(self, path: Path, prompt: str, schema: type[ModelT]) -> ModelT:
        return self._structured(prompt, schema, role="vision", video_path=path)

    def act(self, prompt: str, schema: type[ModelT] | None = None) -> Any:
        return self._structured(prompt, schema, role="agent")

    def judge(
        self, prompt: str, schema: type[ModelT], images: list[Path] | None = None
    ) -> ModelT:
        return self._structured(prompt, schema, role="judge", images=images)

    def _structured(
        self, prompt: str, schema: type[ModelT] | None, *, role: str,
        video_path: Path | None = None, images: list[Path] | None = None,
    ) -> ModelT:
        if not self.available():
            raise ProviderError("GEMINI_API_KEY/GOOGLE_API_KEY is not set")
        if schema is None:
            raise ProviderError(f"{self.id} requires a schema for structured output (role={role})")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self._api_key)
        contents: list[Any] = []
        if video_path is not None:
            contents.append(client.files.upload(file=str(video_path)))
        for path in images or []:
            if path.exists():
                contents.append(client.files.upload(file=str(path)))
        contents.append(prompt)

        response = client.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=schema
            ),
        )
        if response.parsed is None:
            raise ProviderError(f"{self.id}: structured output did not parse (role={role})")
        usage = response.usage_metadata
        self.record(
            role,
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
        )
        return response.parsed
