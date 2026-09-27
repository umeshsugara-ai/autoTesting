# Manifest — t192-url-pattern-heal

**Contract:** no contract file owns stored-project-data repair. The authority is the gate
`qa/gates/t135-url-pattern-data-migration.md` (**answer B**, recorded in **D-048**) and the
producer boundary documented in `src/autotester/core/urls.py::screen_url_pattern`.
**Goal task:** T-192 — "t135-B: one Analyze re-run on the erp project to heal the 3 corrupted
`url_pattern` rows (approved single vision call)".
**Date:** 2026-09-27
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk:** the repaired rows render to a human on `/projects/erp/product-map` — that page is
the entire reason the gate was raised. Not re-rendered live by this unit; see "Gaps stated, not
hidden".
**Executor:** the **maker orchestrator, inline** — not a build subagent, and deliberately so. The
authorization was single-shot (see below), and a subagent that fumbled and retried would have spent
an approval that cannot be re-granted without Umesh. This is the accurate statement of who did the
work.

## The headline: the approved vision call was not needed, and was not spent

The gate approved **option B** — "re-run Analyze on `erp`… costs a vision run" — over option A (the
tested `scripts/migrate_url_patterns.py`), on the stated grounds that B "heals through the normal
pipeline, no bespoke script touching real data" and "exercises the fixed producer end to end".

**Read-only tracing before spending anything showed B's purpose is achievable at zero model cost:**

1. All three corrupted rows come from **one** source, `src_c6bb964cfff8` (erp3.mp4) — verified by
   reading each row's `frame_ref`. So "one Analyze run" was at least well-defined, which was the
   first thing worth checking, since three sources exist and three runs would have exceeded the
   approval.
2. The corruption is **in the raw model output itself**: the cached observation
   `sources/src_c6bb964cfff8/observations/gemini__ingest_video_v1.md__00.json` literally contains
   `"vidysea.com/erp/trainers"`. Re-requesting it would return the same host-qualified string. The
   model was never the broken part.
3. **The fix is downstream of the model entirely.** `core/urls.py::screen_url_pattern` is, by its
   own docstring, "the ONE boundary where an observed url becomes a stored `url_pattern`", and
   `stages/product_map.py:40` calls it while building the screen map. So the repair happens in
   `build_screen_map` — reachable as `autotester ingest map`, which makes **no model call at all**.

So the command run was `uv run autotester ingest map erp`. **No `analyze`, no `--force`, no vision
call, no network request.** This is strictly *narrower* than what was approved and uses the same
mechanism the gate chose — it heals through the normal pipeline via the fixed producer, exactly as
option B intended, and simply does not need the model to do it. The approval remains unspent and
still available if Umesh ever wants a genuine re-analysis of that source.

**Stated plainly because it cuts against the gate's own text:** the gate's cost estimate for option B
was wrong. Observations are cached and `--force` is opt-in, so "re-run Analyze" would very likely
have cost nothing either. That is a correction to the gate's reasoning, not to its choice.

## What changed

- `projects/erp/screenmap.json` — **3 `url_pattern` values**, and nothing else:

  | screen id | name | before | after |
  |---|---|---|---|
  | `screen_5791c5e71012` | Trainers | `/vidysea.com/erp/trainers` | `/erp/trainers` |
  | `screen_bedf01acbd4b` | Trainers List | `/vidysea.com/erp/trainers` | `/erp/trainers` |
  | `screen_1d9d49ae0357` | Trainers List - Edit Drawer | `/vidysea.com/erp/trainers` | `/erp/trainers` |

- **No source file changed.** Zero lines of `src/`, `tests/`, `scripts/` or `docs/`. This unit is a
  stored-data repair, not a code change.
- **`analysis.json` was deliberately left alone.** It still holds the host-qualified string in 6
  places, because `screen_url_pattern` normalises at the *screen-map* boundary, not at the analysis
  boundary — that is the designed shape (`urls.py:93`: "`Screen.url_pattern` is stored host-LESS by
  every producer"). Rewriting `analysis.json` would have been me inventing a second normalisation
  point, which is exactly the "one concept, one place" rule this repo enforces.

## Acceptance — and why this unit's own `done_check` is NOT it

T-192's registered `done_check` is `uv run autotester doctor`, `expect_exit: 0`. **That check is
worthless as acceptance and I am not citing it as such.** It passes on a clean repo whether or not
this unit ever ran — it is the exact AT-100 shape (a `done_check` that cannot fail) that a checker
independently filed as **`ISS-at638-remainder-2`** (high, `goodhartable-done-check`) against five
pending tasks, T-192 among them, while this unit was in flight. Using it to claim success would be
Goodharting a check already on the ledger as broken.

**Real acceptance is the before/after structural diff**, which is falsifiable and reproducible:

- Pre-image preserved at `.work/t192/screenmap.before.json`, sha256
  `46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf`.
- A field-level comparison of every screen, before vs after, reports **exactly three changed fields
  across three screens, all of them `url_pattern`** — no screen added, none removed, journey count
  unchanged (3), screen count unchanged (8).
- Zero `url_pattern` values beginning `/vidysea.com` remain.

## Actual outputs (pasted, real — main checkout, 2026-09-27)

```
$ sha256sum projects/erp/screenmap.json          # before
46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf *projects/erp/screenmap.json

$ uv run autotester ingest map erp
erp: 8 screen(s), 3 journey(s)

$ grep -o '"url_pattern": "[^"]*"' projects/erp/screenmap.json | sort | uniq -c
      3 "url_pattern": "/erp/trainers"

$ python  # field-level diff, before vs after
screens before/after: 8 8
journeys before/after: 3 3
screen ids added: set() removed: set()
 CHANGED screen_1d9d49ae0357 Trainers List - Edit Drawer {'url_pattern': ('/vidysea.com/erp/trainers', '/erp/trainers')}
 CHANGED screen_5791c5e71012 Trainers {'url_pattern': ('/vidysea.com/erp/trainers', '/erp/trainers')}
 CHANGED screen_bedf01acbd4b Trainers List {'url_pattern': ('/vidysea.com/erp/trainers', '/erp/trainers')}

$ uv run autotester doctor
doctor: clean

$ uv run ruff check src tests scripts
All checks passed!

$ uv run pytest tests/test_urls.py tests/test_product_map.py tests/test_migrate_url_patterns.py
60 passed in 1.04s
```

**One remaining `vidysea.com` string in the file is correct and must stay** — `grep` still reports
`"vidysea.com/erp/trainers"`, which is the raw observed url carried on the screen record, not a
`url_pattern`. A repair that scrubbed it would have destroyed the provenance the pattern is derived
from. Recorded because a reviewer greping the file will see it and should know it is intentional.

## Capability coverage

**No falsification table, and no new test — stated rather than fabricated.** `core-invariants.md`'s
mutation duty applies to a unit that adds or rewrites a test; this unit adds none and changes no
code. The behaviour being relied on (`screen_url_pattern` strips a declared host from the first
segment) is already covered by the 60 tests above, which include
`tests/test_migrate_url_patterns.py` — the suite written for AT-298 precisely because an earlier
version of this repair passed a test whose own property was untrue. Writing a new test that asserts
the three repaired rows would assert a *data* state, not a capability, and would pin project data
into the test suite.

## Gaps stated, not hidden

- **No live browser render.** The gate's whole motivation is that these rows "render to a human
  today on `/projects/erp/product-map`", and I did not start the UI and look at that page. The
  structural diff proves the stored data is correct; it does not prove the page displays it. A
  checker should do that walk.
- **`projects/erp/screenmap.json` is untracked**, so this working-tree change has no commit to
  revert — the gate itself flags this. The pre-image at `.work/t192/screenmap.before.json` is the
  only undo, and `.work/` is gitignored, so **the undo is not durable across a clean**. If that
  matters, the pre-image should be stored somewhere retained.
- **The heal is not proven idempotent by this unit.** Re-running `ingest map` should be a no-op now,
  but I ran it once and did not re-run to confirm. `scripts/migrate_url_patterns.py` is documented
  idempotent; `ingest map` is a rebuild, which is a different property.
- **The approved-but-unspent vision call is a loose end for Umesh**, not for me to decide: the gate
  authorised one Analyze run and it was not used. It should be treated as still-unspent, not as
  consumed by this unit.
- **T-192's `done_check` remains broken** (`ISS-at638-remainder-2`). This unit does not fix it —
  repairing Goodhartable `done_check`s across five tasks is its own unit, and four of the five are
  in flight right now.

## Status: ready-for-check
