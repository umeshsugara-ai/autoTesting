"""The enforcement layer must actually catch the drift it claims to catch."""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester import doctor

try:
    import _winapi
except ImportError:  # not Windows
    _winapi = None


def make_repo(tmp_path: Path) -> Path:
    (tmp_path / "src" / "autotester").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    return tmp_path


def write_module(root: Path, name: str, body: str) -> None:
    (root / "src" / "autotester" / name).write_text(body, encoding="utf-8")


def test_clean_repo_reports_nothing(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write_module(root, "ok.py", "def small():\n    return 1\n")
    assert doctor.run(root) == []


def test_long_file_is_flagged(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write_module(root, "big.py", "x = 1\n" * (doctor.MAX_FILE_LINES + 5))
    assert any(v.rule == "file-too-long" for v in doctor.run(root))


def test_the_line_cap_reads_every_file_c2_names_not_only_python(tmp_path: Path) -> None:
    """AT-419: C2 says "no file in src/ or tests/". Doctor measured only *.py, so a
    316-line visual_order.js printed "doctor: clean"."""
    root = make_repo(tmp_path)
    write_module(root, "browser.js", "x;\n" * (doctor.MAX_FILE_LINES + 1))
    fixtures = root / "tests" / "fixtures" / "site"
    fixtures.mkdir(parents=True)
    page = "<p>x</p>\n" * (doctor.MAX_FILE_LINES + 1)
    (fixtures / "page.html").write_text(page, encoding="utf-8")
    flagged = {v.location.replace("\\", "/") for v in doctor.run(root) if v.rule == "file-too-long"}
    assert flagged == {"src/autotester/browser.js", "tests/fixtures/site/page.html"}


def test_the_line_cap_allows_exactly_the_cap_and_skips_binary_files(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write_module(root, "at_cap.js", "x;\n" * doctor.MAX_FILE_LINES)
    (root / "tests" / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe" + b"\n" * 400)
    assert not any(v.rule == "file-too-long" for v in doctor.run(root))


needs_junctions = pytest.mark.skipif(not hasattr(_winapi, "CreateJunction"),
                                     reason="Windows junctions only")


@needs_junctions
def test_the_line_cap_never_follows_a_junction_in_or_out_of_the_tree(tmp_path: Path) -> None:
    """AT-461: rglob walked junctions, so a loop crashed doctor (WinError 1921) and a
    junction to a foreign folder had that folder's files capped as if they were ours."""
    root = make_repo(tmp_path / "repo")
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "big.txt").write_text("x\n" * (doctor.MAX_FILE_LINES + 100), encoding="utf-8")
    (root / "tests" / "loop").mkdir()
    _winapi.CreateJunction(str(root / "tests" / "loop"), str(root / "tests" / "loop" / "back"))
    _winapi.CreateJunction(str(outside), str(root / "tests" / "ext"))
    assert not any(v.rule == "file-too-long" for v in doctor.run(root))


@needs_junctions
def test_the_line_cap_still_walks_a_repo_opened_through_a_junction(tmp_path: Path) -> None:
    """The prune compares a directory with its RESOLVED parent, so a checkout reached
    through a junction is still ours, not a foreign tree."""
    real = make_repo(tmp_path / "real")
    (real / "tests" / "fixtures").mkdir()
    (real / "tests" / "fixtures" / "big.html").write_text("x\n" * (doctor.MAX_FILE_LINES + 1),
                                                          encoding="utf-8")
    _winapi.CreateJunction(str(real), str(tmp_path / "alias"))
    flagged = [v for v in doctor.run(tmp_path / "alias") if v.rule == "file-too-long"]
    assert [v.location.replace("\\", "/") for v in flagged] == ["tests/fixtures/big.html"]


def test_the_line_cap_skips_tool_cache_directories(tmp_path: Path) -> None:
    """AT-461: a gitignored .pytest_cache under tests/ is tooling output, not a file of ours."""
    root = make_repo(tmp_path)
    cache = root / "tests" / ".pytest_cache" / "v" / "cache"
    cache.mkdir(parents=True)
    (cache / "nodeids").write_text("t\n" * (doctor.MAX_FILE_LINES + 1), encoding="utf-8")
    assert not any(v.rule == "file-too-long" for v in doctor.run(root))


def test_long_function_is_flagged(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    body = "def huge():\n" + "    x = 1\n" * (doctor.MAX_FUNCTION_LINES + 5)
    write_module(root, "long_fn.py", body)
    assert any(v.rule == "function-too-long" for v in doctor.run(root))


def test_versioned_filename_is_flagged(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write_module(root, "runner_v2.py", "x = 1\n")
    violations = doctor.run(root)
    assert any(v.rule == "drift-filename" for v in violations)


def test_duplicate_concept_across_modules_is_flagged(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    write_module(root, "a.py", "class Runner:\n    pass\n")
    write_module(root, "b.py", "class Runner:\n    pass\n")
    violations = doctor.run(root)
    assert any(v.rule == "duplicate-concept" for v in violations)


def test_root_clutter_is_flagged(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "_scratch_run.log").write_text("noise", encoding="utf-8")
    assert any(v.rule == "root-clutter" for v in doctor.run(root))


def test_a_second_ai_tools_instruction_file_is_not_root_clutter(tmp_path: Path) -> None:
    """AT-283: AGENTS.md is a real project-instruction surface (parallel to CLAUDE.md
    for a different AI tool), not scratch — it must not trip the same gate a stray
    log file does."""
    root = make_repo(tmp_path)
    (root / "AGENTS.md").write_text("# instructions\n", encoding="utf-8")
    assert not any(v.rule == "root-clutter" for v in doctor.run(root))


# -- AT-496: a handshake artifact naming an issue that has no ledger row -------


def _qa(root: Path, ledger: str, manifests: dict | None = None,
        verdicts: dict | None = None) -> None:
    (root / "qa").mkdir(parents=True, exist_ok=True)
    (root / "qa" / "issues.jsonl").write_text(ledger, encoding="utf-8")
    for kind, files in (("manifests", manifests or {}), ("verdicts", verdicts or {})):
        (root / "qa" / kind).mkdir(exist_ok=True)
        for name, body in files.items():
            (root / "qa" / kind / name).write_text(body, encoding="utf-8")


ROW = '{"id": "AT-900", "severity": "low", "title": "t", "status": "%s"}'


def test_an_issue_a_manifest_names_must_still_have_a_ledger_row(tmp_path: Path) -> None:
    """AT-496: two loops share this tree, and a commit built from a stale copy of
    qa/issues.jsonl drops rows another loop appended. AT-494's row vanished that way
    while its verdict stayed in git — so the verdict is what makes the loss visible."""
    _qa(tmp_path, ledger="", manifests={"u.md": "**Issues addressed:** AT-900 (low, open)"})

    codes = [(v.rule, v.location) for v in doctor.check_qa_issue_rows(tmp_path)]

    assert ("ledger-row-lost", "qa/manifests/u.md") in codes


def test_an_issue_a_verdict_wrote_must_still_have_a_ledger_row(tmp_path: Path) -> None:
    _qa(tmp_path, ledger=ROW % "open",
        verdicts={"u.md": "ISSUES-WRITTEN: AT-900 (low), AT-901 (medium)"})

    lost = [(v.rule, v.detail) for v in doctor.check_qa_issue_rows(tmp_path)]

    assert [r for r, d in lost if "AT-901" in d] == ["ledger-row-lost"], lost
    assert not any("AT-900" in d for _, d in lost), "AT-900 has a row; only AT-901 is missing"


def test_a_passed_unit_whose_issue_is_still_open_is_a_stale_row(tmp_path: Path) -> None:
    """AT-401's row was flipped to `fixed` by its PASS and then reverted to `open` by a
    later stale write. Nothing noticed, because the verdict file was still right."""
    _qa(tmp_path, ledger=ROW % "open",
        manifests={"u.md": "**Issues addressed:** AT-900 (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: PASS"})

    codes = [v.rule for v in doctor.check_qa_issue_rows(tmp_path)]

    assert "ledger-row-stale" in codes


def test_a_passed_unit_whose_issue_is_fixed_is_not_flagged(tmp_path: Path) -> None:
    _qa(tmp_path, ledger=ROW % "fixed",
        manifests={"u.md": "**Issues addressed:** AT-900 (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: PASS"})

    assert doctor.check_qa_issue_rows(tmp_path) == []


def test_a_failed_or_unchecked_unit_leaves_its_issue_open(tmp_path: Path) -> None:
    """Only a PASS is evidence the issue was closed; an open row is correct otherwise."""
    _qa(tmp_path, ledger=ROW % "open",
        manifests={"u.md": "**Issues addressed:** AT-900 (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: FAIL"})

    assert doctor.check_qa_issue_rows(tmp_path) == []


def test_a_project_with_no_qa_directory_is_not_a_violation(tmp_path: Path) -> None:
    assert doctor.check_qa_issue_rows(tmp_path) == []


@pytest.mark.parametrize("issue", ["AT-900", "AT-900b"])
def test_a_letter_suffixed_id_is_an_id_too(issue: str, tmp_path: Path) -> None:
    r"""AT-500: when two checkers file the same defect, the second row takes a letter
    suffix — AT-297b, AT-298b and AT-299b are live rows filed under that convention.
    Both regexes ended at a word boundary straight after the digits, and `\bAT-\d+\b`
    matches nothing at all inside `AT-297b`, so a manifest naming one was invisible."""
    _qa(tmp_path, ledger="", manifests={"u.md": f"**Issues addressed:** {issue} (low, open)"})

    lost = [(v.rule, v.detail) for v in doctor.check_qa_issue_rows(tmp_path)]

    assert [r for r, d in lost if issue in d] == ["ledger-row-lost"], lost


@pytest.mark.parametrize("issue", ["AT-900", "AT-900b"])
def test_a_letter_suffixed_id_is_read_on_both_sides_of_the_comparison(
    issue: str, tmp_path: Path
) -> None:
    """Widening only the handshake side would turn every suffixed row into a phantom
    loss: the id is read a second time out of the LEDGER, and the two must agree or
    the check reports a row it is looking at as missing."""
    _qa(tmp_path, ledger=ROW.replace("AT-900", issue) % "open",
        manifests={"u.md": f"**Issues addressed:** {issue} (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: PASS"})

    codes = [v.rule for v in doctor.check_qa_issue_rows(tmp_path)]

    assert codes == ["ledger-row-stale"], "the row EXISTS (never lost), it is only stale"


@pytest.mark.parametrize("line", [
    "ISSUES-WRITTEN: AT-900",
    "**ISSUES-WRITTEN:** AT-900",
    "## ISSUES-WRITTEN: AT-900",
    "  - ISSUES-WRITTEN: AT-900",
])
def test_a_decorated_marker_line_is_still_a_marker_line(line: str, tmp_path: Path) -> None:
    """The AT-504 fix must not read the marker so strictly that real claims vanish.
    Both decorated forms are live: `at097-session-start-hook-regression.md` writes
    `**ISSUES-WRITTEN:**` and `at206-guards-that-guard.md` writes `## ISSUES-WRITTEN:`.
    Measured before the fix: a bare `startswith` would have dropped 12 real claims."""
    _qa(tmp_path, ledger="", verdicts={"u.md": line})

    assert [v.rule for v in doctor.check_qa_issue_rows(tmp_path)] == ["ledger-row-lost"]


@pytest.mark.parametrize("line", [
    "on manifest `**Issues addressed:**` lines: AT-900 (at900-thing.md)",
    "none of them sits on a `**Issues addressed:**` line, so AT-900 is invisible",
])
def test_prose_that_quotes_the_marker_is_not_a_claim(line: str, tmp_path: Path) -> None:
    """AT-504: `marker in line` read a document DISCUSSING the marker as one USING it,
    so at500's own manifest counted itself and then its verdict counted too — the
    probe's violation count compounded 2 -> 3 -> 4 as each artifact appeared, without
    bound. A backtick is what separates the two cases; markdown decoration is not."""
    _qa(tmp_path, ledger="", manifests={"u.md": line})

    assert doctor.check_qa_issue_rows(tmp_path) == []


def test_a_line_opening_with_the_marker_in_backticks_is_not_a_claim(tmp_path: Path) -> None:
    """The real shape from at500's own verdict, and the reason a backtick is not
    stripped as decoration: here the marker IS at the start of the line's content, so
    only the backtick separates prose from a claim."""
    _qa(tmp_path, ledger="",
        verdicts={"u.md": "`ISSUES-WRITTEN` marker. The only id it newly reads is AT-900."})

    assert doctor.check_qa_issue_rows(tmp_path) == []


def test_an_issue_a_manifest_says_it_did_NOT_fix_stays_open(tmp_path: Path) -> None:
    """A manifest may name issues it filed and deliberately left open —
    `at227-first-paint-modal` names AT-335 that way. Reading "NOT fixed" as a fix
    claim made that unit's PASS look like a stale row."""
    _qa(tmp_path, ledger=ROW % "open",
        manifests={"u.md": "**Issues addressed:** AT-900 (filed, NOT fixed - reasons below)"},
        verdicts={"u.md": "VERDICT: PASS"})

    assert doctor.check_qa_issue_rows(tmp_path) == []
