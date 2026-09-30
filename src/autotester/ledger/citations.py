"""Does every `D-NNN` cited in a gate, contract, manifest, verdict or doc resolve to an
appended decision entry? (`qa/contracts/living-ledger.md` L9, AT-710.)

`scripts/append_decision.ps1` validates ids on WRITE, so the log cannot hold a gap; nothing
validated them on READ, so a phantom `D-056` written into a gate was trusted by every later
reader and the question it was meant to close reached the human a third time. This module is
that read-side check. It is a sibling of `checks.py` (288/300) and `evidence_specs.py` under
the AT-506 split precedent: a new check family gets its own module (D-058 point 1).

Two exemptions exist and both are DECLARED, never inferred from prose (L9): a foreign id space
is out of scope at ENTRY granularity inside `docs/DECISIONS.md`, and a non-claiming occurrence
is a `NON_CLAIMING` row carrying its reason. Neither is ever a whole-file exemption.
"""

from __future__ import annotations

import re
from itertools import pairwise
from pathlib import Path

from autotester.doctor import Violation

CITING_GLOBS = ("qa/gates/*.md", "qa/contracts/*.md", "qa/manifests/*.md",
                "qa/verdicts/*.md", "docs/*.md")
_CITATION = re.compile(r"\bD-\d+\b")
_LOG_HEADER = re.compile(r"^##\s+(D-\d+)\b", re.MULTILINE)
_ARCHIVE_LINE = re.compile(r"^(?:##\s+)?(D-\d+)\s*\|", re.MULTILINE)
_FOREIGN_LOG = re.compile(r"decisions[/\\]log\.md", re.IGNORECASE)

NON_CLAIMING: dict[tuple[str, str, str], str] = {
    ("qa/contracts/living-ledger.md", "already cites `D-088` twice", "D-088"):
        "L9 quotes the foreign-id-space example (the id lives in the AIOS log, not this one)",
    ("qa/contracts/living-ledger.md", "and `:638` cite `D-088`", "D-088"):
        "Amendment-log entry describing the same foreign-id-space example",
    ("qa/manifests/at710-decision-citation-resolver.md", "citing `D-088`, exempted", "D-088"):
        "the resolver's own manifest reporting which lines its entry-scoped rule exempted",
}
"""(file, distinctive text on the line, cited id) -> why the occurrence claims no
authorization. Keyed by line TEXT rather than number so an appended amendment above it
does not silently un-declare it; per occurrence, never per file."""


def appended_ids(root: Path) -> set[str]:
    """Ids with an entry in `docs/DECISIONS.md` or `docs/archive/` (archiving is not deletion)."""
    found: set[str] = set()
    log = root / "docs" / "DECISIONS.md"
    if log.exists():
        found |= set(_LOG_HEADER.findall(log.read_text(encoding="utf-8", errors="replace")))
    for path in sorted((root / "docs" / "archive").glob("*.md")):
        found |= set(_ARCHIVE_LINE.findall(path.read_text(encoding="utf-8", errors="replace")))
    return found


def foreign_ids_by_line(text: str) -> set[tuple[int, str]]:
    """(1-indexed line, id) pairs in `docs/DECISIONS.md` an entry qualifies by another log.

    Scope is the ENTRY, not the line: an id on a line with a path to a decisions log
    exempts that id everywhere in the same `## D-NNN` entry.
    """
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if _LOG_HEADER.match(ln)] + [len(lines)]
    exempt: set[tuple[int, str]] = set()
    for begin, end in pairwise(starts):
        entry = lines[begin:end]
        foreign = {cid for ln in entry if _FOREIGN_LOG.search(ln)
                   for cid in _CITATION.findall(ln)}
        exempt |= {(begin + off + 1, cid) for off, ln in enumerate(entry)
                   for cid in _CITATION.findall(ln) if cid in foreign}
    return exempt


def _declared(rel: str, line: str, cid: str) -> bool:
    return any(rel == f and cid == i and snippet in line for f, snippet, i in NON_CLAIMING)


def _scan(path: Path, root: Path, appended: set[str]) -> list[Violation]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    foreign = foreign_ids_by_line(text) if rel == "docs/DECISIONS.md" else set()
    out = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for cid in dict.fromkeys(_CITATION.findall(line)):
            if cid in appended or (line_no, cid) in foreign or _declared(rel, line, cid):
                continue
            out.append(Violation(
                "decision-citation-dangling", f"{rel}:{line_no}",
                f"cites {cid}, which has no `## {cid}` entry in docs/DECISIONS.md "
                "or docs/archive/"))
    return out


def check_decision_citations(root: Path) -> list[Violation]:
    """L9: every cited `D-NNN` resolves to a header, or is a declared exemption."""
    appended = appended_ids(root)
    if not appended:
        return []
    out: list[Violation] = []
    for glob in CITING_GLOBS:
        for path in sorted(root.glob(glob)):
            out.extend(_scan(path, root, appended))
    return out
