"""Score AutoTester's issues against a human tester's sheet — T-136's acceptance.

    uv run python scripts/score_video_issues.py --project erp \
        --truth "C:/Users/Lenovo/Videos/Screen Recordings/ERP_Issues_Trainers.xlsx" \
        --sheet "Trainer module"

Prints JSON and exits 0 **only when it actually scored something**. Exit 2 means
it could not: no issues derived yet, or a sheet it cannot read. That distinction
is the whole point of the exit code — a scorer that exits 0 having compared an
empty list to seven truth rows reports `recall: 0.0` and looks like a run, which
is AT-100's class ("a check that cannot fail") pointed at the north star's own
metric. The `done_check` for T-136 runs this command, so it has to be able to
fail.

It also reports **coverage** (AT-207): `observations_used` / `observations_expected`
travel with every `VideoAnalysis` but until now reached no reader. A recall
computed from an analysis built out of 1 of 24 model calls is not a measurement
of this pipeline, and the reader has to be told which one they are holding.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotester.core.paths import ProjectPaths
from autotester.stages.score import (
    TruthSheetError,
    load_truth,
    score,
)
from autotester.store.project_store import ProjectStore

DERIVE_HINT = "autotester issues derive"
"""Named once so the advice-collector guard can see it and the CLI-resolve test
can prove it is a command that exists (AT-163/172/176's whole lineage)."""


def coverage(store: ProjectStore, source_ids: set[str]) -> dict:
    """How complete the analyses behind these issues are.

    AT-207: these numbers existed and nothing read them. A partial reading and a
    complete one produce the same screens and the same issues, so a recall taken
    off a fragment is indistinguishable from a real one unless this is printed."""
    used = expected = 0
    partial: list[str] = []
    for source_id in sorted(source_ids):
        analysis = store.load_analysis(source_id)
        if analysis is None:
            continue
        used += analysis.observations_used
        expected += analysis.observations_expected
        if not analysis.is_complete:
            partial.append(source_id)
    return {
        "observations_used": used,
        "observations_expected": expected,
        "complete": not partial and expected > 0,
        "partial_sources": partial,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True)
    parser.add_argument("--truth", required=True, type=Path)
    parser.add_argument("--sheet", required=True)
    parser.add_argument("--window", type=float, default=20.0,
                        help="seconds a report may differ from the human's timestamp")
    parser.add_argument("--threshold", type=float, default=0.30,
                        help="minimum title+description similarity to count as the same fault")
    parser.add_argument("--root", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        truth = load_truth(args.truth, args.sheet)
    except (TruthSheetError, FileNotFoundError) as error:
        print(f"cannot read the truth sheet: {error}", file=sys.stderr)
        return 2
    if not truth:
        print(f"{args.truth.name}/{args.sheet} has no data rows", file=sys.stderr)
        return 2

    root = args.root or ProjectPaths(args.project).root.parent.parent
    store = ProjectStore(args.project, root)
    issues = store.list_issues()
    if not issues:
        print(
            f"project {args.project!r} has no derived issues, so there is nothing to score "
            f"against {len(truth)} truth rows. Run `{DERIVE_HINT} {args.project}` first "
            f"(which needs an analysis, which needs a vision provider — "
            f"`autotester providers`).",
            file=sys.stderr)
        return 2

    card = score(truth, issues, window_s=args.window, threshold=args.threshold)
    report = card.as_dict()
    report["coverage"] = coverage(store, {i.source_id for i in issues})
    report["truth_sheet"] = f"{args.truth.name}/{args.sheet}"
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
