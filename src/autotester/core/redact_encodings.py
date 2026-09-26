"""Exact encoded-spelling search: precompute how a declared secret would look
base64/base32/hex-encoded, so a caller can search RAW (unfolded) text for
those exact substrings.

Split out of `core.redact_fold` (AT-352 cycle 2; that module was about to
cross the C2 300-line cap adding this) because it is the opposite direction
from everything else there: `redact_fold` widens by DECODING/folding the
candidate TEXT; this module widens by ENCODING the SECRET and searching for
the result, which is what makes it immune to adjacency (see
`_declared_secret_encodings`'s docstring). `core.redact_fold` imports the one
name it needs from here; nothing outside that pair imports this module.
"""

from __future__ import annotations

import base64
from collections.abc import Callable


def _base64_alignment_needles(secret_bytes: bytes, encoder: Callable[[bytes], bytes]) -> list[str]:
    r"""3 alignment-offset substrings of `encoder(secret_bytes)`, each
    guaranteed to appear byte-for-byte in `encoder(anything containing
    secret_bytes as a contiguous run)` regardless of what the neighbouring
    bytes actually ARE -- only their COUNT (the byte offset mod 3) matters,
    because every base64 output character is a function of exactly the 3-byte
    group it belongs to, never of any other byte.

    For offset `o` in `(0, 1, 2)`: pad `secret_bytes` with `o` leading zero
    bytes standing in for "whatever `o` unknown bytes precede the secret at
    runtime", then with just enough trailing zero bytes to reach a multiple
    of 3 (so `encoder` never emits `=` padding, which would only be correct
    if the secret were the END of the real message). The leading 4-character
    group is dropped whenever `o > 0` (it mixes bits from the unknown prefix
    bytes) and the trailing 4-character group is dropped whenever trailing
    padding was added (it mixes bits from the unknown suffix bytes). Coarse
    -- an entire 4-character group is discarded even where only 1-2 of its
    characters are actually affected -- deliberately: correctness over a
    couple of extra characters of needle length.

    AT-352 cycle 2. Named "alignment offsets" in the fix brief; this is the
    same technique YARA's `base64` string modifier uses to find a known
    plaintext inside a base64 blob without knowing what surrounds it.
    """
    needles = []
    for offset in (0, 1, 2):
        padded = (b"\x00" * offset) + secret_bytes
        tail_pad = (-len(padded)) % 3
        padded += b"\x00" * tail_pad
        encoded = encoder(padded).decode("ascii")
        start = 4 if offset else 0
        end = len(encoded) - 4 if tail_pad else len(encoded)
        core = encoded[start:end]
        if core:
            needles.append(core)
    return needles


def declared_secret_encodings(value: str) -> list[str]:
    """Every exact encoded spelling of one declared secret worth searching
    for as a literal substring of raw, unfolded text: base64 (standard and
    URL-safe, at each of the 3 possible byte-alignment offsets, so padding
    never appears -- see `_base64_alignment_needles`), base32, and hex
    (upper and lower).

    AT-352 cycle 2: searching for the SECRET's own precomputed encodings is
    exact and immune to adjacency -- unlike scanning `text` for base64/
    base32/hex-SHAPED runs and trying to decode them (cycle 1's approach,
    which lived in `core.redact_fold._obfuscated_spellings` and was removed),
    which over-matched into neighbouring alphanumeric characters (a filename's
    `_`/`-`, a token prefix/suffix) into one oversized run that decoded as
    nothing, so the credential escaped both `Redactor.contains_folded` and
    `assert_no_raw_secrets`. Deliberately NOT folded/case-normalised before
    the substring check: base64 is case-significant by construction (`A` and
    `a` encode different bits), so folding the candidate text first would
    destroy the very encoding it is trying to match.
    """
    raw = value.encode("utf-8")
    needles: list[str] = [
        *_base64_alignment_needles(raw, base64.b64encode),
        *_base64_alignment_needles(raw, base64.urlsafe_b64encode),
    ]
    b32 = base64.b32encode(raw).decode("ascii")
    needles.extend((b32, b32.rstrip("=")))
    hexed = raw.hex()
    needles.extend((hexed, hexed.upper()))
    return [needle for needle in needles if needle]
