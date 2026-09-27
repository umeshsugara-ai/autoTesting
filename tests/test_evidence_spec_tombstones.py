"""AT-516(c), D-048: a stale `mutations.json` stays byte-intact and gets tagged
by a sidecar `mutations.stale.json`; the check tells "stale on purpose" apart
from "stale by neglect" by RESOLVING the tag, never by trusting its presence
(AT-218's vacuous-guard class)."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from autotester import doctor
from autotester.core.paths import repo_root
from autotester.ledger.evidence_specs import check_stale_evidence_specs
from autotester.schema.evidence_tombstone import EvidenceTombstoneEntry


def _spec(kills: list[str], tests: list[str] | str = "tests/") -> dict:
    return {"tests": tests, "mutations": [
        {"name": "m", "file": "src/x.py", "old": "a", "new": "b", "kills": kills}]}


def _write_spec(root: Path, slug: str, kills: list[str],
                tests: list[str] | str = "tests/", tombstone: dict | None = None) -> None:
    spec_dir = root / "qa" / "evidence" / slug
    spec_dir.mkdir(parents=True)
    (spec_dir / "mutations.json").write_text(json.dumps(_spec(kills, tests)), encoding="utf-8")
    if tombstone is not None:
        (spec_dir / "mutations.stale.json").write_text(json.dumps(tombstone), encoding="utf-8")


def _make(root: Path, rel: str, funcname: str = "test_thing") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"def {funcname}():\n    pass\n", encoding="utf-8")


def test_a_spec_whose_kills_still_resolve_is_not_stale(tmp_path: Path) -> None:
    _write_spec(tmp_path, "u1", ["tests/test_x.py::test_thing"])
    _make(tmp_path, "tests/test_x.py")

    assert check_stale_evidence_specs(tmp_path) == []


def test_a_stale_path_qualified_id_with_no_tombstone_is_flagged(tmp_path: Path) -> None:
    _write_spec(tmp_path, "u2", ["tests/test_old.py::test_thing"])
    # tests/test_old.py is never created -- the function moved, nobody said where

    out = check_stale_evidence_specs(tmp_path)

    assert [(v.rule, v.location) for v in out] == [
        ("evidence-spec-stale-unexplained",
         "qa/evidence/u2/mutations.json::tests/test_old.py::test_thing")]
    assert "no mutations.stale.json entry" in out[0].detail


def test_a_tombstone_whose_moved_to_actually_resolves_is_accepted(tmp_path: Path) -> None:
    _write_spec(tmp_path, "u3", ["tests/test_old.py::test_thing"], tombstone={
        "entries": [{"old_nodeid": "tests/test_old.py::test_thing",
                     "moved_to": "tests/test_new.py::test_thing",
                     "moved_by_unit": "u9"}]})
    _make(tmp_path, "tests/test_new.py")

    assert check_stale_evidence_specs(tmp_path) == []


def test_a_tombstone_whose_moved_to_does_not_resolve_is_still_flagged(tmp_path: Path) -> None:
    """AT-218: a tag is a claim, not a comment. Trusting a tombstone's mere
    PRESENCE is the exact vacuous-guard shape this repo keeps re-discovering --
    a lying tombstone (`moved_to` that resolves nowhere) must fail exactly like
    no tombstone at all, and say so distinctly from the no-tombstone case."""
    _write_spec(tmp_path, "u4", ["tests/test_old.py::test_thing"], tombstone={
        "entries": [{"old_nodeid": "tests/test_old.py::test_thing",
                     "moved_to": "tests/test_nowhere.py::test_thing",
                     "moved_by_unit": "u9"}]})
    # tests/test_nowhere.py is never created -- the tombstone is lying

    out = check_stale_evidence_specs(tmp_path)

    assert len(out) == 1
    assert out[0].rule == "evidence-spec-stale-unexplained"
    assert "does not resolve either" in out[0].detail


def test_a_tombstone_covers_every_parametrize_id_of_the_moved_function(tmp_path: Path) -> None:
    _write_spec(tmp_path, "u5", ["tests/test_old.py::test_p[a]",
                                "tests/test_old.py::test_p[b]"], tombstone={
        "entries": [{"old_nodeid": "tests/test_old.py::test_p",
                     "moved_to": "tests/test_new.py::test_p", "moved_by_unit": "u9"}]})
    _make(tmp_path, "tests/test_new.py", funcname="test_p")

    assert check_stale_evidence_specs(tmp_path) == []


def test_a_bare_kills_name_resolves_against_the_specs_own_tests_scope(tmp_path: Path) -> None:
    """`mutation_check.py` itself accepts a `kills` entry with no `::` and
    resolves it against the spec's OWN declared `tests` field, not the whole
    repo (`scripts/mutation_check.py::collected_tests`). Treating every bare
    name as unresolvable is exactly the false positive this unit's own build
    hit against the repo's real at311/at520/at523 specs."""
    _write_spec(tmp_path, "u6", ["test_thing"], tests="tests/test_x.py")
    _make(tmp_path, "tests/test_x.py")

    assert check_stale_evidence_specs(tmp_path) == []


def test_a_bare_kills_name_outside_the_specs_tests_scope_is_stale(tmp_path: Path) -> None:
    """The mirror of the case above: a bare name that only exists OUTSIDE the
    spec's declared `tests` scope is exactly what `mutation_check.py` itself
    would refuse to collect, so this check must refuse it too."""
    _write_spec(tmp_path, "u7", ["test_thing"], tests="tests/test_x.py")
    _make(tmp_path, "tests/test_elsewhere.py")  # the scope names test_x.py, not this

    out = check_stale_evidence_specs(tmp_path)

    assert [(v.rule, v.location) for v in out] == [
        ("evidence-spec-stale-unexplained", "qa/evidence/u7/mutations.json::test_thing")]


def test_browser_evidence_directories_are_never_treated_as_mutation_specs(tmp_path: Path) -> None:
    """A checker's own sabotage log under a `browser-*` evidence directory is a
    LIST of rows (row/file/baseline/after/detail), a different artifact shape
    entirely from a maker's `{"mutations": [...]}` spec."""
    spec_dir = tmp_path / "qa" / "evidence" / "browser-something-checker"
    spec_dir.mkdir(parents=True)
    (spec_dir / "mutations.json").write_text(
        json.dumps([{"row": "1", "file": "x"}]), encoding="utf-8")

    assert check_stale_evidence_specs(tmp_path) == []


def test_a_non_dict_mutations_json_is_never_crashed_on(tmp_path: Path) -> None:
    spec_dir = tmp_path / "qa" / "evidence" / "u8"
    spec_dir.mkdir(parents=True)
    (spec_dir / "mutations.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    assert check_stale_evidence_specs(tmp_path) == []


def test_no_qa_evidence_directory_is_not_an_error(tmp_path: Path) -> None:
    assert check_stale_evidence_specs(tmp_path) == []


def test_the_tombstone_entry_forbids_an_unknown_key() -> None:
    with pytest.raises(ValidationError):
        EvidenceTombstoneEntry.model_validate({
            "old_nodeid": "a.py::b", "moved_to": "c.py::d", "moved_by_unit": "u9",
            "unexpected": "nope"})


def test_the_tombstone_entry_refuses_a_bare_moved_to() -> None:
    """Both ids must be `file::function` -- a bare `moved_to` would reopen the
    exact "which file?" ambiguity the tombstone exists to remove."""
    with pytest.raises(ValidationError):
        EvidenceTombstoneEntry.model_validate({
            "old_nodeid": "a.py::b", "moved_to": "bare_name", "moved_by_unit": "u9"})


def test_the_check_is_wired_into_autotester_doctor() -> None:
    """A check nobody wires into `autotester doctor`'s run() is a check nobody
    runs -- the exact silent-omission shape this project keeps rediscovering."""
    assert "check_stale_evidence_specs" in inspect.getsource(doctor.run)


def test_the_repos_own_evidence_specs_are_clean_or_honestly_tombstoned() -> None:
    """Anti-regression over the real repo: every mutations.json this project
    carries today either still resolves or is tagged stale-on-purpose with a
    tombstone whose `moved_to` actually resolves. AT-469, AT-496, AT-500,
    AT-504, AT-506, AT-509 and AT-511 are the seven this unit tagged; AT-311,
    AT-520 and AT-523 use the bare-name style and were never actually stale."""
    assert check_stale_evidence_specs(repo_root()) == []
