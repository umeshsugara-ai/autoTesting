"""`GeminiProvider._config`'s model-version detection and the 3.x-only
settings it gates. Contract: qa/contracts/ingest.md (provider seam), C8.

Split from test_gemini_schema.py (already scoped to the response-schema
sanitiser, AT-230) — this is a different seam: which generation-config
fields a given model string gets, not how a response schema is rendered.
"""

from __future__ import annotations

from autotester.providers.gemini import GeminiProvider, _is_gemini_3
from autotester.schema.observation import VisionOptions

# -- AT-127: the SDK's fully-qualified `models/gemini-3.x` form -------------

def test_is_gemini_3_recognises_the_bare_form() -> None:
    assert _is_gemini_3("gemini-3.6-flash") is True


def test_is_gemini_3_recognises_the_fully_qualified_sdk_form() -> None:
    """AT-127: `client.models.list()` and the SDK's own examples return/accept
    `models/gemini-3.x` — a bare `startswith` silently lost `media_resolution`
    for a provider configured this (entirely legitimate) way."""
    assert _is_gemini_3("models/gemini-3.6-flash") is True


def test_is_gemini_3_rejects_an_older_model_either_way() -> None:
    assert _is_gemini_3("gemini-2.0-flash") is False
    assert _is_gemini_3("models/gemini-2.0-flash") is False


def test_config_applies_media_resolution_for_the_fully_qualified_form() -> None:
    provider = GeminiProvider(api_key="fake-key", model="models/gemini-3.6-flash")
    config = provider._config(None, VisionOptions(media_resolution="high"))
    assert config.media_resolution == "MEDIA_RESOLUTION_HIGH"


def test_config_falls_back_to_temperature_for_an_older_model() -> None:
    provider = GeminiProvider(api_key="fake-key", model="gemini-2.0-flash")
    config = provider._config(None, VisionOptions(temperature=0.2))
    assert config.temperature == 0.2
    assert config.media_resolution is None


# -- AT-126: thinking_level was documented but never applied -----------------

def test_config_applies_thinking_level_for_a_3x_model() -> None:
    """The docstring already promised this ('3.x models take media_resolution
    and a thinking level'); `thinking_config` was never built."""
    provider = GeminiProvider(api_key="fake-key", model="gemini-3.6-flash")
    config = provider._config(None, VisionOptions(thinking_level="high"))
    assert config.thinking_config.thinking_level == "HIGH"


def test_config_thinking_level_follows_the_declared_option() -> None:
    provider = GeminiProvider(api_key="fake-key", model="gemini-3.6-flash")
    config = provider._config(None, VisionOptions(thinking_level="low"))
    assert config.thinking_config.thinking_level == "LOW"


def test_config_does_not_set_thinking_config_for_an_older_model() -> None:
    provider = GeminiProvider(api_key="fake-key", model="gemini-2.0-flash")
    config = provider._config(None, VisionOptions())
    assert config.thinking_config is None
