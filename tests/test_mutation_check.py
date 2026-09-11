"""The mutation instrument itself. Contract: qa/contracts/core-invariants.md C7.

C7 now obliges any unit that adds or rewrites a test to prove the test dies when
the behaviour it names is reverted. That makes `scripts/mutation_check.py` a
gate, and a gate nobody attacks is the thing this whole session kept finding.

Its predecessor reported four confident kills while its `defends:` label named a
test that **did not exist** (AT-311), and defined a kill as `exit != 0`, so a
red baseline (AT-307) or a mutation that broke collection entirely both counted
as proof. Every test below exists to make one of those refusals real.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from mutation_check import MutationError, check, failed_tests
from tests_mutation_fixtures import TESTS, spec

# -- the happy path ----------------------------------------------------------

def test_a_real_mutation_is_killed_and_attributed(mutation_repo: Path) -> None:
    result = check(spec(), mutation_repo)[0]

    assert result["killed"] is True
    assert result["survivors"] == []
    # AT-320: attribution is by full nodeid, never a bare name — a bare name is
    # satisfied by a same-named test in a module the mutation never touched.
    assert result["failed"] == ["tests/test_mod.py::test_small_values_are_small"]
    assert result["expected"] == ["tests/test_mod.py::test_small_values_are_small"]


def test_the_live_tree_is_never_touched(mutation_repo: Path) -> None:
    """Mutations run in a copy outside the repo."""
    before = (mutation_repo / "scripts" / "mod.py").read_bytes()

    check(spec(), mutation_repo)

    assert (mutation_repo / "scripts" / "mod.py").read_bytes() == before


# -- AT-311: a `kills` label is a claim, not a comment ------------------------

def test_it_refuses_a_kills_label_naming_a_test_that_does_not_exist(mutation_repo: Path) -> None:
    """The exact defect: the predecessor's label named a renamed test for four
    runs and reported KILLED each time, because nothing checked the name."""
    with pytest.raises(MutationError, match="not collected"):
        check(spec(mutation={"kills": ["test_this_was_renamed_ages_ago"]}), mutation_repo)


def test_it_refuses_when_the_named_test_survives_but_another_fails(mutation_repo: Path) -> None:
    """The suite going red is not evidence that THIS test noticed."""
    result = check(spec(mutation={"kills": ["test_big_values_are_big"]}), mutation_repo)[0]

    assert result["killed"] is False
    assert result["survivors"] == ["tests/test_mod.py::test_big_values_are_big"]
    assert result["failed"] == ["tests/test_mod.py::test_small_values_are_small"]


# -- AT-307: a kill measured against a red baseline is meaningless ------------

def test_it_refuses_a_red_baseline(mutation_repo: Path) -> None:
    (mutation_repo / "tests" / "test_mod.py").write_text(
        TESTS + "\n\ndef test_already_broken():\n    assert False\n", encoding="utf-8")

    with pytest.raises(MutationError, match="baseline is NOT green"):
        check(spec(), mutation_repo)


# -- AT-311: an exit code is not a kill --------------------------------------

def test_a_mutation_that_breaks_collection_is_not_a_kill(mutation_repo: Path) -> None:
    """A syntax error exits non-zero having run NOTHING. The predecessor
    reported that as `KILLED  1 error` with an empty failure list."""
    result = check(spec(mutation={"new": "if value > (((:"}), mutation_repo)[0]

    assert result["killed"] is False
    assert result["failed"] == []
    assert result["no_test_results"] is True


# -- the anchor discipline ---------------------------------------------------

def test_it_refuses_an_anchor_that_matches_more_than_once(mutation_repo: Path) -> None:
    with pytest.raises(MutationError, match="anchor matched"):
        check(spec(mutation={"old": "value", "new": "value"}), mutation_repo)


def test_it_refuses_an_anchor_that_matches_nothing(mutation_repo: Path) -> None:
    with pytest.raises(MutationError, match="anchor matched 0 times"):
        check(spec(mutation={"old": "no such source line"}), mutation_repo)


def test_it_refuses_a_mutation_that_changes_nothing(mutation_repo: Path) -> None:
    with pytest.raises(MutationError, match="changed nothing"):
        check(spec(mutation={"old": "if value > 10:", "new": "if value > 10:"}), mutation_repo)


def test_it_refuses_a_spec_with_no_mutations(mutation_repo: Path) -> None:
    with pytest.raises(MutationError, match="no mutations"):
        check({"tests": "tests/test_mod.py", "mutations": []}, mutation_repo)


# -- output parsing ----------------------------------------------------------

def test_failed_tests_reads_names_out_of_pytest_output() -> None:
    output = (
        "FAILED tests/test_mod.py::test_small_values_are_small - assert" + chr(10)
        + "FAILED tests/other/test_mod.py::test_small_values_are_small" + chr(10)
        + "1 failed, 1 passed" + chr(10))

    # Two tests sharing a bare NAME in different files stay distinct (AT-320).
    assert failed_tests(output) == {"tests/test_mod.py::test_small_values_are_small",
                                    "tests/other/test_mod.py::test_small_values_are_small"}


def test_the_spec_round_trips_through_json(mutation_repo: Path) -> None:
    """Specs live on disk beside a unit's evidence, so they must survive JSON."""
    path = mutation_repo / "mutations.json"
    path.write_text(json.dumps(spec()), encoding="utf-8")

    assert check(json.loads(path.read_text(encoding="utf-8")), mutation_repo)[0]["killed"] is True


def test_a_suite_split_across_files_is_still_one_suite(mutation_repo: Path) -> None:
    """C2 splits a suite at 300 lines; a mutation must still be run against the
    WHOLE of it. Running only half would let a mutation look survived because
    the test that notices lives in the other file."""
    second = mutation_repo / "tests" / "test_mod_more.py"
    second.write_text(
        "import sys" + chr(10)
        + "from pathlib import Path" + chr(10)
        + "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))" + chr(10)
        + "from mod import classify" + chr(10) + chr(10)
        + "def test_in_the_other_half():" + chr(10)
        + "    assert classify(1) == 'small'" + chr(10), encoding="utf-8")

    result = check(spec(tests=["tests/test_mod.py", "tests/test_mod_more.py"],
                        mutation={"kills": ["test_in_the_other_half"]}), mutation_repo)[0]

    assert result["killed"] is True
    # The named test lives in the OTHER file; running only the first would have
    # reported it survived.
    assert "tests/test_mod_more.py::test_in_the_other_half" in result["failed"]
