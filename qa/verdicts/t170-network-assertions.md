# Verdict — t170-network-assertions

**Date:** 2026-09-24
**Cycle checked:** 1
**Contract:** `qa/contracts/network-assertions.md` (NA1-NA6, DRAFT -> ACTIVE on this PASS) +
  `qa/contracts/core-invariants.md` (C1, C2, C3, C5, C7, C8, C10)
**Manifest:** `qa/manifests/t170-network-assertions.md`
**Bound root:** `D:/autoTesting/.worktrees/t170-network-assertions` (branch `wave/t170-network-assertions`, head `d81d6cf`)
**Executor:** claude-sonnet-subagent (checker: claude-sonnet-subagent — fresh session, no `ANTHROPIC_BASE_URL` override, `self != executor` holds trivially since both are Claude but this is a separate fresh subagent with no builder context)
**Mode:** A (Mode D not applicable — see below)

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (NA1-NA6), 7/7 invariants hold (C1,C2,C3,C5,C7,C8,C10)
FAILURES: none
CAPABILITY-COVERAGE: 6/6 rows reproduced (throwaway copy, green before every edit, PYTHONPATH-forced
  to import the copy's own src — the shared .venv's editable .pth points at the bound root)
LIVE-BROWSER: not-applicable (changed paths are browser/observe.py, browser/assertions.py,
  browser/session.py [docstring], stages/execute.py, stages/explore.py, stages/network_capture.py
  [new], core/paths.py, store/crawl_store.py, tests/test_network_assertions.py, docs/MAP.md
  [generated]. Independently traced, not just pattern-matched on paths: grepped every ui/*.py for
  consumers of the new `list_crawl_network`/NETWORK-kind evidence and found none — routes_report.py's
  `_step_flow` filters `r.evidence` to SCREENSHOT only, crawl_view.py's `.kind` use is on
  `CrawlIssue`, an unrelated enum. No rendered page's data flows through this change.)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All six NA criteria are evidenced by code I read myself (not just the manifest's
prose) and by falsifying edits I reproduced myself in an isolated copy. The two full-suite
failures are confirmed pre-existing and untouched by this unit's diff via `git diff ea6b7c3 -- 
.goal/goal.json` and `tests/test_flake_probe_real_process.py` (both empty). Diff scope is exactly
the manifest's "What changed" list, no deletions or renames. Contract taken DRAFT->ACTIVE.
```

## What I re-ran myself (no pasted output trusted)

| command | my result | manifest claim | match |
|---|---|---|---|
| `uv run pytest tests/test_network_assertions.py` | `12 passed in 0.30s` | `12 passed in 0.33s` | ✔ |
| `uv run ruff check src tests scripts` | `All checks passed!` | same | ✔ |
| `uv run autotester doctor` | `doctor: clean` | same | ✔ |
| `uv run pytest` (full suite, bare, no `-q`) | `2 failed, 1616 passed, 5 skipped, 32 xfailed, 1 warning in 959.36s` | `2 failed, 1616 passed, 5 skipped, 32 xfailed, 1 warning in 852.78s` | ✔ (same two named failures, only wall-time differs) |

## Diff scope (step 4c) — `git diff ea6b7c3 d81d6cf --stat`

```
 docs/MAP.md                              |   1 +
 qa/manifests/t170-network-assertions.md  | 121 +++++++++++++
 src/autotester/browser/assertions.py     |  29 +++-
 src/autotester/browser/observe.py        |  16 ++
 src/autotester/browser/session.py        |   6 +-
 src/autotester/core/paths.py             |   4 +
 src/autotester/stages/execute.py         |  39 ++++-
 src/autotester/stages/explore.py         |  17 +-
 src/autotester/stages/network_capture.py |  44 +++++
 src/autotester/store/crawl_store.py      |   8 +
 tests/test_network_assertions.py         | 289 +++++++++++++++++++++++++++++++
 11 files changed, 559 insertions(+), 15 deletions(-)
```

Read the full diff, not just the stat. No existing function, class, test, or config key is deleted
or renamed. `session.py`'s hunk is exactly 3 lines replaced by 3 lines (confirmed also by `wc -l` =
299, under the 300-line cap) — the "line-neutral docstring edit" claim holds, and I read the new text
for meaning loss: it still correctly states `dom_asserts`/`network` are deterministic and
`visual_signal` is the judge's, only trimmed to fit. `.goal/goal.json` and
`tests/test_flake_probe_real_process.py` are both **absent** from this diff (`git diff ea6b7c3 d81d6cf
-- .goal/goal.json` and `-- tests/test_flake_probe_real_process.py` both empty), which is what makes
the two full-suite failures provably not-this-unit's rather than merely asserted:

- `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` (ISS-t164-1) — file untouched by
  this diff.
- `test_every_base_criticality_is_a_value_the_classifier_recognises` — `git show ea6b7c3:.goal/goal.json`
  already carries T-175 with `"base_criticality": "normal"` (outside `CLASSIFIER_VOCABULARY`), so the
  failure predates this branch's first commit; `.goal/goal.json` is untouched by this diff. The dispatch
  brief says a separate fix unit is already in flight elsewhere; I filed no duplicate issue for it.

Every file this diff touches is named in the manifest's "What changed"; nothing is touched outside it.

## NA1-NA6 — read against the code, not only the tests

- **NA1.** `observe.py`'s `_on_response` now appends `(method, url, status)` to `self.responses` for
  every response (`observe.py:67-73`), independent of the `>= 400` branch that only feeds `.failed`.
  `network_capture.first_party_evidence` filters through `explore_safety.classify_request` (reused,
  not duplicated — confirmed by reading `explore_safety.py:142-151`, which returns exactly
  `"first_party"`/`"ignored"`/`"noise"`, and the capture module drops anything `!= "first_party"`).
  Both the run path (`execute.py::_drain_network_evidence`, called after every step) and the crawl path
  (`explore.py::_fold_network_evidence`, called once from `_finish`) route through this one function.
- **NA2.** `network_capture.py` and `execute.py` both import only `redact`, `crawl`/`enums`/`project`/
  `run` schema modules and `explore_safety` — no `stages.grade` import anywhere (confirmed by reading
  the import blocks, not just the grep-shaped test). `_drain_network_evidence` only extends
  `session.state.evidence`; it never reads or writes `RawResult.outcome` itself, and
  `_assertions_unmet` (the thing that does flip the outcome) only reacts to `"assert "`-prefixed
  items, which raw capture rows are not.
- **NA3.** `assertions.py::assert_expected` now loops `expected.network`, calls the new `_network_met`
  (a pure read of already-captured NETWORK evidence, excluding its own `"assert "` labels so a prior
  assertion can't satisfy a later one), and records `assert network: met|unmet (<pattern>)`. `execute.py`
  folds `_ASSERT_EVIDENCE_KINDS` to include `"network"` so an unmet one now flips
  `Outcome.ASSERTION_FAILED` exactly like `dom` already does. `browser/assertions.py`'s module
  docstring and `browser/session.py`'s `assert_expected` docstring are both updated in place to say
  `network` is handled — the D-032 deferral text is gone, not merely superseded elsewhere.
- **NA4.** No `Provider`/vendor import anywhere in `network_capture.py` (read, not only grepped);
  `execute.py`'s new imports are schema + `network_capture` only.
- **NA5.** `network_capture.first_party_evidence` scrubs every path through the caller's `Redactor`
  before constructing `Evidence` (`network_capture.py:40`) — confirmed the `MASK` constant is
  `"[REDACTED]"` (`core/redact.py:14`), matching the test's literal assertion.
- **NA6.** `grep -rn 'on("response"' src/autotester/` returns exactly one hit,
  `browser/observe.py:53`, inside `attach()`. No second listener anywhere in `src/`.

`schema/enums.py:137`'s `EvidenceKind.NETWORK` and `schema/flowspec.py:68`'s `ExpectedState.network`
are both pre-existing fields this unit newly *acts on*, not new schema surface — C1 unaffected.

## Capability coverage — 6/6 reproduced

Throwaway copy at `C:/Users/Lenovo/AppData/Local/Temp/claude/checker-t170/copy` (tracked files only,
`git ls-files` list, no `.git`/`.venv`), run with the project's own venv interpreter
(`.venv/Scripts/python.exe` from the bound worktree — no full `uv sync` needed) with `PYTHONPATH`
forced to the copy's `src`. Verified the force actually worked before trusting any row:
`python -c "import autotester; print(autotester.__file__)"` resolved to the **copy's** path, not the
bound root's — the worktree's `.venv/Lib/site-packages/autotester.pth` does point at
`D:\autoTesting\.worktrees\t170-network-assertions\src`, exactly the trap the dispatch warned about.
**Copy validity, green before any edit:** `12 passed in 6.16s` on the whole test file. Never edited the
bound tree.

| row | file edited | before | after | assertion that fired | isolated? |
|---|---|---|---|---|---|
| NA1 | `network_capture.py` (`!=` → `==` "first_party") | `1 passed` | `FAILED ... assert 'app.pathlynks.test/api/students' in 'GET https://cdn.unrelated-third.test/px.gif -> 200'` | exact match to manifest | yes, reverted, re-confirmed clean |
| NA2 | `network_capture.py` docstring (`from autotester.stages import grade`) | `1 passed` | `FAILED ... assert 'grade' not in ...` (matched `es import grade`) | exact match | yes, reverted |
| NA3 | `assertions.py` (`assert network` label hardcoded to `"met"`) | `1 passed` | `FAILED ... AssertionError: assert <Outcome.COMPLETED> is <Outcome.ASSERTION_FAILED>` | exact match | yes, reverted |
| NA4 | `network_capture.py` docstring (`import anthropic`) | `1 passed` | `FAILED ... assert not <re.Match ... match='import anthropic'>` | exact match | yes, reverted |
| NA5 | `network_capture.py` (dropped `redactor.scrub(...)`) | `1 passed` | `FAILED ... AssertionError: assert 'hunter2' not in 'GET https:/...nter2 -> 200'` | exact match | yes, reverted |
| NA6 | `observe.py` (duplicated `page.on("response", ...)` in `attach()`) | `1 passed` | `FAILED ... AssertionError: ['observe.py:53', 'observe.py:54'] ... assert 2 == 1'` | exact match | yes, reverted |

Every edit was single-hunk, single-file, to a file the manifest's "What changed" names
(`network_capture.py`, `assertions.py`, `observe.py`) — no cell required `CONTRACT_MISMATCH`
treatment. Final re-run after all six reverts: `12 passed in 0.59s`, and `diff -q` of all three
mutated files against the bound tree's copies came back empty (byte-identical, fully reverted).

## Core invariants

- **C1** — unaffected; `Evidence`/`EvidenceKind.NETWORK`/`ExpectedState.network` all pre-exist, this
  unit only newly populates/reads them.
- **C2** — `doctor: clean`; `explore.py` sits exactly at 300 (not over), `session.py` at 299, all
  other touched files well under.
- **C3** — one listener (NA6), one conversion function (`network_capture.first_party_evidence`, called
  by both `execute.py` and `explore.py` rather than duplicated), new module justified in the manifest
  (`assertions.py`/`session.py` were already at/near the 300-line cap per their own headers).
- **C5** — NA5.
- **C7** — sabotage-assertion clause: each row's anchor matched exactly once (single-hunk Edit) and the
  named test's specific assertion fired, not a generic collection/import error. Baseline asserted green
  before each edit, from the copy itself (not reused from step 3). Zero-failure clause: no row produced
  zero failures. This unit's new test file (`tests/test_network_assertions.py`, 12 tests) is an ADD, not
  a REWRITE of an existing test, and the mutation duty is discharged at the capability level (one row
  per NA criterion, the established reading in this repo's own amendment log, 2026-09-16 ruling) —
  every claimed capability has its row; none is missing.
- **C8** — confirmed by reading imports directly (not only the NA4 test's regex).
- **C10** — this verdict's own commit below is scoped to only this unit's qa/ paths.

No criterion was softened to pass this artifact; none needed softening.

## Issues

None found. `qa/issues.jsonl` unchanged by this unit.

## Verdict

**PASS, cycle 1 of 1.** Every NA criterion is evidenced in the code itself and independently
falsified in an isolated copy; the diff touches nothing beyond its own claim; the two full-suite
failures are proven pre-existing and out of this unit's diff; no UI surface consumes the new evidence.
Contract `qa/contracts/network-assertions.md` moves DRAFT -> ACTIVE on this PASS.
