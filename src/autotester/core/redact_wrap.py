"""Whitespace normalisation for the exact-encoding needle search.

AT-599: `redact_encodings.declared_secret_encodings` needles are literal,
unfolded substrings of an encoded secret -- exactly what makes them immune to
whatever sits next to them (AT-352 cycle 2). That same literalness makes them
blind to a needle broken by ANY whitespace, not only a line break: a
`\n`/`\r\n` inserted mid-token, MIME's fixed 76-character line wrapping once
the encoded form is longer than that, a single space or tab dropped mid-token,
or a newline followed by indentation (an RFC 5322 folded header, an indented
log dump, a YAML/PEM block) all put one or more bytes in the middle of the
needle that the needle itself does not contain, and a literal substring
search cannot see across any of them -- reproduced as 48 misses for a
newline-split needle and 2 for MIME-wrapped hex of a 40-char secret (checker
probe, at347 cycle 2), and separately for space/tab/indent splits (checker
probe, cycle 1 of this unit: newline caught, space and newline+4-space indent
both missed).

Split out of `core.redact_fold` (which was already at 292 of its 300-line C2
cap) rather than folded in inline, for the same reason `redact_encodings` was
split out in AT-352 cycle 2: a distinct concern -- this one widens by
stripping whitespace from the TEXT side, never the secret -- with its own
docstring and its own tests (`tests/test_redact_wrap_perf.py`).
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from autotester.core.redact_encodings import declared_secret_encodings

_WHITESPACE_RE = re.compile(r"\s+")


def contains_wrapped_encoding(
    text: str, widened_secrets: Sequence[tuple[str, str]], min_raw_len: int,
) -> bool:
    r"""True when a declared secret's exact encoding (base64/base32/hex, from
    `declared_secret_encodings`) is present in `text` once every run of
    whitespace is removed -- catching a needle split by a single mid-token
    newline, by MIME's fixed-width wrapping, by a bare space or tab, or by a
    newline followed by indentation (RFC 5322 header folding, an indented log
    dump, a YAML/PEM block), none of which the unwrapped exact search in
    `redact_fold._contains_folded_secret` can see (AT-599).

    Widened from line-breaks-only to `\s+` in cycle 2: a checker's repro
    showed a needle split by a plain space or by a newline-plus-indent both
    still evaded the line-break-only strip, because neither is a `\r`/`\n`
    itself -- the earlier version searched for `\r\n|\r|\n` and left every
    other whitespace character untouched, so a run of `\n    ` (newline then
    4-space indent) removed only the newline and left the spaces splitting the
    needle in two.

    Deliberately unscoped to runs that already look encoded: every whitespace
    run in `text` is collapsed away, not only ones sitting inside something
    that already looks like base64/hex, because a wrapped needle by
    definition does not look like one yet on either side of the split. This
    does not widen the false-positive surface the way folding does -- the
    needle stays an exact, case-significant substring of a real secret's own
    computed encoding, so an accidental collision with ordinary wrapped prose
    needs the exact needle bytes to reappear right at the join, which is what
    `test_line_wrapped_benign_prose_has_no_false_positive` and
    `test_space_separated_benign_prose_has_no_false_positive` guard.

    Cheap on the common case: a `text` with no whitespace at all returns
    `False` before doing any work, so a caller that always asks this question
    pays nothing extra on the vast majority of real payloads.
    """
    if not _WHITESPACE_RE.search(text):
        return False
    unwrapped = _WHITESPACE_RE.sub("", text)
    return any(
        needle in unwrapped
        for raw_value, _folded in widened_secrets
        if len(raw_value) >= min_raw_len
        for needle in declared_secret_encodings(raw_value)
    )
