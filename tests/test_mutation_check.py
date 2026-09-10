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

MODULE = '''def classify(value):
    if value > 10:
        return "big"
    return "small"
'''

TESTS = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from mod import classify


def test_big_values_are_big():
    assert classify(50) == "big"


def test_small_values_are_small():
    assert classify(1) == "small"
'''


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts" / "mod.py").write_text(MODULE, encoding="utf-8")
    (tmp_path / "tests" / "test_mod.py").write_text(TESTS, encoding="utf-8")
    return tmp_path


def spec(**overrides) -> dict:
    mutation = {
        "name": "threshold broken", "file": "scripts/mod.py",
        "old": 'if value > 10:', "new": 'if value > 0:',
        "kills": ["test_small_values_are_small"],
    }
    mutation.update(overrides.pop("mutation", {}))
    return {"tests": "tests/test_mod.py", "mutations": [mutation], **overrides}


# -- the happy path ----------------------------------------------------------

def test_a_real_mutation_is_killed_and_attributed(repo: Path) -> None:
    result = check(spec(), repo)[0]

    assert result["killed"] is True
    assert result["failed"] == ["test_small_values_are_small"]
    assert result["survivors"] == []


def test_the_live_tree_is_never_touched(repo: Path) -> None:
    """Mutations run in a copy outside the repo."""
    before = (repo / "scripts" / "mod.py").read_bytes()

    check(spec(), repo)

    assert (repo / "scripts" / "mod.py").read_bytes() == before


# -- AT-311: a `kills` label is a claim, not a comment ------------------------

def test_it_refuses_a_kills_label_naming_a_test_that_does_not_exist(repo: Path) -> None:
    """The exact defect: the predecessor's label named a renamed test for four
    runs and reported KILLED each time, because nothing checked the name."""
    with pytest.raises(MutationError, match="not collected"):
        check(spec(mutation={"kills": ["test_this_was_renamed_ages_ago"]}), repo)


def test_it_refuses_when_the_named_test_survives_but_another_fails(repo: Path) -> None:
    """The suite going red is not evidence that THIS test noticed."""
    result = check(spec(mutation={"kills": ["test_big_values_are_big"]}), repo)[0]

    assert result["killed"] is False
    assert result["survivors"] == ["test_big_values_are_big"]
    assert result["failed"] == ["test_small_values_are_small"]


# -- AT-307: a kill measured against a red baseline is meaningless ------------

def test_it_refuses_a_red_baseline(repo: Path) -> None:
    (repo / "tests" / "test_mod.py").write_text(
        TESTS + "\n\ndef test_already_broken():\n    assert False\n", encoding="utf-8")

    with pytest.raises(MutationError, match="baseline is NOT green"):
        check(spec(), repo)


# -- AT-311: an exit code is not a kill --------------------------------------

def test_a_mutation_that_breaks_collection_is_not_a_kill(repo: Path) -> None:
    """A syntax error exits non-zero having run NOTHING. The predecessor
    reported that as `KILLED  1 error` with an empty failure list."""
    result = check(spec(mutation={"new": "if value > (((:"}), repo)[0]

    assert result["killed"] is False
    assert result["failed"] == []
    assert result["collected_nothing"] is True


# -- the anchor discipline ---------------------------------------------------

def test_it_refuses_an_anchor_that_matches_more_than_once(repo: Path) -> None:
    with pytest.raises(MutationError, match="anchor matched"):
        check(spec(mutation={"old": "value", "new": "value"}), repo)


def test_it_refuses_an_anchor_that_matches_nothing(repo: Path) -> None:
    with pytest.raises(MutationError, match="anchor matched 0 times"):
        check(spec(mutation={"old": "no such source line"}), repo)


def test_it_refuses_a_mutation_that_changes_nothing(repo: Path) -> None:
    with pytest.raises(MutationError, match="changed nothing"):
        check(spec(mutation={"old": "if value > 10:", "new": "if value > 10:"}), repo)


def test_it_refuses_a_spec_with_no_mutations(repo: Path) -> None:
    with pytest.raises(MutationError, match="no mutations"):
        check({"tests": "tests/test_mod.py", "mutations": []}, repo)


# -- output parsing ----------------------------------------------------------

def test_failed_tests_reads_names_out_of_pytest_output() -> None:
    output = ("FAILED tests/test_mod.py::test_small_values_are_small - assert 'big' == 'small'\n"
              "FAILED tests/test_mod.py::test_big_values_are_big\n"
              "1 failed, 1 passed\n")

    assert failed_tests(output) == {"test_small_values_are_small", "test_big_values_are_big"}


def test_the_spec_round_trips_through_json(repo: Path) -> None:
    """Specs live on disk beside a unit's evidence, so they must survive JSON."""
    path = repo / "mutations.json"
    path.write_text(json.dumps(spec()), encoding="utf-8")

    assert check(json.loads(path.read_text(encoding="utf-8")), repo)[0]["killed"] is True
