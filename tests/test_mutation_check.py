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


def test_failed_tests_reads_pytests_own_report_and_nothing_else(tmp_path: Path) -> None:
    """AT-320 + AT-478: full nodeids, straight from the report the sandbox plugin writes.
    Two tests sharing a bare name stay distinct; no report means no failures."""
    work = tmp_path / "repo"
    work.mkdir()
    assert failed_tests(work) == set(), "no report must never read as a failure"
    (tmp_path / "mutation-report.json").write_text(json.dumps([
        "tests/test_mod.py::test_small_values_are_small",
        "tests/other/test_mod.py::test_small_values_are_small",
        "tests/t.py::test_x[a b] - r]"]), encoding="utf-8")

    assert failed_tests(work) == {"tests/test_mod.py::test_small_values_are_small",
                                  "tests/other/test_mod.py::test_small_values_are_small",
                                  "tests/t.py::test_x[a b] - r]"}

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


# -- AT-478 / AT-479: failures come from pytest's own reports, not from text ------

def _write(path: Path, *lines: str) -> None:
    path.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")


IMPORT_SCRIPTS = ('import sys', 'from pathlib import Path', 'import pytest',
                  'sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))')


def test_a_failing_test_that_prints_a_summary_line_cannot_fake_a_kill(
    mutation_repo: Path,
) -> None:
    """AT-478: `^FAILED` matched captured stdout, so a failing test printing
    "FAILED <sibling> - boom" made that PASSING sibling read KILLED."""
    _write(mutation_repo / "tests" / "test_p.py", *IMPORT_SCRIPTS, "from mod import classify",
           "", "", "def test_printer():",
           '    print("FAILED tests/test_p.py::test_ns[x] - boom")',
           '    assert classify(1) == "small"',
           "", "", '@pytest.mark.parametrize("v", ["x"])', "def test_ns(v):",
           '    assert classify(50) == "big"')

    result = check(spec(tests=["tests/test_mod.py", "tests/test_p.py"],
                        mutation={"kills": ["tests/test_p.py::test_ns[x]"]}), mutation_repo)[0]

    assert "tests/test_p.py::test_printer" in result["failed"], "precondition: the printer failed"
    assert result["killed"] is False, result


def test_a_named_test_that_did_not_run_under_the_mutation_is_never_killed(
    mutation_repo: Path,
) -> None:
    """AT-479: the mutation renames a parametrize id, so `test_gen[c]` does not exist in the
    mutated run. Its replacement `test_gen[c] - Failed: q]` fails, and its summary line fit
    the baseline nodeid, which was credited with a kill it never took part in."""
    _write(mutation_repo / "scripts" / "gen.py", 'GEN = ["c"]')
    _write(mutation_repo / "tests" / "test_gen.py", *IMPORT_SCRIPTS, "from gen import GEN",
           "", "", '@pytest.mark.parametrize("v", GEN)', "def test_gen(v):",
           '    if v != "c":', '        pytest.fail("w")')

    result = check(spec(tests=["tests/test_mod.py", "tests/test_gen.py"], mutation={
        "file": "scripts/gen.py", "old": 'GEN = ["c"]', "new": 'GEN = ["c] - Failed: q"]',
        "kills": ["tests/test_gen.py::test_gen[c]"]}), mutation_repo)[0]

    assert result["killed"] is False, result
    assert "tests/test_gen.py::test_gen[c]" not in result["failed"]


def test_a_named_test_that_errors_in_setup_is_not_a_kill(mutation_repo: Path) -> None:
    """Only a failed CALL is the test noticing the mutation. A fixture that errors never ran
    the test's own assertion, so it stays out of the failures, as ERROR lines always did."""
    _write(mutation_repo / "tests" / "test_setup.py", *IMPORT_SCRIPTS, "from mod import classify",
           "", "", "@pytest.fixture", "def small():",
           '    assert classify(1) == "small"', "    return 1",
           "", "", "def test_uses_fixture(small):", "    assert small == 1")

    result = check(spec(tests=["tests/test_mod.py", "tests/test_setup.py"],
                        mutation={"kills": ["tests/test_setup.py::test_uses_fixture"]}),
                   mutation_repo)[0]

    assert result["killed"] is False, result
    assert "tests/test_setup.py::test_uses_fixture" not in result["failed"]


@pytest.mark.parametrize("tamper", ['os.environ["MUTATION_REPORT"] = "elsewhere.json"',
                                    'os.environ.pop("MUTATION_REPORT")'],
                         ids=["reassigned", "removed"])
def test_a_test_that_touches_the_report_variable_cannot_hide_a_kill(
    mutation_repo: Path, tamper: str,
) -> None:
    """AT-481: the plugin read MUTATION_REPORT at session end, after every test had run, so a
    test that reassigned it read every kill as SURVIVED, and one that removed it broke the run."""
    _write(mutation_repo / "tests" / "test_env.py", "import os", "", "", "def test_env():",
           f"    {tamper}")

    result = check(spec(tests=["tests/test_env.py", "tests/test_mod.py"]), mutation_repo)[0]

    assert result["killed"] is True, result
