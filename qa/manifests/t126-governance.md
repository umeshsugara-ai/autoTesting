# Manifest — t126-governance

**Contract:** plan.md §5A "T-126 — governance debt sweep"; docs/DECISIONS.md D-018
**Goal task:** T-126
**Date:** 2026-09-25
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** none (governance/config unit; no `qa/issues.jsonl` rows touched — checker-owned)
**Executor:** claude-sonnet-subagent
**Executor rationale:** governance/config-and-ledger unit touching adapter.json security-allowlist wording and CLI-driven ledger rows — not delegated (config/security-adjacent judgment call, cheap to build directly).

## Scope note (maker side only)

This manifest covers only the **maker-side** slice of T-126: widening `qa/adapter.json`'s
read-only allowlist (D-018 item 3) and backfilling `docs/FEATURES.jsonl` for T-130/T-140/T-141.
The rest of plan.md's T-126 text (commit `.goal/*` + `SNAPSHOT.md`, regenerate SNAPSHOT/MAP,
refresh `qa/QUEUE.md`, dispatch `/checker sweep` including a verification pass over the 32
`fixed` issues) is checker/sweep-owned per this dispatch's explicit scope boundary and is not
attempted here. `qa/issues.jsonl`, `qa/QUEUE.md`, `qa/contracts/*`, `qa/verdicts/*` were not
touched.

## What changed

- `qa/adapter.json:3` — top-level `_note` gains one sentence pointing at the new
  `verify.read_only_allowlist` block and citing D-018 + the 2026-09-24 feedback-inbox entry.
  `verify.commands` (the three required gates: `uv run pytest`, `uv run ruff check src tests
  scripts`, `uv run autotester doctor`) is byte-unchanged.
- `qa/adapter.json:15-25` — **new** `verify.read_only_allowlist` object: a `_note` explaining the
  section is evidence-gathering commands checkers already legitimately run mid-check, distinct
  from the mandatory pass/fail gate above, and a `commands` array of 9 entries, each
  `{cmd_prefix, note}` with a one-line rationale:
  - `uv run python scripts/explore_proof.py` (the literal string `check_deliverable.py`'s
    done_check for this task asserts)
  - `uv run python scripts/regression_proof.py`
  - `docker inspect`
  - `git show`
  - `git diff`
  - `git log`
  - `md5sum`
  - `certutil -hashfile`
  - `.work/` (checker-authored probe scripts scoped to scratch)

  All nine are read-only/inspection: none write, push, delete, or reach the network. Existing
  file structure and `_note` style preserved — no key renamed, no existing entry altered beyond
  the one-word rewording on the `regression_proof.py` entry's `note` (see Capability coverage —
  its original wording accidentally duplicated the substring `explore_proof`, which would have
  made the done_check's falsifying-edit row above pass even with the explore_proof entry
  removed; reworded to "mirrors the explorer's proof script" so the done_check's single point of
  truth is the one entry, not an incidental second mention).
- `docs/FEATURES.jsonl` — 3 new rows appended via `autotester ledger add` (never hand-edited):
  - `F-048` `video-learning-schema`, event `live`, `--unit T-130 --verdict
    qa/verdicts/track-a1-video-schema.md --date 2026-09-07`
  - `F-049` `explorer-observation-primitives`, event `live`, `--unit T-140 --verdict
    qa/verdicts/track-b1-observation-primitives.md --date 2026-09-07`
  - `F-050` `explorer-screen-identity`, event `live`, `--unit T-141 --verdict
    qa/verdicts/track-b2-screen-identity.md --date 2026-09-07`
  - All three `--value normal` (matching `.goal/goal.json`'s `user_value: normal` for T-130/T-140/
    T-141) and every `reason` is prefixed `PREFILLED -- Umesh to confirm or edit.` exactly as the
    dispatch required.
  - Checked first: `T-142`/`T-143` (siblings built the same day) already carry rows (`F-033`,
    `F-034`); `T-130`/`T-140`/`T-141` had **none** — confirmed by grepping `docs/FEATURES.jsonl`
    for each task id before adding anything, so no duplicate row was created.
- `docs/SNAPSHOT.md` — regenerated automatically by `autotester ledger add` (its own
  `docs.snapshot.write_text(render.render_snapshot(docs))` call); not hand-edited. Diff is limited
  to the "normal" features line picking up F-048/F-049/F-050.

## How to verify (commands + expected)

- `uv run python scripts/check_deliverable.py --contains qa/adapter.json explore_proof` →
  expected: exit 0, `OK 1 deliverable(s) present`
- `uv run autotester doctor` → expected: exit 0, `doctor: clean`
- `uv run pytest tests/test_ledger_checks.py` → expected: exit 0 (the adapter-reading pytest-q
  guard tests — `grep -rl adapter.json tests/` found only this file)
- `uv run ruff check src tests scripts` → expected: exit 0
- `python -c "import json; json.load(open('qa/adapter.json', encoding='utf-8'))"` → expected: no
  exception (valid JSON)

## Actual outputs (from maker's own run)

```
$ uv run python scripts/check_deliverable.py --contains qa/adapter.json explore_proof
OK 1 deliverable(s) present

$ uv run autotester doctor
doctor: clean

$ uv run pytest tests/test_ledger_checks.py
............................                                             [100%]
28 passed in 1.78s

$ uv run ruff check src tests scripts
All checks passed!

$ python -c "import json; d=json.load(open('qa/adapter.json', encoding='utf-8')); print('valid json, keys:', list(d.keys())); print('read_only entries:', len(d['verify']['read_only_allowlist']['commands']))"
valid json, keys: ['adapter', '_note', 'unit_vocab', 'verify', 'artifact', 'isolation', 'tools']
read_only entries: 9
```

**FULL SUITE NOT RUN — RAM ceiling; checker to run it.** `Get-CimInstance
Win32_OperatingSystem` measured **0.68 GB free** at build time, far under the project's 3.5 GB
floor for `uv run pytest` (the full suite spins browsers/providers). This unit changes
config data (`qa/adapter.json`) and ledger rows (`docs/FEATURES.jsonl` via the CLI) only —
no `src/` behavior changed — so the targeted `tests/test_ledger_checks.py` run above (the only
test file that reads `adapter.json`, confirmed by `grep -rl adapter.json tests/`) plus `ruff`
and `doctor` are the maker's verify; the checker should run the full `uv run pytest` once RAM
allows.

## Capability coverage (each new claim -> its isolating falsification)

| capability (one line) | the check that covers it | the falsifying edit | observed (pasted runner output) |
|---|---|---|---|
| `qa/adapter.json` names the `scripts/explore_proof.py` allowlist entry the done_check requires | `uv run python scripts/check_deliverable.py --contains qa/adapter.json explore_proof` | single-hunk removal of the `explore_proof` entry (and only that entry) from `verify.read_only_allowlist.commands`, in a throwaway copy of `qa/` + `scripts/` under the scratchpad dir, OUTSIDE the worktree | before: `OK 1 deliverable(s) present` (exit 0) / after: `FAIL qa/adapter.json does not mention 'explore_proof'` (exit 1) — see transcript below |
| `qa/adapter.json` stays valid JSON after the widening edit | `python -c "import json; json.load(open('qa/adapter.json', encoding='utf-8'))"` | N/A — this row is a structural precondition of every other row (a JSON syntax error would fail ALL of them, including doctor and check_deliverable, which both parse the file); no separate isolating edit needed beyond the two above, which already exercise parse + read paths | both commands above ran clean against the edited file, which is proof-by-construction that the parse succeeds |
| `docs/FEATURES.jsonl` gained exactly the three missing T-130/T-140/T-141 rows, none duplicated | `grep -c '"unit":"T-130"' docs/FEATURES.jsonl` (and T-140/T-141) | N/A — CLI-appended data row, not logic; the falsifying check is the grep itself, run before (0 matches each) and after (1 match each) the three `ledger add` calls | before: `grep -n '"T-130"\|"T-140"\|"T-141"' docs/FEATURES.jsonl` → no output (0 rows). after: `F-048 …"unit":"T-130"…`, `F-049 …"unit":"T-140"…`, `F-050 …"unit":"T-141"…` — one row per task, confirmed by grep on the file after the three CLI calls (see below) |

**Falsifying-edit transcript (throwaway copy, `$SCRATCH/t126-falsify2/`, outside
`D:/autoTesting/.worktrees/t126-governance`):**

```
--- BEFORE edit ---
$ python scripts/check_deliverable.py --contains qa/adapter.json explore_proof
OK 1 deliverable(s) present
EXIT=0

[removed the single `explore_proof` allowlist entry -- cmd_prefix + note -- from
 verify.read_only_allowlist.commands; 9 entries -> 8; no other key touched]

--- AFTER edit ---
$ python scripts/check_deliverable.py --contains qa/adapter.json explore_proof
FAIL qa/adapter.json does not mention 'explore_proof'
EXIT=1
```

**FEATURES.jsonl before/after (real worktree, not the throwaway copy):**

```
$ grep -n '"T-130"\|"T-140"\|"T-141"' docs/FEATURES.jsonl        # before the 3 ledger add calls
(no output)

$ uv run autotester ledger add ... --unit T-130 ...   → F-048 live video-learning-schema
$ uv run autotester ledger add ... --unit T-140 ...   → F-049 live explorer-observation-primitives
$ uv run autotester ledger add ... --unit T-141 ...   → F-050 live explorer-screen-identity

$ grep -o '"unit":"T-1[34][01]"' docs/FEATURES.jsonl              # after
"unit":"T-130"
"unit":"T-140"
"unit":"T-141"
```

## Live browser evidence

`Not UI-touching — no surface changed`. Changed paths: `qa/adapter.json` (config, allowlist
strings), `docs/FEATURES.jsonl` (append-only ledger rows via CLI), `docs/SNAPSHOT.md` (generated,
CLI-regenerated). None of `*.tsx|jsx|vue|svelte|html|css`, `apps/web/**`, `**/routes/**`,
`**/pages/**`, `**/components/**` were touched, and nothing here changes what a UI page renders
or how data flows into one — no `qa/ui-surfaces.json` narrowing needed, no browser step applies.

## Status: checked-PASS (qa/verdicts/t126-governance.md, cycle 1, 2026-09-25; follow-up AT-560 non-blocking)
