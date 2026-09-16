"""Checker's own capability-coverage reproduction, in a THROWAWAY COPY outside the bound root.

Never touches d:/autoTesting. For each manifest row: assert the named check is GREEN in
the copy, apply the single-hunk edit, assert it goes RED, and capture WHICH assertion fired.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path("D:/autoTesting")
COPY = Path(__file__).resolve().parent / "copy"
PY = ROOT / ".venv/Scripts/python.exe"

ROWS = [
    ("row1 AT-379 scrollable pane reported",
     "src/autotester/browser/visual_order.js",
     "      const scrollsY = SCROLLS.test(style.overflowY) && node.scrollHeight > node.clientHeight;",
     "      const scrollsY = false;",
     ["tests/test_browser_unreadable.py::test_text_below_the_fold_of_a_scrollable_pane_is_reported"]),
    ("row2 AT-379 overflow:hidden boundary holds",
     "src/autotester/browser/visual_order.js",
     "  const SCROLLS = /^(auto|scroll)$/;",
     "  const SCROLLS = /^(auto|scroll|hidden)$/;",
     ["tests/test_browser_unreadable.py::test_text_below_the_fold_of_a_scrollable_pane_is_reported",
      "tests/test_browser_unreadable.py::test_text_a_reader_cannot_see_is_not_reported[overflow-clipped]"]),
    ("row3 AT-379 scrollable axis genuinely unbounded",
     "src/autotester/browser/visual_order.js",
     "        bottom: scrollsY ? Infinity : box.bottom,",
     "        bottom: box.bottom,",
     ["tests/test_browser_unreadable.py::test_text_below_the_fold_of_a_scrollable_pane_is_reported"]),
    ("row4 AT-392 vertically scrolled pane loses nothing",
     "src/autotester/browser/visual_order.js",
     "      if (scrollsY) scrollY += node.scrollTop;",
     "      if (false) scrollY += node.scrollTop;",
     ["tests/test_browser_unreadable.py::test_a_pane_the_reader_already_scrolled_loses_nothing"]),
    ("row5 AT-392 horizontally scrolled pane loses nothing",
     "src/autotester/browser/visual_order.js",
     "      if (scrollsX) scrollX += node.scrollLeft;",
     "      if (false) scrollX += node.scrollLeft;",
     ["tests/test_browser_unreadable.py::test_a_pane_the_reader_already_scrolled_loses_nothing"]),
]


def build_copy() -> None:
    if COPY.exists():
        shutil.rmtree(COPY)
    COPY.mkdir(parents=True)
    for d in ("src", "tests", "scripts"):
        shutil.copytree(ROOT / d, COPY / d,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(ROOT / "pyproject.toml", COPY / "pyproject.toml")


def run(nodeids: list[str]) -> tuple[int, str]:
    env = dict(os.environ, PYTHONPATH=str(COPY / "src"))
    p = subprocess.run([str(PY), "-m", "pytest", *nodeids, "-o", "addopts=",
                        "-q", "--no-header", "-p", "no:cacheprovider"],
                       cwd=COPY, capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def main() -> None:
    build_copy()
    env = dict(os.environ, PYTHONPATH=str(COPY / "src"))
    where = subprocess.run(
        [str(PY), "-c", "import autotester.browser.observe as m; print(m.__file__)"],
        cwd=COPY, capture_output=True, text=True, env=env).stdout.strip()
    print("ISOLATION: autotester resolves to", where)
    assert str(COPY).lower() in where.lower(), "copy is NOT isolated — refusing to report reds"

    out = []
    for name, rel, old, new, nodes in ROWS:
        target = COPY / rel
        src = target.read_text(encoding="utf-8")
        assert src.count(old) == 1, f"{name}: anchor matched {src.count(old)} times"
        code, log = run(nodes)
        green = code == 0
        print(f"\n=== {name}\n  BEFORE (copy): exit {code} :: {log.strip().splitlines()[-1]}")
        assert green, f"{name}: copy not green before the edit — row is UNVERIFIED-by-checker"
        target.write_text(src.replace(old, new), encoding="utf-8")
        assert target.read_text(encoding="utf-8") != src, "file did not change"
        code2, log2 = run(nodes)
        asserts = [ln.strip() for ln in log2.splitlines()
                   if ln.strip().startswith(("E       assert", "E       AssertionError"))]
        failed = [ln.split()[1] for ln in log2.splitlines() if ln.startswith("FAILED")]
        print(f"  AFTER  (copy): exit {code2}; FAILED={failed}")
        for a in asserts[:4]:
            print("   ", a[:160])
        target.write_text(src, encoding="utf-8")
        code3, _ = run(nodes)
        out.append({"row": name, "green_before": green, "exit_after": code2,
                    "failed_nodeids": failed, "assertions": asserts[:4],
                    "green_after_revert": code3 == 0,
                    "all_named_failed": set(nodes) <= set(failed)})
    (Path(__file__).resolve().parent / "capcov.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print("\nSUMMARY")
    for r in out:
        print(f"  {r['row']}: green_before={r['green_before']} exit_after={r['exit_after']} "
              f"named_all_failed={r['all_named_failed']} revert_green={r['green_after_revert']}")
    shutil.rmtree(COPY)


if __name__ == "__main__":
    sys.exit(main())
