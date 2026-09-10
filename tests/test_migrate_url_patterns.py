"""The AT-287/AT-294 stored-data repair. Contract: qa/contracts/coverage.md V1.

Checker B's ruling (AT-297b): the maker's first attempt at this was an untracked
hand-edit of `projects/erp/screenmap.json` — a value the code could not
reproduce, backed by a gitignored copy and tested by nothing, made while the
producer that regenerates it was still broken. This is that repair done as
something a person can run, re-run, and read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from migrate_url_patterns import apply, main, repair, scan


def a_screenmap(root: Path, *patterns: str | None) -> Path:
    path = root / "erp" / "screenmap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "project": "erp",
        "screens": [{"name": f"s{i}", "url_pattern": p} for i, p in enumerate(patterns)],
    }), encoding="utf-8")
    return path


def patterns_of(path: Path) -> list[str | None]:
    return [s["url_pattern"] for s in json.loads(path.read_text(encoding="utf-8"))["screens"]]


# -- what counts as mangled --------------------------------------------------

def test_a_swallowed_host_is_repaired() -> None:
    assert repair("/vidysea.com/erp/trainers") == "/erp/trainers"
    assert repair("/demo.test/students/{id}") == "/students/{id}"
    assert repair("/demo.test") == "/"


def test_a_healthy_pattern_is_left_alone() -> None:
    for healthy in ("/erp/trainers", "/", "/students/{id}", "/reports/new"):
        assert repair(healthy) is None, healthy


def test_a_real_path_segment_containing_a_dot_is_not_treated_as_a_host() -> None:
    """The mirror of AT-291: the repair must not eat a legitimate segment. It
    matches only a FIRST segment carrying a dotted label pair, so a versioned or
    file-shaped segment deeper in the path is untouched."""
    assert repair("/v1/release-1.0/notes") is None
    assert repair("/docs/settings.json") is None


# -- the script itself -------------------------------------------------------

def test_it_repairs_a_file_and_reports_what_it_changed(tmp_path: Path) -> None:
    path = a_screenmap(tmp_path, "/vidysea.com/erp/trainers", None, "/erp/ok")

    found = scan(tmp_path)

    assert [p for p, _ in found] == [path]
    assert found[0][1] == [("/vidysea.com/erp/trainers", "/erp/trainers")]
    assert apply(path) == 1
    assert patterns_of(path) == ["/erp/trainers", None, "/erp/ok"]


def test_running_it_twice_changes_nothing_the_second_time(tmp_path: Path) -> None:
    """Idempotent, so a human can re-run it without thinking about it."""
    path = a_screenmap(tmp_path, "/vidysea.com/erp/trainers")
    apply(path)
    before = path.read_bytes()

    assert apply(path) == 0
    assert path.read_bytes() == before


def test_it_is_a_dry_run_unless_told_otherwise(tmp_path: Path, capsys) -> None:
    """Writing to real project data is a human's call, so the default must not."""
    path = a_screenmap(tmp_path, "/vidysea.com/erp/trainers")

    assert main(["--root", str(tmp_path)]) == 0

    assert patterns_of(path) == ["/vidysea.com/erp/trainers"], "dry run wrote to disk"
    assert "dry run" in capsys.readouterr().out


def test_write_applies_the_repair(tmp_path: Path) -> None:
    path = a_screenmap(tmp_path, "/vidysea.com/erp/trainers")

    assert main(["--root", str(tmp_path), "--write"]) == 0

    assert patterns_of(path) == ["/erp/trainers"]


def test_a_clean_tree_reports_nothing_to_do(tmp_path: Path, capsys) -> None:
    a_screenmap(tmp_path, "/erp/trainers", None)

    assert main(["--root", str(tmp_path)]) == 0
    assert "nothing to repair" in capsys.readouterr().out


def test_it_walks_past_json_that_uses_screens_for_something_else(tmp_path: Path) -> None:
    """A crawl manifest carries `"screens": 1` — a COUNT. The script walks every
    json file under the root, so it meets these. The fixture-only tests missed
    it; the dry run against real project data crashed on the first one."""
    (tmp_path / "erp").mkdir(parents=True)
    (tmp_path / "erp" / "crawl.json").write_text(
        json.dumps({"id": "crawl_1", "screens": 1, "edges": 3}), encoding="utf-8")
    (tmp_path / "erp" / "notes.json").write_text(json.dumps(["a", "b"]), encoding="utf-8")
    (tmp_path / "erp" / "broken.json").write_text("{not json", encoding="utf-8")
    target = a_screenmap(tmp_path, "/vidysea.com/erp/trainers")

    found = scan(tmp_path)

    assert [p for p, _ in found] == [target]
