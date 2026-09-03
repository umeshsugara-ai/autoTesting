"""Core utility tests. Redaction is a security control, so it is tested hardest."""

from __future__ import annotations

import time

import pytest

from autotester.core.ids import content_hash, content_id, run_id, ulid
from autotester.core.redact import (
    MASK,
    Redactor,
    assert_no_raw_secrets,
    has_placeholder,
    placeholder_keys,
)


def test_content_hash_ignores_key_order() -> None:
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})


def test_content_id_is_prefixed_and_stable() -> None:
    first = content_id("case", {"x": 1})
    assert first.startswith("case_")
    assert first == content_id("case", {"x": 1})


def test_ulids_are_unique_and_time_ordered() -> None:
    ids = [ulid() for _ in range(50)]
    assert len(set(ids)) == 50
    assert all(len(i) == 26 for i in ids)
    # Ordering is by the 10-char millisecond prefix; ids from the same
    # millisecond are unordered by design (the remaining 16 chars are random).
    time.sleep(0.002)
    later = ulid()
    assert later[:10] >= max(i[:10] for i in ids)
    assert run_id().startswith("run_")


def test_redactor_masks_secret_values_anywhere_in_text() -> None:
    redactor = Redactor({"PASSWORD": "hunter2trombone"})
    scrubbed = redactor.scrub("login failed for hunter2trombone at /login")
    assert "hunter2trombone" not in scrubbed
    assert MASK in scrubbed
    assert "PASSWORD" in scrubbed


def test_redactor_masks_longest_value_first() -> None:
    redactor = Redactor({"SHORT": "abcd", "LONG": "abcdefgh"})
    scrubbed = redactor.scrub("value=abcdefgh")
    assert "abcdefgh" not in scrubbed
    assert "LONG" in scrubbed


def test_redactor_walks_nested_structures() -> None:
    redactor = Redactor({"TOKEN": "s3cr3t-token"})
    payload = {"headers": {"auth": "Bearer s3cr3t-token"}, "list": ["s3cr3t-token"]}
    scrubbed = redactor.scrub_obj(payload)
    assert "s3cr3t-token" not in str(scrubbed)


def test_redactor_ignores_values_too_short_to_be_secrets() -> None:
    redactor = Redactor({"X": "ab"})
    assert redactor.scrub("ab cd") == "ab cd"


def test_placeholder_helpers_find_secret_keys() -> None:
    text = "fill {{SECRET:PATHLYNKS_EMAIL}} then {{SECRET:PATHLYNKS_PASSWORD}}"
    assert has_placeholder(text)
    assert placeholder_keys(text) == ["PATHLYNKS_EMAIL", "PATHLYNKS_PASSWORD"]


def test_assert_no_raw_secrets_blocks_a_leaking_prompt() -> None:
    assert_no_raw_secrets("safe {{SECRET:PW}}", ["hunter2trombone"])
    with pytest.raises(ValueError, match="raw secret"):
        assert_no_raw_secrets("password is hunter2trombone", ["hunter2trombone"])
