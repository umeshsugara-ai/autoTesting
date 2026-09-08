# Verdict — at177-cli-surface

**Cycle checked: 2**
**Date:** 2026-09-09
**Checker:** /checker Mode A, fresh subagent, bound to `D:/autoTesting`
**Adapter:** `qa/adapter.json` (coding) — Docker down, `uv` native, bare `uv run pytest`
**Contract:** `qa/contracts/core-invariants.md` (C2, C4, C7 are the live ones for this unit)
**Manifest:** `qa/manifests/at177-cli-surface.md` (Fix cycle 2)
**HEAD checked:** `bfa02c4` (manifest commit `c66fafc`)

```
VERDICT: PASS
SCOREBOARD: 8/8 criteria met, 9/9 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-184 (verified) · AT-185 (medium, open) · AT-186 (medium, open) ·
                AT-187 (low, open) · AT-188 (low, open);
                AT-179 / AT-180 / AT-181 moved open -> verified
EXPLANATION: The cycle-1 FAIL is closed in my own hands, not on the maker's word: a
marker appended to docs/SNAPSHOT.md survived a full `uv run pytest`, and the repo
fingerprint plus the entire root entry list came back unchanged. All three cycle-2
sabotages reproduce at 1 failure each and at 0 with the new test files ignored, so
each fix is genuinely pinned by work this unit did. The residuals I found — a
20/22 exclusion whose stated reason is measurably wrong, and a live-repo guard that
under-detects — are strength-of-test findings on a unit that now satisfies every
criterion it is judged against, so they are filed rather than charged.
```

---

## 1. The cycle-1 FAIL, re-proved (AT-181) — the criterion, in my hands

This is the one that failed last cycle, so I re-ran the whole proof myself rather
than reading the manifest's claim.

```
$ printf '\n<!-- CHECKER-MARKER-CYCLE2-AT181 -->\n' >> docs/SNAPSHOT.md
marker appended
  (captured: sha256 of docs/*.md + docs/*.jsonl + every repo-root file  -> 18 hashes)
  (captured: full repo-root entry list                                  -> 30 entries)

$ uv run pytest
739 passed, 2 skipped, 1 warning in 74.67s (0:01:14)

$ grep -c 'CHECKER-MARKER-CYCLE2-AT181' docs/SNAPSHOT.md
1
MARKER SURVIVED
FINGERPRINT UNCHANGED
ROOT ENTRIES UNCHANGED
```

`git status --porcelain` after the run showed nothing but the marker itself. The two
`.goal/` files that moved are the `/goal` five-minute monitor's own timestamp tick
(`updated`/`last_deterministic_tick` 23:42:02 -> 23:47:02, a diff of exactly two
timestamp lines and the derived dashboard) — not pytest. I checked the diff rather
than assuming, because a checker that waves off a dirty tree is doing the thing this
unit is about.

The marker was then removed and `docs/SNAPSHOT.md` restored byte-identical
(`git status --porcelain docs/` empty). **C7 holds: the project's own verify command
no longer rewrites the git-tracked files it verifies.**

## 2. Verification, re-run and counted myself

```
$ uv run pytest                          739 passed, 2 skipped   (claimed 739/2 — matches)
$ uv run ruff check src tests scripts    All checks passed!
$ uv run autotester doctor               doctor: clean   (exit 0)
```

## 3. AT-184 — no stray file in the repo root

Covered by the fingerprint run above: the root entry list was captured before and
after a full suite and came back identical (`diff` clean, 30 entries both times). No
file named `nonexistent`, and nothing else, appears at any point during a run.

## 4. AT-180 — I measured the reach rather than accepting 20/22

Walked click's tree and classified all 22 invocations by presence of the `Usage:`
banner, twice:

| placeholder scheme | reached application code | stopped at click's banner |
|---|---|---|
| naive `nonexistent-project nonexistent-id` (the pre-fix form) | **4** | 18 |
| arity derived from click (shipped) | **20** | 2 |

Both of the maker's numbers reproduce exactly. The remaining two are `ledger add`
and `ledger weight`, and the banner text names the cause directly:

```
Usage: root ledger add    [OPTIONS] {feature} {title} {event}:<planned|live|updated|retired>
Usage: root ledger weight [OPTIONS] {feature} {value}:<high|normal|low>
```

So "a closed vocabulary rejecting the placeholder" is accurate — verified, not taken
on trust.

**Is 20/22 with two deliberate exclusions honest?** Yes. The number is measured,
stated in the module docstring, and stated as a limit rather than rounded up. That is
exactly the correction AT-180 asked for.

**Would forcing the last two be safe and better?** Safe — yes, and the maker's stated
reason for not doing so is wrong. The docstring says valid arguments "would make both
commands write, and a write command running for real inside the verify step is
exactly AT-181". But `core/paths.py:15-20` resolves `repo_root()` from
`AUTOTESTER_ROOT`, and `docs_dir`/`features` hang off it, so the temp root already
contains the write. I proved it rather than reasoning about it:

```
$ AUTOTESTER_ROOT=<tmp> autotester ledger add nonexistent-feature "checker probe" planned -d probe
F-001 planned nonexistent-feature
$ ls <tmp>/docs
FEATURES.jsonl  SNAPSHOT.md
$ git status --porcelain docs/
(empty)
```

The maker's own fingerprint test already proves that containment across all 22
commands. Better — marginally: 22/22 with an enum value read off the click `Choice`
would remove a hand-maintained exception, and the two commands it would cover are
the repo's only ledger *write* path. Filed as **AT-185 (medium)**, not charged: no
criterion demands 22/22, and an honestly-labelled 20 is worth more than a forced 22.

## 5. AT-179 — both directions

```
$ AUTOTESTER_ROOT=<tmp> autotester ingest list nonexistent-project
no project 'nonexistent-project' yet
exit=1
```

Guard at `src/autotester/cli_video.py:53-58`. The opposite error — refusing a real
but empty project — is guarded by
`test_listing_sources_for_a_real_but_empty_project_succeeds`, which passes and asserts
exit 0. The maker's stated care here is real, not decorative: a fix that refused both
would have replaced one wrong answer with another.

## 6. Sabotages AU, AV, AW — reproduced in an isolated worktree

Run in `git worktree add .work/wt-at177 HEAD` (never `git stash`/`checkout`/`restore`
in the live tree — AT-101). Every patch asserted **anchor matched exactly once** and
**file changed on disk** before any result was believed, per C7.

| sabotage | mutation | with this unit's tests | with the new test files ignored |
|---|---|---|---|
| **AU** — `ingest list` stops refusing an unknown project | delete the whole AT-179 guard block, `cli_video.py` | **1** `test_listing_sources_for_a_project_that_does_not_exist_refuses` | **0** — INCONCLUSIVE |
| **AV** — `snapshot` runs without `--print` | drop `--print` from the invocation, `test_cli_harness_safety.py` | **1** `test_snapshot_print_is_what_makes_the_repo_level_test_safe` | n/a (the test *is* the new file) |
| **AW** — placeholders escape the temp root | revert the placeholder to a bare `"nonexistent"`, `test_cli_surface.py` | **1** `test_every_placeholder_stays_inside_the_temp_root` | **0** — INCONCLUSIVE |

All three confirmed at 1 each. The right-hand column is the part that matters: each
mutation was genuinely INCONCLUSIVE before this unit's tests existed, so the maker's
"all three fixes first came back INCONCLUSIVE" is not a rhetorical flourish — I
reproduced the null result.

## 7. The two structural-by-necessity tests, judged

### `test_snapshot_print_is_what_makes_the_repo_level_test_safe` — right call, weaker than it says

Running against the live repo is **safe today**: `cli.py:64-66` returns before any
write when `print_only` is set, and I confirmed no repo file moves. The maker's
reasoning for why a temp root cannot pin this — "the original bug was the ABSENCE of
one, so reproducing it there is impossible by construction" — is correct as far as it
goes.

But I sabotaged the **product** rather than the test, removing that early `return` so
`--print` echoes *and* writes, and the full suite came back **0 FAILED —
INCONCLUSIVE**. The reason, measured: `autotester snapshot` regenerated
`docs/SNAPSHOT.md` byte-identically to the committed copy, so a content fingerprint
sees nothing.

So, answering the question directly: **it could not damage the repo today, and it
would not reliably catch the regression it claims to catch.** Two properties, both
short of the docstring's "if that ever stops being true … this fails":

- the detector is content-based, so a write that reproduces the existing bytes is
  invisible — and that is the common case when the docs are current;
- it is a *detector*, not a *preventer*: the write happens first and is judged after,
  which is the exact ordering the maker deliberately avoided one test lower down
  ("asserted on the argv rather than on the filesystem, because the filesystem
  version needs the damage to happen first"). The reasoning was available; it was not
  applied here.

The maker's literal AV does yield 1, and I reproduced that — but it bites on
`len(result.output) > 200`, not on the fingerprint. The guard that is claimed is not
the guard that fires. Filed as **AT-186 (medium)** with a structural fix direction
(assert under a temp root that the file was never created, or assert the write is
never called). Not a FAIL: C7's criterion is that the verify step does not mutate the
repo, and I proved independently that it does not.

### `test_map_has_no_read_only_mode_which_is_why_it_is_excluded` — sound, incomplete

Pinning an exclusion is the right instinct, and the docstring states the reason
correctly: an exclusion nobody justifies is one somebody quietly reverses. Asserting
an absence is legitimate here because the absence *is* the justification — the day
`map` gains a read-only mode, the exclusion should be revisited, and this is what
makes that day visible.

It is not brittle in the false-alarm direction: `map --help` is stable and the test
cannot fire spuriously. It is incomplete in the other — it names `--print` and
`--dry-run` only, so a `--stdout` or `--no-write` would slip past. That is a
one-line widening whenever someone touches it, not a defect, and I have not filed it
separately; it is noted here so the next reader has it.

## 8. The split — nothing lost, and the import is acceptable

```
$ git show d2d547d:tests/test_cli_surface.py | grep -o '^def test_[a-z_]*' | sort   ->  14 names
$ cat tests/test_cli_surface.py tests/test_cli_harness_safety.py | ... | sort      ->  14 names
IDENTICAL TEST SET
```

Nothing was lost, renamed, or quietly dropped in the split.

**Is `from test_cli_surface import invocation_for, shipped_commands` a smell?** In
general, yes — a test module importing another test module couples two files that
should be independently deletable, and it depends on pytest's rootdir/`sys.path`
insertion rather than on a package. Here it is the right call anyway, and for a
reason specific to this unit: `shipped_commands()` and `invocation_for()` are the
*subject* of the harness-safety tests, not incidental helpers. AT-184 was a bug **in
`invocation_for` itself**, and `test_every_placeholder_stays_inside_the_temp_root`
asserts on that function's output directly. Moving them into a `conftest.py` fixture
would hide the thing under test behind indirection; moving them into `src/` would put
test scaffolding into the shipped package. The split was forced by doctor's 300-line
cap and it was split **by responsibility** (what the commands do / what running them
all must never do), which is what the cap asks for. Acceptable, and I would not ask
for it to be changed.

## 9. The doctor-RED push — the account is accurate

Verified rather than accepted:

```
$ git checkout d2d547d && uv run autotester doctor
file-too-long: tests\test_cli_surface.py - 389 lines > 300; split by responsibility
1 violation(s)
```

389 > 300, exactly as the maker describes, in the same output it read for the test
count. Fixed in the next commit `befb425` (the split), and `doctor: clean` at HEAD.
The manifest's self-report — "I took the green I was looking for and stopped reading"
— is correct on every checkable detail, and the decision to leave the commit standing
rather than rewrite history is the right one in a Lab Protocol repo.

One thing the manifest does not mention: `d2d547d`'s **commit message** is a pasted
pytest failure dump, complete with traceback and local temp paths, in a public repo.
Filed as **AT-188 (low)** — a note, not a rebase.

## 10. Adversarial — what else the harness does to the repo

- **Clutter:** `git status --porcelain --ignored=matching` after a full run shows no
  new untracked entries; every ignored path (`.work/`, `.pytest_cache/`, `profiles/`,
  `projects/*/runs/`, `__pycache__/`) predates the run and is gitignored. C4 holds.
- **Temp dirs:** all under pytest's `tmp_path`, none in the repo.
- **Git config / git state:** untouched — no test in either file invokes git, and the
  worktree used for sabotage was removed (`git worktree remove --force`).
- **Does the fingerprint watch enough?** No — and this is the sharper half of the
  question. `_repo_fingerprint` (`test_cli_harness_safety.py:41-48`) covers
  `docs/*.md`, `docs/*.jsonl` and repo-root files. `projects/`, `qa/`, `src/` and
  `.goal/` are unwatched, and `projects/<slug>/` is where the CLI does most of its
  writing (runs, cases, rubrics, flowspec). **Does it matter today? No** — I confirmed
  with `git status` across a full run that every tracked directory is genuinely
  untouched, because `AUTOTESTER_ROOT` redirection contains all of it. It matters
  later: a future command that resolves a project path without going through
  `repo_root()` would rewrite a tracked artifact with this test still green. A
  `git ls-files`-derived watch set would close it. Filed **AT-187 (low)** — a
  strengthening, not a defect.

---

## Criteria judged

| # | Criterion | Verdict |
|---|---|---|
| C2 | file ≤ 300 lines, function ≤ 50, module docstring states its one job | **met** — `doctor: clean`; 296 + 127 lines after the split; both docstrings state one job |
| C4 | repo root stays clean, scratch in `.work/` | **met** — root entry list identical across a full run; no `nonexistent` file |
| C7a | a check someone else can re-run | **met** — I re-ran all three verify commands and reproduced every number |
| C7b | sabotage asserts anchor-matched-once + file-changed | **met** — enforced in my own harness for all four sabotages |
| C7c | a zero-failure sabotage is reported INCONCLUSIVE | **met** — the manifest reports AQ, and all three cycle-2 nulls, as INCONCLUSIVE rather than as vacuous tests |
| AT-179 | unknown project refuses (1), empty project succeeds (0) | **met** — both directions run live |
| AT-180 | reach measured and honestly stated | **met** — 4→20 of 22 reproduced exactly; residual AT-185 |
| AT-181/184 | verify command does not mutate the repo it verifies | **met** — marker survived, fingerprint and root entries unchanged |

Invariants: C1, C3, C5, C6, C8, C9 untouched by this unit and re-confirmed green via
`doctor` + the full suite; C2, C4, C7 as above. **9/9 hold.**

## What I re-ran

- `uv run pytest` (full, bare) ×1 live + ×6 in an isolated worktree
- `uv run ruff check src tests scripts`, `uv run autotester doctor` (live + at `d2d547d`)
- marker-survival + repo-fingerprint + root-entry-list probe around a full suite
- an independent 22-command reach probe, twice (naive vs shipped placeholders)
- live `autotester ingest list`, `autotester ledger add`, `autotester snapshot`
- sabotages AU / AV / AW / AV-literal / a product-level `--print` mutation, each with
  anchor and file-change assertions, each also run with the new test files ignored
