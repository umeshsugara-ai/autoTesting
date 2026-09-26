"""Line-wrap normalisation for the exact-encoding needle search.

AT-599: `redact_encodings.declared_secret_encodings` needles are literal,
unfolded substrings of an encoded secret -- exactly what makes them immune to
whatever sits next to them (AT-352 cycle 2). That same literalness makes them
blind to a needle broken across a line: a `\n`/`\r\n` inserted mid-token, or
MIME's fixed 76-character line wrapping once the encoded form is longer than
that, puts a byte in the middle of the needle that the needle itself does not
contain, and a literal substring search cannot see across it -- reproduced as
48 misses for a newline-split needle and 2 for MIME-wrapped hex of a 40-char
secret (checker probe, at347 cycle 2).

Split out of `core.redact_fold` (which was already at 292 of its 300-line C2
cap) rather than folded in inline, for the same reason `redact_encodings` was
split out in AT-352 cycle 2: a distinct concern -- this one widens by
stripping line breaks from the TEXT side, never the secret -- with its own
docstring and its own tests (`tests/test_redact_wrap_perf.py`).
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from autotester.core.redact_encodings import declared_secret_encodings

_LINE_BREAK_RE = re.compile(r"\r\n|\r|\n")


def contains_wrapped_encoding(
    text: str, widened_secrets: Sequence[tuple[str, str]], min_raw_len: int,
) -> bool:
    """True when a declared secret's exact encoding (base64/base32/hex, from
    `declared_secret_encodings`) is present in `text` once every line break is
    removed -- catching a needle split by a single mid-token newline or by
    MIME's fixed-width wrapping, which the unwrapped exact search in
    `redact_fold._contains_folded_secret` cannot see (AT-599).

    Deliberately unscoped to runs that already look encoded: every line break
    in `text` is removed, not only ones sitting inside something that already
    looks like base64/hex, because a wrapped needle by definition does not
    look like one yet on either side of the break. This does not widen the
    false-positive surface the way folding does -- the needle stays an exact,
    case-significant substring of a real secret's own computed encoding, so an
    accidental collision with ordinary line-wrapped prose needs the exact
    needle bytes to reappear right at the join, which is what
    `test_line_wrapped_benign_prose_has_no_false_positive` guards.

    Cheap on the common case: a `text` with no line break at all returns
    `False` before doing any work, so a caller that always asks this question
    pays nothing extra on the vast majority of real payloads.
    """
    if "\n" not in text and "\r" not in text:
        return False
    unwrapped = _LINE_BREAK_RE.sub("", text)
    return any(
        needle in unwrapped
        for raw_value, _folded in widened_secrets
        if len(raw_value) >= min_raw_len
        for needle in declared_secret_encodings(raw_value)
    )
