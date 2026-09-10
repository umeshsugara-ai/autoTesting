"""The AT-287/AT-294 stored-data repair. Contract: qa/contracts/coverage.md V1.

Two reviews shaped this file, and both are worth remembering.

Checker B (AT-297b) ruled that the maker's first attempt at this repair was an
untracked hand-edit of `projects/erp/screenmap.json` — a value the code could
not reproduce, backed by a gitignored copy and tested by nothing. Hence a script
a person can run, re-run, and read.

Both cycle-3 checkers then filed **AT-298** against the script's guard: it
claimed to refuse a dotted FIRST path segment and did not (`/v1.2/foo` -> `/foo`,
`/index.html` -> `/`), and the test named for that guard asserted only *deeper*
segments — shapes the regex was never at risk of matching. It passed while its
own named property was false. So the guard now matches against the hosts the
project DECLARES, and the tests below assert the first-segment cases that
actually broke, not the deep ones that never could.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from migrate_url_patterns import apply, known_hosts, main, repair, scan

ERP_HOSTS = {"vidysea.com", "www.vidysea.com"}


def a_project(root: Path, slug: str = "erp", *patterns: str | None,
              allowed: list[str] | None = None,
              base_url: str = "https://www.vidysea.com/erp") -> Path:
    """A project directory shaped like a real one: its declared hosts are what
    the repair is judged against."""
    directory = root / slug
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "project.json").write_text(json.dumps({
        "slug": slug, "name": slug, "base_url": base_url,
        "allowed_domains": allowed if allowed is not None else ["vidysea.com", "www.vidysea.com"],
    }), encoding="utf-8")
    path = directory / "screenmap.json"
    path.write_text(json.dumps({
        "project": slug,
        "screens": [{"name": f"s{i}", "url_pattern": p} for i, p in enumerate(patterns)],
    }), encoding="utf-8")
    return path


def patterns_of(path: Path) -> list[str | None]:
    return [s["url_pattern"] for s in json.loads(path.read_text(encoding="utf-8"))["screens"]]


# -- what counts as mangled: a host the PROJECT declares, never a shape --------

def test_a_declared_host_swallowed_into_the_path_is_repaired() -> None:
    assert repair("/vidysea.com/erp/trainers", ERP_HOSTS) == "/erp/trainers"
    assert repair("/www.vidysea.com/erp/x", ERP_HOSTS) == "/erp/x"
    assert repair("/vidysea.com", ERP_HOSTS) == "/"


def test_a_healthy_pattern_is_left_alone() -> None:
    for healthy in ("/erp/trainers", "/", "/students/{id}", "/reports/new"):
        assert repair(healthy, ERP_HOSTS) is None, healthy


def test_a_FIRST_path_segment_that_merely_looks_like_a_host_is_left_alone() -> None:
    """AT-298, the exact shapes the previous guard ate while claiming otherwise.
    These are FIRST segments — the only position the guard ever examines. The
    test this replaces asserted deeper segments, which could never have matched,
    so it passed while the property it was named for was false.
    """
    for real_path in ("/v1.2/foo", "/index.html", "/settings.json", "/sitemap.xml",
                      "/release-1.0/notes", "/main.js"):
        assert repair(real_path, ERP_HOSTS) is None, real_path


def test_another_projects_host_is_not_stripped_from_this_projects_path() -> None:
    """Hosts are per-project. A path segment that happens to be some OTHER
    product's domain is still a path here."""
    assert repair("/saucedemo.com/cart", ERP_HOSTS) is None


def test_a_project_that_declares_nothing_is_never_repaired() -> None:
    """No knowledge, no repair — the one thing this must never do is fall back
    to guessing, which is what AT-298 was."""
    assert repair("/vidysea.com/erp/trainers", set()) is None


def test_declared_hosts_come_from_both_base_url_and_allowed_domains(tmp_path: Path) -> None:
    a_project(tmp_path, "demo", allowed=["one.test"], base_url="https://two.test:8080/app")

    hosts = known_hosts(tmp_path / "demo")

    assert {"one.test", "two.test:8080", "two.test"} <= hosts


def test_a_host_with_a_port_is_matched_either_way() -> None:
    hosts = {"127.0.0.1", "127.0.0.1:46661"}
    assert repair("/127.0.0.1:46661/index.html", hosts) == "/index.html"
    assert repair("/127.0.0.1/index.html", hosts) == "/index.html"


# -- the script itself -------------------------------------------------------

def test_it_repairs_a_file_and_reports_what_it_changed(tmp_path: Path) -> None:
    path = a_project(tmp_path, "erp", "/vidysea.com/erp/trainers", None, "/erp/ok")

    found = scan(tmp_path)

    assert [p for p, _ in found] == [path]
    assert found[0][1] == [("/vidysea.com/erp/trainers", "/erp/trainers")]
    assert apply(path, ERP_HOSTS) == 1
    assert patterns_of(path) == ["/erp/trainers", None, "/erp/ok"]


def test_running_it_twice_changes_nothing_the_second_time(tmp_path: Path) -> None:
    """Idempotent, so a human can re-run it without thinking about it."""
    path = a_project(tmp_path, "erp", "/vidysea.com/erp/trainers")
    apply(path, ERP_HOSTS)
    before = path.read_bytes()

    assert apply(path, ERP_HOSTS) == 0
    assert path.read_bytes() == before


def test_it_is_a_dry_run_unless_told_otherwise(tmp_path: Path, capsys) -> None:
    """Writing to real project data is a human's call, so the default must not."""
    path = a_project(tmp_path, "erp", "/vidysea.com/erp/trainers")

    assert main(["--root", str(tmp_path)]) == 0

    assert patterns_of(path) == ["/vidysea.com/erp/trainers"], "dry run wrote to disk"
    assert "dry run" in capsys.readouterr().out


def test_write_applies_the_repair(tmp_path: Path) -> None:
    path = a_project(tmp_path, "erp", "/vidysea.com/erp/trainers")

    assert main(["--root", str(tmp_path), "--write"]) == 0

    assert patterns_of(path) == ["/erp/trainers"]


def test_a_clean_tree_reports_nothing_to_do(tmp_path: Path, capsys) -> None:
    a_project(tmp_path, "erp", "/erp/trainers", None)

    assert main(["--root", str(tmp_path)]) == 0
    assert "nothing to repair" in capsys.readouterr().out


def test_it_walks_past_json_that_uses_screens_for_something_else(tmp_path: Path) -> None:
    """A crawl manifest carries `"screens": 1` — a COUNT. The script walks every
    json file under the root, so it meets these. The fixture-only tests missed
    it; the dry run against real project data crashed on the first one."""
    target = a_project(tmp_path, "erp", "/vidysea.com/erp/trainers")
    (tmp_path / "erp" / "crawl.json").write_text(
        json.dumps({"id": "crawl_1", "screens": 1, "edges": 3}), encoding="utf-8")
    (tmp_path / "erp" / "notes.json").write_text(json.dumps(["a", "b"]), encoding="utf-8")
    (tmp_path / "erp" / "broken.json").write_text("{not json", encoding="utf-8")

    found = scan(tmp_path)

    assert [p for p, _ in found] == [target]


def test_each_project_is_judged_by_its_own_declared_hosts(tmp_path: Path) -> None:
    """Two projects, two host sets. `/saucedemo.com/cart` is mangled in the shop
    and a real path in the erp — the same string, judged differently, which a
    shape-based guard could never do."""
    erp = a_project(tmp_path, "erp", "/saucedemo.com/cart")
    shop = a_project(tmp_path, "shop", "/saucedemo.com/cart",
                     allowed=["saucedemo.com"], base_url="https://saucedemo.com/")

    found = dict(scan(tmp_path))

    assert erp not in found
    assert found[shop] == [("/saucedemo.com/cart", "/cart")]
