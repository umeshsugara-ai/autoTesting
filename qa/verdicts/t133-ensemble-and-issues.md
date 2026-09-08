# Verdict — t133-ensemble-and-issues

**Unit:** T-133 — Track A4: two-model ensemble + deterministic adjudication + Issue derivation + the 13-column Excel
**Contract:** `qa/contracts/video-learning.md` (VL2, VL2b, VL3, VL4, VL5, VL6; I-VL5, I-VL6 — **authored by this check**)
**Cycle checked: 1**
**Date:** 2026-09-09
**Checker:** fresh Mode A subagent, bound to `D:/autoTesting`. Adapter: `qa/adapter.json` (coding). Docker down; `uv` native.

---

## VERDICT: FAIL

**SCOREBOARD: 3/6 criteria met, 2/2 invariants hold**

Met: VL2, VL5, VL6. Not met: VL2b, VL3, VL4.

---

## What I re-ran (my own output, not the maker's)

| Command | Result |
|---|---|
| `uv run pytest -q` | **exit 0** — 797 passed, 2 skipped. Matches the claim. |
| `uv run pytest tests/test_adjudicate.py tests/test_analyze_video.py tests/test_issues.py -q` (T-133's `done_check`) | **exit 0**, 52 passed |
| `uv run ruff check src tests scripts` | **exit 0** — "All checks passed!" |
| `uv run autotester doctor` | **exit 0** — "doctor: clean" |
| `done_check` at the parent commit `1bf8c36` | all three test files are **ABSENT** at `1bf8c36` (`git cat-file -e` fails for each), so the check could not have exited 0 before this unit. Claim confirmed. |

Verification is green and the manifest's numbers are honest. **The FAIL is not about the verify;
it is about three criteria the verify does not reach.**

## The 15 sabotages — all 15 discriminate; none INCONCLUSIVE

Run in an isolated worktree at HEAD (`git worktree add`, AT-101 respected — nothing stashed,
checked out or restored in the live tree). Each anchor asserted to match **exactly once**, the file
asserted changed, the three T-133 test files re-run, `FAILED` lines counted, the file restored
byte-for-byte before the next.

```
BA severity back to max()            expected 2  measured 2   OK
BB stop sorting the input            expected 1  measured 1   OK
BC merge screens on name alone       expected 1  measured 2   (stronger than claimed)
BD shift mutates the cache           expected 2  measured 2   OK
BE agreement stops raising confidence expected 1 measured 1   OK
BF rename a column                   expected 2  measured 2   OK
BG At written as a number            expected 1  measured 1   OK
BH our severity vocabulary           expected 1  measured 1   OK
BI how-we-know from the claim        expected 2  measured 3   (stronger than claimed)
BJ drop the tester's words           expected 1  measured 1   OK
BK ignore the cache                  expected 2  measured 2   OK
BL a failed provider aborts all      expected 2  measured 2   OK
BM total failure writes an analysis  expected 1  measured 1   OK
BN stop slicing narration            expected 2  measured 2   OK
BO drop the chunk offsets            expected 1  measured 1   OK
```

Baseline in the worktree: 0 failures. The two counts above mine are my sabotage variants biting
harder than the maker's, not a weaker suite — both directions are safe.

**BG verified specifically, as asked.** Reverting `issue_row` to write `issue.at_s` instead of
`at_mmss(issue.at_s)` fails **exactly one** test, and it is
`tests/test_issues.py::test_the_At_CELL_carries_MM_SS_not_a_number` — the workbook test added
*after* the INCONCLUSIVE. The parametrized `at_mmss` test does **not** fire. The maker's account of
BG is exact: the helper being right did not make the sheet right, and the fix is what made the
sabotage bite.

**The severity inversion is genuinely fixed and genuinely unique.** `worst()` verified exhaustively
over all nine `Severity` pairs plus a 3-argument call (`worst(S3, S1, S2) == S1`) — correct in every
case. Swept `src/` for the same pattern: the only `max()`/`min()` calls over an ordered enum are
`adjudicate.py:96` (`t_end`, a float, correct) and unrelated numeric maxima in `core/excel.py`,
`ledger/render.py`, `ledger/store.py`, `schema/media.py`. **No second instance of the inverted
pattern exists in the codebase.**

---

## FAILURES

### [VL4] sev: high · adjudication is NOT a function of content alone in the shipped configuration · issue: AT-197

The determinism claim is the load-bearing one, and it does not hold.

`adjudicate` sorts by `(offset_s, provider_label, chunk_index)`. `PROMPT_NAMES` has **two**
entries. So for one model and one chunk, the mapping-pass observation and the issues-pass
observation are **equal under that key** — and Python's sort is stable, which hands the tie
straight back to the caller's list order. Every downstream merge is first-seen-wins.

Measured, not argued. Two `ModelObservation`s identical but for `prompt_name` (one carrying
screens/`url`/`purpose`, the other an issue and a different summary), permuted:

```
ATTACK1 two-prompt tie: distinct outputs = 2
   differs in: screens
   differs in: journey
   differs in: issues
   differs in: summary
```

The module docstring — *"Given the same cached observations in any order it produces byte-identical
output"* — is false in exactly the shape this unit ships.

I attacked the rest of the surface too, and the rest holds: 500 shuffles of the maker's
single-prompt shape → **0** mismatches (his 8 were not the weakness); identical timestamps from
different models → 1 distinct output; labels that sort in either direction (`a`/`b`, `Z`/`a`) → 1
distinct output each; an empty ensemble produces an empty analysis without raising; a **negative**
offset (−50.0) and a **huge** one (1e18) both pass through arithmetically and unremarkably. The
single hole is the tie, and it is the production shape.

Not yet a live divergence — `analyze()` always appends in provider→prompt→chunk order, and
`store.list_observations()` glob-sorts to the same order, so today's two producers happen to agree.
It goes live the moment anything re-adjudicates from a differently-ordered source (T-136's scorer,
a reordered provider list). The `sorted()` call exists so nobody has to know that.

**Fix direction:** add `prompt_name` to the sort key so it is total over the same tuple the cache
is keyed on, and add an order-test fixture in which two observations differ *only* in
`prompt_name`. The current test cannot see this: every fixture in it is built by `obs()`, which
hardcodes one prompt name.

### [VL3] sev: high · a 1-of-24 analysis is indistinguishable from a complete one · issue: AT-198

"Failure is partial, never total" is built and evidenced (BL, BM). But the guard stops at zero, and
the manifest's own reasoning does not: *"an empty analysis on disk reads as 'we watched it and
found nothing' — the opposite of what happened."* A 4 %-coverage analysis reads the same way and
looks populated while doing it.

Measured over 12 chunks × 2 prompts × 2 models — a full run and a run where the second model died
after its very first call:

```
FULL   : (['m1','m2'], ['ingest_video_v1.md','video_issues_v1.md'], 12 screens, 12 issues)
CRIPPLE: (['m1','m2'], ['ingest_video_v1.md','video_issues_v1.md'], 12 screens, 12 issues)
Any field recording attempted-vs-observed? NONE
```

`VideoAnalysis` carries no count of intended or obtained calls anywhere in `model_dump()`. T-136's
recall denominator would be computed against a fragment with no way to know.

**Fix direction:** persist `len(providers) * len(PROMPT_NAMES) * len(prep.chunks)` and
`len(observations)` on the artifact. The field alone discharges the criterion; a coverage floor is
a separate decision.

### [VL2b] sev: high · a damaged cache entry kills the source, and `--force` cannot rescue it · issue: AT-199, AT-200

VL2 proper is **met** and well built — I confirmed zero provider calls on a second `analyze` (0 of
48 at 12 chunks × 2 prompts × 2 models), that `--force` **overwrites in place** (4 files before, the
same 4 names after — no duplicates), and that widening the ensemble costs only the widening. `_cached`
does scan `list_observations()` per call — 48 calls each re-reading up to 48 JSON files — but the
fully-cached second run over the full 48-observation shape took **0.32 s** against a 0.71 s cold
run, so the O(n²) is real and irrelevant at this size. Not filed.

What fails is the *promise* the cache is sold on — safe to re-run after a crash or a code change:

- **After a crash.** A half-written observation file is exactly what an interrupted run leaves.
  Overwriting one of four cached files with `{ this is not json` makes the next `analyze` raise
  `ValueError` out of `read_json`. Valid-JSON-wrong-shape raises too. And `analyze(..., force=True)`
  **also raises** — because `_cached()` is called unconditionally at the top of `observe_chunk`,
  *before* the `not force` test. The override is blocked by the thing it overrides. There is no CLI
  escape short of deleting files by hand. (AT-199)
- **After a code change.** The cache key is the prompt's *name*. Editing `video_issues_v1.md` still
  hits every cached chunk, so the analysis silently mixes answers to two different questions with
  no field recording which. This project treats prompts as code by rule. (AT-200)

**Fix direction:** skip an unreadable cache entry rather than raising (it is a cache, not a ledger —
an absent answer costs one re-request), move the `_cached()` call inside the `not force` branch, and
put a hash of the rendered template into `ModelObservation` and into the match.

---

## Criteria met

- **VL2 — a cached observation is never re-requested.** Verified by execution, not by the maker's
  spies: 0 provider calls on a fully-cached re-run; `--force` overwrites rather than duplicates;
  per-model keying confirmed. Sabotage BK (ignore the cache) fails 2.
- **VL5 — offsets in code, narration sliced.** `shift` deep-copies before mutating (BD → 2);
  offsets are applied by the stage and the prompt forbids the model from adding its own (BO → 1);
  `build_chunk_prompt` slices the transcript to the chunk and a silent section says so rather than
  leaving a gap (BN → 2).
- **VL6 — the sheet is theirs.** I loaded the real workbook myself, from the corpus path the test
  names (`C:/Users/Lenovo/Videos/Screen Recordings/ERP_Issues_ALL.xlsx` — the corpus file, not a
  copy in the repo; `tests/test_issues.py:36` points at that absolute path). Sheet `All issues`:
  **13 columns, identical strings in identical order** to `ISSUE_COLUMNS`; 33 rows total, i.e. **32
  data rows** — the maker's correction of the plan's 33 is right, and it is T-136's denominator.
  `At` cells hold strings (`'00:23'`, `'01:34'`, `'09:17'`); `Severity` cells read `High`/`Medium`,
  matching `SEVERITY_WORDS`. BF (rename a column) fails 2, BH (our vocabulary) fails 1, BG (the
  written cell) fails 1.

## Invariants

- **I-VL5 — a merge never softens a severity.** Holds. `worst()` correct over all nine pairs;
  BA (back to `max()`) fails 2; agreement raises `confidence` and never `severity` (BE fails 1); no
  second inverted-`max` site anywhere in `src/`.
- **I-VL6 — no model decides a merge.** Holds. `adjudicate.py`, `issues.py` and the export contain
  no provider call; the matcher is casefolded names, interval overlap and a fixed 10 s window.

## The sheet: ruling on "the scorer accommodates both"

**Currently false; merely planned.** I loaded both real workbooks. `ERP_Issues_Trainers.xlsx` /
`Trainer module` has **12 columns, 8 rows, no `Date`, and `Clip` where ALL says `Recording`** —
every fact in the docstring is measured and correct. But `scripts/` contains no scorer (nothing
matching `score`), and no file under `src/`, `tests/` or `scripts/` mentions `Clip` or the Trainers
schema anywhere except that docstring's own sentence. The manifest's "What this does NOT claim"
discloses the boundary honestly; the shipped code states it in the present tense. Filed AT-201
(medium) — not scored against VL6, which covers the sheet this exporter writes.

## The prompt, judged as a prompt

`video_issues_v1.md` forbids all three failure modes that matter, and each is independently
evidenced rather than merely written: inventing ("Report only what you can point at"; "Anything you
did not see or hear in **this** section"; "return an empty list — that is a real answer, and a
normal one"), paraphrasing narration ("verbatim from the transcript below. Never paraphrase and
never re-transcribe" — BN bites), and adding its own offset ("Do not add any offset; the system adds
the section's offset itself" — BO bites). That is a good prompt.

The false-positive risk at scale is not in what it forbids but in what it omits: **it never mentions
`confidence`.** `ObservedIssue.confidence` defaults to MEDIUM, the prompt maximises recall of spoken
remarks ("**Take them at their word**"; a requested change "is a real finding"), and tells the model
to judge the product rather than its own certainty. `join_issues` then raises confidence to HIGH on
agreement and has **no path that lowers it** — and two models given the same "take them at their
word" instruction are not independent on an offhand aside. The predicted shape at scale is HIGH-
confidence S2 rows derived from asides. The recall bias is deliberate and justified (the taxonomy
records that 10/33 real ground-truth rows were spoken change requests), and T-136 is where precision
gets measured — so this is filed medium (AT-203) to make the measurement expected rather than
discovered, not scored against a criterion.

## Adversarial pass — could `analyze` overstate what happened?

Yes, once: **AT-198** above (a fragment that looks whole). Two lesser paths, both filed:
two providers sharing a `provider_label` collapse the ensemble to one silently — measured, provider
A made 4 calls and provider B made 0 — though the artifact stays honest (`provider_labels=['dup']`,
`models_agreeing=1`), so AT-204 is low. And `at_mmss(-5.0)` renders `'-1:55'`, a plausible-looking
time; negative offsets are unvalidated all the way through (`offset_s = -50.0` shifts a screen to
t=−40.0 without complaint), latent today, AT-205 low.

One more merge defect found while attacking VL4: **`_merge_lists` unions `signals`, `ui_elements`
and `screenshot_ts` but not `fields`** — `join_screens` over two models seeing `['email']` and
`['password']` returns `['email']`. The function's own docstring states the rule it breaks ("if one
model noticed a **field** the other missed, the field exists"), and
`test_a_field_only_one_model_noticed_survives_the_merge` asserts on `signals` and `url`, not on
`ObservedScreen.fields`. Input fields are what a generated eval fills in, so a lost field is a flow
never exercised. AT-202, medium.

## Contract action taken

Authored **VL2, VL2b, VL3, VL4, VL5, VL6** and **I-VL5, I-VL6** into `qa/contracts/video-learning.md`
with an amendment-log entry recording, per criterion, what was taken as requested and what was
changed on evidence. VL2/VL5/VL6 are substantially as the maker asked. VL2b is a checker addition;
VL3 was widened past "total failure refuses"; VL4 was tightened from "in any order" to "in any order
the system actually produces". **None of the three failing criteria was softened to fit the
artifact** — VL4 in particular is the maker's own stated property, restated so that a test can
actually reach it.

## Issues written

**AT-197** (high, VL4) · **AT-198** (high, VL3) · **AT-199** (high, VL2b) · **AT-200** (high, VL2b) ·
AT-201 (medium) · AT-202 (medium) · AT-203 (medium) · AT-204 (low) · AT-205 (low)

`Issues addressed` — the manifest claims none closed by this unit; AT-192, AT-193 and AT-196 are
correctly left open and untouched. Nothing in the ledger was moved to `fixed` by this check.

## Goal task

**T-133 stays open.** A FAIL never closes a goal task. No `docs/FEATURES.jsonl` row is due yet; when
this unit PASSes, one is (`user_value: high`, so with a prefilled reason for Umesh to confirm).

---

## Returned block

```
VERDICT: FAIL
SCOREBOARD: 3/6 criteria met, 2/2 invariants hold
FAILURES:
- [VL4] sev: high · adjudicate's sort key omits prompt_name, so in the shipped 2-model x 2-prompt
  ensemble the merge is order-dependent: permuting two observations that differ only in prompt_name
  changes screens, journey, issues and summary · add prompt_name to the sort key and give the order
  test a fixture where only prompt_name differs · issue: AT-197
- [VL3] sev: high · an analysis built from 1 of 24 intended calls is indistinguishable from a full
  one — same provider_labels, same prompt_names, no coverage field anywhere · persist intended and
  obtained call counts on VideoAnalysis · issue: AT-198
- [VL2b] sev: high · a truncated cached observation raises ValueError out of analyze and --force
  cannot get past it, because _cached() runs before the not-force test — the crash the cache exists
  to survive bricks the source; and the key is the prompt's name, not its content, so an edited
  prompt silently reuses the old answer · skip unreadable entries, move _cached inside the not-force
  branch, hash the template into the key · issues: AT-199, AT-200
ISSUES-WRITTEN: AT-197, AT-198, AT-199, AT-200, AT-201, AT-202, AT-203, AT-204, AT-205
EXPLANATION: Verification reproduces exactly (797 passed / 2 skipped, ruff clean, doctor clean,
done_check green and absent at the parent), all 15 sabotages discriminate with none INCONCLUSIVE,
BG's story checks out precisely, and worst() is correct over every severity pair with no second
inverted-max site in the codebase — this is careful work. It fails on the one claim it is built
around: adjudication is not order-independent in the configuration it ships, because the sort key
omits prompt_name and the determinism test's every fixture carries a single prompt name, so the tie
the criterion is about cannot arise in it. Alongside that, the honesty guard that refuses to persist
an empty analysis stops one step short — a 1-of-24 fragment persists looking complete — and the
cache's crash-safety promise inverts under a truncated entry that --force cannot clear.
```
