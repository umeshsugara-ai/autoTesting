"""Identifier generation. The ONLY place ids are minted."""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_HASH_LEN = 12


def content_hash(payload: Any) -> str:
    """Stable 12-char hash of any JSON-serialisable payload.

    Used for immutable, content-addressed objects (sources, cases, scripts).
    Key order is normalised so logically identical payloads hash identically.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:_HASH_LEN]


def file_sha256(path: str | os.PathLike[str]) -> str:
    """Full sha256 of a file's bytes, streamed (videos can be large)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_id(prefix: str, payload: Any) -> str:
    """`<prefix>_<12-char content hash>` — same input always yields the same id."""
    return f"{prefix}_{content_hash(payload)}"


def ulid() -> str:
    """Lexicographically sortable time-ordered id, for runs and results.

    26 chars: 10 of millisecond timestamp + 16 of randomness, Crockford base32.
    """
    timestamp = int(time.time() * 1000)
    randomness = int.from_bytes(os.urandom(10), "big")
    value = (timestamp << 80) | randomness
    chars = []
    for _ in range(26):
        chars.append(_ULID_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def run_id(prefix: str = "run") -> str:
    """`<prefix>_<ulid>` — sortable by creation time."""
    return f"{prefix}_{ulid()}"
