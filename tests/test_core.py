"""Core utility tests. Redaction is a security control, so it is tested hardest."""

from __future__ import annotations

import time

import pytest

from autotester.core.ids import content_hash, content_id, run_id, ulid
from autotester.core.redact import (
    MASK,
    Redactor,
    assert_no_raw_secrets,
    fold_credential,
    has_placeholder,
    placeholder_keys,
)

# Synthetic fake secret used throughout this repo's fold-coverage tests/evidence
# (AT-339/AT-345/AT-346/AT-351) -- not a real credential.
CRED = "ZEBRA_QUILT_APIKEY_31"


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


def test_redactor_masks_even_very_short_declared_values() -> None:
    # AT-002: a declared value is known-exact, so no length floor applies.
    redactor = Redactor({"X": "ab"})
    assert "ab" not in redactor.scrub("token=ab")
    assert redactor.scrub("") == ""
    assert Redactor({"EMPTY": ""}).scrub("nothing to mask") == "nothing to mask"


def test_placeholder_helpers_find_secret_keys() -> None:
    text = "fill {{SECRET:PATHLYNKS_EMAIL}} then {{SECRET:PATHLYNKS_PASSWORD}}"
    assert has_placeholder(text)
    assert placeholder_keys(text) == ["PATHLYNKS_EMAIL", "PATHLYNKS_PASSWORD"]


def test_assert_no_raw_secrets_blocks_a_leaking_prompt() -> None:
    assert_no_raw_secrets("safe {{SECRET:PW}}", ["hunter2trombone"])
    with pytest.raises(ValueError, match="raw secret"):
        assert_no_raw_secrets("password is hunter2trombone", ["hunter2trombone"])


def _interleave(text: str, mark: str) -> str:
    return mark.join(text)


def test_fold_credential_strips_visible_combining_marks_after_decomposition() -> None:
    # AT-356: U+0301 (combining acute) and U+0335 (combining short stroke
    # overlay) interleaved between every character render as a struck-through
    # or accented but perfectly readable credential in a real browser. Neither
    # is Default_Ignorable (unlike AT-351's U+034F/variation selectors), so
    # they must be handled by NFKD-decompose-then-strip-Mn, not by
    # `_is_ignorable`.
    plain_fold = fold_credential(CRED)
    assert fold_credential(_interleave(CRED, "́")) == plain_fold
    assert fold_credential(_interleave(CRED, "̵")) == plain_fold


def test_fold_credential_keeps_precomposed_and_decomposed_accents_symmetric() -> None:
    # AT-351's own scenario must stay fixed: a precomposed accented stored
    # value and the same value spelled with a decomposed combining accent
    # still fold identically (both now fold to the bare letter, which is
    # STRONGER than AT-351's original "both fold to the accented letter"
    # resolution, but the equality -- the property AT-351 needed -- holds).
    precomposed = "CAFÉ_QUILT_APIKEY_31"  # accented E precomposed
    decomposed = "CAFÉ_QUILT_APIKEY_31"  # E + combining acute
    assert fold_credential(precomposed) == fold_credential(decomposed)


@pytest.mark.parametrize(
    "label,payload",
    [
        ("base64", __import__("base64").b64encode(CRED.encode()).decode()),
        ("base32", __import__("base64").b32encode(CRED.encode()).decode()),
        ("hex", __import__("binascii").hexlify(CRED.encode()).decode()),
        ("html-dec-entities", "".join(f"&#{ord(c)};" for c in CRED)),
        ("html-hex-entities", "".join(f"&#x{ord(c):X};" for c in CRED)),
        ("double-percent", "".join(f"%25{ord(c):02X}" for c in CRED)),
        ("plain-reversed", CRED[::-1]),
    ],
)
def test_contains_folded_catches_encoded_and_reversed_spellings(label: str, payload: str) -> None:
    # AT-352: each of these six spellings used to sail past `contains_folded`
    # -- the UI intake door -- because it folded only the literal text.
    redactor = Redactor({"DEMO_PASSWORD": CRED})
    assert redactor.contains_folded(payload), f"{label} bypassed contains_folded"


@pytest.mark.parametrize(
    "label,payload",
    [
        ("base64", __import__("base64").b64encode(CRED.encode()).decode()),
        ("base32", __import__("base64").b32encode(CRED.encode()).decode()),
        ("hex", __import__("binascii").hexlify(CRED.encode()).decode()),
        ("html-dec-entities", "".join(f"&#{ord(c)};" for c in CRED)),
        ("html-hex-entities", "".join(f"&#x{ord(c):X};" for c in CRED)),
        ("double-percent", "".join(f"%25{ord(c):02X}" for c in CRED)),
        ("plain-reversed", CRED[::-1]),
        ("combining-acute", _interleave(CRED, "́")),
        ("combining-short-stroke", _interleave(CRED, "̵")),
    ],
)
def test_assert_no_raw_secrets_blocks_obfuscated_spelling_in_prompt_text(
    label: str, payload: str,
) -> None:
    # AT-347: assert_no_raw_secrets is the hard gate before a model prompt
    # (browser/secrets.py::guard_prompt's only caller path) and was never
    # taught to fold, so any of these spellings reached an external provider
    # verbatim. Embedded inside a larger sentence, matching how a real prompt
    # looks -- a bare payload alone is not the realistic caller shape.
    text = f"Here is some context: {payload} -- please proceed."
    with pytest.raises(ValueError, match="raw secret"):
        assert_no_raw_secrets(text, [CRED])


def test_assert_no_raw_secrets_does_not_false_positive_on_ordinary_prose() -> None:
    # The widened check must not turn every unrelated model prompt into a
    # run-killing exception -- the false-positive-rate concern AT-347's own
    # issue text raised. MIN_FOLDED_LEN and the byte-level word-boundary
    # requirement of the actual secret keep ordinary text clean.
    prose = (
        "You are grading a student essay for clarity and structure. "
        "Respond with a JSON object containing a score and a short rationale."
    ) * 5
    assert_no_raw_secrets(prose, [CRED])  # must not raise


def test_assert_no_raw_secrets_short_secret_stays_floorless_on_exact_match() -> None:
    # AT-002, preserved: MIN_FOLDED_LEN only gates the WIDENED (folded/
    # obfuscated) check. A short secret is still refused byte-exact.
    assert_no_raw_secrets("nothing secret here", ["ab"])
    with pytest.raises(ValueError, match="raw secret"):
        assert_no_raw_secrets("value=ab", ["ab"])
