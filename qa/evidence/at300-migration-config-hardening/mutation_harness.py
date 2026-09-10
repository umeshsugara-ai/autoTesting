"""Mutation-check a unit's own tests, in a copy OUTSIDE the repo.

Each mutation reverts one specific fix. The test named for that fix must fail.
A mutation that kills nothing means the test is vacuous for its property.

`KILLED` means "the suite went red", so the baseline MUST be green or every
result is meaningless — asserted below, per AT-307.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(r"D:\autoTesting")
work = Path(tempfile.mkdtemp(prefix="mut-at300-"))
copy = work / "repo"
shutil.copytree(REPO / "scripts", copy / "scripts")
shutil.copytree(REPO / "tests", copy / "tests", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copytree(REPO / "src", copy / "src", ignore=shutil.ignore_patterns("__pycache__"))
(copy / "pyproject.toml").write_bytes((REPO / "pyproject.toml").read_bytes())

TARGET = copy / "scripts" / "migrate_url_patterns.py"
ORIGINAL = TARGET.read_text(encoding="utf-8")

MUTATIONS = [
    ("M1 allowed_domains list-guard removed",
     '''        {d.strip().lower() for d in declared if isinstance(d, str) and d.strip()}
        if isinstance(declared, list) else set()''',
     '''        {str(d).strip().lower() for d in declared if d}
        if declared else set()''',
     "test_allowed_domains_given_as_a_string_contributes_no_hosts"),

    ("M2 hostname/port reverted to netloc.split",
     '''        try:
            parts = urlsplit(base)
            host, port = parts.hostname, parts.port
        except ValueError:  # malformed authority, e.g. a bad port
            host, port = None, None
        if host:
            hosts.add(host)
            if port:
                hosts.add(f"{host}:{port}")''',
     '''        netloc = urlsplit(base).netloc.lower()
        if netloc:
            hosts.add(netloc)
            hosts.add(netloc.split(":", 1)[0])''',
     "test_base_url_userinfo_is_not_treated_as_a_host / test_an_ipv6_base_url_does_not_declare_a_bracket_as_a_host"),

    ("M3 port fallback in repair removed",
     '    if candidate not in hosts and candidate.split(":", 1)[0] not in hosts:',
     '    if candidate not in hosts:',
     "test_a_pattern_carrying_a_port_matches_a_host_declared_without_one"),

    ("M4 _project_dir_of reverted to depth-1",
     '''    for parent in (path.parent, *path.parent.parents):
        if (parent / "project.json").is_file():
            return parent
        if parent == root:
            break
    return root''',
     '''    relative = path.relative_to(root)
    return root / relative.parts[0] if len(relative.parts) > 1 else root''',
     "test_a_file_nested_below_the_project_is_still_judged_by_it / flat-root"),
]


def run() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_migrate_url_patterns.py",
         "-o", "addopts=", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=copy, capture_output=True, text=True)
    return proc.returncode, proc.stdout


code, out = run()
baseline_line = out.strip().splitlines()[-1] if out.strip() else ""
print(f"BASELINE: exit={code}  {baseline_line}")
# AT-307: `KILLED` is `exit != 0`, so a suite that is ALREADY red certifies every
# test non-vacuous. The baseline was printed and never asserted, which made the
# whole run meaningless exactly when it mattered most (this repo has a documented
# flake, AT-196). Assert it, and refuse to report on a red baseline.
assert code == 0, f"baseline is NOT green - every KILLED below would be a lie: {baseline_line}"
print()
for name, old, new, defends in MUTATIONS:
    assert ORIGINAL.count(old) == 1, f"{name}: anchor matched {ORIGINAL.count(old)} times"
    TARGET.write_text(ORIGINAL.replace(old, new, 1), encoding="utf-8", newline="\n")
    assert TARGET.read_text(encoding="utf-8") != ORIGINAL, f"{name}: file unchanged"
    code, out = run()
    tail = out.strip().splitlines()[-1] if out.strip() else ""
    failed = [ln.split("::")[-1] for ln in out.splitlines() if ln.startswith("FAILED")]
    verdict = "KILLED" if code != 0 else ">>> SURVIVED (vacuous!)"
    print(f"{name}\n  defends: {defends}\n  {verdict}  {tail}")
    for f in failed:
        print(f"    - {f}")
    print()
    TARGET.write_text(ORIGINAL, encoding="utf-8", newline="\n")

assert TARGET.read_text(encoding="utf-8") == ORIGINAL, "restore failed"
print("target restored byte-identically; live repo never touched")
