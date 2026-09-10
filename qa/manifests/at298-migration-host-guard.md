# Manifest — at298-migration-host-guard

**Contract:** qa/contracts/coverage.md (V1 — the one place a URL becomes a screen-identity path) ·
qa/contracts/core-invariants.md
**Goal task:** none (ledger issue fix, not a goal row)
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no  ← not a `criticality: critical` goal task
**Issues addressed:** AT-298 (checker A, medium) · AT-298b (checker B, high) — the same defect,
filed twice under the `b`-suffix convention AT-293 established

## Why this unit exists

`scripts/migrate_url_patterns.py` shipped in T-135 cycle 3 with a guard that claimed to refuse a
dotted **first** path segment. It did not:

```
repair('/v1.2/foo')      -> '/foo'
repair('/index.html')    -> '/'
repair('/settings.json') -> '/'
```

The same false sentence appeared in **three** places — the script's own module docstring, the T-135
manifest, and `qa/gates/t135-url-pattern-data-migration.md`, **the document the human reads to
decide whether to run it**. `projects/` is untracked, so `--write` has no undo.

And the test named for that guard, `test_a_real_path_segment_containing_a_dot_is_not_treated_as_a_host`,
asserted only `/v1/release-1.0/notes` and `/docs/settings.json` — **deeper** segments, which a regex
anchored to the first segment could never have matched. It passed while the property it was named
for was false. Checker B: *"it passes while its own named property is false."*

That is the third vacuous test I have written in this sequence (a source-inspection test in T-135
cycle 1, a same-scheme cross-seam test in cycle 2, this one in cycle 3). The pattern is asserting
what is already true rather than what could break, and it is why this unit's tests are written
first against the shapes that actually failed.

## What changed

- `scripts/migrate_url_patterns.py` — **the shape guess is deleted.** New `known_hosts(project_dir)`
  reads the project's own `project.json` (`base_url` netloc + `allowed_domains`); `repair(pattern,
  hosts)` strips a first segment **only when it is a host that project declares**. `scan` resolves
  hosts per `projects/<slug>/`, so each project is judged by its own knowledge; `apply` takes the
  hosts explicitly. `re` is no longer imported — there is no pattern-matching left to do.
- `tests/test_migrate_url_patterns.py` — rewritten, 14 tests. The guard test now asserts the
  **first-segment** shapes that actually broke (`/v1.2/foo`, `/index.html`, `/settings.json`,
  `/sitemap.xml`, `/release-1.0/notes`, `/main.js`), plus: another project's host is not stripped
  here, a project declaring nothing is never repaired, hosts come from both config fields, ports
  match either way, and two projects judge the same string differently — which a shape-based guard
  could not do by construction.
- `qa/gates/t135-url-pattern-data-migration.md` — the false guarantee is replaced with what is now
  true, and option A is marked safe to choose.
- `docs/SNAPSHOT.md`, `docs/MAP.md` — regenerated (doctor flagged SNAPSHOT stale).

**This is the same fix AT-294 needed:** use knowledge the system already has, never infer from
string shape. `/v1.2/foo` and `/vidysea.com/erp` are indistinguishable as strings — but a project
that declares `allowed_domains: ["vidysea.com", "www.vidysea.com"]` has already told us which one
it is.

## How to verify (commands + expected)

- `uv run pytest -q` → exit 0
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → exit 1, **exactly one** violation (untracked root `AGENTS.md`,
  AT-283 — the certified baseline)
- `uv run python scripts/migrate_url_patterns.py` → 3 rows in 1 file, writes nothing

**The defect, reproducible on the pre-fix code** (`git show cc00e9b:scripts/migrate_url_patterns.py`):
`repair('/v1.2/foo')` returns `'/foo'`. The new
`test_a_FIRST_path_segment_that_merely_looks_like_a_host_is_left_alone` asserts `None` for exactly
that input, so it fails against the old implementation — which is the property the test it replaces
never had.

**Sabotage:** make `repair` ignore `hosts` and fall back to the old
`^/(host-shaped)(rest)` regex → the first-segment test and
`test_another_projects_host_is_not_stripped_from_this_projects_path` must fail.
Separately, make `known_hosts` return `set()` unconditionally → the repair tests and the real dry
run must find nothing.

## Actual outputs (from maker's own run, after the final edit)

```
$ uv run pytest -q
1047 passed, 2 skipped, 1 warning in 88.69s        exit=0

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1

$ uv run python scripts/migrate_url_patterns.py     # real data, dry run
projects\erp\screenmap.json
    '/vidysea.com/erp/trainers'  ->  '/erp/trainers'   (x3)
would repair 3 url_pattern(s) across 1 file(s)
dry run - re-run with --write to apply              exit=0
```

Guard behaviour, probed directly against real project config:

```
erp declared hosts: ['vidysea.com', 'www.vidysea.com']
  /vidysea.com/erp/trainers    -> '/erp/trainers'
  /www.vidysea.com/erp/x       -> '/erp/x'
  /v1.2/foo                    -> None
  /index.html                  -> None
  /settings.json               -> None
  /erp/trainers                -> None
```

## Live browser evidence

`Not UI-touching — no surface changed.` Changed paths are `scripts/`, `tests/`, `qa/gates/` and two
regenerated `docs/` files. Nothing under `ui/`, and no data a page renders is altered — the
migration still writes nothing without `--write`, and it has not been run.

## Judgements offered to the checker (please rule)

1. **Is `known_hosts` reading `project.json` directly the right seam?** `ProjectStore` exists and
   could load a typed `Project`, but the script deliberately avoids importing the store so it can
   run over an arbitrary `--root` (including a copied tree) without a store rooted there. Tolerating
   a malformed/absent `project.json` as "no hosts, no repair" is the fail-safe direction.
2. **`repair` now returns None when `hosts` is empty.** That means a project with no `project.json`
   is never repaired, even if visibly mangled. I judged silent no-op safer than a fallback guess —
   the fallback guess is precisely AT-298.
3. **Sub-domain handling is exact-match only.** `pathlynks.vidysea.com` is not repaired by an
   `allowed_domains: ["vidysea.com"]` entry, because a suffix match would re-introduce a guess.
   `projects/pathlynks` declares exactly that and holds no `url_pattern` values today, so nothing is
   affected — but it is a real limitation and I would rather it be ruled on than discovered.
4. **AT-299 / AT-299b are NOT addressed here** (`absolute_url` on free-form model text like
   `'Sign in page'` → `/`). Deliberately out of scope; checker A raised it as a question, not a
   defect, and it wants a ruling on AT-103 doctrine before code.

## Status: ready-for-check
