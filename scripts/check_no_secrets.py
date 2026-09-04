"""Scan files for any real value currently loaded in .env. Prints OK/LEAK only.

Exists because a human or an agent hand-typing an "example" secret-shaped
string into a manifest or doc is itself a leak if it happens to equal a real
value (found the hard way — AT-025). This script never prints or accepts a
secret value as an argument; it reads `.env` itself and checks silently.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotester.browser.secrets import parse_env
from autotester.core.paths import ProjectPaths
from autotester.store import ProjectStore


def _public_base_urls(root: Path | None = None) -> set[str]:
    """AT-037: a project's own `base_url` is meant to be public (it's the
    product's sign-in page) -- if the SAME string also happens to sit in
    `.env` as a convenience value, that coincidence is not a leak. Excluded
    by exact string match only, never a prefix/substring rule."""
    projects_dir = ProjectPaths("_", root).root / "projects"
    if not projects_dir.exists():
        return set()
    urls = set()
    for slug_dir in projects_dir.iterdir():
        if (slug_dir / "project.json").exists():
            project = ProjectStore(slug_dir.name, root).load_project()
            if project is not None:
                urls.add(project.base_url)
    return urls


def real_values(root: Path | None = None) -> list[str]:
    """Every non-empty value currently in the repo-root .env, plus each value's
    dot-escaped form (`a.b` -> `a\\.b`) -- a trivial regex-escape is not enough
    to turn a real secret into an innocent "pattern" (found the hard way when a
    checker's own literal-vs-regex reasoning missed exactly this, AT-025).

    AT-037/AT-038: a `.env` value is excluded ONLY when it (a) exactly equals a
    project's own public base_url AND (b) sits under a key whose name marks it
    as a URL (`"URL" in KEY`) -- excluding by bare value alone (AT-037's first
    fix) meant a genuinely different secret that happened to coincide with a
    base_url string would go uncaught (AT-038). Scoping to the key name closes
    that: a password-shaped key never matches, no matter what its value is.
    """
    env_path = ProjectPaths("_", root).root / ".env"
    if not env_path.exists():
        return []
    public = _public_base_urls(root)
    present = parse_env(env_path.read_text(encoding="utf-8"))
    values = [
        v for k, v in present.items()
        if v and not (v in public and "URL" in k.upper())
    ]
    escaped = [v.replace(".", "\\.") for v in values if "." in v]
    return values + escaped


def scan(paths: list[Path], values: list[str]) -> dict[Path, bool]:
    """Path -> True if clean, False if any real value was found inside it."""
    results: dict[Path, bool] = {}
    for path in paths:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except (UnicodeDecodeError, OSError):
            continue  # binary (screenshots) -- nothing to scan as text
        results[path] = not any(value in text for value in values)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: check_no_secrets.py <file-or-dir> [...]")
        raise SystemExit(2)
    targets: list[Path] = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        targets.extend(p.rglob("*") if p.is_dir() else [p])
    outcome = scan(targets, real_values())
    leaks = [str(p) for p, clean in outcome.items() if not clean]
    for path in leaks:
        print(f"LEAK: {path}")
    print(f"scanned {len(outcome)} file(s); {len(leaks)} leak(s)")
    raise SystemExit(1 if leaks else 0)
