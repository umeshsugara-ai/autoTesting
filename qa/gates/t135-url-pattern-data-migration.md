# HUMAN_GATE — run the url_pattern data migration on real project data?

**Raised:** 2026-09-11T02:40+05:30 · maker, T-135 cycle 3
**Blocks:** nothing (T-135 ships without it; this is stored-data cleanup)
**Authority for raising it:** checker B, T-135 cycle-2 verdict, AT-297b — *"a committed,
idempotent, tested migration under scripts/, run AFTER the AT-294 producer fix; raise a HUMAN_GATE
rather than edit real project artifacts in-flight."*

## The question

`projects/erp/screenmap.json` holds 3 `url_pattern` values corrupted by AT-287/AT-294:

```
'/vidysea.com/erp/trainers'  ->  '/erp/trainers'   (Trainers)
'/vidysea.com/erp/trainers'  ->  '/erp/trainers'   (Trainers List)
'/vidysea.com/erp/trainers'  ->  '/erp/trainers'   (Trainers List - Edit Drawer)
```

They render to a human today on `/projects/erp/product-map`. Do we repair them now?

## What is already true, either way

- **The producer is fixed.** `build_screen_map(ProjectStore('erp'))` on the real analyses now
  yields `/erp/trainers`. Nothing new is corrupted, and re-running Analyze on this project heals it.
- **The migration exists, is committed, and is tested** — `scripts/migrate_url_patterns.py`,
  9 tests in `tests/test_migrate_url_patterns.py`. Dry run by default; idempotent; it refuses to
  touch a first path segment that merely contains a dot.
- **I did NOT run it.** In cycle 2 I hand-edited this file mid-unit, and checker B was right to
  fail that: the value was one the code could not then reproduce, the backup lived in gitignored
  `.work/`, and nothing tested it. That edit has been reverted; the file is back to its real state.

## Options

| | Action | Consequence |
|---|---|---|
| **A** | `uv run python scripts/migrate_url_patterns.py --write` | 3 rows repaired now; product-map reads correctly immediately. `projects/erp/screenmap.json` is untracked, so this is a working-tree data change with no commit to revert — take a copy first if that matters. |
| **B** | Re-run Analyze on `erp` | Heals through the normal pipeline, no bespoke script touching real data. Costs a vision run. |
| **C** | Leave it | Stale display on one page for one project until either A or B happens. Nothing else depends on it — coverage compares against the FlowSpec, and `projects/erp` has no `flowspec.json`. |

**Maker's recommendation: B, else A.** B exercises the fixed producer end to end and proves the fix
on real data rather than asserting it. A is the cheap equivalent if a vision run is not worth it.

## Answer

_(unanswered — append `Answered: <ISO date> — <choice> — <where>` below before acting)_
