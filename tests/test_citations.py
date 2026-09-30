"""L9 (AT-710): a cited `D-NNN` must resolve to an appended decision entry.

Every fixture is a shape that has occurred in this repo. Synthetic trees are built in
`tmp_path`; the last tests read the real tree so the check is judged against what exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester import doctor
from autotester.core.paths import repo_root
from autotester.ledger import citations
from autotester.ledger.citations import appended_ids, check_decision_citations


def _repo(root: Path, log: str, files: dict[str, str] | None = None,
          archive: str = "") -> Path:
    (root / "docs" / "archive").mkdir(parents=True)
    (root / "docs" / "DECISIONS.md").write_text(log, encoding="utf-8")
    (root / "docs" / "archive" / "INDEX.md").write_text(archive, encoding="utf-8")
    for rel, body in (files or {}).items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body, encoding="utf-8")
    return root


LOG = "## D-001 | 2026-09-01 | type: decision | status: ACTIVE\n**What:** x\n"


def test_a_dangling_id_fires_naming_file_line_and_id(tmp_path: Path) -> None:
    _repo(tmp_path, LOG, {"qa/gates/g.md": "ok D-001\nauthorized by D-056 here\n"})
    found = check_decision_citations(tmp_path)
    assert [(v.location, "D-056" in v.detail) for v in found] == [("qa/gates/g.md:2", True)]


def test_a_resolving_id_is_clean(tmp_path: Path) -> None:
    _repo(tmp_path, LOG, {"qa/manifests/m.md": "Links: D-001\n"})
    assert check_decision_citations(tmp_path) == []


def test_an_archived_entry_resolves(tmp_path: Path) -> None:
    """Archiving is not deletion: an id living only in docs/archive/ still resolves."""
    _repo(tmp_path, LOG, {"qa/gates/g.md": "see D-014\n"},
          archive="D-014 | 2026-07-10 | experiment | REJECTED | x | DECISIONS-2026-Q3.md\n")
    assert "D-014" in appended_ids(tmp_path)
    assert check_decision_citations(tmp_path) == []


def test_matching_is_by_header_not_by_substring(tmp_path: Path) -> None:
    """A mention of `D-056` inside another entry's body is not a `## D-056` header."""
    _repo(tmp_path, LOG + "Body says D-056 did not exist.\n",
          {"qa/gates/g.md": "cites D-056\n"})
    assert "D-056" not in appended_ids(tmp_path)
    found = [v.location for v in check_decision_citations(tmp_path)]
    assert found.count("qa/gates/g.md:1") == 1


def test_the_citation_pattern_is_word_bounded(tmp_path: Path) -> None:
    """SD-3, MD-3 and ID-040 are real strings in this repo and are not citations."""
    _repo(tmp_path, LOG, {"docs/x.md": "SD-3 MD-3 ID-040\nD-001/D-002/D-003\n"})
    assert sorted(v.detail.split()[1].rstrip(",") for v in check_decision_citations(tmp_path)) == [
        "D-002", "D-003"]


def test_only_the_five_named_globs_are_citation_sources(tmp_path: Path) -> None:
    _repo(tmp_path, LOG, {"qa/feedback-inbox.md": "D-777\n", "docs/research/r.md": "D-777\n"})
    assert check_decision_citations(tmp_path) == []


def test_a_foreign_id_is_exempt_across_its_whole_entry_only(tmp_path: Path) -> None:
    """The real shape: D-088 in prose on one line, qualified by a log path on another."""
    log = (LOG + "## D-002 | 2026-09-02 | type: decision | status: ACTIVE\n"
           "prose about D-088 failure\n**Links:** D-088, `D:/ai_os/umesh/decisions/log.md`\n"
           "## D-003 | 2026-09-03 | type: decision | status: ACTIVE\nunqualified D-088\n")
    found = check_decision_citations(_repo(tmp_path, log))
    assert [v.location for v in found] == ["docs/DECISIONS.md:7"]


def test_a_non_claiming_row_is_per_occurrence_never_per_file(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(citations.NON_CLAIMING,
                        ("qa/contracts/c.md", "did not exist", "D-056"), "self-reference")
    _repo(tmp_path, LOG, {"qa/contracts/c.md": "D-056 did not exist\nreal claim D-056\n"
                          "D-057 did not exist\n", "qa/gates/g.md": "D-056 did not exist\n"})
    assert sorted(v.location for v in check_decision_citations(tmp_path)) == [
        "qa/contracts/c.md:2", "qa/contracts/c.md:3", "qa/gates/g.md:1"]


def test_seven_citations_of_an_unwritten_entry_all_fire(tmp_path: Path) -> None:
    """Fixture (c): the precondition (the id is unwritten) is asserted, not assumed."""
    gate = "\n".join(f"line {n} authorized by D-0{57 + 900}" for n in range(7)) + "\n"
    _repo(tmp_path, LOG, {"qa/gates/at654.md": gate})
    assert "D-957" not in appended_ids(tmp_path)
    assert len(check_decision_citations(tmp_path)) == 7


def test_doctor_run_includes_the_citation_check(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = doctor.Violation("decision-citation-dangling", "x:1", "wired")
    monkeypatch.setattr(citations, "check_decision_citations", lambda _root: [marker])
    assert marker in doctor.run(tmp_path)


def test_the_real_tree_has_no_dangling_citation() -> None:
    """The live tree: every declared exemption still matches a real line, and nothing else fires."""
    root = repo_root()
    assert check_decision_citations(root) == []
    assert {"D-055", "D-056", "D-057", "D-058"} <= appended_ids(root)
