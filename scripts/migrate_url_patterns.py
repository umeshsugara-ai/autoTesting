"""Repair `url_pattern` values mangled by AT-287/AT-294, in stored project data.

Before the AT-294 fix, a vision model's address-bar transcription arrived
SCHEMELESS (`vidysea.com/erp/trainers`, because browsers hide `https://`).
`urlsplit` had no `//` to anchor on, put the host in `.path`, and `url_template`
templated it as a path segment — so the stored pattern became
`/vidysea.com/erp/trainers` and matched no observed path. Every screen learned
that way was invisible to coverage.

A pattern counts as mangled ONLY when its first segment is a host the project
itself declares in `project.json` (`base_url` / `allowed_domains`). An earlier
version guessed from shape and silently ate real paths (`/v1.2/foo` -> `/foo`,
`/index.html` -> `/`) while three documents claimed it did not - AT-298.

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
import sys
from pathlib import Path
from urllib.parse import urlsplit

from autotester.core.urls import url_template


def known_hosts(project_dir: Path) -> set[str]:
    """Every host this project is actually about, from its own `project.json`.

    This is the whole point of the AT-298 rewrite. The first version guessed
    from SHAPE - "a first segment with a dotted label pair is a host" - and that
    guess is unwinnable for the third time in this saga: `/v1.2/foo`,
    `/index.html` and `/vidysea.com/erp` are indistinguishable as strings, so it
    ate the first two (`/v1.2/foo` -> `/foo`, `/index.html` -> `/`) while three
    documents, including the human gate, claimed it refused them.

    A project declares `base_url` and `allowed_domains`. A swallowed host can
    only ever be one of those. So match against what the project SAYS, never
    against what a string looks like.
    """
    try:
        config = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(config, dict):
        return set()

    # AT-300: `allowed_domains` given as a JSON STRING iterates CHARACTERS, which
    # made every single-character first segment strippable. A malformed config
    # must contribute nothing, not a set of letters.
    declared = config.get("allowed_domains")
    hosts = (
        {d.strip().lower() for d in declared if isinstance(d, str) and d.strip()}
        if isinstance(declared, list) else set()
    )

    # AT-301/AT-302: `.netloc` carries userinfo (`user:pw@host`) and IPv6
    # brackets. Splitting it on ":" made the USERNAME a declared host, so
    # `/user/foo` repaired to `/foo`; an IPv6 literal yielded `[`. `.hostname`
    # is the parsed host - lowercased, userinfo stripped, brackets removed -
    # and `.port` is the port or None.
    base = config.get("base_url")
    if isinstance(base, str) and base:
        try:
            parts = urlsplit(base)
            host, port = parts.hostname, parts.port
        except ValueError:  # malformed authority, e.g. a bad port
            host, port = None, None
        if host:
            hosts.add(host)
            if port:
                hosts.add(f"{host}:{port}")
    return {h for h in hosts if h}


def repair(pattern: str, hosts: set[str]) -> str | None:
    """The corrected pattern, or None when `pattern` is not mangled.

    Mangled means: the first path segment is a host THIS PROJECT declares. A
    segment that merely looks host-shaped is left alone - it is a real path.
    """
    if not pattern.startswith("/") or not hosts:
        return None
    first, _, rest = pattern[1:].partition("/")
    candidate = first.lower()
    if candidate not in hosts and candidate.split(":", 1)[0] not in hosts:
        return None
    fixed = url_template("/" + rest if rest else "/", keep_host=False)
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


def _project_dir_of(path: Path, root: Path) -> Path:
    """The project directory a file belongs to, so the hosts used to judge it
    are the ones that project itself declares.

    Walks UP looking for the `project.json` that actually governs the file.
    AT-304: assuming the project is always exactly one level below the root
    silently skipped anything nested deeper (`projects/erp/crawl/x/map.json`)
    and anything under a flat `--root` that IS a project.
    """
    for parent in (path.parent, *path.parent.parents):
        if (parent / "project.json").is_file():
            return parent
        if parent == root:
            break
    return root


def scan(root: Path) -> list[tuple[Path, list[tuple[str, str]]]]:
    """Every file needing repair, with its (before, after) pairs."""
    found: list[tuple[Path, list[tuple[str, str]]]] = []
    hosts_by_dir: dict[Path, set[str]] = {}
    for path in sorted(root.rglob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        project_dir = _project_dir_of(path, root)
        hosts = hosts_by_dir.setdefault(project_dir, known_hosts(project_dir))
        changes = [
            (screen["url_pattern"], fixed)
            for screen in _screens(doc)
            if isinstance(screen, dict) and isinstance(screen.get("url_pattern"), str)
            and (fixed := repair(screen["url_pattern"], hosts)) is not None
        ]
        if changes:
            found.append((path, changes))
    return found


def apply(path: Path, hosts: set[str]) -> int:
    """Repair one file in place. Returns how many patterns changed."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for screen in _screens(doc):
        if not (isinstance(screen, dict) and isinstance(screen.get("url_pattern"), str)):
            continue
        fixed = repair(screen["url_pattern"], hosts)
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
            apply(path, known_hosts(_project_dir_of(path, args.root)))

    verb = "repaired" if args.write else "would repair"
    print(f"\n{verb} {total} url_pattern(s) across {len(found)} file(s)")
    if not args.write:
        print("dry run — re-run with --write to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
