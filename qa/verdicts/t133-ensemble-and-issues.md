# Verdict — t133-ensemble-and-issues

**Unit:** T-133 — Track A4: two-model ensemble + deterministic adjudication + Issue derivation + the 13-column Excel
**Contract:** `qa/contracts/video-learning.md` (VL2, VL2b, VL3, VL4, VL5, VL6; I-VL5, I-VL6)
**Cycle checked: 2**
**Date:** 2026-09-09
**Checker:** fresh Mode A subagent, bound to `D:/autoTesting`. Adapter: `qa/adapter.json` (coding).
**Replaces** the cycle-1 verdict (FAIL, 3/6), which stays readable in git at `847bb28`.

---

## VERDICT: PASS

**SCOREBOARD: 6/6 criteria met, 2/2 invariants hold**

All three cycle-1 failures (VL4, VL3, VL2b) are closed by measurement, not by claim. All nine
issues AT-197..AT-205 were re-verified independently and moved `fixed → verified`. Three new
issues filed, none of them a criterion failure: **AT-207** (medium), **AT-208** (medium),
**AT-209** (low).

---

## What I re-ran (my own output; no pasted result was trusted)

| Command | My result |
|---|---|
| `uv run pytest` (bare — `addopts = "-q"` already set) | **exit 0 — 804 passed, 2 skipped**, 0 `FAILED` lines. Matches the manifest exactly. |
| `uv run ruff check src tests scripts` | exit 0 — "All checks passed!" |
| `uv run autotester doctor` | exit 0 — "doctor: clean" |
| `done_check` (the five test files, widened this cycle) | exit 0, **59 passed** — matches the manifest's 59 |
| `uv run pytest -rs` | the 2 skips are `tests/test_db.py:93` (live Mongo, opt-in) and `tests/test_ui.py:163` (POSIX bits). **`test_the_header_matches_the_real_human_sheet` is NOT among them** — the corpus is present on this host and VL6's real-workbook test actually executed. |

## The split — nothing dropped, nothing weakened

Compared `git show 847bb28:tests/test_adjudicate.py` and `:tests/test_analyze_video.py` (17 + 12 =
**29** test functions) against the four post-split files (**35**). Every one of the 29 is present.
The single rename is `test_a_field_only_one_model_noticed_survives_the_merge` →
`test_every_descriptive_list_only_one_model_noticed_survives_the_merge`, and it is a
**strengthening**: it now asserts on `signals`, `fields`, `ui_elements` and `url` where before it
asserted on `signals` and `url` only (that was AT-202's hiding place). Six tests are new. Shared
fakes live once in `tests/video_fakes.py`; `obs()` gained a `prompt` parameter and the two importers
use the one definition. **No test was silently dropped and none was weakened.**

## Sabotage — 8 sabotages, isolated `git archive HEAD` extract, `PYTHONPATH` pinned

Per C7 and AT-101: nothing was stashed, checked out or restored in the live tree. Extract at
`%TEMP%/sb133c2`, run with `PYTHONPATH=<extract>/src` against the repo venv's interpreter. **Every
anchor was asserted to match exactly once and the file re-read as changed before the run**; the file
was restored byte-for-byte after each. Baseline in the extract: **0 failures**.

```
CA sort key drops prompt_name              anchor=1 changed=1  FAILED=1
     test_adjudicate_determinism.py::test_order_still_does_not_matter_with_TWO_prompts_per_chunk
CB cache ignores prompt_sha256             anchor=1 changed=1  FAILED=1
     test_analyze_cache.py::test_editing_a_prompt_invalidates_its_cached_answers
CC list_observations stops skipping        anchor=1 changed=1  FAILED=1
     test_analyze_cache.py::test_a_half_written_observation_heals_instead_of_blocking
CD cache read before the force test        anchor=1 changed=1  FAILED=0   -> INCONCLUSIVE (AT-209)
CE _merge_lists drops `fields`             anchor=1 changed=1  FAILED=1
     test_adjudicate.py::test_every_descriptive_list_only_one_model_noticed_survives_the_merge
CF at_mmss renders a negative              anchor=1 changed=1  FAILED=1
     test_issues.py::test_a_negative_second_is_refused_not_rendered
CG duplicate provider labels allowed       anchor=1 changed=1  FAILED=1
     test_analyze_video.py::test_two_providers_under_one_label_are_refused
CH coverage counters made vacuous          anchor=1 changed=1  FAILED=2
     test_adjudicate_determinism.py::test_a_partial_reading_says_how_partial_it_is
     test_analyze_cache.py::test_the_analysis_records_how_many_calls_it_is_missing
```

**CD is reported INCONCLUSIVE, not as a vacuous guard.** Reverting only the *ordering* — putting
`_cached()` back above the `force` test — fails nothing, because `skip_unreadable=True` now means
the read cannot raise, so the two orderings are behaviourally identical. The ordering is the right
shape and the manifest's description of it is true; the finding is that AT-199's crash-safety is
carried by **one** mechanism rather than two, and a future change that reintroduces a raise inside
`_cached` would re-block `--force` with no test noticing. Filed AT-209 (low), with the exact test
that would close it — I ran that test by hand and it passes.

---

## Criterion by criterion

### VL4 — adjudication is a function of content alone · **MET** (was a cycle-1 FAIL)

The sort key is now `(offset_s, provider_label, prompt_name, chunk_index)` — total over exactly the
tuple the cache is keyed on. Measured three ways:

- **The cycle-1 attack, re-run:** two observations differing only in `prompt_name` (one carrying
  screens/`purpose`, the other an issue and a different summary) → **1 distinct output** across both
  permutations, where cycle 1 measured 2, differing in `screens`, `journey`, `issues` and `summary`.
- **500 shuffles of the real shipped shape** — 2 models × 2 prompts × 3 chunks, each observation
  carrying a distinct `purpose`, `url`, summary and issue so that every first-seen-wins merge has
  something to disagree about: **0 mismatches**.
- **Sabotage CA** reverts the key and fails exactly the new two-prompt test. The property now rests
  on a test a single-prompt fixture cannot pass by accident, and `obs()`'s own docstring records why
  the parameter exists.

**I pressed for a second tie, as asked, and this is the honest answer.** One residual tie exists:
two observations sharing `(offset_s, provider_label, prompt_name, chunk_index)` but differing in
content still permute to 2 distinct outputs (measured). It is **not reachable from the shipped
system** — `core/paths.source_observation()` names the cache file from exactly that tuple and
`save_observation` overwrites it, so the store can hold at most one answer per key; a prompt edit
rewrites the same path rather than adding a second file (verified: 12 files before a `--force`
re-run, the same 12 names after). The key is therefore total over everything the producer can
produce. Recorded as a question, not a failure.

I also swept every other `sorted()` / `.sort()` under `src/` (31 sites). `join_screens` keys on
`(t_start, screen_key)` — two entries tying there necessarily share a key and an overlapping
interval and so would already have merged. `join_issues` keys on `(t_start, issue_key)` — the same
argument through `SEAM_WINDOW_S`; I additionally confirmed its greedy chaining is stable by
permuting three issues 8 s apart on one screen and category (**1** distinct output across three
permutations). `stages/issues.py:133` keys the workbook rows on `(recording_label, at_s)`, which
*can* tie, but its input list is already deterministically ordered by `adjudicate`, so the written
sheet is deterministic. **No non-total key with a reachable tie remains.**

### VL3 — failure is partial, and an analysis says what it is made of · **MET** (was a cycle-1 FAIL)

`VideoAnalysis` carries `observations_used` / `observations_expected`, and `analyze` computes
expected as `len(providers) * len(PROMPT_NAMES) * len(prep.chunks)`. Verified **end to end on disk**,
not on the field's existence: a run over 3 chunks × 2 prompts × 2 models in which one provider was
dead and the other died after its first call persists `"observations_used": 1,
"observations_expected": 12` into the analysis JSON, with `is_complete` False. Total failure still
raises `NoObservations` and writes no analysis (confirmed: the analysis path does not exist).
Sabotage CH fails 2. **Two numbers rather than a boolean** is the right call, and the manifest's
reasoning for it is sound.

Two things I checked and am **filing rather than scoring**, because VL3's letter — "in a field, not
in a log line" — is met, and the cycle-1 verdict's own fix direction said the field alone discharges
the criterion:

- **AT-207 (medium): the numbers reach no reader.** A repo-wide grep finds four sites — the two
  fields, the property, and the one producer at `adjudicate.py:208-209` — and the only consumers
  anywhere are two tests. No CLI command prints the ratio, the 13-column export has no channel for
  it (correctly — the sheet's shape is the tester's), and `ui/` never mentions it. `is_complete` is
  a `@property`, so it is not even serialised: I confirmed `is_complete` is absent from the
  persisted JSON's keys, and a downstream reader must recompute it. A human who does not open the
  JSON still cannot tell a full reading from a fragment. That is VL3's stated *purpose*, unrealised
  — but it is downstream work (T-136 is the first unit that computes a number against this
  artifact), and hardening a criterion at the moment of a passing verdict is the mirror image of
  softening one at the moment of a failing verdict. Filed with the fix direction instead.
- **AT-208 (medium): `expected=None` defaults to `len(shifted)`.** Any caller other than `analyze`
  gets `used == expected` and `is_complete is True` — a default-value fallback inside the very field
  added to stop one. Latent (`analyze` always passes the real product), reachable by the stated next
  consumer (T-136 re-adjudicating cached observations). One line: make it required, or default to 0,
  which `is_complete` already reads correctly as "nobody told me what was intended".

### VL2b — the cache's promise is SAFE, not merely cheap · **MET** (was a cycle-1 FAIL)

Both halves re-derived by execution, not by reading the diff:

- **A damaged entry degrades to a re-request.** After a clean 12-observation run I overwrote one
  cache file with `{ this is not json` and called `analyze(force=True)` — it **completed, 12 calls**,
  where cycle 1 measured a `ValueError` out of `analyze` that `--force` could not clear. Then I wrote
  a second file as valid-JSON-wrong-shape (`{"schema_version":1}`) and called `analyze` **without**
  force: it completed with exactly **1** re-request — the damaged entry alone, the other eleven still
  free hits — and I read the file back to confirm it had been rewritten with a `prompt_sha256`.
  Skipped means re-requested and overwritten, never treated as an answer. Sabotage CC fails 1.
- **A cached answer is reusable only while the question is unchanged.** `observe_chunk` builds the
  prompt and its sha256 *before* the cache is consulted, and `_cached` matches on `prompt_sha256`.
  Sabotage CB (drop the digest from the comparison) fails exactly
  `test_editing_a_prompt_invalidates_its_cached_answers`.

### VL2 — a cached observation is never re-requested · **MET** (re-verified, not carried over)

12 provider calls on a first run over 3 chunks × 2 prompts × 2 models, **0 on the second**.
`--force` re-spends all 12 and leaves **the same 12 filenames** — overwrite in place, not an append
log. Adding a model costs only the model. The digest in the key did not weaken the hit rate: the
second run's zero calls is the proof that an unedited prompt is still a free hit.

### VL5 — offsets in code, narration sliced · **MET**

Unchanged this cycle and re-checked: `shift` deep-copies before mutating, offsets are applied by the
stage, `build_chunk_prompt` slices the transcript to the chunk, and a silent section says so rather
than leaving a gap. The prompt still forbids the model from adding its own offset in as many words.

### VL6 — the exported sheet is the human sheet's shape, verified against the file · **MET**

`test_the_header_matches_the_real_human_sheet` executed (it is not in the skip list) against
`ERP_Issues_ALL.xlsx` on this host, and `test_the_At_CELL_carries_MM_SS_not_a_number` judges the
written workbook rather than the helper. Sabotage CF (remove `at_mmss`'s negative guard) fails the
new refusal test: `at_mmss(-5.0)` now raises instead of rendering `-1:55`.

### I-VL5 — a merge never softens a severity · **HOLDS**

`worst()` unchanged and correct; agreement raises `confidence` and never `severity`.

### I-VL6 — nothing in the analysis half asks a model to decide a merge · **HOLDS**

`adjudicate.py`, `issues.py` and the export contain no provider call of any kind. The new
`DuplicateProviders` guard is a refusal in `analyze`, not a merge decision.

---

## The five smaller issues, each re-verified

| Issue | How I verified it | Result |
|---|---|---|
| AT-201 docstring claim | Read `stages/issues.py:10-21`. The present-tense "The scorer accommodates both" is gone; it now says **"No scorer exists yet — it is T-136"** and keeps the measured 12-vs-13-column facts. | closed |
| AT-202 `fields` | Sabotage CE fails 1; the test is renamed for what it does and asserts on each list. | closed |
| AT-203 `confidence` | Read `prompts/video_issues_v1.md:41-46`. The field is documented **with a rule tied to evidence** — high when there is nothing to interpret, low when reading intent into a half-sentence — plus "Say `low` freely" and a note that the system may raise it on agreement. A better answer than the one I asked for. | closed |
| AT-204 duplicate labels | Ran it: two providers labelled `dup` raise `DuplicateProviders` naming the collision. Sabotage CG fails 1. | closed |
| AT-205 negative second | Ran it: `at_mmss(-5.0)` raises `ValueError`. Sabotage CF fails 1. | closed |

## Ledger

`AT-197 … AT-205` moved **`fixed → verified`** (`verified_date: 2026-09-09`), each with the
measurement above recorded on the row — a `fixed` flag is the maker's word and none was taken on it.
New: **AT-207** (medium, coverage numbers reach no reader), **AT-208** (medium, `expected=None`
self-declares complete), **AT-209** (low, force-before-read ordering unevidenced — CD's
INCONCLUSIVE). The manifest's `Issues addressed` claims exactly AT-197..AT-205, and that claim is
accurate. AT-192, AT-193 and AT-196 remain correctly open and untouched.

## Contract action

**No criterion changed, and none was softened.** VL3 was deliberately NOT tightened to swallow
AT-207. A routine amendment-log entry records the cycle-2 measurements (the residual unreachable
tie, the single-mechanism crash safety, the unread coverage numbers) so the next reader does not
re-derive them.

## Goal task

**T-133 closes on this PASS.** `user_value: high`, so a `docs/FEATURES.jsonl` row is due with a
prefilled reason for Umesh to confirm or edit — that is the maker's close-out step, not mine.

---

## Returned block

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met, 2/2 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-207 (medium), AT-208 (medium), AT-209 (low)
EXPLANATION: All three cycle-1 failures are closed by my own measurement: 500 shuffles of the real
two-model x two-prompt x three-chunk shape give 0 mismatches and the cycle-1 tie attack now yields
one output (VL4); a crippled run persists observations_used=1 / observations_expected=12 on disk
(VL3); and analyze(force=True) over a deliberately corrupted cache completes with 12 calls where it
previously raised, while a wrong-shaped entry is re-requested and rewritten alone (VL2b). Eight
sabotages, each anchor-matched-once and file-verified-changed in an isolated git-archive extract,
discriminate seven of the eight guards; CD (force-before-read ordering) fails 0 and is reported
INCONCLUSIVE, not vacuous -- skip_unreadable now carries that promise single-handed, filed AT-209.
The test split dropped nothing (all 29 prior tests present, one renamed and strengthened). Two
residual weaknesses are filed rather than scored: the coverage numbers reach no reader outside two
tests, and adjudicate's expected=None default makes any caller but analyze declare itself complete.
```
