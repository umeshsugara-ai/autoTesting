# Manifest — at097-session-start-hook-regression
**Contract:** `qa/contracts/core-invariants.md` (C7 independent verification) + the Lab Protocol in
`CLAUDE.md` (enforcement paths change only under an authorizing DECISIONS entry). No feature
contract governs the hook itself; **that is part of the finding.**
**Goal task:** none (issue-fix unit)
**Date:** 2026-09-08
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** **AT-097** (high), **AT-029** (medium) — the same defect's two halves
**Authorized by:** **D-019** (appended before any file was touched)

## The finding, verified independently before fixing
`.claude/hooks/lab-session-start.ps1` injects this project's ground truth into every session.
I executed its on-disk filter against the real `docs/ARCHITECTURE.md` (150 lines, 11 named
headings):

```
CURRENT FILTER kept lines: 1
  |# AutoTester - architecture
```

**One line. The title.** Every session started since 2026-09-05 has been injected an empty
ground-truth block. `D-008` and `D-010` are both ACTIVE, both `Approved-by: Umesh`, and both
authorize the opposite; `D-010`'s Result names the exact line and value. The disk disagreed with
both because commit `051303e` (D-013) — a *"byte-identical to the AIOS template"* sync whose own
text says *"Behaviour otherwise unchanged"* — reverted them as a side effect, with no `Supersedes:`
line. History: `5f83bdb` cap=100/numbered → `f9e3456` cap=150/named (the authorized fix) →
`051303e` cap=100/numbered (the silent revert).

This is the hook whose job is to make the protocol survive forgetting, and it had been quietly
forgetting for three days.

## What changed
- `.claude/hooks/lab-session-start.ps1` — filter restored to D-008's rule (keep every `## ` section
  except the generated `## Directory map and schema summary`), cap restored to D-010's 150, label
  text corrected, and a comment recording that this file is **deliberately not** byte-identical to
  the AIOS template so a future sync re-applies both deltas.
- **New** `tests/test_session_start_hook.py` (6 tests) — reads the **real** `.ps1`, not a copy.
- `docs/DECISIONS.md` — **D-019** (written first, per the Lab Protocol).

After the fix, the same probe keeps **140 lines and all 10 named headings** — Design rules,
Commands and Status now reach the session, which is AT-029's half.

## Why there was no test, and why that is the actual bug
Nothing tested this hook, so the same defect shipped twice and was caught both times only by a
sweep that happened to look. The tests are therefore **driven by the file itself**: the excluded
heading pattern and the cap are parsed out of the live `.ps1` and used to run the filter. If the
filter is reverted, the parse fails and every behavioural test fails with it, rather than quietly
simulating a filter the hook no longer contains.

## Sabotage — I re-applied `051303e`'s exact revert
```
=== SABOTAGE APPLIED (051303e's exact revert) ===
FAILED tests/test_session_start_hook.py::test_the_numbered_heading_filter_is_not_back
FAILED tests/test_session_start_hook.py::test_the_excerpt_cap_is_the_authorized_one
FAILED tests/test_session_start_hook.py::test_every_named_section_survives_the_filter
FAILED tests/test_session_start_hook.py::test_the_generated_directory_map_is_the_only_thing_dropped
FAILED tests/test_session_start_hook.py::test_the_excerpt_is_not_effectively_empty
=== RESTORED === 6 passed
```
**First attempt was weaker and I am recording it rather than only the good result:** my initial
tests mirrored the filter with a hardcoded constant, so the same sabotage failed only the 2
string-checking tests while the 3 behavioural ones passed against a fiction. Driving them from the
parsed file is what took it from 2/6 to 5/6 (the 6th is "the hook exists", correctly unaffected).

## The approval question — read this, it is the one judgement call
This is an **enforcement path**, which the Lab Protocol says needs `Approved-by:` from Umesh, and
**Umesh has not been asked this session.** D-019 records the reasoning explicitly: D-008 and D-010
are standing, ACTIVE, Umesh-approved authorizations for exactly these two values, so this restores
their effect and creates **no new authority**. I did not express it as `Supersedes: D-013`, because
D-013's real purpose (ASCII-escaping hook JSON, which fixed a genuine harness rejection) is
correct and load-bearing; marking it SUPERSEDED would tell every future reader to discard it.
**The checker should judge whether that reasoning holds.** If it does not, the correct outcome is
FAIL and a HUMAN_GATE, not a softened criterion — and it is one commit to reverse.

## How to verify (commands + expected)
- `docker compose exec -T autotester uv run pytest -q` → **560 passed, 1 skipped** at cycle 2 (549 before this unit began). The xfail is gone: it
  is a live passing assertion now.
- `docker compose exec -T autotester uv run ruff check src tests scripts` → `All checks passed!`
- `docker compose exec -T autotester uv run autotester doctor` → `doctor: clean`
- Re-run the sabotage above yourself; 5 of 6 must fail.
- Independently execute the repaired filter against `docs/ARCHITECTURE.md` and confirm ≥100 lines
  and all 10 named headings — **do not** take my probe's word for it.
- Confirm `D-013`'s ASCII-escaping is untouched (`git diff 051303e -- .claude/hooks/`).

## Cycle 1 verdict: FAIL — and it was right

Verdict: `qa/verdicts/at097-session-start-hook-regression.md` (**Cycle checked: 1**, FAIL, 5/6).

**The checker was right and my fix was to dead code.** The hook reads
`Join-Path $root "ARCHITECTURE.md"` (line 118) — the repo root — and this project keeps the file
at `docs/ARCHITECTURE.md`. A root copy has **never existed** (`git log --all --diff-filter=A --
ARCHITECTURE.md` is empty). I ran the real hook to confirm rather than take the verdict's word:

```
[WARN] ARCHITECTURE.md missing at repo root -- protocol expects it. Run /init-lab repair.
## headings injected: 0
```

So the excerpt block has never executed since the genesis commit, the empty-ground-truth defect is
older than AT-097 described, and four DECISIONS entries have been arguing about the contents of
unreachable code. The sibling line 50 already reads `docs\DECISIONS.md` — the prefix is present
for decisions and missing for architecture, in the same file.

**AT-107 is the part that should sting, and it is mine.** My test hardcoded the architecture path,
so all six passed green while the hook injected nothing. That is *exactly* the "simulating a
fiction" failure I had just written a paragraph in this manifest congratulating myself for
avoiding — one axis over. Catching it on the filter constant and then missing it on the path is
not a smaller version of the same mistake; it is the same mistake.

### Cycle 2 — what I fixed and what I cannot
- **AT-107 fixed.** `tests/test_session_start_hook.py` now parses `$archPath` out of the `.ps1`
  too, and `test_the_hook_reads_the_file_the_project_actually_has` is
  `xfail(strict=True)` — it stays green while the defect is real and **fails loudly the moment the
  path is corrected**, so the fix cannot land with a stale xfail hiding it. 6 passed, 1 xfailed.
- **AT-106 BLOCKED on HUMAN_GATE** — `qa/gates/at106-hook-architecture-path.md`. Correcting the
  path changes an enforcement-path value no DECISIONS entry authorizes, and the checker applied
  this repo's own AT-030/AT-031 precedent (a batch approval does not cover a specific value by
  extension). I am not extending D-019 to cover it; that would be the exact move that failed twice.

**Upheld from cycle 1, and worth recording because I flagged it as my one judgement call:** the
checker judged the D-008/D-010/D-011 standing-authorization reasoning adversarially and **upheld
it** — no HUMAN_GATE was owed on the filter and cap, D-013's revert was genuinely unintended, and
declining `Supersedes: D-013` was correct because the marker is machine-consumed into every
session's decision index and would print "discard this" over a live fix. One fair correction: my
"creates NO new authority" was slightly overstated, since D-019's byte-identity clause does narrow
something D-013 approved.

### Cycle 2 continued — the gate was answered, and the real defect is fixed

**Umesh answered the gate on 2026-09-08: Option 1, correct the path.** Asked directly via an
AskUserQuestion presenting all three options with the diff and each one's blast radius; recorded in
`qa/gates/at106-hook-architecture-path.md` **before** any file was touched, and authorized by
**D-020** (its own entry, with his `Approved-by` — not an extension of D-019, which is the move
this repo has failed two checks for).

- `.claude/hooks/lab-session-start.ps1:118` — `Join-Path $root "ARCHITECTURE.md"` →
  `Join-Path $root "docs\ARCHITECTURE.md"`. The sibling line 50 already read `docs\DECISIONS.md`.
- The `[WARN]` text now names `docs/ARCHITECTURE.md` so a future failure points at the real path.
- **The strict xfail is removed and its assertion is live** — that is what it was for.

**The real hook, run end to end, before and after:**
```
BEFORE:  total lines emitted: 52    [WARN] ARCHITECTURE.md missing at repo root
         architecture headings injected: 0

AFTER:   total lines emitted: 193   actual [WARN] lines: none
         architecture headings injected: 10
         --- ARCHITECTURE.md (all sections except the generated directory map; ground truth) ---
```
All ten named sections — What it does, Pipeline, Concept → file, Data model, Execution model,
Security, Storage, Design rules, Commands, Status — reach a session for the first time in this
repo's history.

## Status: ready-for-check
