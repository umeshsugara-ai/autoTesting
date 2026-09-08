"""Assert a task's deliverables exist — a `done_check` that can actually fail.

AT-100/AT-115/AT-141. A `done_check` of `uv run autotester doctor` passes on a
clean repo whether or not the task it guards has been started, so it reports
"done" for work nobody has done. Three tasks carried exactly that (T-126,
T-135, T-150), and the shape recurred three times before anything named it.

This script exists so such a task can name a deliverable instead of a
repo-wide health command:

    python scripts/check_deliverable.py --exists qa/contracts/ai-target.md
    python scripts/check_deliverable.py --contains qa/adapter.json explore_proof

Exit 0 only when every assertion holds. Deliberately dumb: it checks that the
artifact is THERE, not that it is good — that is the checker's job, and a
`done_check` that tried to judge quality would be a second, worse checker.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def check_exists(paths: list[str]) -> list[str]:
    return [f"missing: {p}" for p in paths if not _resolve(p).exists()]


def check_contains(pairs: list[list[str]]) -> list[str]:
    failures = []
    for path_str, needle in pairs:
        path = _resolve(path_str)
        if not path.exists():
            failures.append(f"missing: {path_str}")
        elif needle not in path.read_text(encoding="utf-8"):
            failures.append(f"{path_str} does not mention {needle!r}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exists", nargs="+", default=[], metavar="PATH")
    parser.add_argument("--contains", nargs=2, action="append", default=[],
                        metavar=("FILE", "SUBSTRING"))
    args = parser.parse_args(argv)

    if not args.exists and not args.contains:
        print("FAIL nothing asserted — a check with no assertion cannot fail")
        return 2

    failures = check_exists(args.exists) + check_contains(args.contains)
    for failure in failures:
        print(f"FAIL {failure}")
    if failures:
        return 1
    print(f"OK {len(args.exists) + len(args.contains)} deliverable(s) present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
