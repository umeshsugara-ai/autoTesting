# Verdict — at185-at187-write-not-change

**Date:** 2026-09-09
**Cycle checked:** 1
**Manifest:** `qa/manifests/at185-at187-write-not-change.md` (commit `8298020`)
**Contract:** `qa/contracts/core-invariants.md` — C4, C7 (and C2, C3 via doctor)
**Adapter:** `qa/adapter.json` (coding). Docker down; `uv` native; bare `uv run pytest`.

## VERDICT: PASS

Every claim in this manifest was re-derived by execution, not read. The unit's whole
claim — that the checker's own product sabotage now fails where it previously left the
suite green — is confirmed, and confirmed *by the mechanism the fix names* (`mtime_ns`,
with the sha256 and the size both identical).

---

## 1. AT-186 — sabotage AX re-run (the unit's whole claim)

Isolated worktree at `8298020` (AT-101: no `git stash`/`checkout`/`restore` in the live
tree). Harness asserts C7's two preconditions before believing anything.

Mutation — the exact product mutation, `src/autotester/cli.py:60-68`, removing the early
`return` so `snapshot --print` echoes **and** writes:

```
ANCHOR count = 1
anchor matched once, file changed
 src/autotester/cli.py | 1 -
 1 file changed, 1 deletion(-)
```

Result:

```
>       assert before == after, "snapshot --print wrote to the repository"
E       AssertionError: snapshot --print wrote to the repository
E         Differing items:
E         {'docs\SNAPSHOT.md': (1788892987910587700, 10568, 'd6100b26...b5b8')}
E      != {'docs\SNAPSHOT.md': (1788893032245811700, 10568, 'd6100b26...b5b8')}
FAILED tests/test_cli_harness_safety.py::test_snapshot_print_is_what_makes_the_repo_level_test_safe
1 failed, 3 passed in 7.28s
```

Note what the diff shows: **size identical, sha256 identical, mtime_ns the only field that
moved.** That is exactly the claim — a content hash saw nothing here, and the previous
fingerprint was a content hash. The green-to-failing transition is real and it is caused
by the added field, not by an incidental side effect. Sabotage reverted afterwards
(`git -C <worktree> checkout -- src/autotester/cli.py`).

## 2. Verification re-run (counted, not read)

```
uv run pytest                          739 passed, 2 skipped, 1 warning in 77.66s   (FAILED lines: 0)
uv run ruff check src tests scripts    All checks passed!
uv run autotester doctor               doctor: clean
```

All three match the manifest exactly.

## 3. Attack on the new fingerprint

| Probe | Result |
|---|---|
| identical bytes, identical size, write visible? | **caught** — via `mtime_ns` (sabotage AX above) |
| equal-sized *different* file | caught — `sha256` differs |
| file deleted and recreated | caught — `mtime_ns` differs |
| file deleted, not recreated | caught — `after.get(k)` is `None != before[k]`, lands in `changed` |
| new file created | caught — `created = set(after) - set(before)` |
| new **directory** at repo root + files inside | **NOT caught** — filed AT-190 (low) |
| mtime granularity | ~0.5 ms real, not 1 ns — filed AT-191 (low), no live risk |

**mtime granularity, measured on this host:** 200 successive identical-byte writes to one
file produced only **41 distinct `st_mtime_ns` values** (minimum non-zero delta 479 700 ns
≈ 0.48 ms); in a tight stat/write/stat loop **40 of 50 writes left `st_mtime_ns`
unchanged**. So the instrument is a ~0.5 ms tick, not a nanosecond. It does not threaten
either test: the baseline walk stats and sha256s **1258 files** before any command runs,
and the observed sabotage delta was 44.3 ms. Recorded as AT-191 so nobody later reads
`mtime_ns` as "nanosecond-exact".

**Does the `.goal/` exclusion open a hole?** No — for `.goal/`. `grep -rn "\.goal"
src/autotester/ --include=*.py` finds only *reads* (`core/paths.py:230`,
`ledger/render.py:170`, `cli.py:117`, `doctor.py`), no write path, and `repo_root()` is the
temp root during the matrix anyway. The exclusion is correctly reasoned and costs nothing.

**But the same reasoning condemns `qa/`, which this commit ADDED** — see AT-189 below.

**Is watching `src/` sensible?** Defensible but low-value: no CLI code writes into `src/`,
so it is insurance rather than detection. `__pycache__` is excluded and `.pyc` files cannot
live outside it, so the ordinary pytest workflow does not perturb it. The residual is a
human editing `src/` inside the few-second window between one test's `before` and `after` —
inherent to any filesystem-diff guard, not specific to this change, and not worth a finding.
Cost is real though: 1258 files hashed twice per test, twice over (98 `src/`, 207 `qa/`,
923 `projects/`).

## 4. AT-185 — all 22 reach application code, and the matrix writes nothing

Walked the shipped surface myself in the worktree with `AUTOTESTER_ROOT` on a temp dir and
classified each result as "click `Usage:` banner" vs "reached application code":

```
total: 22   stopped at click banner: 0
temp root entries: []
```

Every one of the 22 produces an application-level message or an application-level
exception. The two that AT-185 is about:

* `ledger add` → `pydantic_core.ValidationError: 1 validation error for FeatureEvent /
  feature / String should match pattern '^[a-z0-9][a-z0-9-]*$'` — that is
  `schema/ledger.py`, well past the parser.
* `ledger weight` → `ValueError: unknown feature '<temp>/nonexistent'` — application code.

**The repo-damage question, which the maker got wrong once before.** I ran the full matrix
including `ledger add` with the real enum value, then diffed:

```
git status --short          ?? probe.py          (my own probe, nothing else)
sha256sum docs/FEATURES.jsonl   88be1b6c...5c3304   (unchanged; last touched by 65becbec)
```

`docs/FEATURES.jsonl` is byte-identical. To show the redirection is actually load-bearing
rather than accidental, I re-ran with a temp root that *has* a `docs/` directory: `snapshot`
then exits 0 and writes — and the write lands in the **temp root**
(`temp tree: ['docs', 'docs\SNAPSHOT.md']`), not the repository. The manifest's correction
is right and its old justification was indeed wrong: `repo_root()` honours
`AUTOTESTER_ROOT`, so forcing those two past the vocabulary is safe.

## 5. The placeholder exemption — is "has choices" ever also "is a path"?

Enumerated every parameter of all 22 commands that carries a `choices` attribute:

```
ledger add     event       required=True  type=TyperChoice  click.Path=False  ['planned','live','updated','retired']
ledger add     user_value  required=False type=TyperChoice  click.Path=False  ['high','normal','low']
ledger weight  value       required=True  type=TyperChoice  click.Path=False  ['high','normal','low']
```

Three parameters, two closed vocabularies, none path-typed, no value that could be read as
a destination. The exemption is sound as the surface stands today. One looseness worth
naming without filing: the test exempts by **token value** against the union of the whole
command's vocabularies rather than per-parameter, so a *positional path* placeholder whose
value happened to equal a vocabulary word would slip through. Placeholders are absolute
temp-root paths, so a collision cannot arise; it is a shape to remember if placeholders
ever become short strings again.

## 6. The extraction

* `tests/cli_walk.py` — `shipped_commands` and `invocation_for` moved verbatim apart from
  the AT-185 `choices` branch; nothing lost.
* **pytest does not collect it:** `uv run pytest --collect-only -q tests/cli_walk.py`
  returns nothing (`testpaths = ["tests"]`, default `test_*.py` discovery).
* **Import direction is clean:** `grep -rn "from test_cli_surface|import test_cli_surface"
  tests/` returns nothing. Both test modules now import the helper; the helper imports only
  `click`, `typer`, and `autotester`. Same shape as `tests/crawl_fake.py`.

## 7. The doctor-red account

Line-count history of `tests/test_cli_surface.py`:

```
81efef9  201   test(cli): AT-177 -- drive the 15 shipped commands
d2d547d  389   FFFF..FF                     <- the committed doctor-RED, already on record
befb425  296   test(cli): split the harness-safety tests out
8298020  237   this unit
```

Only **one** doctor-red state was ever committed (`d2d547d`, 389 lines). The maker's "it
had crossed again by 9 lines" is therefore about the *working tree* between `befb425` (296)
and this commit — 296 + the AT-185 additions ≈ 305 — caught by reading doctor's output and
resolved by the extraction rather than by a commit. The arithmetic is consistent and the
history contains no second red commit. Account accepted; the claim is not inflated.

## 8. Adversarial — flakiness and legitimate writes

**`projects/`:** no command in the 22 writes into the repo's `projects/` during the matrix.
Measured: the temp root ends the matrix empty, and the worktree ends it clean. Because
`repo_root()` honours `AUTOTESTER_ROOT`, legitimate temp-root behaviour never touches
`projects/` in the repo, so adding it does not manufacture false repo-damage reports. This
part of AT-187 is a straight strengthening.

**`qa/` is the one that is wrong (AT-189, medium).** The very docstring that adds
`WATCHED_DIRS` excludes `.goal/` because "the /goal monitor rewrites its timestamp every few
minutes, so including it would make this test fail on the clock rather than on a command" —
and then includes `qa/`, which has exactly that property. During this check:

```
qa/.last-tick     written 00:12   (every maker tick)
qa/issues.jsonl   written 00:02
qa/.last-sweep    23:09           qa/QUEUE.md  23:09
qa/verdicts/      00:03           <- this verdict file itself
```

and both `qa\.last-tick` and `qa\issues.jsonl` are confirmed present in the fingerprint
(207 of 1258 watched files are under `qa/`). Meanwhile the detection value is nil: no CLI
code writes into `qa/`, and the matrix runs against the temp root regardless. So `qa/` buys
nothing and reintroduces the clock-failure mode this same commit's reasoning rejects — a
maker tick or a checker sweep landing during `uv run pytest` fails the suite on a file no
command touched. Not a failure of anything this unit claimed, and not enough to withhold a
PASS the sabotage evidence has earned; filed as the next fix.

---

## SCOREBOARD

```
VERDICT: PASS
SCOREBOARD: 3/3 unit claims evidenced, 4/4 invariants hold (C2, C3, C4, C7)
FAILURES: none
ISSUES-WRITTEN: AT-189 (medium), AT-190 (low), AT-191 (low)
ISSUES-CLOSED: AT-185, AT-186, AT-187 -> verified
EXPLANATION: The unit's central claim is confirmed by execution in an isolated worktree —
the checker's own product mutation (removing snapshot --print's early return) now FAILS
where it left the suite green, and the failing field is mtime_ns with size and sha256 both
identical, which is precisely the property the fix added. 739 passed / 2 skipped, ruff and
doctor clean, all counted here. AT-185 verified independently: 0 of 22 commands stop at
click's Usage banner, the full matrix including `ledger add` leaves docs/FEATURES.jsonl
byte-identical and the worktree clean, and a temp root with a docs/ directory proves the
redirection is load-bearing rather than accidental. The placeholder exemption is not a hole
— all three choice-typed parameters are short closed vocabularies, none path-typed. The
extraction lost nothing, is not collected by pytest, and removes the module-imports-module
smell. Three new findings, none of them a broken claim: qa/ was added to the watched set
despite being rewritten on a timer by the pair's own automation (AT-189, the same hazard
.goal/ was excluded for, with zero detection value), the repo-root walk is files-only so a
new root DIRECTORY is invisible (AT-190), and mtime_ns is a ~0.5 ms tick on this host
rather than nanosecond-exact (AT-191, measured, no live risk).
```
