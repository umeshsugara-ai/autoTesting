"""Regression suite for AT-598 (double base64, UTF-16 hex needles) and
AT-607 (documented encoding-coverage boundaries: the <8-char floor and the
8-char base32 offset-1 gap) -- both filed against
`qa/verdicts/at347-352-356-redact-fold.md`'s probe matrix.

Split into its own file rather than folded into `test_redact_obfuscation.py`
(AT-352/347/356's suite) because this is a distinct fix unit (at598-607) with
its own falsification evidence, and to keep that file from re-approaching the
C2 300-line cap. Synthetic fake secrets only -- never a real credential, and
this suite never reads or writes `.env`.
"""

from __future__ import annotations

import base64
import json
import random
import uuid

import pytest

from autotester.core.redact import Redactor, assert_no_raw_secrets

# Fake secrets only (per the fix brief): a realistic-length one for the new
# needle families, and an exactly-8-char one for the documented boundary.
CRED = "hunter2-super-secret"
EIGHT_CHAR = "hunter22"
SEVEN_CHAR = "hunter2"


# -- AT-598: double base64 (b64(b64(secret))) --------------------------------


def _double_b64(secret: str, *, outer_urlsafe: bool = False) -> str:
    inner = base64.b64encode(secret.encode())
    encoder = base64.urlsafe_b64encode if outer_urlsafe else base64.b64encode
    return encoder(inner).decode("ascii")


@pytest.mark.parametrize(
    "label,payload",
    [
        ("isolated-std-outer", _double_b64(CRED)),
        ("isolated-urlsafe-outer", _double_b64(CRED, outer_urlsafe=True)),
        ("prefix_suffix", f"prefix_{_double_b64(CRED)}_suffix"),
        ("token_end", f"tok_{_double_b64(CRED)}_end"),
    ],
)
def test_contains_folded_catches_double_base64(label: str, payload: str) -> None:
    # AT-598: at347 cycle-2 probe found 5/5 secret lengths missed -- the
    # needle search only ever looked one level of UTF-8 encoding deep.
    redactor = Redactor({"DEMO": CRED})
    assert redactor.contains_folded(payload), f"{label} bypassed contains_folded"


@pytest.mark.parametrize(
    "label,payload",
    [
        ("isolated-std-outer", _double_b64(CRED)),
        ("isolated-urlsafe-outer", _double_b64(CRED, outer_urlsafe=True)),
        ("prefix_suffix", f"prefix_{_double_b64(CRED)}_suffix"),
    ],
)
def test_assert_no_raw_secrets_blocks_double_base64(label: str, payload: str) -> None:
    with pytest.raises(ValueError, match="raw secret"):
        assert_no_raw_secrets(payload, [CRED])


@pytest.mark.parametrize("prefix_len", [0, 1, 2])
def test_contains_folded_catches_double_base64_at_outer_byte_alignment(prefix_len: int) -> None:
    # The outer encoding pass gets the same 3-offset alignment immunity a
    # single level already has, via the shared `_alignment_needles` helper --
    # a double-encoded blob co-encoded with neighbouring bytes at the OUTER
    # layer is still caught, not only the isolated double-encoding.
    inner = base64.b64encode(CRED.encode())
    prefix = b"x" * prefix_len
    combined = base64.b64encode(prefix + inner).decode()
    redactor = Redactor({"DEMO": CRED})
    assert redactor.contains_folded(combined), f"outer prefix_len={prefix_len} bypassed"


# -- AT-598: hex of the UTF-16-LE / UTF-16-BE byte encodings -----------------


@pytest.mark.parametrize(
    "label,payload",
    [
        ("le-lower", CRED.encode("utf-16-le").hex()),
        ("le-upper", CRED.encode("utf-16-le").hex().upper()),
        ("be-lower", CRED.encode("utf-16-be").hex()),
        ("be-upper", CRED.encode("utf-16-be").hex().upper()),
        ("le-adjacent", f"prefix_{CRED.encode('utf-16-le').hex()}_suffix"),
        ("be-adjacent", f"prefix_{CRED.encode('utf-16-be').hex()}_suffix"),
    ],
)
def test_contains_folded_catches_utf16_hex(label: str, payload: str) -> None:
    # AT-598: at347 cycle-2 probe found 10/10 misses -- realistic in
    # Windows/PowerShell logs, which are UTF-16 internally, and the needle
    # search only ever hex-encoded the UTF-8 bytes.
    redactor = Redactor({"DEMO": CRED})
    assert redactor.contains_folded(payload), f"{label} bypassed contains_folded"


@pytest.mark.parametrize(
    "label,payload",
    [
        ("le", CRED.encode("utf-16-le").hex()),
        ("be", CRED.encode("utf-16-be").hex()),
    ],
)
def test_assert_no_raw_secrets_blocks_utf16_hex(label: str, payload: str) -> None:
    text = f"Here is some context: {payload} -- please proceed."
    with pytest.raises(ValueError, match="raw secret"):
        assert_no_raw_secrets(text, [CRED])


# -- AT-607: documented boundaries, pinned so they cannot silently widen ----


def test_seven_char_secret_gets_no_encoding_protection_by_design() -> None:
    # AT-607 part (a): MIN_FOLDED_LEN=8 gates the exact-encoding search on the
    # RAW secret's length; a 7-char secret is below the floor and gets none
    # of base64/base32/hex/double-b64/utf16-hex protection. This is the
    # accepted, documented floor (AT-002/AT-352 cycle 3) -- pinned here so a
    # future change either keeps it or updates redact.py's docstring
    # deliberately, not by accident.
    redactor = Redactor({"DEMO": SEVEN_CHAR})
    for payload in (
        base64.b64encode(SEVEN_CHAR.encode()).decode(),
        base64.b32encode(SEVEN_CHAR.encode()).decode(),
        SEVEN_CHAR.encode().hex(),
    ):
        assert not redactor.contains_folded(payload), f"{payload!r} unexpectedly caught"
    assert_no_raw_secrets(base64.b64encode(SEVEN_CHAR.encode()).decode(), [SEVEN_CHAR])


def test_eight_char_secret_base32_offset_one_is_a_known_uncovered_gap() -> None:
    # AT-607 part (b): documented in redact.py::assert_no_raw_secrets rather
    # than fixed (route (b) of the two the issue accepts) -- an EXACTLY
    # 8-character secret co-encoded into one base32 blob with exactly 1 byte
    # of unrelated prefix material lands at byte-alignment offset 1 (mod 5),
    # where `_alignment_needles`' coarse group-drop leaves no non-empty core
    # (both of the resulting 2 groups are edges). This test PINS the gap as
    # it exists today: if a future change closes it, this assertion should be
    # flipped (to `is_caught`) in the same commit that fixes it, not left
    # silently passing on a gap that no longer exists.
    prefix = b"x" * 1
    combined = base64.b32encode(prefix + EIGHT_CHAR.encode()).decode()
    redactor = Redactor({"DEMO": EIGHT_CHAR})
    assert not redactor.contains_folded(combined), (
        "offset-1 base32 case now caught -- update this pin (and the "
        "redact.py docstring) to reflect the fix, do not just relax the "
        "assertion"
    )
    assert_no_raw_secrets(combined, [EIGHT_CHAR])  # must not raise: same known gap


@pytest.mark.parametrize("offset", [0, 2, 3, 4])
def test_eight_char_secret_base32_is_caught_at_every_other_offset(offset: int) -> None:
    # The gap is specific to offset 1, not the whole alignment mechanism --
    # pin that offsets 0, 2, 3, 4 all still work for an 8-char secret, so a
    # regression that widens the gap (rather than narrows it) is caught here.
    prefix = b"x" * offset
    combined = base64.b32encode(prefix + EIGHT_CHAR.encode()).decode()
    redactor = Redactor({"DEMO": EIGHT_CHAR})
    assert redactor.contains_folded(combined), f"offset={offset} unexpectedly missed"


# -- False-positive guard: prose, JSON, hex-looking IDs ----------------------


def test_new_needle_families_do_not_false_positive_on_benign_corpus() -> None:
    # The two new needle families (double-b64 alignment, utf16-hex) widen the
    # substring search space; this guards against them turning ordinary
    # prose, JSON payloads, UUIDs, or hex-looking ids into false positives.
    rng = random.Random(2026_09_26)

    def rand_hex(n: int) -> str:
        return "".join(rng.choice("0123456789abcdef") for _ in range(n))

    def rand_b64(n: int) -> str:
        return base64.b64encode(bytes(rng.getrandbits(8) for _ in range(n))).decode()

    prose = (
        "You are grading a student essay for clarity and structure. "
        "Respond with a JSON object containing a score and a short rationale. "
    ) * 40
    parts = [prose]
    for _ in range(150):
        parts.append(str(uuid.uuid4()))
        parts.append(rand_hex(64))
        parts.append(rand_b64(48))
        parts.append(json.dumps(
            {"id": str(uuid.uuid4()), "token": rand_hex(32), "blob": rand_b64(40)}
        ))
    corpus = "\n".join(parts)

    redactor = Redactor({"DEMO": CRED, "SHORT": EIGHT_CHAR})
    assert not redactor.contains_folded(corpus)
    assert_no_raw_secrets(corpus, [CRED, EIGHT_CHAR])  # must not raise
