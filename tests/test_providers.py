"""Provider registry + AnthropicProvider plumbing. No live network call here —
the anthropic SDK is imported lazily inside `_structured`, so these tests never
need a real API key or a socket (AL's no-fire list)."""

from __future__ import annotations

import pytest

from autotester import providers
from autotester.providers.anthropic import AnthropicProvider
from autotester.providers.base import ProviderError


def test_anthropic_registered_and_resolvable() -> None:
    provider = providers.get("anthropic")
    assert isinstance(provider, AnthropicProvider)
    assert provider.id == "anthropic"


def test_available_reflects_api_key_presence() -> None:
    assert AnthropicProvider(api_key="sk-test-key").available() is True
    assert AnthropicProvider(api_key=None).available() is False


def test_act_without_a_key_raises_without_touching_the_network() -> None:
    provider = AnthropicProvider(api_key=None)
    with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY"):
        provider.act("do something")


def test_act_without_a_schema_raises() -> None:
    provider = AnthropicProvider(api_key="sk-test-key")
    with pytest.raises(ProviderError, match="requires a schema"):
        provider.act("do something")
