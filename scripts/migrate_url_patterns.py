"""Repair `url_pattern` values mangled by AT-287/AT-294, in stored project data.

Before the AT-294 fix, a vision model's address-bar transcription arrived
SCHEMELESS (`vidysea.com/erp/trainers`, because browsers hide `https://`).
`urlsplit` had no `//` to anchor on, put the host in `.path`, and `url_template`
templated it as a path segment — so the stored pattern became
`/vidysea.com/erp/trainers` and matched no observed path. Every screen learned
that way was invisible to coverage.

The producers are fixed, so nothing new is mangled. This repairs what was
already written. It is deliberately a script and not an in-flight edit: a
maker hand-editing real project artifacts mid-cycle leaves a value the code
cannot reproduce, backed by nothing and tested by nothing (AT-297b).

DRY RUN BY DEFAULT. Writing to real project data is a human's call:

    uv run python scripts/migrate_url_patterns.py                # report only
    uv run python scripts/migrate_url_patterns.py --write        # apply
    uv run python scripts/migrate_url_patterns.py --root <dir>   # a sandbox

Idempotent: a repaired file is left byte-identical on a second run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from autotester.core.urls import url_template

# The AT-287/AT-294 signature: a LEADING slash in front of something host-shaped.
# Only a schemeless host-ful input, pre-fix, could produce it — a genuine path
# segment carrying a dot (`/v1.2/foo`) is NOT matched, because the host must be
# the FIRST segment and carry a dotted label pair.
_MANGLED = re.compile(r"^/(?P<host>[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+(?::\d+)?)(?P<rest>/.*|$)")


def repair(pattern: str) -> str | None:
    """The corrected pattern, or None when `pattern` is not mangled."""
    match = _MANGLED.match(pattern)
    if match is None:
        return None
    fixed = url_template(match.group("rest") or "/", keep_host=False)
    return fixed if fixed != pattern else None


def _screens(doc: object) -> list[dict]:
    """The screen rows of a screenmap/flowspec, or nothing.

    Deliberately defensive: this walks EVERY json file under the root, and other
    artifacts use the same key for something else entirely — a crawl manifest
    carries `"screens": 1`, a count. Found by running the dry run against real
    project data, which the fixture-only tests never exercised.
    """
    if not isinstance(doc, dict):
        return []
    screens = doc.get("screens")
    return screens if isinstance(screens, list) else []


def scan(root: Path) -> list[tuple[Path, list[tuple[str, str]]]]:
    """Every file needing repair, with its (before, after) pairs."""
    found: list[tuple[Path, list[tuple[str, str]]]] = []
    for path in sorted(root.rglob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        changes = [
            (screen["url_pattern"], fixed)
            for screen in _screens(doc)
            if isinstance(screen, dict) and isinstance(screen.get("url_pattern"), str)
            and (fixed := repair(screen["url_pattern"])) is not None
        ]
        if changes:
            found.append((path, changes))
    return found


def apply(path: Path) -> int:
    """Repair one file in place. Returns how many patterns changed."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for screen in _screens(doc):
        if not (isinstance(screen, dict) and isinstance(screen.get("url_pattern"), str)):
            continue
        fixed = repair(screen["url_pattern"])
        if fixed is not None:
            screen["url_pattern"] = fixed
            changed += 1
    if changed:
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="projects", type=Path)
    parser.add_argument("--write", action="store_true",
                        help="actually rewrite files (default: report only)")
    args = parser.parse_args(argv)

    if not args.root.exists():
        print(f"no such directory: {args.root}")
        return 2

    found = scan(args.root)
    if not found:
        print(f"{args.root}: nothing to repair")
        return 0

    total = 0
    for path, changes in found:
        print(path)
        for before, after in changes:
            print(f"    {before!r}  ->  {after!r}")
        total += len(changes)
        if args.write:
            apply(path)

    verb = "repaired" if args.write else "would repair"
    print(f"\n{verb} {total} url_pattern(s) across {len(found)} file(s)")
    if not args.write:
        print("dry run — re-run with --write to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
