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


def real_values(root: Path | None = None) -> list[str]:
    """Every non-empty value currently in the repo-root .env, plus each value's
    dot-escaped form (`a.b` -> `a\\.b`) -- a trivial regex-escape is not enough
    to turn a real secret into an innocent "pattern" (found the hard way when a
    checker's own literal-vs-regex reasoning missed exactly this, AT-025)."""
    env_path = ProjectPaths("_", root).root / ".env"
    if not env_path.exists():
        return []
    values = [v for v in parse_env(env_path.read_text(encoding="utf-8")).values() if v]
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
