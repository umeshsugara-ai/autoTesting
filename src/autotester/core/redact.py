"""Secret redaction. Every log line and stored artifact passes through here.

The rule this module exists to enforce: a secret VALUE must never reach a model
prompt, a log file, or an artifact on disk. Only placeholders travel.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

MASK = "[REDACTED]"
PLACEHOLDER_RE = re.compile(r"\{\{SECRET:([A-Z0-9_]+)\}\}")

_FOLD_STRIP = re.compile(r"[\s\-_.]+")
MIN_FOLDED_LEN = 8
"""Folded matching needs a floor, because folding is a HEURISTIC widening: it
deliberately matches strings that are not byte-equal to any secret, so a very
short folded value would start refusing ordinary text that merely contains its
letters (`A-B` folds to `ab`, which appears in half the English language).
Exact and variant matching stay floorless, so AT-002 -- "a three-character
password is a bad password, but leaking it is still a leak" -- is untouched:
the real value is still refused at any length, by `is_clean`."""


def fold_credential(text: str) -> str:
    """Casefold and drop separators, so the forms of a credential that anyone
    can reverse in their head compare equal.

    AT-339: a checker put slug `zebra-quilt-apikey-31` past the guard for the
    live value `ZEBRA_QUILT_APIKEY_31`; it became the on-disk directory name,
    every page URL, and text on the home index. `is_clean` is a plain substring
    test, and `_credential_variants` had learned encoding (AT-074) and
    whitespace (AT-071) but never CASE -- because every test in the suite used
    a value that was already lowercase-with-hyphens, the one casing where a
    substring test happens to work.
    """
    return _FOLD_STRIP.sub("", text).casefold()


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
        (AT-339). Deliberately separate from `is_clean`, and NOT used by
        `scrub`: you cannot mask a transform, because the literal bytes are not
        there to replace. This answers the guard's question -- "could a reader
        recover a credential from what we are about to store?" -- which is a
        different question from redaction's."""
        folded = fold_credential(text)
        return any(value in folded for value in self._folded)


def placeholder_keys(text: str) -> list[str]:
    """Secret keys referenced as `{{SECRET:KEY}}` inside `text`."""
    return PLACEHOLDER_RE.findall(text)


def has_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_RE.search(text))


def assert_no_raw_secrets(text: str, secrets: Iterable[str]) -> None:
    """Raise if a raw secret value is present. Used as a hard gate before prompting.

    Any non-empty declared value counts, regardless of length (AT-002).
    """
    for value in secrets:
        if value and value in text:
            raise ValueError("refusing to proceed: raw secret value present in payload")
