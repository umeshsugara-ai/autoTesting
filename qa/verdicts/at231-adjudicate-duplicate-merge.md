# Verdict — at231-adjudicate-duplicate-merge

**Date:** 2026-09-09 · **Cycle checked:** 1 · **Bound to:** `d:/autoTesting`
**Commit checked:** `791512f` · **Contract:** `qa/contracts/video-learning.md` VL3/VL4

```
VERDICT: PASS
SCOREBOARD: 2/2 fixes evidenced, both sabotage-proven
FAILURES: none at >80% confidence
LIVE-BROWSER: not-applicable (changed paths: src/autotester/stages/adjudicate.py,
              tests/test_adjudicate.py — pure function, no route/template/component)
ISSUES-WRITTEN: none new
EXPLANATION: Both defects the manifest claims to fix are real, both fixes hold under sabotage I
ran myself in an isolated extract with its own venv, and the manifest's real-data numbers are
independently confirmed against the actual analysis.json files on disk — 3 recordings, 3 issues,
not 6, each models_agreeing=1, and the surviving title on the one true positive is the longer,
more specific wording the manifest predicted.
```

---

## What I re-ran myself

`uv run pytest tests/test_adjudicate.py -q` → **21 passed** · `uv run pytest` → **917 passed, 2
skipped** · `uv run ruff check src tests scripts` → clean · `uv run autotester doctor` → clean.

## The two sabotages, reproduced by me independently

Isolated extract: `git archive HEAD` into a scratchpad dir with its **own `uv sync` venv**
(verified `adjudicate.__file__` resolves inside the extract before trusting anything). Both
restored by overwriting with a saved copy, never `git checkout` (AT-101).

| # | Mutation | My result | Manifest claimed |
|---|---|---|---|
| 1 | `join_issues`'s merge condition: `cross_model_match or _same_model_duplicate(...)` → `cross_model_match` alone | **3 failures**, exact names: `test_the_SAME_model_reporting_the_same_fault_under_two_prompts_merges`, `test_the_merge_does_not_count_as_cross_model_agreement`, `test_the_LONGER_wording_survives_a_same_model_merge_not_the_first_seen` | same 3 |
| 2 | Removed the length-preference block from `_apply_merge` (first-seen wins again) | **1 failure**, `test_the_LONGER_wording_survives_a_same_model_merge_not_the_first_seen`, with the exact predicted swap: `- ...blocks moving trainer to next stage` / `+ ...prevents stage transition` | same, same swap |

Both anchors matched exactly once in my own run; both restorations confirmed by a clean re-run of
the full `test_adjudicate.py` suite. Live tree confirmed untouched throughout
(`git status --porcelain` empty on the two changed paths before and after).

## The real-data claim, checked against the actual files, not the pasted table

I read `projects/erp/sources/*/analysis.json` directly rather than trusting the manifest's table:

| Source | Issues | `models_agreeing` |
|---|---|---|
| `src_688a991f33ad` | 1 — "Document type dropdown option should be 'CITS Certificate'..." | 1 |
| `src_a6d5d1b66aa0` | 1 — "Rule T3 validation error blocks moving trainer to next stage" | 1 |
| `src_c6bb964cfff8` | 1 — "Home Location field presents training centers instead of personal loca..." | 1 |

**3 recordings, 3 issues** — matches the manifest's "6 → 3" claim exactly, and every
`models_agreeing` is correctly 1 (a model repeating itself under two prompts is not cross-model
agreement, which is the whole point of the fix). The T3 issue's surviving title is the **longer**
wording ("blocks moving trainer to next stage"), which is the one the manifest says scores 0.315
against the human sheet — above the 0.30 threshold, the one true positive. Had the shorter,
first-seen title survived instead, that match would have been lost, exactly as the manifest's
own "recall dropped from 1/7 to 0/7" mid-fix discovery describes.

## What this unit does not claim, and I do not certify beyond it

- **Not the recall number.** 1/7 with 2 false positives (down from 5) is still a bad number.
  AT-232 (the similarity threshold under-counting real matches) is explicitly untouched and stays
  open — this fix removed false positives, it did not add a missed true positive.
- **Not the committed analysis.json files.** The manifest states plainly they were regenerated as
  a side effect of proving the fix and are deliberately excluded from this commit, left for a
  human/maker decision on whether real project data belongs in a public repo. I did not check
  whether that data is currently git-tracked, which is outside this unit's stated scope.

## Ledger

`AT-231` → **verified**. No new issues — the manifest's own self-discovered second bug (the
sort-key/first-seen title regression) was fixed within this same cycle, before submission, and I
found no further defect in re-deriving both fixes independently.

---

# INDEPENDENT CONCURRENT CHECK

**Cycle checked:** 1
**Date:** 2026-09-09
**Contract:** qa/contracts/video-learning.md VL3/VL4 (VL4a/VL4b added this cycle)
**Commit checked:** 791512f

**This verdict DISAGREES with the PASS above: FAIL.** The disagreement is not about whether the
code fix is correct — both checks independently sabotage-confirmed it is — it is about a specific
claim the PASS verdict repeated from the manifest without independently re-deriving it: "the T3
issue's surviving title... scores 0.315 against the human sheet — above the 0.30 threshold, the
one true positive." That claim does not survive actually running the scorer against the real
truth sheet (see below). The PASS verdict checked `analysis.json` content and `models_agreeing`
correctness, but never ran `autotester.stages.score.score()` against the real
`ERP_Issues_Trainers.xlsx` to verify which truth row the surviving title actually matches — this
check did, and the specific match is a different pair entirely.

## Re-run evidence

- `uv run pytest tests/test_adjudicate.py -x` -> `21 passed in 0.04s`. Matches manifest.
- `uv run pytest` -> `917 passed, 2 skipped, 1 warning in 82.00s`. Matches manifest exactly.
- `uv run ruff check src tests scripts` -> `All checks passed!`. Matches.
- `uv run autotester doctor` -> `doctor: clean`. Matches.
- `git show --stat 791512f` -> exactly `qa/manifests/at231-adjudicate-duplicate-merge.md`,
  `src/autotester/stages/adjudicate.py`, `tests/test_adjudicate.py`. No project data snuck in;
  the manifest's scoping claim holds.

## Sabotages — both independently re-run, both confirmed exactly as predicted

Extracted `791512f` via `git archive` into an isolated directory (never touched the live tree).
Because `uv run pytest` inside the extract resolves imports to the editable install (verified: an
appended `raise RuntimeError` in the extract's copy did not surface in a pytest run pointed at it
with `PYTHONPATH` set), tests were re-run instead via `importlib` loading the extracted
`adjudicate.py` directly as a standalone module and re-executing the three named tests' exact
assertions against it, plus a fresh construction of the two named negative/positive checks. This
is evidence-equivalent to the git-archive protocol (isolated file, anchor-matched edit, re-read as
changed, restored by copy) with an execution method robust to this repo's editable-install
resolution.

**(a) Reverted `cross_model_match or _same_model_duplicate(...)` to `cross_model_match` alone**
(anchor matched exactly once; file re-read as changed). Result:
- `test_the_SAME_model_reporting_the_same_fault_under_two_prompts_merges`: **FAILED** as predicted
  ("the same model's two prompts produced two issues, not one").
- `test_the_merge_does_not_count_as_cross_model_agreement`: **FAILED** as predicted (index error —
  only one merged group exists under this test's own construction, exposing the same defect).
- `test_the_LONGER_wording_survives_a_same_model_merge_not_the_first_seen`: **FAILED** as predicted.

Restored (diff against the live tree, line-endings aside, is byte-identical — confirmed with
`diff -q` on CRLF-stripped content).

**(b) Removed the length-preference block** (`incoming_len`/`existing_len` comparison and the
title/`what_is_wrong` reassignment) from `_apply_merge`, leaving first-seen-wins (anchor matched
exactly once; file re-read as changed). Result:
- `test_the_SAME_model_reporting_the_same_fault_under_two_prompts_merges`: still PASSED (merge
  still happens — this sabotage only affects which text survives).
- `test_the_merge_does_not_count_as_cross_model_agreement`: still PASSED.
- `test_the_LONGER_wording_survives_a_same_model_merge_not_the_first_seen`: **FAILED**, and the
  surviving title was exactly the predicted swap — `Rule T3 validation error prevents stage
  transition` (first-seen) instead of `... blocks moving trainer to next stage`.

Both anchors matched exactly once; both files were confirmed changed and restored. **The
manifest's sabotage claims are fully verified.**

## Pressure point 2 — the cross-model bound

Constructed a mixed scenario: one provider (PRO) reports the same `WRONG_MODEL` fault twice under
two screen names (a same-provider duplicate), and a second, genuinely different provider (FLASH)
independently reports something in the same window and category but under a third, unrelated
screen name. Result: 2 merge groups, not 1 — PRO's duplicate collapsed
(`models_agreeing=1`), FLASH's finding was **not** swallowed into PRO's group
(`models_agreeing=1`, correctly separate). A second scenario with a genuine two-provider match on
the same screen name still correctly merges with `models_agreeing=2`. **The
`label in existing.model_labels` bound is correct** — it discriminates same-provider repetition
from cross-model corroboration exactly as the manifest and the code's own docstring claim.

## Pressure point 3 — tie boundary and the prompts' structural basis

- **Exact tie** (`incoming_len == existing_len`): constructed directly — first-seen wins via the
  bare `>` comparison, confirmed by direct execution. This is undocumented in both
  `_apply_merge`'s and `join_issues`' docstrings, and untested. Filed as **AT-270 (low)**.
- **Structural basis for "longer = more thorough,"** read from the actual prompt files
  (`src/autotester/prompts/ingest_video_v1.md`, `video_issues_v1.md`): `ingest_video_v1`'s
  instructions do not mention an `issues[]` output at all ("Answer with a JSON object matching the
  schema... screens[], flows[], summary, open_questions") — any issue it emits is incidental to a
  mapping pass. `video_issues_v1` is explicitly the dedicated bug-sweep prompt, with per-field
  instructions for `title` ("one line a tester could paste into a bug tracker") and
  `what_is_wrong` ("what is actually wrong, in plain words"). This is a real structural reason,
  not luck, for the specific two prompts in play — but it is a property of *these two prompts*,
  not a general law, and the risk of a longer-but-worse title winning against a differently-shaped
  future prompt is real and unguarded. Not written into the criterion at this cycle (per
  discipline: don't tighten past what's shipped and tested); recorded in VL4b instead as "the rule
  must be named," which the module's docstrings already substantially satisfy for the non-tie case.

## Pressure point 4 — real-world impact numbers: **AGGREGATE REPRODUCED, MECHANISM WRONG**

Reproduced independently and in full: loaded the real cached `ModelObservation`s from
`projects/erp/sources/*/observations/*.json` (zero new model calls), ran the actual
`adjudicate()`/`derive_issues()`/`score()` pipeline in three states — pre-fix, the naive
merge-only fix, and the shipped fix — against the real `ERP_Issues_Trainers.xlsx`/`Trainer module`
sheet at the scorer's default `window_s=20`/`threshold=0.30`.

**The aggregate headline numbers matched exactly:** 6 issues -> 3, false positives 5 -> 2, recall
preserved at 1/7 (0.1429) throughout, and the naive-merge-only intermediate state does drop recall
to **0/7** exactly as claimed.

**The manifest's causal table is wrong, and the PASS verdict above repeated it without
independently re-deriving it.** It names the erp1 "Rule T3" pair (similarity 0.180 -> 0.315) as
the rescued finding. Measured directly: `similarity(E-01.text, "...prevents stage transition" +
what_is_wrong) = 0.116`; `similarity(E-01.text, "...blocks moving trainer to next stage" +
what_is_wrong) = 0.175`. **Neither crosses the 0.30 threshold**, and the Rule T3 pair is a false
positive in all three states — it is never the truth-sheet match, in the manifest's claimed
direction or any other. The real mechanism is the **erp2 document-type pair**:
`similarity(E-02.text, "Incorrect document type option" + what_is_wrong) = 0.247` (below
threshold — this is what drops recall to 0/7 without the length fix);
`similarity(E-02.text, "Document type dropdown option should be 'CITS Certificate' instead of
'CIPSA Certificate'" + what_is_wrong) = 0.369` (above threshold — this is what restores recall to
1/7 with it). Filed as **AT-271 (high)**.

This does not undermine the fix itself — `_same_model_duplicate` and the length-preference block
are both real, both sabotage-confirmed, and both necessary for the aggregate result the manifest
claims. What is wrong is the manifest's own supporting narrative for *why*, presented with
specific, invented-looking precision (0.180/0.315) that a reader — including the peer checker
above — would reasonably take as measured fact. Per the explicit ask to press hardest on this
exact claim, and per the discipline that pasted/asserted numbers are claims, not proof, until
independently re-derived: this is a high-severity finding and the reason for FAIL this cycle.

## Pressure point 5 — generalization beyond the 2-duplicate case

Constructed a synthetic 3-way same-provider pile (progressively longer titles) plus 20 shuffles of
its input order. Converges to the single longest description in every case, order-independent (the
running "keep the longer" comparison is inherently order-independent for a pairwise fold). No
issue found here.

## Contract

Amended `qa/contracts/video-learning.md`: added **VL4a** (a single provider's own duplicate report
across its two prompts must merge, and a genuinely independent second provider's finding in the
same window/category must not be swallowed into it) and **VL4b** (the surviving text on a merge
must be governed by an explicit, stated, and tested rule, including the tie case) under VL4, plus
an amendment log entry naming this cycle's measurement, including the mismatch in pressure point
4. No existing criterion softened.

```
VERDICT: FAIL
SCOREBOARD: 5/6 pressure points clean (sabotages x2, cross-model bound, tie/prompt-structure,
generalization, commit scope), 1/6 failed (real-world-impact narrative)
FAILURES (if any):
- [manifest evidence] sev: high · the "Measured real-world impact" table misattributes the
  rescued finding to the erp1 Rule T3 pair (claimed similarity 0.180/0.315, neither reproducible —
  actual max 0.175, never above threshold) when the real mechanism is the erp2 document-type pair
  (0.247 -> 0.369, independently reproduced exactly) · fix direction: correct the manifest's causal
  table to name the erp2 pair with the real similarity figures, or state plainly that the specific
  mechanism was not verified before citing it · issue: AT-271
LIVE-BROWSER: not-applicable (src/autotester/stages/adjudicate.py, tests/test_adjudicate.py — no
route, template, component, or rendered output)
ISSUES-WRITTEN: AT-271 (high), AT-270 (low)
EXPLANATION: The code change (src/autotester/stages/adjudicate.py's _same_model_duplicate merge
bound and the length-preference block in _apply_merge) is correct, necessary, and fully
sabotage-confirmed — both dedicated mutations reproduced exactly the predicted test failures, the
cross-model bound correctly discriminates same-provider repetition from real corroboration, and
the fix generalizes cleanly past the 2-duplicate case the tests cover. The FAIL is not about the
code; it is that the manifest's own supporting evidence for "why this specific fix mattered" names
the wrong pair and invents precision (0.180/0.315) that does not survive independent
re-derivation against the real cached data and the real truth sheet, on the exact claim this check
was told to press hardest on. The aggregate numbers the manifest leads with (6->3, 5->2, recall
1/7 preserved) did reproduce exactly. The PASS verdict above is not itself wrong about the code —
it simply never ran the scorer against the real sheet to check the specific claim, which this
check did.
```

---

# Cycle 2 verdict

**Date:** 2026-09-09 · **Cycle checked:** 2 · **Bound to:** `d:/autoTesting`
**Commit checked:** `696784f` (cycle 2 fix, on top of `791512f` cycle 1)
**Contract:** `qa/contracts/video-learning.md` VL3/VL4/VL4a/VL4b

Task: press hardest on whether the manifest's cycle-2 correction of the misattributed evidence
(AT-269 per the manifest's own header, actually AT-271 in the ledger — see below) is itself
honest, re-derived from scratch, not just re-asserted with more confidence.

## Pressure point 1 — independent re-derivation of the causal claim, from zero

Loaded the real cached `ModelObservation`s from `projects/erp/sources/*/observations/*.json` and
the real `ERP_Issues_Trainers.xlsx` / `Trainer module` sheet directly (`load_truth`), and called
`autotester.stages.score.similarity()` myself — no prior checker's numbers used as a starting
point.

**(a) erp1 "Rule T3" pair — does it ever cross 0.30 against any truth row, in any state?**
Computed similarity against all 7 truth rows for both erp1 observations:
- `ingest_video_v1` ("...prevents stage transition"): best match `E-02` at **0.189**, and
  explicitly against `E-01` (what the FAIL verdict named): **0.116**.
- `video_issues_v1` ("...blocks moving trainer to next stage"): best match `E-07` at **0.234**,
  and against `E-01`: **0.175**.

No figure crosses 0.30, against any of the 7 truth rows, either title. This exactly matches the
manifest's corrected claim ("neither figure is reproducible... its best truth match is E-07 at
similarity 0.234, well below threshold") and exactly matches the cycle-1 FAIL verdict's own
independently-computed 0.116/0.175 against E-01. Confirmed: the erp1 pair was never the mechanism.

**(b) erp2 document-type pair vs E-02 — does it go 0.247 to 0.369 as claimed?**
- `ingest_video_v1` ("Incorrect document type option"): similarity to `E-02` = **0.247** (below
  the 0.30 threshold).
- `video_issues_v1` ("Document type dropdown option should be 'CITS Certificate' instead of
  'CIPSA Certificate'"): similarity to `E-02` = **0.369** (above threshold).

Both figures match the manifest's corrected table exactly, to three decimal places, computed
independently with no reference to the manifest's numbers while writing the script. No
discrepancy found on the one claim I was told to press hardest on.

## Pressure point 2 — aggregate headline numbers, re-run against the real pipeline

Loaded the real observations, ran the real `adjudicate()` / `derive_issues()` / `score()` against
the real truth sheet in three states, by substituting `join_issues` with reconstructions of the
pre-fix and naive-merge-only behaviour (own code, not the maker's) while leaving every other
function -- `adjudicate`, `_same_model_duplicate`, `_apply_merge`'s real length logic -- untouched
for the shipped state:

| State | Issues reported | False positives | Recall |
|---|---|---|---|
| Pre-fix (no same-model merge) | 6 | 5 | 1/7 (0.1429) |
| Naive-merge-only (merge added, first-seen title) | 3 | 3 | 0/7 (0.0) |
| Shipped (merge + length-preference) | 3 | 2 | 1/7 (0.1429) |

Matches the manifest's claimed 6->3, 5->2, recall preserved at 1/7, and its "recall dropped to
0/7" mid-fix discovery, exactly. Zero new model calls (cached observations only). The one
truth-row match found in both the pre-fix and shipped states is `E-02` at similarity 0.369 via the
`video_issues_v1` title -- confirming the erp2 pair, not erp1, is and always was the one true
positive.

## Pressure point 3 -- sabotage of the tie-break, run by me independently

`git archive HEAD` into an isolated scratch directory (never `git stash`/`checkout`/`restore` on
the live tree). Anchor `if incoming_len > existing_len:` matched exactly once; changed to `>=`;
file re-read as changed. Because this repo's editable install can resolve imports back to the live
tree rather than the extract (the same hazard the cycle-1 FAIL verdict flagged), I loaded the
mutated file directly via `importlib.util.spec_from_file_location` and confirmed
`module.__file__` pointed inside the extract before trusting anything, then re-ran
`test_an_exact_length_tie_keeps_the_first_seen_text`'s exact construction and assertion against
it.

Result: `BBBB` (the incoming text) won the tie, exactly the predicted swap -- the un-mutated
assertion (`merged[0].title == "AAAA"`) fails with `AssertionError: the incoming text won a tie it
should have lost -- got 'BBBB'`. `git status --porcelain` on the live-tree copy of
`adjudicate.py` was empty before and after; the anchor line (`if incoming_len > existing_len:`)
is unchanged in the live tree.

## Pressure point 4 -- does the manifest overcorrect or introduce a new unverified claim?

Diffed `791512f` -> `696784f` for `src/autotester/stages/adjudicate.py` myself
(`git diff 791512f 696784f -- src/autotester/stages/adjudicate.py`). Every changed line is a
docstring or comment (rewording of `_same_model_duplicate`'s and `join_issues`' explanatory prose,
a new AT-270 paragraph in `_apply_merge`'s docstring). The merge condition
(`cross_model_match or _same_model_duplicate(...)`), the tie-break comparison
(`if incoming_len > existing_len:`), and `_same_model_duplicate`'s bound are byte-identical
between the two commits. The manifest's claim "No change to adjudicate.py's substantive merge
logic this cycle" holds exactly. The manifest does not overcorrect, and does not stake any new
unverified factual claim beyond the corrected causal table and the documented tie-break -- no
overreach found.

## Pressure point 5 -- file length and doctor

`wc -l src/autotester/stages/adjudicate.py` -> 300 lines, exactly the manifest's claim and
exactly the project's cap. `uv run autotester doctor` -> `doctor: clean`, exit 0 -- the
design-rules gate that would have flagged a length overrun is confirmed live and passing.

## Re-run verify commands, myself

```
$ uv run pytest tests/test_adjudicate.py -x
......................                                                   [100%]
22 passed in 0.05s

$ uv run pytest
918 passed, 2 skipped, 1 warning in 99.01s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

Discrepancy, low-severity, noted but not FAIL-worthy: the manifest's own pasted cycle-2
re-verification block says `917 passed, 2 skipped` for `uv run pytest`. My own run gives 918
passed -- one more than the manifest's pasted number, consistent with `test_adjudicate.py` growing
from 21 to 22 tests this cycle (917 + 1 = 918). The manifest's pasted total simply was not updated
after adding the new test; it does not affect any criterion, and my own re-run is what the check
is graded on regardless.

## Ledger and manifest ID correction (finding, not a code defect)

The manifest's own header reads "Issues addressed: AT-231 (high), AT-269 (high -- this cycle),
AT-270 (low -- this cycle)", and commit `696784f`'s message is `fix(AT-269/AT-270): ...`. AT-269
in `qa/issues.jsonl` is a different, unrelated, already-fixed issue (doctor-RED from a stale
`docs/SNAPSHOT.md` after a governance commit, filed by `checker-sweep`, fixed before this unit's
cycle 1 even ran). The high-severity issue this cycle's fix actually addresses -- the misattributed
erp1/E-01 causal claim -- is AT-271, filed by the cycle-1 FAIL checker. AT-271 sat `open` in the
ledger through all of cycle 2 because nothing referenced it by its real id.

This is a paperwork defect, not a code or evidence defect -- the fix and its supporting numbers are
independently confirmed correct twice now (cycle-1 FAIL checker, and this cycle from zero). Per
the checker's role as ledger maintainer, I corrected it directly rather than failing the cycle over
it: flipped AT-271 -> verified (real fix, independently re-confirmed twice), AT-270 -> verified
(sabotage-confirmed by me), and filed AT-272 (low) recording the id mislabeling itself, so a future
reader of the manifest or the commit message is not misdirected to the wrong ledger row. The
cycle-1 split-verdict history (one PASS, one FAIL, reconciled by the FAIL's independent
re-derivation) remains intact above, untouched, per the concurrent-verdict protocol -- nothing
here erases or overwrites it.

## VL4a/VL4b -- still satisfied, not re-litigated

No code change to `_same_model_duplicate`'s merge bound this cycle (confirmed in pressure point
4), so VL4a's cross-model-non-swallowing property, already sabotage- and scenario-tested in cycle
1, is unchanged and still holds. VL4b (an explicit, stated, tested tie-break rule) is now more
fully satisfied than at cycle 1: the tie case AT-270 flagged as unstated is now named in
`_apply_merge`'s docstring and pinned by a dedicated test, sabotage-confirmed by me independently.
No further gap found; not amending the contract further.

```
VERDICT: PASS
SCOREBOARD: 6/6 pressure points clean (causal-claim re-derivation, aggregate numbers, tie-break
sabotage, no-overcorrection diff check, file-length/doctor, VL4a/VL4b satisfaction)
FAILURES: none at >80% confidence
LIVE-BROWSER: not-applicable (changed paths: src/autotester/stages/adjudicate.py,
              tests/test_adjudicate.py -- pure function, no route/template/component)
ISSUES-WRITTEN: AT-272 (low, ledger-hygiene -- manifest/commit cite AT-269 instead of AT-271)
EXPLANATION: Independently re-derived the exact claim this cycle was told to press hardest on --
loading the real cached observations and the real truth sheet from scratch, with no reference to
either prior checker's figures while computing -- and got 0.247 -> 0.369 for the erp2/E-02 pair
and a sub-threshold 0.234 ceiling for the erp1/E-01 pair, matching the manifest's corrected table
exactly. Re-ran the real pipeline in three states and reproduced the aggregate 6->3/5->2/1-7-recall
numbers exactly. Sabotage-confirmed the tie-break fix myself in an isolated extract (BBBB winning
the tie exactly as predicted when reverted). Diffed 791512f->696784f to confirm no substantive
merge-logic change, only docstrings, as the manifest claims. File length (300) and doctor (clean)
confirmed. The one real defect found is bookkeeping, not code: the manifest and commit message
close out the wrong issue id (AT-269, an unrelated already-fixed issue) instead of AT-271 (the
actual high-severity finding this fix resolves) -- corrected in the ledger directly since fixing
qa/issues.jsonl is this role's own responsibility, filed as AT-272 for the record, and does not
implicate the fix or its evidence, both of which are independently correct.
```
