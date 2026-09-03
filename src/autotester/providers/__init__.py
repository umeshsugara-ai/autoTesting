"""Provider registry. Stages ask for a role; this module resolves the vendor."""

from __future__ import annotations

from typing import Any

from autotester.providers.base import Provider, ProviderError, Unsupported
from autotester.providers.mock import MockProvider

_REGISTRY: dict[str, type[Provider]] = {"mock": MockProvider}


def register(provider_id: str, cls: type[Provider]) -> None:
    """Add a provider implementation. Called by each vendor module on import."""
    _REGISTRY[provider_id] = cls


def get(provider_id: str, **options: Any) -> Provider:
    """Instantiate a provider by id, raising a clear error when unknown."""
    try:
        cls = _REGISTRY[provider_id]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY))
        raise ProviderError(f"unknown provider '{provider_id}'; known: {known}") from None
    return cls(**options)


def available_ids() -> list[str]:
    """Providers whose credentials or binaries are actually present."""
    ready = []
    for provider_id, cls in _REGISTRY.items():
        try:
            if cls().available():
                ready.append(provider_id)
        except Exception:
            continue
    return sorted(ready)


__all__ = ["Provider", "ProviderError", "Unsupported", "available_ids", "get", "register"]
