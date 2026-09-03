# Manifest — at011-loop-md

**Contract:** qa/contracts/core-invariants.md (general doc-quality invariants) + the maker skill's
own step-3b spec (`C:/Users/Lenovo/.claude/skills/maker/SKILL.md` "/maker init" step 3b) and
`/loopify`'s publishable schema (`D:/ai_os/.claude/skills/loopify/SKILL.md` Step 5), which
together are the de-facto "contract" for `qa/loop.md` — no dedicated `qa/contracts/loop.md`
exists or is warranted (this is process/meta infrastructure, not a product feature).
**Goal task:** none (this is a `qa/` infra fix, not a `.goal/goal.json` task)
**Date:** 2026-09-03
**Fix cycle:** 2 of max 3
**Issues addressed:** AT-011 (S3, `/maker init` step 3b was skipped — `qa/loop.md` never authored),
AT-027 (this cycle's fix — cycle 1's Verify line didn't match `qa/adapter.json` verbatim)

## Cycle 2 — fix for verdict `qa/verdicts/at011-loop-md.md` (Cycle checked: 1, FAIL)

- **AT-027**: cycle 1's Verify line said `uv run ruff check src tests scripts`, but
  `qa/adapter.json`'s actual slot-1 command (line 10) is `uv run ruff check src tests` — no
  `scripts` token. Independently re-confirmed by reading `qa/adapter.json` directly (`grep -n
  "cmd" qa/adapter.json`) before fixing, not just trusting the verdict's claim. Fixed by removing
  ` scripts` from `qa/loop.md`'s Verify line so it now matches the adapter byte-for-byte.
  **Not fixed, deliberately, and flagged instead:** the adapter's own command actually omits a
  directory (`scripts/`) that this session has been linting as part of standard verify all along
  (`uv run ruff check src tests scripts` has been the real command run in every manifest this
  session, including this one below) — `scripts/` holds real production code
  (`onboard_pathlynks.py`, `check_no_secrets.py`) added after the adapter's commands were fixed
  at the START gate. That's a genuine staleness in `qa/adapter.json` itself, not in `qa/loop.md`
  — `qa/adapter.json` is an enforcement-surface file the maker should not edit unilaterally
  mid-cycle (its commands are allowlisted at START). Filed as a new low-severity note for the
  checker/a future sweep to decide whether to amend the adapter, rather than silently expanding
  this cycle's scope to fix it.

## Why this unit

The checker sweep at 12:22 (commit `48438ca`) confirmed T-050 and T-060 are the only remaining
substantive dev work and both are genuinely human-gated right now, and ranked its own top-3
buildable candidates: AT-011 (`qa/loop.md`, no gate needed) · AT-015 (needs a DECISIONS entry
first) · AT-026 (a larger scoping decision). AT-011 is the only one buildable in one cycle with
no gate — picked it.

## What changed

- `qa/loop.md` (new) — the project's explicit loop spec, in `/loopify`'s publishable schema
  (Use when / Prompt / Verify / Steps / Stop / Human gate), populated from this project's actual
  state rather than generic placeholders:
  - **Verify** names the adapter's actual slot-1 commands (`qa/adapter.json`'s three shell
    commands), not a hardcoded assumption.
  - **Stop** lists all seven of the maker skill's named terminal states verbatim
    (ADVANCED/BACKLOG_EMPTY/HUMAN_GATE/STALLED/EXHAUSTED/BLOCKED/PAUSED), each with its actual
    `ScheduleWakeup` delay from THE CONTINUATION RULE.
  - **Human gate** lists this project's actual CRITICAL actions, not a generic list: live
    Pathlynks/Mongo actions (the rule currently blocking T-050), DECISIONS entries touching an
    enforcement path (needs `Approved-by: Umesh` — the rule blocking AT-015's own fix),
    credential/`.env` changes (the AT-025 incident class), irreversible/outward-facing git ops
    (noting D-007's narrow, already-checker-verified push exception explicitly, so it isn't
    mistaken for a blanket push authorization), and GRILL findings.

## How to verify (commands + expected)

- `Test-Path qa/loop.md` (or `ls qa/loop.md`) → exists
- `Select-String -Path qa/loop.md -Pattern "ADVANCED","BACKLOG_EMPTY","HUMAN_GATE","STALLED","EXHAUSTED","BLOCKED","PAUSED"` → all 7 terminal states present (Stop section)
- `grep -n "uv run ruff check" qa/loop.md` vs `grep -n "cmd" qa/adapter.json` → the ruff line
  matches the adapter's command byte-for-byte (`uv run ruff check src tests`, no extra token)
- `Select-String -Path qa/loop.md -Pattern "Pathlynks","DECISIONS","Approved-by"` → the project's actual gate triggers are named, not generic placeholders (Human gate section)
- `uv run pytest -q` → exit 0 (no code touched by this unit; regression check only)
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"

## Actual outputs (from maker's own run)

```
$ grep -oE "ADVANCED|BACKLOG_EMPTY|HUMAN_GATE|STALLED|EXHAUSTED|BLOCKED|PAUSED" qa/loop.md | sort -u
ADVANCED
BACKLOG_EMPTY
BLOCKED
EXHAUSTED
HUMAN_GATE
PAUSED
STALLED
$ grep -n "uv run ruff check" qa/loop.md
15:exit 0, `uv run ruff check src tests` clean, `uv run autotester doctor` clean — re-run
$ grep -n "cmd" qa/adapter.json
9:      { "cmd": "uv run pytest -q", "expect": "exit 0" },
10:      { "cmd": "uv run ruff check src tests", "expect": "exit 0" },
11:      { "cmd": "uv run autotester doctor", "expect": "exit 0" }
$ uv run pytest -q
................................s....................................... [ 57%]
.........................................................                [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- No code changed — this is a pure documentation/process artifact. No `docs/FEATURES.jsonl` row
  is warranted (not a `.goal/goal.json` task, no `user_value`).
- Per AT-015's own status (open, not addressed by this unit): the Human gate section explicitly
  names "DECISIONS entries touching an enforcement path... need Approved-by: Umesh" — this is
  accurate to why AT-015 itself hasn't been fixed yet (its own fix needs that gate), not a claim
  that AT-015 is resolved.
- D-007's push exception is described narrowly in the Human gate section specifically so a future
  reader of `qa/loop.md` doesn't misread it as blanket permission to push anything.

## Status: checked-PASS

Verdict: `qa/verdicts/at011-loop-md.md` (Cycle checked: 2, PASS, 7/7; commit `77cbc3d`, pushed).
AT-027 flipped `open → fixed` by the checker. AT-028 (low, open) newly recorded — the adapter's
own ruff command omits `scripts/`, a genuine staleness needing a DECISIONS entry to fix, correctly
deferred rather than silently edited mid-cycle. **Correction:** the verdict's own prose says
"AT-011 PASSes" but the checker's issues.jsonl write only flipped AT-027 — AT-011 itself stayed
`open` on disk. Flipped it myself as the documented fallback (disk state over chat/verdict-prose
claims), citing the verdict file as evidence.
