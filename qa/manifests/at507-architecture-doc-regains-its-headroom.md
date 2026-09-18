# Manifest — at507-architecture-doc-regains-its-headroom

**Unit:** AT-507 — `docs/ARCHITECTURE.md` sat at exactly its 150-line C2 budget with zero
headroom after AT-506's authorized row edit (D-026). The next prose change to it has nowhere to
go, and `doctor` will not warn until the file is already over. Measure the real cost, choose
trim / raise-budget / split on the evidence, and fix it before the next unit hits the wall.
**Contract:** `qa/contracts/core-invariants.md` (C2 — file size budgets; C10 — generated docs stay
fresh); `check_docs_routed` (every `docs/*.md` self-describes and is routed in `CLAUDE.md`).
**Goal task:** none named directly — same shape as AT-513, filed against the architecture doc
whose C2 budget exists for agent context cost, not source-code readability.
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** the "zero headroom" condition described in the unit brief (not a filed
`qa/issues.jsonl` row — this maker does not write that file).

## Measure before deciding (the brief's own instruction)

**1. Where is the budget enforced, and what does it count?**
`src/autotester/doctor.py::check_architecture_budget` (line 156) reads `ARCHITECTURE_MAX_LINES`
from `src/autotester/ledger/render.py` (= 150) and compares it to
`len(path.read_text(encoding="utf-8").splitlines())` — **every physical line in the file**, with
no distinction between generated and hand-written content. There is no generated/prose split to
exploit inside `check_architecture_budget` itself.

**2. How much of the 150 lines is generated vs hand-written?**
None of it is generated. At genesis (commit `2785312`) the "Directory map and schema summary"
section was already split out into `docs/MAP.md` specifically so `docs/ARCHITECTURE.md` would
stay under this same 150-line budget — confirmed by `git log -p --follow -- docs/ARCHITECTURE.md`
and the file's own line 130-132: "Generated from module and model docstrings into `docs/MAP.md`
by `autotester map`; not kept here so this file stays inside its 150-line budget." All 150 lines
at the point of measurement were hand-written prose. This rules out the cheapest version of
option (a) (discount generated content) before it starts.

**3. What's duplicated with `docs/MAP.md` or `docs/SNAPSHOT.md`?**
Checked both, row by row:
- `docs/MAP.md`'s "Directory map" (117 rows, one per **module**, one-line docstring each) does
  **not** literally duplicate `ARCHITECTURE.md`'s "Concept → file" table (34 rows, one per
  **concept**, several concepts per module or several modules per concept). Verified every one of
  the 41 file paths that table references resolves under `src/autotester/` — zero stale rows, so
  there is nothing dead to cut there either.
- `docs/SNAPSHOT.md` ("the whole project in one screen … what is live … what is next", generated,
  session-start-injected) **does** duplicate `ARCHITECTURE.md`'s hand-written `## Status` section
  (lines 146-150) — and the hand-written copy had drifted **false**: it said "the P0–P5 goal
  backlog is closed" while `.goal/goal.json` currently carries 10 `pending` tasks (T-122, T-123,
  T-136, T-145, T-125, T-126, T-150 … T-153) and `docs/SNAPSHOT.md`'s own generated "Next (open
  goal tasks)" section lists five of them. This is the one genuine, safe trim target.

**4. What did I look at and reject, and why?**
- **`## Commands`** (7 command lines) overlaps 4 of 7 lines with `CLAUDE.md`'s own Commands
  section, but not literally — `pytest` vs `pytest -q`, `ruff check src tests` vs
  `...tests scripts` — and it carries 3 commands (`map`, `snapshot`, `ledger add`) `CLAUDE.md`
  does not. Removing it would delete information, and fixing the overlap needs an edit to
  `CLAUDE.md`, which is outside this unit's file set (a second build subagent owns it
  concurrently this same session). Left alone.
- **Collapsing hard-wrapped paragraphs** (e.g. the `FlowSpec`/Execution-model/Security prose,
  several of which are one sentence spread over 2-4 physical lines) onto single long lines would
  cut the raw newline count `check_architecture_budget` counts, without cutting a single
  character an agent has to read. I measured this and rejected it explicitly: the budget exists
  for **agent context cost** (characters/tokens read), and this move changes the line-count proxy
  while leaving the actual cost identical — a fake saving, not a real one. Not applied anywhere.

## What changed (chose (a): trim, not (b) raise or (c) split)

- `docs/ARCHITECTURE.md`: removed the `## Status` section (the blank separator line plus the
  heading, `**Built:**` line, and two-line `**Next:**` paragraph — 6 physical lines) and nothing
  else. 150 → **144 lines**, 6 lines of real headroom at the **same** 150-line budget. No text was
  moved elsewhere because nothing in it was information not already covered, correctly and
  automatically, by `docs/SNAPSHOT.md`, which `CLAUDE.md`'s router already names for exactly this
  purpose ("every session start … the whole project in one screen").
- `docs/MAP.md`: regenerated (`uv run autotester map`) — **byte-identical**, confirmed by
  `git status` showing no diff. Expected: nothing that feeds it changed.
- `docs/SNAPSHOT.md`: regenerated (`uv run autotester snapshot`) — only its generated
  "Last decisions" tail changed, picking up D-027 and D-028 (see diff below).
- `src/autotester/doctor.py`, `src/autotester/ledger/render.py`: **untouched**. The 150-line
  `ARCHITECTURE_MAX_LINES` constant is unchanged — my own measurement contradicted the brief's
  suggestion that a raise might be needed: trimming was not skipped, it was attempted and found
  one safe, real target, and recovered enough headroom to answer the stated problem (zero
  headroom → 6 lines). No test or mutation-check changes are owed, because no code changed.
- `docs/DECISIONS.md`: two entries appended via `scripts/append_decision.ps1` — **D-027**
  (authorizes the `## Status` removal, with the measurement above as its Why) and **D-028** (a
  same-session arithmetic correction: D-027's `**Result:**` line said "150 → 145 lines"; the
  actual six-line removal, re-counted immediately after applying the edit, is 144, not 145. Per
  the append-only rule D-027 cannot be edited, so D-028 corrects the record the same way D-011
  corrected D-010's authorization text — code/choice unchanged, number fixed).

## How to verify (commands + expected)

```
uv run autotester doctor                    # expect: doctor: clean
uv run ruff check src tests scripts         # expect: All checks passed!
uv run pytest -q -o addopts= tests/test_ledger.py tests/test_doctor.py   # expect: N passed
wc -l docs/ARCHITECTURE.md                  # expect: 144
git diff docs/ARCHITECTURE.md               # expect: only the ## Status section removed
git status --porcelain docs/MAP.md          # expect: empty (byte-identical regeneration)
git diff docs/SNAPSHOT.md                   # expect: only the Last-decisions tail changed
uv run pytest                                # full suite; redirect to a file, scan the whole
                                              # log (not tail) — `-q` here resolves to `-qq` and
                                              # prints no summary line (AT-503)
```

## Actual outputs (from maker's own run)

```
$ uv run autotester map
map: docs/MAP.md regenerated
$ uv run autotester snapshot
snapshot: 44 lines written
$ uv run autotester doctor
doctor: clean
$ uv run ruff check src tests scripts
All checks passed!
$ uv run pytest -q -o addopts= tests/test_ledger.py tests/test_doctor.py
34 passed in 2.49s
$ wc -l docs/ARCHITECTURE.md
144 docs/ARCHITECTURE.md
$ git status --porcelain docs/ARCHITECTURE.md docs/MAP.md docs/SNAPSHOT.md docs/DECISIONS.md
 M docs/ARCHITECTURE.md
 M docs/DECISIONS.md
 M docs/SNAPSHOT.md
                                              # docs/MAP.md absent from the list = no diff
```

Full-suite run (`uv run pytest`, redirected to `.work/at507_full_suite.log`, whole file scanned
for the terminal summary line and exit code — not touched by C2's `.work/` scratch exemption
since it is verification evidence, not a deliverable): **result folded in below once the
background run completes** — see Known limits if it is still running when this manifest is
checked; the change touches no `src/` or `tests/` file, so risk of a full-suite regression is
effectively zero, and the two targeted files that exercise `check_architecture_budget` and
`check_docs_routed` (`tests/test_ledger.py`, `tests/test_doctor.py`) both already passed above.

## Capability coverage (each claim → its isolating check)

| capability | check | falsifying condition | observed |
|---|---|---|---|
| File is back under budget with real headroom, not a re-formatted illusion | `wc -l docs/ARCHITECTURE.md` before/after | edit adds back ≥7 lines anywhere | 150 → 144, confirmed by two independent counts (`git show HEAD:… \| wc -l` vs working tree) |
| Nothing but `## Status` was touched | `git diff docs/ARCHITECTURE.md` | any other section's text differs | diff shows exactly the Status block removed, nothing else |
| No information was actually lost | manual cross-check against `docs/SNAPSHOT.md`'s Live/Next sections | SNAPSHOT lacks something Status said that isn't stale | SNAPSHOT already carries "what is live"/"what is next" as generated, current content; the only Status content SNAPSHOT does *not* carry ("P0–P5 backlog is closed") is the part that was false |
| No stale file references remain in the concept table | scripted path-existence check over every `` `path.py` `` backtick span | any referenced path missing under `src/autotester/` | 0 missing (39 real paths after excluding Status's own removed `bench.py` mention) |
| `check_architecture_budget` / `check_docs_routed` still pass on synthetic fixtures | `tests/test_ledger.py`, `tests/test_doctor.py` | either test regresses | both green, 34 passed |
| Generated docs still match their source | `autotester map` / `autotester snapshot` re-run, diffed | MAP or SNAPSHOT differs from what's committed | MAP byte-identical; SNAPSHOT differs only in its generated decisions tail (D-027, D-028 added) |
| The append-only decision log stays honest even after my own arithmetic slip | `docs/DECISIONS.md` diff | D-027 edited directly, or the wrong number left standing uncorrected | D-027 appended once, never edited; D-028 appended as a same-session correction (precedent: D-011 correcting D-010) |

## Live browser evidence

Not UI-touching — no `src/` file, no `ui/` route, no browser surface changed. Changed paths:
`docs/ARCHITECTURE.md`, `docs/SNAPSHOT.md` (regenerated), `docs/DECISIONS.md` (D-027, D-028),
`qa/evidence/at507-architecture-doc-regains-its-headroom/*`.

## Known limits (disclosed, not claimed)

- **6 lines of headroom is modest, not a structural fix.** If concept rows keep being added at
  roughly one per unit (the pattern D-026 itself describes for `doctor.py`'s own cap), this
  recovers a handful of units' worth of room, not a standing solution. I deliberately did **not**
  raise the 150-line budget to buy more margin than the measurement justified — per the unit's own
  framing, a raise is legitimate only for what trimming fails to recover, and trimming here
  recovered a real, if small, amount by removing content that was actually redundant (not by
  reformatting). If the table keeps growing, that is arithmetic to re-measure next time it
  recurs, the same way D-026 re-measured `doctor.py`'s.
- **The `## Commands` section's overlap with `CLAUDE.md` is real but left unresolved.** 4 of its 7
  lines duplicate `CLAUDE.md`'s Commands section under slightly different flags. I did not touch
  it because fixing the overlap cleanly needs a matching edit to `CLAUDE.md`, which this unit is
  explicitly barred from touching (a concurrent build subagent owns it). This is a second, smaller
  trim candidate for a future unit, not claimed as done here.
- **This does not address the "next prose change has nowhere to go" problem permanently** — it
  answers it for the next several small changes, not forever. I considered and rejected line-
  collapsing purely because it would have made `doctor` say "fine" while the real agent-context
  cost of reading the file stayed exactly the same; that gap between the line-count proxy and the
  cost it stands in for is not fixed by this unit, only avoided this once.
- **D-028 exists because of my own counting error while drafting D-027**, not because the edit was
  wrong. The file matches D-027's `**What:**` exactly; only its `**Result:**` arithmetic (145 vs
  the actual 144) needed the follow-up entry. Flagging this plainly rather than quietly hoping the
  checker doesn't recount.
- **Full-suite (`uv run pytest`) result**: see the line appended below this section once the
  background run this manifest started finishes — the change is docs-only, so this is
  belt-and-suspenders, not a live risk.

## Status: ready-for-check
