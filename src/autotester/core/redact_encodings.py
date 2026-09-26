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


# AT-352 cycle 2 gave base64 exactly the treatment `_alignment_needles` below
# implements (as `_base64_alignment_needles`, generalised into this shared
# form in cycle 3) but left base32 with none -- `declared_secret_encodings`
# computed only the isolated `base64.b32encode(secret_bytes)`, with zero
# offset handling, so a secret embedded inside a byte stream that is
# base32-encoded AS ONE BLOB together with neighbouring bytes missed at 4 of
# the 5 possible byte offsets (prefix lengths 1-4 mod 5; only offset 0 --
# and its restatement at offset 5 -- happened to line up). A checker caught
# this precisely because the maker's own cycle-2 base32 tests wrapped an
# already-isolated encoding in literal surrounding text
# (`f"SECRET{b32encode(secret)}CODE"`), which any substring search catches
# trivially since the literal wrap never touches the encoding stream -- it
# never exercised alignment at all. Named "alignment offsets" in the fix
# brief; this is the same technique YARA's `base64` string modifier uses to
# find a known plaintext inside a base64 blob without knowing what surrounds
# it, generalised here to any encoding with a fixed byte-group size.
def _alignment_needles(
    secret_bytes: bytes, encoder: Callable[[bytes], bytes], group_bytes: int, group_chars: int,
) -> list[str]:
    r"""`group_bytes` alignment-offset substrings of `encoder(secret_bytes)`,
    each guaranteed to appear byte-for-byte in `encoder(anything containing
    secret_bytes as a contiguous run)` regardless of what the neighbouring
    bytes actually ARE -- only their COUNT (the byte offset mod `group_bytes`)
    matters, because every output character is a function of exactly the
    `group_bytes`-byte group it belongs to, never of any other byte. Base64
    groups 3 bytes into 4 characters (`group_bytes=3, group_chars=4`); base32
    groups 5 bytes into 8 characters (`group_bytes=5, group_chars=8`) -- one
    more possible offset than base64 has, 0-4 instead of 0-2. See the comment
    above this function for why base32 needed this and base64 already had it.

    For offset `o` in `range(group_bytes)`: pad `secret_bytes` with `o`
    leading zero bytes standing in for "whatever `o` unknown bytes precede the
    secret at runtime", then with just enough trailing zero bytes to reach a
    multiple of `group_bytes` (so `encoder` never emits `=` padding, which
    would only be correct if the secret were the END of the real message).
    The leading `group_chars`-character group is dropped whenever `o > 0` (it
    mixes bits from the unknown prefix bytes) and the trailing `group_chars`-
    character group is dropped whenever trailing padding was added (it mixes
    bits from the unknown suffix bytes). Coarse -- an entire group is
    discarded even where only some of its characters are actually affected --
    deliberately: correctness over a few extra characters of needle length.
    """
    needles = []
    for offset in range(group_bytes):
        padded = (b"\x00" * offset) + secret_bytes
        tail_pad = (-len(padded)) % group_bytes
        padded += b"\x00" * tail_pad
        encoded = encoder(padded).decode("ascii")
        start = group_chars if offset else 0
        end = len(encoded) - group_chars if tail_pad else len(encoded)
        core = encoded[start:end]
        if core:
            needles.append(core)
    return needles


def declared_secret_encodings(value: str) -> list[str]:
    """Every exact encoded spelling of one declared secret worth searching
    for as a literal substring of raw, unfolded text: base64 (standard and
    URL-safe, at each of the 3 possible byte-alignment offsets, so padding
    never appears), base32 (standard and lowercase, at each of the 5 possible
    byte-alignment offsets, PLUS the plain isolated encoding of each case with
    and without `=` padding stripped, as an explicit belt-and-suspenders pair
    alongside the alignment needles -- see `_alignment_needles`), and hex
    (upper and lower; unchanged since cycle 2 -- a checker's cycle-3 mixed-
    case-hex claim did not reproduce, so hex is deliberately left alone this
    cycle).

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

    AT-352 cycle 3: base32 got neither case variants nor alignment offsets in
    cycle 2 -- only the isolated uppercase encoding, decoded with `casefold`
    in cycle 1's now-removed scanner but never re-added when the search
    direction flipped. Lowercase base32 is genuinely different bytes from
    uppercase (`base64.b32decode` accepts both only because it casefolds on
    the way IN; there is no such step on the way out), so it needs its own
    needles, generated through the same alignment machinery as the uppercase
    ones (`encoder=lambda b: base64.b32encode(b).lower()`) so a lowercase
    spelling gets the SAME adjacency immunity the uppercase one does, not a
    narrower one.

    AT-606 cycle 1's `@lru_cache` here was unproven and retained raw secrets
    in memory, so cycle 2 drops it -- the real speed-up is `_is_ignorable`'s cache.
    """
    raw = value.encode("utf-8")
    needles: list[str] = [
        *_alignment_needles(raw, base64.b64encode, 3, 4),
        *_alignment_needles(raw, base64.urlsafe_b64encode, 3, 4),
        *_alignment_needles(raw, base64.b32encode, 5, 8),
        *_alignment_needles(raw, lambda b: base64.b32encode(b).lower(), 5, 8),
    ]
    b32_upper = base64.b32encode(raw).decode("ascii")
    b32_lower = b32_upper.lower()
    needles.extend((b32_upper, b32_upper.rstrip("="), b32_lower, b32_lower.rstrip("=")))
    hexed = raw.hex()
    needles.extend((hexed, hexed.upper()))
    return [needle for needle in needles if needle]
