"""The one legitimate WRITE path to the repo-root `.env` (every other module
only reads it via `SecretStore`/`parse_env`). Sets one key's value without
ever returning, logging, or echoing the value itself — the caller passes it
straight through to disk.
"""

from __future__ import annotations

import contextlib
import os
import re
from pathlib import Path

from autotester.browser.secrets import parse_env

_KEY_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


class InvalidEnvValue(ValueError):
    """Refused a key or value that could corrupt or inject a `.env` line."""


def _render_value(value: str) -> str:
    """The `.env` right-hand side that `parse_env` reads back as `value` exactly.

    AT-082: written bare, a value containing ` #`, leading/trailing whitespace,
    or wrapped in quotes came back MANGLED — `_clean_value` strips a trailing
    whitespace-`#` comment, rstrips, and unquotes — while the Credentials page
    still reported "Set". A password like `p@ss #1` was silently stored as
    `p@ss`, and the failure would surface much later as a wrong-password login.

    Quoting round-trips all three, because `_clean_value` returns everything
    between a leading quote and its next match. A value containing BOTH quote
    characters cannot round-trip through that parser, so it is refused rather
    than written wrong — saying no is better than lying about what was stored.
    """
    for quote in ('"', "'"):
        if quote not in value:
            candidate = f"{quote}{value}{quote}"
            if parse_env("K=" + candidate + chr(10)).get("K") == value:
                return candidate
    raise InvalidEnvValue(
        "this value cannot be stored safely because it contains both a single and a "
        "double quote. Change the credential, or set it directly in the .env file."
    )


def set_env_value(env_path: Path, key: str, value: str) -> None:
    """Write `key=value` into `env_path`: replaces an existing line for `key`,
    else appends a new one. Every other line is preserved untouched.

    Refuses a `key` that isn't `UPPER_SNAKE_CASE`, and a `value` containing a
    `\\n`/`\\r` — either one would let a caller inject an arbitrary extra
    `.env` line (a second key, an overridden earlier one) disguised as a
    single value, corrupting the file `SecretStore` parses line-by-line.

    Writes owner-only (0o600) since this file holds real credentials — a
    world/group-readable `.env` defeats the whole credential boundary before
    a value ever reaches `SecretStore`. `os.chmod` is a no-op for POSIX group/
    other bits on Windows (only the read-only flag applies there), so this is
    a real restriction on POSIX deployments and harmless on Windows dev boxes.
    """
    if not _KEY_RE.fullmatch(key):
        raise InvalidEnvValue(f"'{key}' is not a valid .env key (expected UPPER_SNAKE_CASE)")
    if "\n" in value or "\r" in value:
        raise InvalidEnvValue("value must not contain a newline")
    rendered = _render_value(value)

    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    prefix = f"{key}="
    new_line = f"{key}={rendered}"
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(prefix):
            out.append(new_line)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(new_line)

    env_path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(out) + "\n"
    fd = os.open(str(env_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
    finally:
        with contextlib.suppress(OSError):
            os.chmod(env_path, 0o600)
