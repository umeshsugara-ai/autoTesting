# Verdict — at500-a-letter-suffixed-id-is-an-id

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`
**Unit commit:** `17d0d58`. Tick stamp `6c8b3fa` confirmed to touch only `qa/.last-tick`.
**Contract:** `qa/contracts/core-invariants.md` C10 (also touches C7's mutation duty, since this
unit adds tests).

## Re-run, independently, everything the manifest claims

- `uv run pytest -q -o addopts= tests/test_doctor.py` → **23 passed** (matches).
- `uv run ruff check src tests scripts` → **All checks passed!** (matches).
- `uv run autotester doctor` → **doctor: clean** (matches). Confirmed this is not a false
  "clean": diffed the OLD (`AT-\d+`) vs NEW (`AT-\d+[a-z]?`) `named`-extraction regex over every
  line in `qa/manifests/*.md` and `qa/verdicts/*.md` that contains the `**Issues addressed:**` /
  `ISSUES-WRITTEN` marker. The only ids the widening newly picks up are `AT-297b`, `AT-298b`,
  `AT-299b` — all three have real, current ledger rows, so nothing new is reported. No
  over-widening onto prose that isn't a real id.
- `uv run python scripts/mutation_check.py qa/evidence/at500-a-letter-suffixed-id-is-an-id/mutations.json`
  → **5/5 mutations killed**, exit 0. Checked each kill's actual failure list against its
  claimed `kills:` list (C7 attribution clause): all 5 claimed tests are present in the actual
  failure list for their mutation (mutation 2's actual list is a proper superset of its claim —
  admissible under C7's "appear in that run's failure list" wording, not an exact-match
  requirement).
- `uv run pytest -q` → judged by the exit code and the progress line, per the manifest's own
  documented `-qq` limitation (no summary line at this verbosity; filed as AT-503). Captured raw
  output myself (not a pasted count): progress reaches `[100%]` with only `.`/`x` characters (one
  `s` skip, several expected `x` xfails) — no `F` or `E` anywhere, and the run proceeds straight
  from `[100%]` into the warnings summary with no `FAILURES` section, which only appears on a red
  run. That is independent, re-derived evidence of a fully green suite, not a trusted count.
- **Diff scope (C10 / step 4c):** `git show --name-only 17d0d58` is exactly `src/autotester/doctor.py`,
  `tests/test_doctor.py`, `qa/manifests/at500-a-letter-suffixed-id-is-an-id.md`, and the unit's own
  `qa/evidence/at500-a-letter-suffixed-id-is-an-id/*` — a byte-for-byte match with the manifest's
  "What changed". No unrelated file touched, nothing deleted. `6c8b3fa` (the tick stamp) touches
  only `qa/.last-tick`. Clean.

## Capability coverage — re-derived, not read off the table

All 5 rows independently reproduced via `mutation_check.py`, which applies each single-hunk edit,
confirms the named test(s) actually appear in the resulting failure list, and reverts. This
directly answers the brief's "half-widening" concern: mutations 3, 4 and 5 each revert exactly
ONE of the three call sites (`status_of`, `named`, `claimed`) in isolation, and each still kills —
proving no one call site is silently covering for another. Mutation 2 (suffix made mandatory)
correctly kills the plain-id tests, proving the fix doesn't accidentally exclude un-suffixed ids.

## The real-repo falsification — reproduced, with one discrepancy found

Regenerated `doctor_before.py` myself (`git show a0155f2:src/autotester/doctor.py`, not committed,
matches the manifest's instruction) and re-ran both probes independently, over a temp copy
(nothing in the working tree touched, no stash/checkout):

- `probe_before.py`: **0 violations** naming `AT-298b` when its row is deleted — matches.
- `probe_after.py`, row intact: **0 violations** — matches (no false positive).
- `probe_after.py`, row deleted: **3 violations** at first re-run, not the 2 the manifest's own
  `real-repo-probe.out` records. The third: `qa/manifests/at500-a-letter-suffixed-id-is-an-id.md`
  itself — its own prose (line 25) reads `` on manifest `**Issues addressed:**` lines:  AT-298b ``,
  which contains the literal marker substring inside backticks while merely *describing* the bug.
  `check_qa_issue_rows`'s `named` extraction tests `if marker in line` (bare substring, unchanged
  by this unit), so it treats that descriptive line as a real claim line and extracts `AT-298b`
  from it.
  **Corrected after a second, coordinator-prompted re-check that I reproduced myself before
  accepting it: the count compounds.** Once this checker's own first verdict draft existed on
  disk (quoting the same marker line to explain the finding), re-running the identical probe gave
  **4**, not 3 — the verdict itself became a fourth "source". Nothing here is a fluke of run
  order: it is a pre-existing imprecision in the marker-line test (`if marker in line` is a bare
  substring check, unrelated to this unit's regex change), and it is **self-reinforcing** — every
  future document that discusses this bug by quoting the marker, including a verdict that files
  it, adds one more phantom attribution, with no upper bound. Raised from low to **medium** in
  **AT-504** on that basis: it doesn't fail today (see below) but it degrades the precision of the
  exact guard AT-500/AT-496 exist to provide, and the triggering population can only grow.
  Not a reason to fail this unit, because: (a) it doesn't touch any of the 5 declared capabilities
  or the C10 criterion this unit is judged against — it lives in the pre-existing, unchanged
  `if marker in line` test, not in `ISSUE_ID` or its three call sites; (b) on the real, undeleted
  ledger it stays inert — re-confirmed **0 violations** with `AT-298b`'s row present and
  `doctor: clean`, because `named - set(status_of)` already excludes an id that has a real row;
  (c) its failure direction is an extra, still-correctly-directed "lost" citation (never a missed
  loss, never a false "fixed"), so it cannot mask the exact class of bug AT-500 exists to catch —
  it only adds noise around a real, correctly-detected loss.

## Known-limits disclosure — spot-checked

- "`AT-466a/b`, `AT-480a/b` ... `AT-294b`, `AT-295b` appear in `qa/` prose with no ledger row, none
  on a marker line" — verified true for all four of these: their manifests'
  `**Issues addressed:**` lines cite the plain (unsuffixed) ids only; the suffixed forms appear
  only in body prose/tables.
- "`AT-290a/b`" in that same list does **not** actually check out: that literal string does not
  appear anywhere in `qa/` prose. The only place `AT-290` combines with a `a`/`b` suffix idea is a
  `note` field on the ledger's own `AT-293` row, proposing `AT-290a / AT-290b` as a *hypothetical*
  naming convention that was explicitly **not adopted** (the checker ruling on that row chose a
  `checker` discriminator field instead, and reserved the `b`-suffix convention for *future*
  dual-check ids going forward, which is where `AT-297b`/`298b`/`299b` come from). Minor
  documentation inaccuracy in the manifest's own self-check, not a functional issue — noted here,
  not filed as a ledger row, since it isn't a code defect.
- The adapter's-own-verify-command limitation is real (confirmed independently: `-q` +
  `pyproject.toml`'s `addopts = "-q"` → `-qq`, no summary line) and is filed as **AT-503** (low),
  by me per the manifest's own request and the AT-499 ledger-single-writer precedent.
- `claimed`'s dropped trailing `\b`: confirmed harmless — `\s*\(` immediately after the (greedy)
  optional-letter group already forces a non-word character next, so no additional match becomes
  possible relative to the old anchored form.

## Issues ledger

- **AT-500** closed `open → fixed`, `fixed_by` citing commit `17d0d58` and this verdict.
- **AT-503** opened (low) — adapter verify command unreadable (`-qq`), disclosed by the manifest,
  filed by me.
- **AT-504** opened (**medium**, raised from an initial low after independently reproducing that
  the count compounds — see above) — `named`'s substring marker-test admits prose that merely
  quotes the marker; found independently during falsification re-run, not disclosed by the
  manifest.

## Live browser

Not UI-touching. Changed paths are `src/autotester/doctor.py`, `tests/test_doctor.py`, and the
unit's own manifest/evidence — no rendered surface changed. Mode D correctly not run.

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (C10), 5/5 capabilities reproduced, 5/5 mutations killed
FAILURES (if any):
- none at >80% confidence against this unit's own criteria/capabilities
CAPABILITY-COVERAGE: 5/5 rows reproduced (mutation_check.py, isolated single-hunk edits, kill-attribution confirmed)
LIVE-BROWSER: not-applicable (changed paths: src/autotester/doctor.py, tests/test_doctor.py, qa/manifests/…, qa/evidence/…)
ISSUES-WRITTEN: AT-500 (closed fixed), AT-503 (new, low), AT-504 (new, medium)
EXPLANATION: The ISSUE_ID widening is correct and independently proven — all 5 falsifying edits
reproduce, the three call sites are cross-immune (no one covers for another), plain ids stay
plain, and the live suffixed rows (AT-297b/298b/299b) produce no new doctor noise. One real
discrepancy surfaced during independent re-verification, then got worse on a second check: the
manifest's flagship real-repo falsification claims 2 violations on row-deletion; it reproduced as
3 once the at500 manifest itself existed (its own bug-description prose trips the check's
separate, pre-existing "marker substring anywhere in the line" imprecision), then as 4 once this
checker's own verdict draft existed too, because it quotes the same marker line. The mechanism
compounds without bound as more qa/ artifacts discuss the bug by name — raised to AT-504 (medium,
not the low I first filed) for that reason, though it stays inert on the real, undeleted ledger
today (0 violations, doctor: clean, reconfirmed) and is not caused by this unit's regex change. A
second, unrelated minor inaccuracy: the manifest's Known-limits list includes "AT-290a/b" as
prose-mentioned-but-unfiled, which doesn't hold up on inspection (only a hypothetical, unadopted
note exists) — documentation nit, not a functional gap. Neither affects the unit's own criterion
or capability claims, so PASS stands.
```
