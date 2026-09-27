# Verdict — at621-exit-call-aliases

**Date:** 2026-09-27
**Cycle checked:** 1 (matches manifest's `Fix cycle: 1 of max 3`)
**Unit:** AT-621 — T-195. Code commit `5c7a9e47`, manifest commit `c893bcb1`, branch
`wave/at621-exit-call-aliases`.
**Contract:** `qa/contracts/core-invariants.md` C2, C3, C7, C10, C11.
**Checker:** fresh Claude subagent (claude-sonnet), Mode A. Ran afresh — a prior checker session
filed `AT-626` against this same unit on 2026-09-27 and died before writing a verdict; this run
reaches its own conclusion from its own evidence, described below.

## What I re-ran myself (real output, not pasted)

```
$ uv run pytest tests/test_doctor.py -v          (in the bound worktree)
39 passed in 3.54s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest                                   (full suite, bound worktree, no -q)
1 failed, 2012 passed, 6 skipped, 32 xfailed, 15 warnings in 1172.18s
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
```

**The one full-suite failure is an environmental flake, not a regression from this diff.**
`test_flake_probe_real_process.py` is untouched by this unit (`git diff master...HEAD --stat`
below lists only `render.py`, `test_doctor.py`, and this unit's manifest). The test spawns a real
subprocess with a real grandchild and asserts the grandchild's pid file exists before
`flake_probe.run_once`'s 10s timeout fires. `tasklist` at the time showed 27 concurrent
`python.exe` and 7 concurrent `uv.exe` processes from other sessions sharing this machine. I
reproduced the failure deterministically twice in isolation
(`uv run pytest tests/test_flake_probe_real_process.py -v`, then the single-test form),
both times under the same measured contention, both times failing identically —
`FileNotFoundError` reading `child.pid`, i.e. the grandchild never got scheduled in time to write
the file, before any kill-tree assertion is even reached. Same failure direction the contract's
own amendment log already carves out (2026-09-09, AT-196: "a false FAIL on a busy machine, never
a false PASS... recorded so the next maker or checker meeting an unrelated red suite reads this
instead of learning to re-run until green") — a different file than AT-196/AT-612, so filed fresh
as **AT-627** (low, test-infra) rather than folded into either. Not counted against this unit.

## C11 — direct probe (own script, own colorama install, outside pytest)

Built a standalone probe (`doctor.run` called directly against synthetic repos with an
installed-but-undeclared `colorama`) in a throwaway `git archive HEAD` copy under my scratch dir,
covering exactly the shapes AT-621 claims to fix plus the AT-626 shape for comparison:

```
bare_import_colorama_control                            -> HARD (flagged)
except_ImportError_os_exit__import_os                   -> HARD (flagged)
except_ImportError_s_exit__import_sys_as_s              -> HARD (flagged)
except_ImportError_bye__from_sys_import_exit_as_bye     -> HARD (flagged)
AT626_except_ImportError_os_exit__import_os_dot_path    -> SOFT (0 violations)
```

The three shapes AT-621's manifest names (`import os` + `os._exit`, `import sys as s` +
`s.exit()`, `from sys import exit as bye` + `bye(1)`) are now correctly classified HARD end to
end against a real undeclared dependency. `import os.path` + `os._exit(1)` (AT-626's shape) is
still SOFT, confirmed independently — see below.

## Capability coverage (step 4b)

Copied the worktree via `git archive HEAD` (post-fix state, matching the manifest) into a
throwaway dir outside `D:/autoTesting`, ran `uv sync --frozen` there once.

| claim | check | before (copy, fix intact) | falsifying edit | after (copy) |
|---|---|---|---|---|
| AT-621: `os._exit`, an aliased `sys`/`os` module, and a directly-imported `exit`/`_exit` name in an `ImportError` handler are hard exits | `uv run pytest tests/test_doctor.py -k "os_exit or sysalias or aliased_name_import_exit or unrelated_dot_exit"` | **4 passed** (own run in the copy) | replaced `render.py` in the copy with `git show master:src/autotester/ledger/render.py` (pre-fix) | **3 failed** (`os_exit`, `sysalias`, `aliased_name_import_exit`, all `AssertionError: assert False` on `any("opt.py" in v.location for v in violations)`) / `unrelated_dot_exit_on_non_sys_object_stays_soft` still passed, as the manifest predicts |

Green came from the copy's own run (not reused from the bound-tree run above). Reproduced exactly
as the manifest describes, including the negative control staying unaffected. This same
falsification also discharges C7's mutation duty for the three new test rows (reverting the
guard is the mutation; it reddens precisely the three assertions that claim to defend the new
behaviour, and no others — kill-attribution holds) and its failing-first sabotage duty for the
guard itself.

## C2 / C3 / C10

- `wc -l`: `render.py` and `test_doctor.py` both exactly 300/300, matching the manifest's claim.
  `soft_import_ids` (the touched function) is 43 lines by AST span — under the 50-line cap.
- `doctor: clean` (no duplicate-definition or drift-filename hit).
- `git diff master...HEAD --stat`: `qa/manifests/at621-exit-call-aliases.md`,
  `src/autotester/ledger/render.py`, `tests/test_doctor.py` only — matches the manifest's "What
  changed" exactly. Full diff read: no function, class, or test deleted or renamed beyond what the
  manifest names; `_is_exit_call` was folded into a nested `is_exit_call` closure as the manifest
  discloses (line-budget move, not a silent removal — the old top-level `_is_exit_call` was
  replaced by a documented equivalent, not dropped unexplained). No docstring wording changed
  besides what the manifest discloses.

## AT-626 — independently re-judged, not merely re-read

The prior (crashed) checker session filed AT-626 ("`import os.path` also binds `os`, but the
alias resolver's `a.name in {"sys","os"}` check misses the dotted form") and marked it "not
charged to at621". I re-derived this myself rather than trusting that note: reproduced the SOFT
misclassification directly (probe table above), and read `soft_import_ids`'s alias-collection
line (`render.py:157-158`) to confirm the mechanism the AT-626 row describes is real. I agree
with — and independently confirm — leaving it uncharged: AT-621's manifest states its covered
aliasing shapes narrowly and explicitly ("local names bound to the sys/os module via `import sys
as s` / `import os`"), never claims dotted-submodule imports, and its capability-coverage table
and tests only exercise the shapes it names. That is a materially different AST shape
(`ast.Import` alias `name="os.path"` vs `name="os"`) than any of the three AT-621 fixed, and this
project's own ledger already treats this class of incremental heuristic gap as a follow-on
low-severity issue rather than a blocker on the fix that came before it (AT-590 → AT-619 is the
same shape: a scoped fix ships, a checker's adversarial pass finds the next uncovered idiom, files
it fresh). AT-626 stays `open`, uncharged to this unit.

## Persona walk / Mode D

Changed paths are `src/autotester/ledger/render.py` and `tests/test_doctor.py` only — a doctor/AST
classifier and its tests, no UI surface, no retrieval/ranking change. The manifest's
`Persona walk: skip (doctor internals, no UI)` is correct against the actual diff.
`LIVE-BROWSER: not-applicable (src/autotester/ledger/render.py, tests/test_doctor.py — backend
AST classifier, no UI surface touched)`.

## Issues addressed

AT-621 verifiably fixed by this unit's diff (probe + capability coverage above). Ledger flip and
new-issue filing (AT-627) done as part of this verdict; see `qa/issues.jsonl`.

## Verdict

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (C2, C3, C7, C10, C11), 0/0 invariants (none apply beyond the criteria)
FAILURES: none
CAPABILITY-COVERAGE: 1/1 rows reproduced
LIVE-BROWSER: not-applicable (src/autotester/ledger/render.py, tests/test_doctor.py)
ISSUES-WRITTEN: AT-627
EXECUTOR: claude-opus-subagent (manifest) / checker: claude-sonnet-subagent
EXPLANATION: All three named aliasing shapes (os._exit under import os, s.exit() under import sys
as s, bye(1) under from sys import exit as bye) are now correctly classified HARD, verified both
via the manifest's own capability-coverage falsification (reproduced fresh in a throwaway copy)
and via an independent direct probe against a real installed-but-undeclared package. C2/C3/C10
hold on inspection of the diff and line counts. The one full-suite test failure
(test_flake_probe_real_process.py) is a reproduced environmental flake on a heavily loaded
machine, unrelated to this diff, filed as AT-627. AT-626 (a distinct, narrower uncovered shape,
import os.path) is independently reconfirmed and correctly left open and uncharged to this unit.
```
