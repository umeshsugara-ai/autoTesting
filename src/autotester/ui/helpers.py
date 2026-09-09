"""Shared request-validation and lookup helpers used by every UI route module.

One place for slug/id validation so `ui/app.py`, `ui/routes_runs.py` and
`ui/routes_credentials.py` never each grow their own copy (AT-035's
attribute-injection hole started exactly there).
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote_plus

from fastapi import HTTPException

from autotester.browser.secrets import SecretStore, host_of
from autotester.core.paths import repo_root
from autotester.core.redact import PLACEHOLDER_RE
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore

# Same shape as schema.project.Project.slug's own field pattern -- a slug is a
# single safe path segment, never `..`, `/`, `\`, or a null byte, before it is
# ever handed to ProjectPaths/ProjectStore as a directory name.
_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# run/case ids are ulid- or content_id-shaped: alnum plus `_`/`-` only.
_HOSTNAME_RE = re.compile(r"^(?=.*\.)[a-z0-9.-]+$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _require_slug(slug: str) -> str:
    if not _SLUG_RE.fullmatch(slug):
        raise HTTPException(400, "invalid project slug")
    return slug


def _require_safe_id(value: str, label: str) -> str:
    if not _SAFE_ID_RE.fullmatch(value):
        raise HTTPException(400, f"invalid {label}")
    return value


def _require_reachable_base_url(base_url: str, domains: list[str]) -> None:
    """Refuse a project whose own `base_url` host is outside its `allowed_domains`.

    AT-058: such a project can never test anything — every run dies at the first
    step with `NavigationRefused`, hours after the mistake was made and with no
    hint that onboarding was where it went wrong. Umesh hit this by typing "all"
    in Allowed domains, meaning "allow everything": it was stored verbatim as a
    literal domain named `all`, and the project was dead on arrival.

    Deliberately NOT solved by teaching `allowed_domains` a wildcard —
    `allowed_domains` is the documented boundary the browser is never allowed to
    cross, and an allow-anything escape hatch is a security decision, not a
    validation fix.
    """
    host = host_of(base_url)
    if not host:
        # AT-088: never echo the submitted URL -- this check runs BEFORE the
        # credential guard, so a password pasted here would be handed straight
        # back in the response body and the access log (the fourth occurrence
        # of the AT-068/AT-075 pattern).
        raise HTTPException(400, "that is not a URL the browser can open")
    probe = Project(slug="probe", name="probe", base_url=base_url, allowed_domains=domains)
    if not probe.allows_domain(host):
        # AT-088: `host_of` returns a pseudo-host for garbage, so naming it
        # unconditionally would echo back a credential pasted into this box.
        # Name it only when it is genuinely hostname-shaped; otherwise say what
        # is wrong without quoting what was sent.
        if _HOSTNAME_RE.fullmatch(host):
            raise HTTPException(400, (
                f"this project could never run: its base URL host '{host}' is not covered "
                f"by allowed domains {domains}. Add '{host}' to the allowed domains."
            ))
        raise HTTPException(400, (
            "that base URL does not look like an address the browser can open. Enter the "
            "product's URL, e.g. https://app.example.com/signin."
        ))


def _project_slugs() -> list[str]:
    projects_dir = repo_root() / "projects"
    if not projects_dir.exists():
        return []
    return sorted(p.name for p in projects_dir.iterdir() if (p / "project.json").exists())


def _load_project_or_404(slug: str) -> tuple[ProjectStore, Project]:
    _require_slug(slug)
    store = ProjectStore(slug)
    project = store.load_project()
    if project is None:
        raise HTTPException(404, f"no project '{slug}'")
    return store, project

def _credential_variants(text: str) -> list[str]:
    """The forms a pasted credential can arrive in that all recover trivially.

    AT-074: `Redactor.is_clean` is a plain substring test, so a value that was
    URL-encoded, or that a user broke with a stray space or newline, sailed
    through and was written to a git-tracked file — recoverable with one
    `unquote_plus` or a whitespace strip. Matching is done against every form,
    not just the literal one.
    """
    decoded = unquote_plus(text)
    return [
        text,
        decoded,
        "".join(text.split()),
        "".join(decoded.split()),
    ]


def _refuse_unsafe_value(
    value: str, project: Project, secrets: SecretStore, *, field: str = "this field",
    exempt: frozenset[str] = frozenset(),
) -> None:
    """One field. Placeholders must name a declared key; a literal must not be a
    real `.env` value.

    Two distinct mistakes, both silent before this existed:
    - Typing the credential ITSELF into a text box. `cases.jsonl` is git-TRACKED
      in a public repo, so that is a credential committed in cleartext; and
      because no `{{SECRET:KEY}}` placeholder is present, `session.fill` never
      tags the field, so it shows up in every screenshot too.
    - Referencing a key the project has not declared. That resolved only at
      typing time, deep inside `_value_for`, surfacing as a stringified
      `UndeclaredSecret` inside a generic ERRORED outcome.
    """
    if not value:
        return
    referenced = PLACEHOLDER_RE.findall(value)
    if referenced:
        for key in referenced:
            if project.secret(key) is None:
                raise HTTPException(400, (
                    f"this project has not declared a credential called '{key}'. "
                    f"Declare it in Project settings first, then use it here."
                ))
        return
    if value in exempt:
        # AT-078: a field re-submitted byte-identical to what is already on
        # disk for that same field of that same project. `.env` holds plain
        # configuration as well as credentials -- `pathlynks`'s own base_url
        # is byte-identical to the non-secret PATHLYNKS_USER_LOGIN_URL -- so
        # without this, a no-op save of a project's own data was refused with
        # no fix the user could express. Narrow on purpose: it exempts only
        # data the system itself already stored, never fresh input (AT-083).
        return
    redactor = secrets.redactor()
    if any(not redactor.is_clean(v) for v in _credential_variants(value)):
        raise HTTPException(400, (
            f"{field} looks like it contains a real credential. Values are stored in "
            f"the repository in plain text and appear in screenshots, so they must "
            f"never be typed in directly. Declare it in Project settings and use "
            f"{{{{SECRET:KEY}}}} in a step's Value box — note that only a Value is "
            f"substituted, not a URL or a title."
        ))


def _refuse_unsafe_submission(
    texts: list[tuple[str, str]], project: Project, secrets: SecretStore,
    *, exempt: frozenset[str] = frozenset(),
) -> None:
    """Every user-supplied field of a case, and their concatenation.

    AT-070: the guard was wired to the value box alone, so the same credential
    typed into the title, the target or the expect box sailed through into a
    git-tracked `cases.jsonl`. The title was the worst of the three — U6 leaves
    `rationale=None`, so `claim_of` falls back to the title and feeds it to the
    grade prompt, where `guard_prompt` raises and 500s every later run.

    AT-083: matching runs over EVERY value in `.env`, declared or not -- an
    undeclared key (a provider API key, say) is still a credential, and this
    repo is public. Scoping to declared-only was a real hole.

    AT-071: checking fields one at a time also missed a value split across two
    rows, which reassembles byte-for-byte on disk. So the joined text is checked
    too. A false positive there costs a clear error message asking for a
    placeholder; a false negative costs a committed credential.
    """
    for label, text in texts:
        _refuse_unsafe_value(text.strip(), project, secrets, field=label, exempt=exempt)
    # An exempt field holds data the system itself already stored, so it cannot
    # be half of a freshly-pasted credential -- and leaving it in would re-fire
    # the very false positive the exemption exists to stop (AT-078: pathlynks's
    # own base_url contains a non-secret .env URL, so the join always matched).
    fresh = [(label, text.strip()) for label, text in texts if text.strip() not in exempt]
    joined = "".join(text for _label, text in fresh)
    redactor = secrets.redactor()
    if joined and any(not redactor.is_clean(v) for v in _credential_variants(joined)):
        raise HTTPException(400, (
            "a real credential appears to be split across "
            f"{', '.join(sorted({label for label, _t in fresh}))}. Declare it in Project "
            "settings and use {{SECRET:KEY}} in a step's Value box instead."
        ))


def _reserved_temp_path(suffix: str, directory: Path | None = None) -> Path:
    """Reserve a unique filename via mkstemp, then hand it to the exporter to
    create fresh — the exporters all write a brand-new file, so the
    mkstemp-opened fd is closed and the placeholder removed immediately.

    Lives here rather than in one route module because three download routes
    now need it (run report, portable HTML, crawl report) — C3.
    """
    if directory is not None:
        directory.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=suffix, dir=directory)
    os.close(fd)
    path = Path(tmp)
    path.unlink()
    return path
