# VERDICT — at298-migration-host-guard

**Date:** 2026-09-11 · **Checker:** /checker Mode A (fresh subagent, read-only toward the artifact)
**Bound to:** `d:/autoTesting` · **Commit checked:** `d674083`
**Contract:** `qa/contracts/coverage.md` (V1) · `qa/contracts/core-invariants.md`
**Manifest:** `qa/manifests/at298-migration-host-guard.md`
**Cycle checked: 1**

```
VERDICT: PASS
SCOREBOARD: 4/4 manifest verify items reproduced, 9/9 core invariants hold (C1-C9), coverage V1-V6 untouched and green
FAILURES: none at >80% confidence that falsify a contract criterion
LIVE-BROWSER: not-applicable (changed paths: scripts/migrate_url_patterns.py, tests/test_migrate_url_patterns.py, qa/gates/, qa/manifests/, qa/.last-tick, docs/SNAPSHOT.md — no ui/ file, no template, no static asset, and `grep -rn migrate_url_patterns src/` returns nothing, so no page renders anything this unit changed; Mode D is NOT required for this unit)
ISSUES-WRITTEN: AT-300, AT-301, AT-302, AT-303, AT-304, AT-305, AT-306 (all residual, none blocking)
ISSUES-CLOSED: AT-298 open->fixed, AT-298b open->fixed
EXPLANATION: The guard really was rewritten from shape-guessing to project-declared knowledge, and
this checker proved the new test suite is non-vacuous by re-running it against the pre-fix
SEMANTICS in an isolated `git archive HEAD` extract: 4 tests fail, two more than the manifest
claimed. All 4 verify commands reproduce exactly (1049 collected = 1047 passed + 2 skipped; ruff 0;
doctor exit 1 with exactly one violation; dry run 3 rows / 1 file with the live file byte-identical
and its mtime unchanged). Seven residuals are filed — the most serious is that `known_hosts` does
NOT fail safe on a malformed `allowed_domains`, which is precisely what the manifest's judgement #1
claims it does; it cannot fire on today's data, so it does not block.
```

## What I re-ran (never read)

All sabotage/mutation work ran in a `git archive HEAD` extract under the session scratchpad
(`…/scratchpad/ext`), **never** the live tree. Import resolution was asserted before any result was
believed:

```
autotester -> …\scratchpad\ext\src\autotester\__init__.py
migrate    -> …/scratchpad/ext/scripts\migrate_url_patterns.py
```

| Manifest claim | My result | Verdict |
|---|---|---|
| `uv run pytest -q` → exit 0, 1047 passed / 2 skipped | exit 0, twice. The project's `addopts = "-q"` plus a CLI `-q` makes `-qq`, which suppresses the summary line, so I derived the counts instead: `pytest --collect-only` = **1049 tests collected**, and the run's progress output carries exactly **two `s`** ⇒ 1047 passed + 2 skipped | ✅ reproduced |
| `uv run ruff check src tests scripts` → exit 0 | `All checks passed!` exit 0 | ✅ |
| `uv run autotester doctor` → exit 1, exactly one violation | `root-clutter: AGENTS.md` · `1 violation(s)` · exit 1 | ✅ exactly one, and it is the AT-283 certified baseline |
| dry run → 3 rows in 1 file, writes nothing | 3 rows in `projects\erp\screenmap.json`, exit 0; md5 `4a73116d792b26226bc499be43b4cd8b` **and** mtime `2026-09-11 02:45:01.885760300` identical before and after | ✅ byte-identical, not merely same size |
| migration not run on real data | all three stored `url_pattern`s are still `/vidysea.com/erp/trainers`; the file's mtime (02:45) predates this unit's commit (03:27) | ✅ confirmed NOT run |

## Sabotage 1 — `repair` ignores `hosts` and falls back to the pre-fix shape regex

The pre-fix code has a different signature (`repair(pattern)`, no `known_hosts`), so running the new
tests against `cc00e9b` verbatim would only prove an ImportError. The honest comparison is the
pre-fix **semantics** inside the new signature — which is exactly the manifest's sabotage 1.

Anchor asserted before believing anything (C7): **ANCHOR COUNT: 1 · FILE CHANGED: True**. The
mutation was then shown to change behaviour (C7's zero-failure clause), reproducing AT-298 exactly:

```
'/v1.2/foo'                 -> '/foo'
'/index.html'               -> '/'
'/settings.json'            -> '/'
'/saucedemo.com/cart'       -> '/cart'
'/vidysea.com/erp/trainers' -> '/erp/trainers'
```

Result: **4 failed, 10 passed** —
`test_a_FIRST_path_segment_that_merely_looks_like_a_host_is_left_alone`,
`test_another_projects_host_is_not_stripped_from_this_projects_path`,
`test_a_project_that_declares_nothing_is_never_repaired`,
`test_each_project_is_judged_by_its_own_declared_hosts`.

The manifest predicted 2; the real delta is 4 (a delta, not a suite total). **The named property is
now genuinely defended.** The maker's "third vacuous test" worry does not apply to the guard test.

## Sabotage 2 — `known_hosts` returns `set()` unconditionally

**ANCHOR COUNT: 1 · FILE CHANGED: True.** Against a sandbox COPY of the real erp tree the dry run
printed `…realcopy: nothing to repair` (the manifest's prediction), and the file's suite went
**6 failed**: `declared_hosts_come_from_both_base_url_and_allowed_domains`,
`it_repairs_a_file_and_reports_what_it_changed`, `it_is_a_dry_run_unless_told_otherwise`,
`write_applies_the_repair`, `it_walks_past_json_that_uses_screens_for_something_else`,
`each_project_is_judged_by_its_own_declared_hosts`. Both halves of the manifest's sabotage
reproduce.

## Per-test non-vacuity — the crux, all 14 mutation-tested

Ten further mutations were applied one at a time, each with an anchor-count assertion and a
file-changed assertion. A test counts as non-vacuous only when a mutation that demonstrably changes
behaviour kills it.

| # | Test | Fails vs pre-fix semantics? | Killed by | Ruling |
|---|---|---|---|---|
| 1 | `a_declared_host_swallowed_into_the_path_is_repaired` | no (old regex repaired it too) | M3 `repair`→None | non-vacuous (positive) |
| 2 | `a_healthy_pattern_is_left_alone` | no | M4 strip-first-segment-unconditionally | non-vacuous |
| 3 | `a_FIRST_path_segment_that_merely_looks_like_a_host_is_left_alone` | **YES** | M1, M4 | **the discriminating test — real** |
| 4 | `another_projects_host_is_not_stripped_from_this_projects_path` | **YES** | M1, M4 | non-vacuous |
| 5 | `a_project_that_declares_nothing_is_never_repaired` | **YES** | M1 | non-vacuous |
| 6 | `declared_hosts_come_from_both_base_url_and_allowed_domains` | n/a (new API) | M2, M7 drop-netloc | non-vacuous |
| 7 | `a_host_with_a_port_is_matched_either_way` | no | M3 only | **VACUOUS for its named property → AT-303** |
| 8 | `it_repairs_a_file_and_reports_what_it_changed` | no | M3, M4, M10 | non-vacuous |
| 9 | `running_it_twice_changes_nothing_the_second_time` | no | M4 | non-vacuous (see the C7 note) |
| 10 | `it_is_a_dry_run_unless_told_otherwise` | no | M5 write-on-dry-run (uniquely) | non-vacuous |
| 11 | `write_applies_the_repair` | no | M3 | non-vacuous |
| 12 | `a_clean_tree_reports_nothing_to_do` | no | M4 | non-vacuous |
| 13 | `it_walks_past_json_that_uses_screens_for_something_else` | no | M9 drop-isinstance-list (uniquely) | non-vacuous |
| 14 | `each_project_is_judged_by_its_own_declared_hosts` | **YES** | M1, M2, M10 | non-vacuous |

**Test #7 is the one bad one, and the maker's stated failure mode did recur — in a different test
than it feared.** Its fixture declares `{"127.0.0.1", "127.0.0.1:46661"}` — *both* forms — so the
port-normalising branch the test is named for (`candidate.split(":", 1)[0] not in hosts`) is never
reached: the plain `candidate in hosts` arm satisfies both assertions. Deleting that branch entirely
(mutation M8) leaves **0 failures**, and `grep` confirms nothing else in the repo exercises it. That
is a live, deletable code branch with no defending test, inside the very unit written to end this
pattern. Filed **AT-303** (medium). Not a FAIL: no contract criterion demands per-test strength, the
unit's own claimed property is proven, and the standing precedent in this ledger (AT-261, filed low
on exactly this shape) is a residual rather than a rejection.

**C7's zero-failure clause, applied to myself:** mutation M6 (`apply` rewrites the file even when
nothing changed) produced **0 failures**, and I report that as **INCONCLUSIVE — mutation not shown
to change behaviour**, not as "test #9 is vacuous". Re-serialising unchanged data yields identical
bytes and the `changed` counter is still 0, so the mutation is observationally inert. Test #9
asserts the observable property (byte-identical file, 0 changes), which is the right one.

## Attacks on the guard itself (probed, not reasoned)

| Attack | Behaviour | Ruling |
|---|---|---|
| Case: `/VIDYSEA.COM/erp/x` | → `/erp/x` | correct — both sides lower-cased |
| Trailing dot: `/vidysea.com./erp/x` | → `None` | fail-safe (under-repairs) |
| IDN / punycode mismatch | → `None` | fail-safe |
| Declared domain a PREFIX of a real segment (`/vidysea.community/x`) | → `None` | correct — exact match, no `startswith` |
| Declared domain a SUFFIX (`pathlynks.vidysea.com` vs `vidysea.com`) | → `None` from `allowed_domains` alone | correct by design; see ruling #3 |
| Port either way (`/vidysea.com:8080/x`, host declared bare) | → `/x` | correct — but untested (AT-303) |
| Absent / unreadable / non-JSON `project.json` | → `set()` → no repair | **fail-safe ✅** |
| **`allowed_domains` as a JSON string** `"vidysea.com"` | hosts = every CHARACTER; `/v/foo` → `/foo`, `/a/b` → `/b` | **NOT fail-safe → AT-300** |
| `allowed_domains: [80, true]` | hosts = `{"80","true"}` | same class → AT-300 |
| **`base_url` with userinfo** `https://user:pass@vidysea.com/erp` | hosts = `{"user", "user:pass@vidysea.com"}` — the real host is absent and **`/user/foo` → `/foo`** | → AT-301 |
| `base_url` an IPv6 literal `http://[::1]:8080/` | hosts = `{"[", "[::1]:8080"}` — the real host `[::1]` is absent | → AT-302 |
| `--root` = a flat project dir (`projects/erp`) | a file directly in it is repaired ✅; a file in a SUB-directory is **silently skipped** | the manifest's claim is half true → AT-304 |
| A file directly in `projects/` (not inside a project subdir) | `_project_dir_of` → root → no `project.json` → no repair | fail-safe, correct |

`allowed_domains` as a dict is harmless (iteration yields the keys). None of AT-300/301/302 can fire
on today's data: I checked all nine real `project.json` files and every one declares
`allowed_domains` as a proper list of strings with a `base_url` carrying neither userinfo nor an
IPv6 literal.

## Rulings on the four judgements the manifest offered

**1. `known_hosts` reading `project.json` directly — the SEAM is right, the FAIL-SAFE claim is not
fully earned.** Bypassing `ProjectStore` so the script can run over an arbitrary `--root` is the
correct call and is consistent with C6 ("a human can open, edit or delete any artifact and the
system still loads"). But the manifest states that "tolerating a malformed/absent `project.json` as
*no hosts, no repair* is the fail-safe direction", and that holds only for *absent / unreadable /
non-JSON*. A structurally valid JSON file with a mis-typed `allowed_domains` produces the most
dangerous host set this script can hold — one entry per character. The direction is endorsed; the
implementation does not yet reach it. **AT-300** (medium); one `isinstance(..., list)` guard closes
it. This matters because it is AT-298's own shape: a document asserting a guard property the code
does not have.

**2. `repair` returning `None` when `hosts` is empty — CORRECT, and I would refuse any softening of
it.** A silent no-op on an undeclared project is strictly better than a fallback guess, and the
fallback guess is exactly AT-298 (and AT-287 before it). Test #5 pins it and dies under the pre-fix
semantics. Endorsed without reservation.

**3. Sub-domain handling — the CALL is right, the manifest's worked example is WRONG.** Exact match
is correct: a suffix match re-introduces the guess this unit exists to delete, and it would mean an
`allowed_domains: ["vidysea.com"]` entry silently claiming authority over every sub-domain anyone
ever mounts. Keep it. **However**, the manifest says `pathlynks.vidysea.com` "is not repaired by an
`allowed_domains: ["vidysea.com"]` entry" and cites `projects/pathlynks` as the example. That
project's `base_url` is `https://pathlynks.vidysea.com/signin`, whose netloc `known_hosts` *does*
add — measured against the real config:

```
known_hosts('projects/pathlynks') == ['pathlynks.vidysea.com', 'vidysea.com']
repair('/pathlynks.vidysea.com/signin', those_hosts) == '/signin'
```

So `pathlynks` is fully covered and the limitation is narrower than stated: it bites only a
sub-domain named in **neither** `base_url` **nor** `allowed_domains` (e.g. an `admin.vidysea.com`
screen inside `projects/erp`). In that case the pattern is left alone — an under-repair, the safe
direction, visible as a stale display rather than as lost data. **Not a gap worth closing in code.**
Recorded as **AT-305** (low) so the corrected example lives on disk rather than only in this verdict.

**4. AT-299 / AT-299b out of scope — AGREED.** `absolute_url` on free-form model text is an ingest
boundary question that turns on AT-103 doctrine, not on this script. Both stay `open`, untouched by
this unit; no criterion here reaches them.

## Ruling on the gate document `qa/gates/t135-url-pattern-data-migration.md`

**"Option A is now safe to choose" is TRUE**, and I verified it independently rather than taking the
maker's word. On an isolated COPY of the real `projects/erp` tree (the live file was never written):

```
repaired 3 url_pattern(s) across 1 file(s)
diff before/after: 3 changed lines (102, 154, 172), 12 diff lines, 11513 -> 11477 bytes
every change is "url_pattern": "/vidysea.com/erp/trainers" -> "/erp/trainers"
second --write: "nothing to repair", md5 unchanged
live projects/erp/screenmap.json: md5 4a73116d792b26226bc499be43b4cd8b throughout
```

Nothing else in the document moves — the `json.dumps(indent=2)` round-trip that AT-298b warned could
make a false positive un-diffable is, on this actual file, a no-op outside the three values. The
document's caveat ("`projects/erp/screenmap.json` is untracked, so take a copy first") is accurate
and should stay. Every factual claim in the `> ✅ RESOLVED` block checks out against the code I read.

**One correction the human should see before answering:** line 26 still says "**9 tests** in
`tests/test_migrate_url_patterns.py`" while the resolved block thirteen lines below says 14. The
file has 14. A stale count in the "what is already true" section of the document a human decides on
is the same species of defect as AT-298, at a much smaller scale. Filed **AT-306** (low); fix it
before the gate is answered.

Everything else in the gate is sound: the producer-is-fixed claim, the three options and their
consequences, the B-else-A recommendation, and the untouched `Answered:` line. The gate correctly
remains **unanswered** — this verdict does not answer it, and the human's choice is unaffected.

## Contract criteria

- **coverage.md V1–V6** — not modified by this unit and green in the full suite. `url_template(...,
  keep_host=False)` remains the single place a URL becomes a screen-identity path, and the script
  calls exactly that function rather than reimplementing path templating, so V1's "one place"
  property is preserved by the change. No amendment is needed for this unit.
- **core-invariants C1–C9** — all hold. C2/C3/C4 via `doctor` (one violation, the certified AGENTS.md
  baseline). C7 is *exceeded*: every sabotage here asserted its anchor count and its file change
  before any result was believed, and the one zero-failure mutation is reported as INCONCLUSIVE
  rather than as a vacuous test.
- **C7 nits, noted rather than charged:** the manifest's pasted dry run collapses three identical
  rows to `(x3)`; the real output prints three separate lines. The numbers are right and reproduce,
  but C7 asks for real output, not a summary. Likewise the manifest lists `docs/MAP.md` as
  regenerated — the commit touches only `docs/SNAPSHOT.md`.

## Issues written

- **AT-300** (medium) — `known_hosts` does not fail safe on a mis-typed `allowed_domains`.
- **AT-301** (medium) — a `base_url` with userinfo injects the username as a declared host.
- **AT-302** (low) — an IPv6-literal `base_url` yields `[` as a host and omits the real one.
- **AT-303** (medium) — the port test is vacuous for its named property; the branch deletes green.
- **AT-304** (low) — a flat `--root` silently skips json files in sub-directories.
- **AT-305** (low) — the manifest's sub-domain example is factually wrong (`pathlynks` IS covered).
- **AT-306** (low) — the gate document says 9 tests in one place and 14 in another.

## Issues closed by this unit

- **AT-298** open → **fixed** — the shape guess is deleted; `repair('/v1.2/foo', erp_hosts)` is
  `None` on the committed code, and the defending test dies against the old semantics.
- **AT-298b** open → **fixed** — the same defect, checker B's filing. Its "expected" asked for either
  a real guard or the deletion of the false claims; this unit did both, and the gate document no
  longer carries the false sentence.

Both move to `verified` only on a later re-check, per the ledger rules.
