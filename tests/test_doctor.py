"""The enforcement layer must actually catch the drift it claims to catch."""

from __future__ import annotations

from pathlib import Path

from autotester import doctor


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
