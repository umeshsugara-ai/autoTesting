"""Secret redaction. Every log line and stored artifact passes through here.

The rule this module exists to enforce: a secret VALUE must never reach a model
prompt, a log file, or an artifact on disk. Only placeholders travel.

Folding internals (Unicode normalisation, homoglyphs, encoded/reversed
spellings) live in `core.redact_fold` -- split out so this file stays under
the C2 line cap; every name anything outside this pair imports is re-exported
here unchanged, so `from autotester.core.redact import ...` keeps working.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from autotester.core.redact_fold import (
    BIDI_OVERRIDES,
    MIN_FOLDED_LEN,
    _contains_folded_secret,
    fold_credential,
)

__all__ = [
    "BIDI_OVERRIDES",
    "MASK",
    "MIN_FOLDED_LEN",
    "PLACEHOLDER_RE",
    "Redactor",
    "assert_no_raw_secrets",
    "fold_credential",
    "has_placeholder",
    "placeholder_keys",
]

MASK = "[REDACTED]"
PLACEHOLDER_RE = re.compile(r"\{\{SECRET:([A-Z0-9_]+)\}\}")


class Redactor:
    """Replaces known secret values with `[REDACTED]` anywhere they appear.

    Construct once per run from the loaded environment, then pass every string
    that is about to be logged, prompted, or persisted through `scrub`.

    There is deliberately no minimum length: these are known-exact declared
    values, not heuristic guesses. A three-character password is a bad
    password, but leaking it is still a leak (checker finding AT-002).
    """

    def __init__(self, secrets: dict[str, str]) -> None:
        # Longest first, so a value that contains another is masked whole.
        self._values = sorted((v for v in secrets.values() if v), key=len, reverse=True)
        self._keys_by_value = {v: k for k, v in secrets.items()}
        self._folded = [
            folded for folded in (fold_credential(v) for v in self._values)
            if len(folded) >= MIN_FOLDED_LEN
        ]

    def scrub(self, text: str) -> str:
        """Return `text` with every known secret value masked."""
        for value in self._values:
            if value in text:
                key = self._keys_by_value.get(value, "")
                text = text.replace(value, f"{MASK}:{key}" if key else MASK)
        return text

    def scrub_obj(self, obj: Any) -> Any:
        """Recursively scrub strings inside dicts, lists, and tuples."""
        if isinstance(obj, str):
            return self.scrub(obj)
        if isinstance(obj, dict):
            return {k: self.scrub_obj(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return type(obj)(self.scrub_obj(v) for v in obj)
        return obj

    def is_clean(self, text: str) -> bool:
        """True when no known secret value appears in `text`, byte for byte."""
        return not any(value in text for value in self._values)

    def contains_folded(self, text: str) -> bool:
        """True when a secret appears in `text` once both sides are folded
        (AT-339), including through an encoded or reversed spelling (AT-352)
        such as base64, hex, HTML entities, double percent-encoding, or plain
        reversal -- see `redact_fold._contains_folded_secret`. Deliberately
        separate from `is_clean`, and NOT used by `scrub`: you cannot mask a
        transform, because the literal bytes are not there to replace. This
        answers the guard's question -- "could a reader recover a credential
        from what we are about to store?" -- which is a different question
        from redaction's."""
        return _contains_folded_secret(text, self._folded)

    def assert_clean(self, text: str) -> None:
        """Hard gate: raise if a known secret value survives in `text` even
        after `scrub` (D-041 RT6) -- the last check before something is
        persisted. Reuses this Redactor's own loaded values, so a caller
        never has to hold the raw secrets separately just to gate on them."""
        assert_no_raw_secrets(text, self._values)


def placeholder_keys(text: str) -> list[str]:
    """Secret keys referenced as `{{SECRET:KEY}}` inside `text`."""
    return PLACEHOLDER_RE.findall(text)


def has_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_RE.search(text))


def assert_no_raw_secrets(text: str, secrets: Iterable[str]) -> None:
    """Raise if a raw secret value is present, or if `text` carries one in a
    folded, encoded, or reversed spelling (AT-347). Used as a hard gate before
    prompting -- this is the ONE gate a folded credential reached unnoticed
    (`browser/secrets.py::guard_prompt`'s only caller path): the UI intake
    door already folds via `Redactor.contains_folded`, this door did not.

    The exact check is floorless: any non-empty declared value counts,
    regardless of length (AT-002). The widened check applies `MIN_FOLDED_LEN`
    the same way `Redactor` does, so a short secret does not start refusing
    ordinary text that merely contains its letters.
    """
    values = [v for v in secrets if v]
    for value in values:
        if value in text:
            raise ValueError("refusing to proceed: raw secret value present in payload")
    folded_secrets = [
        folded for folded in (fold_credential(v) for v in values)
        if len(folded) >= MIN_FOLDED_LEN
    ]
    if _contains_folded_secret(text, folded_secrets):
        raise ValueError(
            "refusing to proceed: raw secret value present in payload "
            "(folded/encoded/reversed match)"
        )
