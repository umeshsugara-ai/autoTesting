# Verdict — at319-issue-id-collision-reconcile

**Date:** 2026-09-11
**Cycle checked:** 1
**Mode:** A (unit check, pure ledger data edit — Mode D not applicable)

## What I re-ran myself

- `git diff -- qa/issues.jsonl` (full, not truncated) against `HEAD` (55efeac-era tree, max id
  `AT-332` at HEAD) — the real diff has **three** hunks: (1) `AT-282` line 279 id → `AT-335` +
  `supersedes_id_collision`, (2) `AT-319` row `status: open → fixed` + `fixed_date` + `note`,
  (3) two brand-new rows `AT-333`/`AT-334` appended at EOF (`found_by: maker-at227-fixture`).
  Net +4/-2 lines, matching the manifest's `git diff --stat` exactly.
- Traced hunk 3: `git diff --stat` (full working tree) shows live, uncommitted changes under
  `src/autotester/stages/explore_*.py`, `explore_safety.py`, `screen_identity.py`, etc. — a
  **concurrent, disclosed** in-progress unit (`qa/manifests/at227-first-paint-modal.md`,
  `Status: draft`). `qa/.last-tick`'s own most recent entry states the at319 maker deliberately
  picked this unit specifically *because* it does not file-collide with that concurrent session,
  and names it explicitly. AT-333/AT-334 are that session's incidentally-found issues, legitimately
  appended to the shared ledger — not scope creep by this unit, and not something this manifest
  needed to narrate. Confirmed **not** a bypass or an undisclosed AT-286-style silent build.
- Duplicate-id scan (`json`/`collections.Counter` over all 335 rows):
  `{'AT-288': 2, 'AT-289': 2, 'AT-290': 2, 'AT-291': 2}` — exactly the four rows AT-293 already
  ruled on; `AT-282` no longer among them. Matches the manifest's expected output verbatim.
- `grep -c '"id": "AT-335"' qa/issues.jsonl` → `1`. `grep -c '"id": "AT-282"' qa/issues.jsonl` → `1`.
- Read the `AT-293` row in full (`checker_ruling` field): confirms the governance ruling really
  does forbid renumbering the `AT-288/289/290/291` group ("the eight existing rows are NOT
  renumbered... instead each colliding row now carries a `checker` discriminator field"). Read
  all eight rows individually: every one of the eight carries `"checker": "checkerA"` or
  `"checker": "checkerB"` plus an `id_collision` note pointing at AT-293 — the promised
  discriminator is actually present on disk, not just claimed.
- `grep -rn "AT-282" qa/verdicts qa/manifests qa/gates docs` myself: two hits outside this
  manifest — `qa/verdicts/at311-mutation-check.md` (names the collision generically, as one of
  five) and `qa/verdicts/t135-coverage-merge-expand.b.md` ("Observation, not filed... a pre-existing
  duplicate id (`AT-282` ×2)"). Neither cites either row by its specific content (adapter-runtime
  wording vs. the row that became AT-335) — renumbering the second occurrence was safe, as claimed.
- `AT-335` was free before this edit: not present in `HEAD:qa/issues.jsonl` (max numeric id there
  is `AT-332`) and not present anywhere else in the ledger before this row. No new collision
  introduced.
- Full JSONL parse of the current working file: all 335 lines parse as valid JSON objects, 0
  invalid lines.
- `uv run --cache-dir .work/uv-cache ruff check src tests scripts` → `All checks passed!` (exit 0).
- `uv run --cache-dir .work/uv-cache pytest -q --basetemp=.work/pytest-tmp` → 1090 passed
  (2 skipped), exit 0.
- `uv run --cache-dir .work/uv-cache autotester doctor` → exit 1, exactly
  `root-clutter: AGENTS.md` / `1 violation(s)` — matches the manifest's stated pre-existing AT-283
  baseline, unchanged by this unit.

## Judgement

- The manifest's only load-bearing numeric claim ("the ledger's next free id — max existing
  numeric id was AT-334") does not match `HEAD` (max `AT-332`), but it does match the actual
  working tree the maker was looking at (which already carried the concurrent session's
  `AT-333`/`AT-334`, disclosed above) — so `AT-335` really was the next free id in the tree that
  existed at edit time. Not a defect; noted for the record since it looked like one until traced.
- Core criterion under test — C7 (verification independence / ledger integrity): the AT-293
  governance ruling was correctly read and correctly left standing rather than re-litigated; its
  promised discriminator fields are genuinely on disk on all eight rows; the one collision AT-293
  did not cover (`AT-282`) was renumbered only after an independent citation check showed it safe;
  the ledger is valid JSONL after the edit; no new duplicate id was introduced. All re-derived by
  me, not trusted from the manifest's pasted output.
- No UI surface changed (`qa/issues.jsonl` only, for this unit's own two hunks) — Mode D correctly
  not invoked, confirmed from `git diff --stat`, not from the manifest's claim alone.

## Findings

None at >80% confidence. No FAILURES.

VERDICT: PASS
SCOREBOARD: 1/1 criteria met (C7 — ledger/verification integrity), 0/0 invariants otherwise triggered (no-fire list covers C1–C6/C8/C9, untouched by this unit)
FAILURES (if any): none
LIVE-BROWSER: not-applicable (qa/issues.jsonl only — data-only ledger edit, no UI/src/tests path touched)
ISSUES-WRITTEN: none
EXPLANATION: Re-derived every claim independently — the AT-293 governance ruling really does forbid renumbering the four-pair group and its discriminator fields are genuinely present on all eight rows; the AT-282 renumbering to AT-335 is citation-safe (both existing mentions are generic); the ledger stays valid JSONL with no new collision. The apparent id-arithmetic mismatch (HEAD max AT-332 vs. manifest's claimed AT-334) traced cleanly to a disclosed, non-colliding concurrent session (AT-227) already tracked in qa/.last-tick and qa/manifests/at227-first-paint-modal.md — not a defect in this unit.
