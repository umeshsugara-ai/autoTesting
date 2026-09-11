# Manifest — at319-issue-id-collision-reconcile

**Unit:** AT-319 — five duplicate ids in `qa/issues.jsonl`, each naming two different findings
**Contract:** `qa/contracts/core-invariants.md` (C7 family — verification-artifact/ledger integrity)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-319 (high)

## What was wrong

`qa/issues.jsonl` had five duplicate ids — `AT-282`, `AT-288`, `AT-289`, `AT-290`, `AT-291` —
each carrying two genuinely different findings under one id. A reader that keys the ledger by
id silently drops one finding per collision.

## What I found before touching anything

Four of the five (`AT-288`/`AT-289`/`AT-290`/`AT-291`) were already ruled on by **AT-293**
(`qa/issues.jsonl`, `checker_ruling` field) — a prior checker governance decision from the T-135
dual check: **do not renumber**, because two cycle-1 verdicts and a manifest already cite those
ids by number and renumbering would destroy the audit trail the dual check exists to create.
Instead, each colliding row already carries a `checker` discriminator field (`checkerA`/
`checkerB`) so a reader can tell the two findings apart. That ruling was already fully applied on
disk — nothing to do there. AT-319 itself doesn't reference AT-293, so it looks like AT-319 was
filed by a checker who found the same collision independently without cross-referencing the
earlier ruling.

The fifth, `AT-282`, was **not** covered by AT-293's ruling — it's an unrelated collision (a
2026-09-10 sweep finding left `open`, and a 2026-09-11 re-test of the same area that closed
`wontfix` after non-reproduction). `grep -rl "AT-282" qa/verdicts qa/manifests qa/gates docs`
found two hits (`qa/verdicts/at311-mutation-check.md`, `qa/verdicts/t135-coverage-merge-expand.b.md`)
and both only describe the collision generically — neither cites either row by its specific
content, so renumbering is safe here in a way it would not have been for the AT-293 group.

## What changed

- `qa/issues.jsonl` line 279 (the `wontfix` occurrence of `AT-282`, dated 2026-09-11): id changed
  to `AT-335` (the ledger's next free id — max existing numeric id was `AT-334`), with a new field
  `"supersedes_id_collision": "AT-282"` naming the id it was mistakenly filed under. The original
  `AT-282` row (line 276, `open`, dated 2026-09-10) is untouched.
- `qa/issues.jsonl` `AT-319` row: `status` → `fixed`, `fixed_date` set, `note` added explaining
  the reconciliation (AT-293's ruling stands for the four-pair group; AT-282 fixed per AT-319's
  own prescribed remedy).

## What I deliberately did NOT do

- Did **not** renumber any of the AT-288/289/290/291 rows — that would override a specific,
  reasoned checker governance ruling (AT-293) with AT-319's more generic default remedy. The
  checker owns that ruling; re-litigating it here would be exactly the drift the ledger's
  append-only, evidence-cited discipline exists to prevent.
- Did **not** build the "duplicate-id guard in the next sweep" AT-319 also asks for — its own
  text says that duty is checker-owned (read-only, no code change needed) since the ledger has no
  reader in `src/`. Left as a note for the checker to adopt in its own sweep protocol, not a
  maker code change.

## How to verify (commands + expected)

- `python3 -c "import json,collections; rows=[json.loads(l) for l in open('qa/issues.jsonl',encoding='utf-8') if l.strip()]; ids=collections.Counter(r['id'] for r in rows); print({k:v for k,v in ids.items() if v>1})"`
  → expected: `{'AT-288': 2, 'AT-289': 2, 'AT-290': 2, 'AT-291': 2}` (exactly the four AT-293 already
  ruled on — AT-282 no longer among them)
- `grep -c '"id": "AT-335"' qa/issues.jsonl` → expected: `1`
- `grep -c '"id": "AT-282"' qa/issues.jsonl` → expected: `1`
- `uv run pytest -q` → expected: exit 0 (data-only change, no code touched)
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 1, exactly the pre-existing AGENTS.md root-clutter
  violation (AT-283), unchanged by this unit

## Actual outputs (from maker's own run)

```
$ python3 -c "... duplicate id check ..."
{'AT-288': [283, 288], 'AT-289': [284, 289], 'AT-290': [285, 290], 'AT-291': [286, 291]}
total rows: 335

$ git diff --stat -- qa/issues.jsonl
 qa/issues.jsonl | 6 ++++--
 1 file changed, 4 insertions(+), 2 deletions(-)
```

Full pytest/ruff/doctor re-run left to the checker — this is a pure JSONL data edit, no `src/`
or `tests/` path touched, so I did not re-run the full suite myself; the checker's own
independent run is the real verification here per the adapter's slot-1 discipline.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `qa/issues.jsonl` only (ledger data).
Nothing under `src/`, `tests/`, or `src/autotester/ui/`.

## What this unit does not claim

- Does not claim the ledger can never collide again — the checker-owned sweep guard AT-319 also
  asked for is still unbuilt; this unit is the one-time data reconciliation only.
- Does not re-open or re-judge any of the underlying findings inside the collision (AT-288/289/
  290/291's content, or AT-282's own substance) — only the id collision itself.

## Status: checked-PASS (cycle 1, verdict qa/verdicts/at319-issue-id-collision-reconcile.md, commit 709741e)
