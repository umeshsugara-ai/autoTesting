# Manifest — at300-migration-config-hardening

**Contract:** qa/contracts/coverage.md (V1) · qa/contracts/core-invariants.md
**Goal task:** none (ledger issue batch)
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no  ← not a `criticality: critical` goal task
**Issues addressed:** AT-300 · AT-301 · AT-302 · AT-303 · AT-304

## Why this unit exists

All five came from the checker's PASS verdict on `at298-migration-host-guard`. None can fire on
today's data — all nine real `project.json` files are well-formed — so this is hardening a script
that rewrites real project artifacts, before anyone gives it `--write` on a tree we did not author.

## What changed — `scripts/migrate_url_patterns.py`

- **AT-300** — `allowed_domains` given as a JSON **string** iterated CHARACTERS, so
  `"vidysea.com"` declared every letter as a host and made any one-character first segment
  strippable. Now only a genuine `list` of non-empty strings contributes; anything else contributes
  nothing. This is the claim the previous manifest's judgement #1 made ("malformed config fails
  safe") and did not hold.
- **AT-301 / AT-302** — `known_hosts` split `.netloc` on `":"`, which made the **username** of a
  `user:pw@host` base_url a declared host (`/user/foo` → `/foo`) and yielded `[` for an IPv6
  literal. Now uses `urlsplit(...).hostname` / `.port` — the parsed host, lowercased, userinfo
  stripped, brackets removed — with a `ValueError` guard for a malformed authority.
- **AT-304** — `_project_dir_of` assumed the project sits exactly one level under the root. Now it
  walks **up** to the nearest directory that actually holds a `project.json`.
- **AT-303** — `test_a_host_with_a_port_is_matched_either_way` was **vacuous**: its fixture declared
  both `127.0.0.1` and `127.0.0.1:46661`, so the `candidate.split(":", 1)[0]` fallback could be
  deleted with the suite green. Replaced by a test declaring only the bare host, plus its mirror.

Behaviour on well-formed config is unchanged: `erp` still resolves to
`['vidysea.com', 'www.vidysea.com']` and the real dry run still reports the same 3 rows in 1 file.

## The part that matters more than the fixes

**I mutation-tested my own tests before submitting, and it caught a fifth vacuous test.**

This session has produced four vacuous tests, every one found by a checker running mutation and
none by me re-reading my own work (see `qa/feedback-inbox.md` 2026-09-11T04:00 for the four, and
the proposal to make this a standing verify step). So this unit ran that step itself first.

`M4` **survived** on the first attempt: my AT-304 tests exercised `--root projects` (where
`parts[0]` is the slug, which the old code handled) and a file directly in a flat root (one part,
also handled). Neither touched the actual defect. The shape that breaks is a flat
`--root projects/erp` with the artifact in a **subdirectory** — `parts[0]` is then `crawl`, which
holds no `project.json`, so the file is silently skipped and its corruption survives the migration.
Test rewritten to that shape; M4 now kills it.

Harness and full output are committed as evidence so the checker can re-run rather than take my
word: `qa/evidence/at300-migration-config-hardening/mutation_harness.py` and `mutation_run.txt`.
It copies `scripts/ tests/ src/` to a temp dir **outside** the repo, asserts each anchor matches
exactly once, asserts the file actually changed, and restores byte-identically.

```
BASELINE: exit=0  21 passed

M1 allowed_domains list-guard removed        KILLED  (1 failed)
M2 hostname/port reverted to netloc.split    KILLED  (2 failed)
M3 port fallback in repair removed           KILLED  (1 failed)
M4 _project_dir_of reverted to depth-1       KILLED  (1 failed)   <- SURVIVED before the rewrite
```

## How to verify (commands + expected)

- `uv run pytest -q` → exit 0
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → exit 1, **exactly one** violation (untracked root `AGENTS.md`, AT-283)
- `uv run python scripts/migrate_url_patterns.py` → 3 rows in 1 file, writes nothing
- `uv run python qa/evidence/at300-migration-config-hardening/mutation_harness.py` → baseline 21
  passed, then all four mutations KILLED

## Actual outputs (from maker's own run, after the final edit)

```
$ uv run pytest -q
1054 passed, 2 skipped, 1 warning in 87.27s        exit=0

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1

$ uv run python scripts/migrate_url_patterns.py
would repair 3 url_pattern(s) across 1 file(s)
dry run - re-run with --write to apply              exit=0
```

Hostile-config probe, run directly:

```
AT-300 allowed_domains as a STRING : []
AT-301 base_url with userinfo      : ['real.test']        (/user/foo -> None)
AT-302 IPv6 literal                : ['::1', '::1:8080']  ('[' absent)
       normal case still works     : ['vidysea.com', 'www.vidysea.com']
```

## Live browser evidence

`Not UI-touching — no surface changed.` Changed paths are `scripts/`, `tests/`, `qa/`. Nothing
under `ui/`; `grep -rn migrate_url_patterns src/` returns nothing; the migration still writes
nothing without `--write` and has not been run. `projects/erp/screenmap.json` is byte-unchanged.

## Judgements offered to the checker (please rule)

1. **AT-305 is deliberately NOT fixed.** The previous checker endorsed exact-match sub-domain
   handling as correct and corrected my example — `pathlynks.vidysea.com` *is* a known host for
   `projects/pathlynks` via its `base_url` netloc. The residual only bites a sub-domain present in
   neither field, which no project has. Fixing it would mean suffix matching, i.e. re-introducing a
   guess. I judged leaving it right; overrule me if the limitation should at least warn.
2. **IPv6 hosts are stored bracketless** (`::1`), while a swallowed IPv6 host in a stored pattern
   would presumably appear as `/[::1]:8080/app`. So AT-302 is fixed in the sense that `[` is no
   longer a declared host, but an actually-mangled IPv6 pattern still would not be repaired. I
   judged that acceptable — no project uses IPv6 and inventing the bracket handling untested would
   be worse — but it is a knowingly partial fix and I would rather declare it than have it found.
3. **The mutation harness is committed under `qa/evidence/`, not `scripts/`.** It is evidence for
   this unit, not a supported tool. Whether it should become part of the adapter's slot-1 verify is
   the open proposal in `qa/feedback-inbox.md`, which is the checker's to fold in — I have not
   pre-empted that ruling by wiring it in.

## Status: checked-PASS

Checker PASS, `qa/verdicts/at300-migration-config-hardening.md` (Cycle checked: 1) — 6/6 criteria,
5/5 applicable invariants, Mode D correctly ruled not-applicable. AT-300..AT-304 closed.

**The vacuous-test streak is broken, and independently so.** The checker re-ran my harness (4/4
KILLED, reproduced verbatim) and then ran **twelve mutations of its own** with the baseline asserted
green, ruling that **no test in this unit is vacuous for its stated property**. Nine of its
mutations survived, but it correctly classified those as *undefended defensive branches* — no test
is named for them — rather than as vacuous tests.

**It found a real hole in my harness (AT-307):** `KILLED` is `exit != 0`, and the baseline was
**printed but never asserted**, so a suite that was already red would certify every test
non-vacuous — precisely when it matters most, since this repo has a documented flake (AT-196).
Fixed in the follow-up unit; C7 tightened by the checker to require a baseline assertion.

Four low residuals filed (AT-307..AT-310): the harness hole; three undefended defensive branches
(the `ValueError` guard, the `_project_dir_of` root-containment `break`, `.is_file()`/`OSError`);
and AT-310, which promotes my judgement #2 out of a manifest — a limitation living only in a
manifest is read once. The checker's ruling on that is worth keeping: *declaring it is necessary
but not sufficient.*

Judgements #1 and #3 upheld. #2 upheld **and measured rather than presumed** — it confirmed
`url_template('[::1]:8080/app')` really is `/[::1]:8080/app` and that `repair` returns `None`, then
declined to fix it, because inventing bracket handling with no specimen is how AT-298 happened.
