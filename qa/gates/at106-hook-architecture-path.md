# GATE — AT-106: the session-start hook reads `ARCHITECTURE.md` from the wrong place

**Opened:** 2026-09-08T01:20:00+05:30 · **Status: OPEN** · **Approver:** Umesh

## The question, in one line
May I change `.claude/hooks/lab-session-start.ps1:118` from
`Join-Path $root "ARCHITECTURE.md"` to `Join-Path $root "docs\ARCHITECTURE.md"` — a one-line
enforcement-path value that no existing DECISIONS entry authorizes?

## Why it needs you and could not just be done
`.claude/hooks/*` is an enforcement path: the Lab Protocol says it changes only under a DECISIONS
entry carrying `Approved-by: Umesh`. This repo has **failed two prior checks (AT-030, AT-031)**
for treating a batch approval as covering a specific value by extension, and the checker applied
that precedent here: D-008/D-010/D-011/D-019 authorize the excerpt *filter* and the *cap* by name,
and none of them says a word about the *path*. So this one is genuinely outside standing approval.

## The evidence (verified by two independent parties)
- `ARCHITECTURE.md` has never existed at the repo root: `git log --all --diff-filter=A --
  ARCHITECTURE.md` is empty. The project keeps it at `docs/ARCHITECTURE.md`.
- Running the real hook emits `[WARN] ARCHITECTURE.md missing at repo root` and injects
  **zero** architecture headings.
- The sibling line 50 already reads `Join-Path $root "docs\DECISIONS.md"` — the `docs\` prefix is
  present for decisions and missing for architecture, in the same file.
- **Consequence:** the excerpt block has never run since the genesis commit. The empty
  ground-truth defect is therefore *older* than AT-097 said, and D-008/D-010/D-019 have all been
  arguing about the contents of dead code.

## Options
1. **Approve the one-line path fix** (recommended). I append a DECISIONS entry with your
   `Approved-by`, change the path, remove the strict xfail, and the hook injects real ground truth
   for the first time. Reversible in one commit.
2. **Move `ARCHITECTURE.md` to the repo root instead**, matching the generic Lab Protocol template
   and this project's own CLAUDE.md wording ("root `ARCHITECTURE.md` is the only ground truth").
   Bigger blast radius: `docs/MAP.md` generation, `autotester doctor`'s freshness and line-cap
   checks, and the `docs/` router table in CLAUDE.md all reference the current location.
3. **Neither** — leave the hook injecting nothing and close AT-097/AT-029 as won't-fix.

## How to answer
Reply with `1`, `2`, or `3`. On any answer I append
`**Answered:** <ISO date> — <choice> — <where>` to this file **before** acting on it.

## What this blocks
- **AT-097** (high) and **AT-029** (medium) cannot close — the committed fix repairs a filter that
  never executes.
- Unit `at097-session-start-hook-regression` is at **FAIL, cycle 2 of max 3**.
- Nothing else. T-124 and the rest of the backlog are unaffected and continue.
