"""AT-065: 4 pre-existing rubrics on disk (written before provenance stamping
existed, AT-059) are NOT in fact indistinguishable from hand-written ones --
they carry the generator's exact template -- but `is_stale_default` treats an
unprovenanced rubric as hand-authored and never touches it, so they can never
self-heal. This script finds rubrics whose shape is byte-identical to what
`run_case_pipeline._rubric_for_claim` would have produced and stamps them with
the SAME provenance the generator writes today -- nothing else in the file
changes. DRY RUN BY DEFAULT, per AT-065's own fix direction: "a one-off
migration ... reviewed by a human per file -- not an automatic runtime
heuristic."
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from migrate_stamp_legacy_rubrics import apply, candidate, main, scan

from autotester.schema.base import Provenance
from autotester.schema.verdict import Criterion, Rubric
from autotester.stages.run_case_pipeline import GENERATOR, _rubric_for_claim


def a_legacy_rubric(root: Path, rubric_id: str, claim: str, case_id: str = "case_1") -> Path:
    """A rubric shaped exactly like `default_rubric` produced before AT-059's
    provenance stamping existed -- same criteria/no_fire, `provenance: null`."""
    generated = _rubric_for_claim(claim, case_id, rubric_id)
    doc = generated.model_dump(mode="json")
    doc["provenance"] = None
    path = root / f"{rubric_id}.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return path


def a_handwritten_rubric(root: Path, rubric_id: str, case_id: str = "case_2") -> Path:
    """A rubric that merely happens to also carry `provenance: null` -- the
    every-day case for a genuinely hand-written rubric. Must never be touched."""
    rubric = Rubric(
        id=rubric_id, case_id=case_id,
        criteria=[Criterion(id="landed", text="the page the user asked for is shown")],
        no_fire=["visual styling"],
    )
    path = root / f"{rubric_id}.json"
    path.write_text(rubric.model_dump_json(indent=2), encoding="utf-8")
    return path


# -- candidate(): shape-only judgement, never a guess ------------------------

def test_a_legacy_generator_shaped_rubric_is_a_candidate(tmp_path: Path) -> None:
    path = a_legacy_rubric(tmp_path, "rub_case_1", "the login page is shown")
    rubric = Rubric.model_validate_json(path.read_text(encoding="utf-8"))

    assert candidate(rubric) == "the login page is shown"


def test_a_hand_written_rubric_is_never_a_candidate(tmp_path: Path) -> None:
    path = a_handwritten_rubric(tmp_path, "rub_case_2")
    rubric = Rubric.model_validate_json(path.read_text(encoding="utf-8"))

    assert candidate(rubric) is None


def test_an_already_stamped_rubric_is_never_a_candidate_again(tmp_path: Path) -> None:
    rubric = _rubric_for_claim("the login page is shown", "case_3", "rub_case_3")
    assert rubric.provenance is not None

    assert candidate(rubric) is None


def test_a_rubric_edited_since_generation_is_never_a_candidate(tmp_path: Path) -> None:
    """Same criterion id, DIFFERENT no_fire -- a human touched it since. Even
    with provenance stripped, its shape no longer matches the template."""
    generated = _rubric_for_claim("the login page is shown", "case_4", "rub_case_4")
    edited = generated.model_copy(update={
        "provenance": None, "no_fire": ["something the human chose to exempt"],
    })

    assert candidate(edited) is None


# -- scan()/apply(): the script over real files -------------------------------

def test_scan_finds_only_the_legacy_shaped_files(tmp_path: Path) -> None:
    legacy = a_legacy_rubric(tmp_path, "rub_case_1", "the login page is shown")
    a_handwritten_rubric(tmp_path, "rub_case_2")

    found = scan(tmp_path)

    assert [p for p, _claim in found] == [legacy]
    assert found[0][1] == "the login page is shown"


def test_apply_stamps_provenance_and_changes_nothing_else(tmp_path: Path) -> None:
    path = a_legacy_rubric(tmp_path, "rub_case_1", "the login page is shown", case_id="case_1")
    before = Rubric.model_validate_json(path.read_text(encoding="utf-8"))

    apply(path, "the login page is shown")

    after = Rubric.model_validate_json(path.read_text(encoding="utf-8"))
    assert after.provenance == Provenance(
        produced_by=GENERATOR, inputs=["case_1"], note="the login page is shown",
    )
    assert after.criteria == before.criteria
    assert after.no_fire == before.no_fire
    assert after.id == before.id
    assert after.case_id == before.case_id


def test_running_it_twice_changes_nothing_the_second_time(tmp_path: Path) -> None:
    path = a_legacy_rubric(tmp_path, "rub_case_1", "the login page is shown")
    apply(path, "the login page is shown")
    before = path.read_bytes()

    assert scan(tmp_path) == []  # no longer a candidate -- provenance is set
    assert path.read_bytes() == before


# -- the CLI: dry run by default ----------------------------------------------

def test_dry_run_reports_but_does_not_write(tmp_path: Path) -> None:
    path = a_legacy_rubric(tmp_path, "rub_case_1", "the login page is shown")
    before = path.read_bytes()

    assert main(["--root", str(tmp_path)]) == 0

    assert path.read_bytes() == before


def test_write_stamps_every_candidate(tmp_path: Path) -> None:
    a_legacy_rubric(tmp_path, "rub_case_1", "the login page is shown")
    a_handwritten_rubric(tmp_path, "rub_case_2")

    assert main(["--root", str(tmp_path), "--write"]) == 0

    stamped = Rubric.model_validate_json((tmp_path / "rub_case_1.json").read_text())
    untouched = Rubric.model_validate_json((tmp_path / "rub_case_2.json").read_text())
    assert stamped.provenance is not None
    assert untouched.provenance is None


def test_write_with_only_stamps_the_named_file_alone(tmp_path: Path) -> None:
    a = a_legacy_rubric(tmp_path, "rub_case_1", "the login page is shown")
    b = a_legacy_rubric(tmp_path, "rub_case_2", "the signup page is shown", case_id="case_2")

    assert main(["--root", str(tmp_path), "--write", "--only", str(a)]) == 0

    assert Rubric.model_validate_json(a.read_text()).provenance is not None
    assert Rubric.model_validate_json(b.read_text()).provenance is None


def test_a_missing_root_is_reported_not_raised(tmp_path: Path) -> None:
    assert main(["--root", str(tmp_path / "nope")]) == 2
