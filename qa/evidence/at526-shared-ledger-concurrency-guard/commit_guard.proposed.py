"""Guard the one shared write surface a checker cannot serialize on: `qa/issues.jsonl`.

AT-526. `git commit --only <path>` restricts which FILES a commit touches, not whose
CHANGES within a shared file are included — it commits that path's current on-disk
content wholesale. On 2026-09-18 two checkers ran concurrently on units with disjoint
*source* file sets and still collided here: the at520 checker had uncommitted edits in
the working tree (an AT-520 status flip, an AT-525 append) when the at521 checker ran
`git commit --only qa/issues.jsonl` for its own unrelated PASS, sweeping both edits into
its commit (`0fe2b6d`) before the at520 unit had a verdict at all. No content was wrong
that time — pure luck, not a property of the mechanism.

This module compares the ledger row-by-row, by issue id, between the last commit and the
working tree, and lets a caller declare which ids it *intended* to touch. Anything else
that changed is someone else's uncommitted edit riding along, and is refused rather than
silently swept in — the fix `qa/manifests/at526-*.md` recommends: verify-before-commit,
not a bigger rewrite of how the ledger is written.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="qa/issues.jsonl -- the checker's shared ledger (AT-499); "
                        "this module's commit guard is AT-526.")

LEDGER_RELATIVE_PATH = "qa/issues.jsonl"


def _rows_by_id(text: str) -> dict[str, str]:
    """Parse JSONL rows into `{issue_id: canonical_json}`.

    Comparing the *parsed and re-sorted* form, not the raw line, means a row that was
    merely reformatted (whitespace, key order, `ensure_ascii` escaping — the a8caf58
    incident) reads as unchanged; only a real field-level difference counts. A row with
    no `"id"` field or a line that fails to parse is skipped rather than raising — this
    is a guard, not a validator (`check_ledger`/`check_qa_issue_rows` already own
    shape validation).
    """
    rows: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        issue_id = row.get("id") if isinstance(row, dict) else None
        if not issue_id:
            continue
        rows[issue_id] = json.dumps(row, sort_keys=True, ensure_ascii=True)
    return rows


def diff_ledger_ids(old_text: str, new_text: str) -> dict[str, str]:
    """`{issue_id: 'added' | 'changed' | 'removed'}` for every row that differs.

    Keyed by id rather than by line position, so a concurrent writer reordering rows
    (append order differs when two agents both append around the same time) is never
    mistaken for a change to the rows it didn't touch.
    """
    old_rows = _rows_by_id(old_text)
    new_rows = _rows_by_id(new_text)
    changed: dict[str, str] = {}
    for issue_id, content in new_rows.items():
        if issue_id not in old_rows:
            changed[issue_id] = "added"
        elif content != old_rows[issue_id]:
            changed[issue_id] = "changed"
    for issue_id in old_rows:
        if issue_id not in new_rows:
            changed[issue_id] = "removed"
    return changed


def unexpected_ledger_changes(
    old_text: str, new_text: str, intended_ids: set[str]
) -> dict[str, str]:
    """The AT-526 check: rows that changed old -> new but weren't declared as intended.

    A non-empty result means someone else's uncommitted edit is sitting in the working
    copy right now — exactly what `git commit --only` would otherwise sweep in silently.
    """
    changed = diff_ledger_ids(old_text, new_text)
    return {i: k for i, k in changed.items() if i not in intended_ids}


def _read_head_ledger(root: Path) -> str:
    """`qa/issues.jsonl` as last committed — `""` if the path has no commit yet."""
    result = subprocess.run(
        ["git", "show", f"HEAD:{LEDGER_RELATIVE_PATH}"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    return result.stdout if result.returncode == 0 else ""


@app.command("commit")
def commit_cmd(
    expect: str = typer.Option(
        ..., "--expect",
        help="comma-separated issue ids this commit intends to touch, e.g. AT-521,AT-522,AT-524"),
    message: str = typer.Option(..., "-m", "--message"),
    root: Path = typer.Option(Path("."), "--root", hidden=True, help="repo root (tests only)"),
) -> None:
    """Commit qa/issues.jsonl -- refusing if any id outside --expect changed underneath you.

    Replaces a bare `git commit --only qa/issues.jsonl` at the end of a checker cycle.
    Run it from the repo root once your own edits are on disk (uncommitted is fine — it
    reads the working tree, not the index).
    """
    root = root.resolve()
    ledger_path = root / LEDGER_RELATIVE_PATH
    if not ledger_path.exists():
        typer.secho(f"no {LEDGER_RELATIVE_PATH} at {root}", fg=typer.colors.RED)
        raise typer.Exit(2)

    intended = {i.strip() for i in expect.split(",") if i.strip()}
    old_text = _read_head_ledger(root)
    new_text = ledger_path.read_text(encoding="utf-8")
    unexpected = unexpected_ledger_changes(old_text, new_text, intended)

    if unexpected:
        typer.secho(
            "REFUSED: qa/issues.jsonl changed underneath you -- someone else's uncommitted "
            "edit would ride along with this commit (AT-526):", fg=typer.colors.RED, bold=True)
        for issue_id, kind in sorted(unexpected.items()):
            typer.secho(f"  {issue_id}: {kind} (not in --expect)", fg=typer.colors.RED)
        typer.secho(
            "Re-read qa/issues.jsonl fresh, confirm those ids are correct, and add them to "
            "--expect (or wait for their owner to commit first) before retrying.",
            fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    subprocess.run(["git", "commit", "--only", LEDGER_RELATIVE_PATH, "-m", message],
                    cwd=root, check=True)
    typer.secho(f"qa/issues.jsonl committed -- {', '.join(sorted(intended)) or '(no ids declared)'}",
                fg=typer.colors.GREEN)
