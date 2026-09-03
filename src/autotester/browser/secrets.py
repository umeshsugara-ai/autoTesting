"""The credential boundary. Secret values live here and nowhere else.

Contract: qa/contracts/browser-and-secrets.md B1-B4.

The design in one line: a secret value is loaded from `.env` into memory, handed
out only at the moment of typing into an allowed host, and is never permitted
into a prompt, a log, or an artifact. Everything upstream carries the
placeholder `{{SECRET:KEY}}` instead.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from autotester.core.redact import PLACEHOLDER_RE, Redactor, assert_no_raw_secrets
from autotester.schema.project import Project, SecretRef

_COMMENT_RE = re.compile(r"\s#")


class SecretError(RuntimeError):
    """Base for every credential-boundary failure."""


class MissingSecret(SecretError):
    """A key the project declares is absent from .env."""


class UndeclaredSecret(SecretError):
    """A key exists in .env that the project never declared."""


class SecretScopeError(SecretError):
    """A secret was requested for a host outside its declared domains."""


def parse_env(text: str) -> dict[str, str]:
    """Parse `KEY=value` lines. Ignores blanks, comments, and `export ` prefixes.

    Deliberately minimal: no interpolation, no multi-line values. A credential
    file that needs a parser with features is a credential file with surprises.
    """
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        values[key.strip()] = _clean_value(value.strip())
    return values


def _clean_value(value: str) -> str:
    """Unquote a value, or strip a trailing whitespace-`#` comment (AT-003, AT-006).

    A quoted value keeps everything inside its quotes (including `#`) and drops
    anything after the closing quote. An unquoted value is cut at the first
    `#` preceded by any whitespace (space or tab); `#` with no whitespace
    before it (a URL fragment) is data.
    """
    if value and value[0] in "\"'":
        closing = value.find(value[0], 1)
        if closing > 0:
            return value[1:closing]
    return _COMMENT_RE.split(value, maxsplit=1)[0].rstrip()


def host_of(url: str) -> str:
    """Hostname the BROWSER will use, lowercased, without port. Empty = refuse.

    Fails closed on anything `urlparse` and WHATWG might disagree about
    (AT-007): a backslash anywhere, or any userinfo (`user@host`). Chromium
    treats `\\` as a path separator, so `https://evil.test\\@good.test` has
    host `evil.test` in the browser while `urlparse` reports `good.test`.
    An empty return makes `resolve()` raise `SecretScopeError`.
    """
    if "\\" in url:
        return ""
    parsed = urlparse(url if "//" in url else f"//{url}")
    if parsed.username is not None or parsed.password is not None:
        return ""
    return (parsed.hostname or "").lower()


def _host_matches(host: str, domain: str) -> bool:
    domain = domain.lower().lstrip(".")
    return host == domain or host.endswith(f".{domain}")


class SecretStore:
    """Loaded credentials for one project, scoped to the domains it declared.

    Construct via `load`. Ask for a value only through `resolve`, which requires
    the host it is about to be typed into.
    """

    def __init__(
        self,
        project: Project,
        values: dict[str, str],
        shadow: dict[str, str] | None = None,
    ) -> None:
        self._project = project
        self._values = values
        self._refs: dict[str, SecretRef] = {s.key: s for s in project.secrets}
        # Undeclared .env values: never resolvable, but still masked (AT-004 —
        # B4 "masks every secret value" wins over B1's "ignored"). The root
        # `.env` is shared across projects, so these are other projects' keys.
        self._shadow: dict[str, str] = shadow or {}
        self.undeclared: list[str] = sorted(self._shadow)

    # -- construction -------------------------------------------------------
    @classmethod
    def load(cls, project: Project, env_path: Path, *, strict: bool = True) -> SecretStore:
        """Read `env_path` and keep only the keys `project` declares.

        Raises `MissingSecret` for a declared key with no value. An undeclared
        key present in the file is dropped and reported via `undeclared` rather
        than being usable — a credential nobody declared has no scope, and an
        unscoped credential is exactly what this class exists to prevent.
        """
        text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        present = parse_env(text)
        declared = {s.key for s in project.secrets}

        missing = sorted(k for k in declared if not present.get(k))
        if missing and strict:
            raise MissingSecret(
                f"{env_path} is missing value(s) for declared key(s): {', '.join(missing)}"
            )

        usable = {k: v for k, v in present.items() if k in declared and v}
        shadow = {k: v for k, v in present.items() if k not in declared and v}
        return cls(project, usable, shadow)

    # -- the boundary -------------------------------------------------------
    def resolve(self, value: str | None, url_or_host: str) -> str | None:
        """Substitute `{{SECRET:KEY}}` placeholders for the given destination.

        Every referenced key must be declared, present, and scoped to this host.
        The returned string is the only form a secret takes outside this class,
        and the caller must pass it straight to the browser without storing it.
        """
        if value is None or not PLACEHOLDER_RE.search(value):
            return value
        host = host_of(url_or_host)
        if not host:
            # Fail CLOSED: an unparseable destination has no scope (AT-001).
            raise SecretScopeError(f"cannot resolve a secret for destination {url_or_host!r}")
        result = value
        for key in PLACEHOLDER_RE.findall(value):
            result = result.replace(f"{{{{SECRET:{key}}}}}", self._value_for(key, host))
        return result

    def _value_for(self, key: str, host: str) -> str:
        ref = self._refs.get(key)
        if ref is None:
            raise UndeclaredSecret(f"'{key}' is not declared in project '{self._project.slug}'")
        if not any(_host_matches(host, d) for d in ref.domains):
            raise SecretScopeError(
                f"'{key}' is scoped to {ref.domains or '[]'} and may not be used on '{host}'"
            )
        value = self._values.get(key)
        if not value:
            raise MissingSecret(f"'{key}' has no value loaded")
        return value

    # -- protection ---------------------------------------------------------
    def _all_values(self) -> dict[str, str]:
        """Declared and undeclared alike — anything in .env is a secret to mask."""
        return {**self._shadow, **self._values}

    def redactor(self) -> Redactor:
        """A `Redactor` that masks every value in .env, declared or not (AT-004)."""
        return Redactor(self._all_values())

    def guard_prompt(self, text: str) -> str:
        """Raise if `text` carries any raw .env value. Call before every model call."""
        assert_no_raw_secrets(text, self._all_values().values())
        return text

    def masked_field_keys(self) -> set[str]:
        """Keys whose inputs must be masked before a screenshot is captured."""
        return {k for k, ref in self._refs.items() if ref.mask_in_screenshot}

    def keys(self) -> list[str]:
        return sorted(self._values)

    def __contains__(self, key: str) -> bool:
        return key in self._values

    def __repr__(self) -> str:
        """Never render values — a repr in a traceback is a leak."""
        return f"SecretStore(project={self._project.slug!r}, keys={self.keys()})"
