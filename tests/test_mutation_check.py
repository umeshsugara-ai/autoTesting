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


# -- AT-324: the ambiguity guard's own prescribed remedy ----------------------


def test_a_kills_entry_may_be_the_full_nodeid_the_guard_asks_for(
    mutation_repo: Path,
) -> None:
    """AT-324. The ambiguity guard says "name the full nodeid", and naming one
    was then refused as "not collected" — the guard's own prescribed remedy did
    not work. Live in this repo: two test files share
    `test_act_without_a_schema_raises`."""
    result = check(spec(mutation={"kills": ["tests/test_mod.py::test_small_values_are_small"]}),
                   mutation_repo)[0]

    assert result["killed"] is True
    assert result["expected"] == ["tests/test_mod.py::test_small_values_are_small"]



# -- AT-469: a parametrized id may contain spaces ------------------------------

def test_failed_tests_keeps_a_nodeid_whose_parametrize_id_contains_spaces() -> None:
    """AT-469: `\S+` cut `test_x[a b]` to `test_x[a`, so the named test never appeared
    in the failures and a genuine kill printed as SURVIVED. The collected nodeids are
    the authority on where a nodeid ends."""
    known = {"tests/t.py::test_x[a]", "tests/t.py::test_x[a b]", "tests/t.py::test_y",
             "tests/t.py::test_z[q]", "tests/t.py::test_z[q] - r]"}
    output = ("FAILED tests/t.py::test_x[a b] - AssertionError: boom" + chr(10)
              + "FAILED tests/t.py::test_y" + chr(10))

    assert failed_tests(output, known) == {"tests/t.py::test_x[a b]", "tests/t.py::test_y"}
    # AT-473: `test_z[q]` failing with message "r] - AssertionError" and `test_z[q] - r]`
    # failing with "AssertionError" print the SAME line. Crediting either is a guess, and
    # crediting the one that passed is a false KILLED, so neither is credited.
    ambiguous = "FAILED tests/t.py::test_z[q] - r] - AssertionError" + chr(10)
    assert failed_tests(ambiguous, known) == set()
    # Unambiguous siblings are still attributed: the SHORTER one failing with a plain message.
    shorter = "FAILED tests/t.py::test_z[q] - AssertionError: boom" + chr(10)
    assert failed_tests(shorter, known) == {"tests/t.py::test_z[q]"}
    # A known nodeid that is merely a PREFIX of an uncollected one must not claim its
    # failure: that would be a false KILLED for `test_y`. The regex reading stands.
    stranger = "FAILED tests/t.py::test_yz - AssertionError" + chr(10)
    assert failed_tests(stranger, known) == {"tests/t.py::test_yz"}


def test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id(
    mutation_repo: Path,
) -> None:
    (mutation_repo / "tests" / "test_spaced.py").write_text(
        "import sys" + chr(10) + "from pathlib import Path" + chr(10)
        + "import pytest" + chr(10)
        + 'sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))' + chr(10)
        + "from mod import classify" + chr(10) + chr(10) + chr(10)
        + '@pytest.mark.parametrize("value", [1, 2], ids=["one small value", "two"])' + chr(10)
        + "def test_small(value):" + chr(10)
        + '    assert classify(value) == "small"' + chr(10), encoding="utf-8")
    spaced = "tests/test_spaced.py::test_small[one small value]"

    result = check(spec(tests=["tests/test_mod.py", "tests/test_spaced.py"],
                        mutation={"kills": [spaced]}), mutation_repo)[0]

    assert result["killed"] is True, result
    assert spaced in result["failed"]


def test_a_passing_sibling_is_never_credited_with_another_tests_failure(
    mutation_repo: Path,
) -> None:
    """AT-473, reproduced through real pytest: only `[a]` fails, with a message that makes
    its summary line read exactly like its sibling's nodeid. The at469 cycle-1 instrument
    reported the sibling -- which PASSED -- as KILLED."""
    (mutation_repo / "tests" / "test_amb.py").write_text(
        "import sys" + chr(10) + "from pathlib import Path" + chr(10)
        + "import pytest" + chr(10)
        + 'sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))' + chr(10)
        + "from mod import classify" + chr(10) + chr(10) + chr(10)
        + '@pytest.mark.parametrize("value", [1, 50], ids=["a", "a] - AssertionError: r"])'
        + chr(10) + "def test_amb(value):" + chr(10)
        + '    assert classify(value) == ("small" if value < 10 else "big"), "r]"' + chr(10),
        encoding="utf-8")
    sibling = "tests/test_amb.py::test_amb[a] - AssertionError: r]"

    result = check(spec(tests=["tests/test_mod.py", "tests/test_amb.py"],
                        mutation={"kills": [sibling]}), mutation_repo)[0]

    assert result["killed"] is False, result
    assert sibling not in result["failed"]
