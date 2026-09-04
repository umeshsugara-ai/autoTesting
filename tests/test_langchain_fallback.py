"""LangChain fallback provider. No real network call anywhere in this file --
fake chat-model objects mimic LangChain's `with_structured_output(...,
include_raw=True).invoke(prompt)` shape so the fallback loop is exercised
without a live API key or SDK call."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from autotester import providers
from autotester.providers.base import ProviderError
from autotester.providers.langchain_fallback import LangChainFallbackProvider


class Answer(BaseModel):
    result: str


class FakeRawMessage:
    def __init__(self, usage: dict | None = None) -> None:
        self.usage_metadata = usage


class FakeStructured:
    def __init__(self, parsed, raise_exc, usage) -> None:
        self._parsed, self._raise, self._usage = parsed, raise_exc, usage
        self.invoked_with = None

    def invoke(self, prompt):
        self.invoked_with = prompt
        if self._raise is not None:
            raise self._raise
        return {"parsed": self._parsed, "raw": FakeRawMessage(self._usage)}


class FakeChatModel:
    def __init__(self, parsed=None, raise_exc: Exception | None = None,
                 usage: dict | None = None) -> None:
        self._parsed, self._raise, self._usage = parsed, raise_exc, usage

    def with_structured_output(self, schema, include_raw: bool = False):
        assert include_raw is True
        self.structured = FakeStructured(self._parsed, self._raise, self._usage)
        return self.structured


def chain_of(*tiers: tuple[str, FakeChatModel]) -> list:
    return [(name, (lambda m=model: m)) for name, model in tiers]


# -- registry ------------------------------------------------------------

def test_registered_and_resolvable() -> None:
    provider = providers.get("langchain-fallback", chain=[])
    assert isinstance(provider, LangChainFallbackProvider)
    assert provider.id == "langchain-fallback"


# -- first tier succeeds ---------------------------------------------------

def test_first_tier_success_sets_id_and_records_usage() -> None:
    chain = chain_of(
        ("anthropic", FakeChatModel(parsed=Answer(result="ok"),
                                     usage={"input_tokens": 10, "output_tokens": 5})),
    )
    provider = LangChainFallbackProvider(chain=chain)
    answer = provider.judge("prompt", Answer)

    assert answer.result == "ok"
    assert provider.id == "anthropic"
    assert provider.usage[0].provider == "anthropic"
    assert provider.usage[0].input_tokens == 10
    assert provider.usage[0].output_tokens == 5


# -- AT-049 images are actually attached, not just described in the prompt --

def test_judge_with_no_images_invokes_with_a_plain_string(tmp_path) -> None:
    """Unchanged behavior for every existing caller -- act() and a
    no-images judge() call must never start building multimodal messages."""
    model = FakeChatModel(parsed=Answer(result="ok"))
    provider = LangChainFallbackProvider(chain=chain_of(("gemini", model)))

    provider.judge("plain text prompt", Answer)

    assert model.structured.invoked_with == "plain text prompt"


def test_judge_with_real_images_invokes_with_a_multimodal_message(tmp_path) -> None:
    from langchain_core.messages import HumanMessage

    png = tmp_path / "01-login.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    model = FakeChatModel(parsed=Answer(result="ok"))
    provider = LangChainFallbackProvider(chain=chain_of(("gemini", model)))

    provider.judge("look at this", Answer, images=[png])

    sent = model.structured.invoked_with
    assert isinstance(sent, list) and len(sent) == 1
    assert isinstance(sent[0], HumanMessage)
    assert sent[0].content[0] == {"type": "text", "text": "look at this"}
    assert sent[0].content[1]["type"] == "image_url"
    assert sent[0].content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_judge_skips_an_image_path_that_does_not_exist_on_disk(tmp_path) -> None:
    """Evidence can reference a screenshot that never made it to disk -- the
    call must still go out as a plain string, never crash reading a missing
    file, when every referenced image is missing."""
    missing = tmp_path / "never-written.png"
    model = FakeChatModel(parsed=Answer(result="ok"))
    provider = LangChainFallbackProvider(chain=chain_of(("gemini", model)))

    provider.judge("plain text prompt", Answer, images=[missing])

    assert model.structured.invoked_with == "plain text prompt"


# -- falls through on failure ------------------------------------------------

def test_falls_through_to_second_tier_on_failure() -> None:
    chain = chain_of(
        ("anthropic", FakeChatModel(raise_exc=RuntimeError("401 unauthorized"))),
        ("gemini", FakeChatModel(parsed=Answer(result="fallback worked"))),
    )
    provider = LangChainFallbackProvider(chain=chain)
    answer = provider.judge("prompt", Answer)

    assert answer.result == "fallback worked"
    assert provider.id == "gemini"


def test_falls_through_three_tiers_deep() -> None:
    chain = chain_of(
        ("anthropic", FakeChatModel(raise_exc=RuntimeError("no key"))),
        ("gemini", FakeChatModel(raise_exc=RuntimeError("quota exceeded"))),
        ("ollama", FakeChatModel(parsed=Answer(result="local model answered"))),
    )
    provider = LangChainFallbackProvider(chain=chain)
    answer = provider.act("prompt", Answer)

    assert answer.result == "local model answered"
    assert provider.id == "ollama"


# -- every tier fails ---------------------------------------------------

def test_raises_when_every_tier_fails() -> None:
    chain = chain_of(
        ("anthropic", FakeChatModel(raise_exc=RuntimeError("no key"))),
        ("gemini", FakeChatModel(raise_exc=RuntimeError("quota exceeded"))),
    )
    provider = LangChainFallbackProvider(chain=chain)

    with pytest.raises(ProviderError, match="every configured provider failed"):
        provider.judge("prompt", Answer)


def test_none_parsed_counts_as_a_failure_and_falls_through() -> None:
    chain = chain_of(
        ("anthropic", FakeChatModel(parsed=None)),
        ("gemini", FakeChatModel(parsed=Answer(result="ok"))),
    )
    provider = LangChainFallbackProvider(chain=chain)
    answer = provider.judge("prompt", Answer)

    assert answer.result == "ok"
    assert provider.id == "gemini"


# -- edge conditions ---------------------------------------------------

def test_available_false_when_chain_is_empty() -> None:
    provider = LangChainFallbackProvider(chain=[])
    assert provider.available() is False


def test_call_with_no_chain_raises_without_a_network_call() -> None:
    provider = LangChainFallbackProvider(chain=[])
    with pytest.raises(ProviderError, match="no configured provider"):
        provider.judge("prompt", Answer)


def test_act_without_a_schema_raises() -> None:
    provider = LangChainFallbackProvider(chain=chain_of(("anthropic", FakeChatModel())))
    with pytest.raises(ProviderError, match="requires a schema"):
        provider.act("prompt")


def test_missing_usage_metadata_defaults_to_zero() -> None:
    chain = chain_of(("gemini", FakeChatModel(parsed=Answer(result="ok"), usage=None)))
    provider = LangChainFallbackProvider(chain=chain)
    provider.judge("prompt", Answer)

    assert provider.usage[0].input_tokens == 0
    assert provider.usage[0].output_tokens == 0
