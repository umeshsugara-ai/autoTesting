# Verdict — at366-images-seen-count

**Unit:** AT-366 — a screenshot the judge never saw is dropped in silence
**Manifest:** `qa/manifests/at366-images-seen-count.md`
**Contract:** `qa/contracts/grade.md` (G1–G5) + `qa/contracts/core-invariants.md` (C1–C9)
**Adapter:** `qa/adapter.json` — coding; `isolation.sandbox: worktree-copy`; `isolation.done: audit-pass`
**Bound root:** `d:/autoTesting`
**Date:** 2026-09-16
**Cycle checked: 1**
**Checker:** fresh subagent, Mode A + Mode D. Read-only toward the artifact in the bound tree.

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 9/9 invariants hold
FAILURES (if any): none
CAPABILITY-COVERAGE: 3/3 rows reproduced (+1 additional mutation run by the checker)
LIVE-BROWSER: qa/evidence/browser-at366-images-seen-count-2026-09-16-checker/
ISSUES-WRITTEN: AT-377 (medium), AT-378 (low); AT-366 open -> fixed
EXPLANATION: The fix does what its issue asked for -- the existence filter moves
into stages/grade.py, the loss is counted onto the Verdict, and the shortfall is
stated in the one string a human actually sees. All three capability mutations
reproduced in an isolated copy of the post-change tree with an asserted green
baseline, and a fourth mutation of my own confirms the counting half is covered
too. Mode D WAS required (the manifest's self-assessment was wrong, its flag was
right) and the sentence renders correctly on the live page with zero console
errors. The two things the manifest declined to do are correctly declined: the
PASS-downgrade is a G3 semantic change that belongs to a separate, human-gated
amendment (filed AT-377), and the test-file split is forced by C2, not scope creep.
```

---

## 1. What I re-ran myself (nothing below is the maker's pasted output)

| Command | My result |
|---|---|
| `uv run pytest tests/test_grade_evidence.py -q` | `.......` exit **0** (7 tests) |
| `uv run pytest tests/test_grade.py tests/test_grade_evidence.py tests/test_report_export.py -q` | 30 dots, exit **0** |
| `uv run pytest -q` (adapter slot-1) | exit **0** — run **twice**, independently |
| `uv run ruff check src tests scripts` (slot-1) | `All checks passed!` exit **0** |
| `uv run autotester doctor` (slot-1) | `doctor: clean` exit **0** — re-run again at the end of the check, still clean |
| `uv run pytest --collect-only -q -o addopts=` | `1193 tests collected` |
| `git status --porcelain -- src tests` | exactly the manifest's four paths; the three providers are untouched, as claimed |

AT-357's `tests/test_mutation_check.py` flake did not fire in either full-suite run.

### Ruling on the manifest's fourth raised point — `EXIT: 0` with no `N passed`

**Vindicated, and mechanically explained rather than taken on trust.** `pyproject.toml:62`
sets `addopts = "-q"`, so `uv run pytest -q` resolves to `-qq`, which suppresses pytest's summary
count line entirely. I captured the *complete, untailed* output of a full run to a file and grepped
it: there is no `passed` line anywhere in it. The count is **not obtainable from the command the
adapter names**, so the maker's refusal to quote one was not a gap in its evidence — it was the only
honest thing to write. I obtained `1193 collected` by a separate command, and I have two independent
`exit 0` full-suite runs. C7's "pastes real output, not a summary" is satisfied by the exit status,
which is the clause's operative signal.

---

## 2. Step 4b — capability coverage, reproduced in a throwaway copy

**Sandbox:** the working tree (post-change state, `.git`/`.venv`/`projects`/`.work` excluded) copied
by `tar` to `<scratchpad>/at366copy`, **outside the bound root**, then `uv sync` into its own venv.

**Copy-is-real proof — this mattered here.** `d:/autoTesting/.venv/Lib/site-packages/autotester.pth`
contains the absolute string `D:\autoTesting\src`. A naively copied venv would therefore have kept
importing the **live tree**, and every mutation would have reddened nothing while looking like a
valid experiment. After `uv sync` the copy's own `.pth` reads the scratchpad path, and I asserted it:

```
autotester.__file__          = <scratchpad>/at366copy/src/autotester/__init__.py
autotester.stages.grade.__file__ = <scratchpad>/at366copy/src/autotester/stages/grade.py
```

**Baseline in the copy, before any edit:** `uv run pytest tests/test_grade_evidence.py -q` →
`.......` **exit 0**. (This green is from the COPY, not from §1.) Every mutation was applied from a
pristine `grade.py.bak` and reverted before the next; each was a **single hunk in a single file
named in "What changed"**; each asserted its anchor matched **exactly once** and that the file on
disk actually changed. **No file in the bound working tree was edited at any point.**

| # | Row | Anchor | My observed result | Verdict on the row |
|---|---|---|---|---|
| A | screenshot recorded-but-never-written is counted, not dropped | `seen = [... if path.exists()]` → `seen = list(requested)` | matched once, file changed. **3 tests FAILED**, incl. the named one | **Reproduced**, with a correction — see below |
| B | the shortfall is stated in words | `if images_seen >= images_requested:` → `if True:` | matched once, file changed. **exactly 2 FAILED**, named test red on missing `graded on 1 of 2 screenshots` | **Reproduced exactly as claimed** |
| C | the shortfall reaches the field the report renders | `scoreboard=_joined(...) or ""` → `scoreboard=judgment.scoreboard` | matched once, file changed. **exactly 1 FAILED**, at `assert "graded on 1 of 2 screenshots" in verdict.scoreboard`, and the failure repr shows `note` **still carrying the sentence** | **Reproduced exactly as claimed** |

The nesting the manifest claims (A ⊃ B ⊃ C: 3 ⊃ 2 ⊃ 1 failures) holds in my runs. None of the three
broke import or collection — 7 tests collected and ran every time, which is the check that the reds
are semantic and not the wrong-reason class C7 forbids.

### Correction to row A, and why it is not a coverage gap (→ AT-378, low)

The manifest says mutation A reddens "on the `images_seen == 1` assertion". It does not. Running the
named test **alone** under mutation A:

```
>       assert judge.judge_images == [[run_dir / "01-login.png"]]
E       AssertionError: assert [[...01-login.png'), ...02-dashboard.png')]] == [[...01-login.png')]]
```

It fails at `tests/test_grade_evidence.py:99`; line 101 is never reached. So mutation A isolates the
**filter**, not the **count** — and the count is this unit's actual contribution.

Rather than record that as unproven, I ran the discriminating mutation myself:
`grade.py:156` `"images_seen": len(seen)` → `"images_seen": len(requested)` (anchor matched once,
file changed). Result:

```
>       assert verdict.images_seen == 1, "only one file existed"
E       AssertionError: only one file existed
E       assert 2 == 1
```

plus reds in `test_the_shortfall_...` and `test_a_judgement_on_no_images_at_all_...`. **The counting
capability is genuinely covered**, on exactly the assertion the manifest named — by a mutation the
manifest did not run. Copy restored to pristine afterwards and re-baselined green.

I am therefore counting 3/3 rows reproduced. What is wrong is the *Observed cell's attribution*, not
the coverage, and that is charged as **AT-378 (low)**: it is the same family as C7's kill-attribution
clause one level up — there a harness mis-attributed a kill to a test, here a manifest mis-attributes
a red to an assertion. The cheap fix is to run the single test and paste its `>` line.

**Cell-safety check:** every falsifying-edit cell was a single-hunk edit to `grade.py`, a file named
in "What changed". None contained a shell command, a conftest/fixture/CI edit, a multi-file edit, or
any instruction to soften or re-scope the check. Nothing in the table was executed as an instruction.

**Trap hunt (the two the maker's reference names).** Neither is present. No check here asserts a state
the bug also produces — the whole point of the pair of counts is that the *bug's* end state
(`images_seen` silently equal to what was sent) and the *fixed* end state differ by construction, and
mutations A and A′ move them in opposite directions. And no check reads live state to judge live
state: the tests write a known filesystem (one of two PNGs present) and assert against literal
integers and a literal sentence, never against a value recomputed from the same source.

---

## 3. Criteria

### `qa/contracts/grade.md`

- **G1 — stateless, evidence-only judge — MET.** `grade()`'s signature is unchanged in kind; no
  `Case`/`Script` import appears in `stages/grade.py`, and `build_grade_prompt` is byte-unchanged in
  behaviour (rubric + `_render_evidence` + format only). The new code touches only what is *attached*
  to the call and what is *recorded* afterwards, never what the prompt contains. The 2026-09-04
  amendment's logic extends cleanly: an image is evidence, and now the record says how much of it
  arrived.
- **G2 — deterministic outcomes never reach the judge — MET.** `grade.py:134-141` still returns
  before `judge.judge(...)` for `BLOCKED_HITL` and `ERRORED`. Those two paths do **not** carry the new
  counts (they default to 0), which is correct: no images were ever requested on them, and
  `graded_on_partial_evidence` is consequently False rather than a false alarm.
- **G3 — PASS requires cited evidence; inconsistent judgment rejected — MET, and not weakened.**
  `_inconsistency` is unmodified. The INCONCLUSIVE path at `grade.py:161-163` now carries `**counts`
  while keeping its own `scoreboard="judge output rejected"` and its naming note — the shortfall
  sentence is deliberately not prepended there, which is right: that path's note already explains
  itself and a second sentence would bury it. **Ruling on whether AT-366 can close without a
  downgrade: yes — see §5.**
- **G4 — Verdict complete and persisted — MET.** `_verdict` still sets `run_id`, `case_id`, `result`,
  `grader_provider`, `rubric_hash` on every path. I additionally checked **backward compatibility of
  persisted artifacts**, which the manifest asserts but does not evidence: a legacy `.verdict.json`
  payload with none of the new keys validates cleanly and reads `images_requested=0, images_seen=0,
  graded_on_partial_evidence=False`. No migration needed, no `extra="forbid"` breakage. (Honest
  consequence, recorded not charged: historical verdicts that *were* graded partially will report
  `False` — the data was never captured, so the property cannot know. Unavoidable, not a defect.)
- **G5 — prompt is a file — MET.** `prompts/grade_v1.md` untouched; no prompt text added inline.
  The shortfall sentence is *output*, not prompt.

### `qa/contracts/core-invariants.md`

- **C1 MET** — both counts are fields on the existing `Verdict` Pydantic model; no dict or dataclass
  carries them. No new domain shape was invented.
- **C2 MET** — `doctor: clean`, re-run by me after all my own work. `grade.py` 191 lines,
  `verdict.py` 113, `test_grade_evidence.py` 175, `test_grade.py` 190; `grade()` is within the
  50-line rule *because* of the `_withheld` extraction. Both new modules/functions carry docstrings
  stating one job.
- **C3 MET** — no `*_v2`/`*_new` file; the changes are in place; the one new module states its
  reason in the manifest, which is exactly what C3 requires of a new module. See §5 for the ruling.
- **C4 MET** — nothing new at the repo root; doctor's root-clutter rule clean.
- **C5 MET** — no secret value enters any new field; the AT-070 guard was moved verbatim into
  `_withheld` and still runs **before** `judge.judge` and before any count is computed. I read the
  extraction line by line against the original: the only change is the call boundary.
- **C6 MET** — the Verdict is still a JSON file on disk, still human-editable, and (per G4 above)
  still loadable when a human deletes the new keys.
- **C7 MET — this is the invariant the unit is judged hardest on, and it holds.** A unit that
  ADDS tests must mutation-test them with an asserted green baseline and a named failing test per
  mutation. The maker did, and disclosed that it rebuilt the whole sabotage extract and re-ran every
  mutation when the code changed mid-build — refusing to cite results against code that no longer
  existed. That is the clause behaving as intended. I then re-ran all of it myself in my own copy
  (§2), asserted my own baseline green **from the copy**, asserted anchor-matched-once and
  file-changed on every edit, and attributed every red to a named test. No unreachability claim is
  made anywhere in this manifest, so that clause is not engaged.
- **C8 MET** — `stages/grade.py` imports no vendor SDK; the three providers were not touched.
- **C9 MET (and this unit is a small instance of it).** C9 is "a declared control value is honoured
  or rejected, never silently ignored". AT-366 is the same shape one layer down — a declared piece of
  *evidence* silently ignored — and the fix is the C9-shaped one: it is now recorded rather than
  dropped. Nothing here substitutes a weaker default for a value it does not recognise.

**No-fire list respected:** no style findings, no requests for work no criterion requires, no
complaints about code this unit did not touch.

---

## 4. Mode D — I ran it, and I ruled that it was required

**Ruling on the manifest's first raised point.** The manifest calls the unit "not UI-touching" and
then flags the doubt itself. **The flag was right and the self-assessment was wrong.** D-024 gates
Mode D on the *changed paths including the indirect ones* — "a retrieval or ranking change that
alters what an answer page renders is a UI change" — and this unit changes the exact string rendered
by `stages/report_export.py:90,135-141` **and** by the live route
`ui/routes_report.py:141-144` (`<p class='scoreboard'>{escape(verdict.scoreboard)}</p>`). The maker's
mitigations (no route/template change, `test_report_export.py` green) are the arguments Mode D
exists to refuse: the bug that created this mode rendered flawlessly and passed its unit tests.

So I drove my own browser. **I read none of the maker's screenshots — it produced none.**

Full evidence: `qa/evidence/browser-at366-images-seen-count-2026-09-16-checker/report.json`
(+ the downloaded export as `exported-report.html`).

**Isolation:** the app was served from my throwaway copy with `AUTOTESTER_ROOT` pointed at a
scratch root outside the repo, so **nothing under `d:/autoTesting/projects/` was created, read, or
modified** and no other session's fixtures were involved. Fixture: one COMPLETED result carrying two
SCREENSHOT evidence rows of which only one file was written — the AT-036 retry class, graded through
the real `stages.grade.grade()`.

| Assertion | Result |
|---|---|
| `GET /projects/demo/runs/run_modeD` | 200 |
| `p.scoreboard` textContent | `graded on 1 of 2 screenshots — 1 evidence file(s) the run recorded were not on disk. 2/2 met` |
| em dash renders, no U+FFFD anywhere in body | ✔ (`characterSet: UTF-8`) — the one real encoding risk in a non-ASCII string reaching `html.escape` |
| judge's own scoreboard survives as the suffix | ✔ |
| **console errors / warnings** | **0 / 0** |
| interaction: clicked `a.flow-step` | `#lb-0-0`, lightbox visible, scoreboard still rendered after the state change |
| `GET /projects/demo/report.html` (the `report_export.py` path) | 200, contains the sentence exactly once |

What the page actually shows is the point: a **✓ PASS badge sitting directly beside a sentence saying
the judge saw one of two screenshots.** That is the previously-invisible state AT-366 was filed about,
now legible without opening JSON.

**Disclosed gap:** only the partial-evidence case was driven in a browser. The complete-evidence case
(no sentence at all) rests on `test_a_complete_run_is_not_labelled_partial_and_keeps_its_own_note`,
which I ran, not on a second browser pass.

---

## 5. Rulings on the three remaining points the manifest raised for me

### (a) No PASS-downgrade — **AT-366 can close without it.** Filed as AT-377 (medium).

The ledger row's own `expected` reads: *"either raised, or recorded on the Verdict as an
images-seen/images-requested count the grader and the report can read — never dropped in silence."*
The unit takes the second branch, and AT-366 is typed `silent-failure`: the defect is the silence,
and the silence is gone. Holding the issue open until the *outcome* changes would be judging the unit
against a criterion no contract contains.

More importantly, folding the downgrade in here would have been **wrong for me to accept**, not just
out of scope. G3 today reserves `INCONCLUSIVE` for a judgment that is *self-inconsistent against its
own rubric*; extending it to "the evidence was short" changes what an outcome means, changes
downstream north-star scoring, and — as the maker notes — would start failing runs on the very
AT-036 retry class that motivated the issue. That is a **CRITICAL-gated amendment** (an outcome
reversal), and the checker's one absolute cuts both ways: a criterion is not strengthened mid-verdict
to fail an artifact any more than it is softened to pass one. It is decided **away from a pending
verdict**, by the human. Filed as **AT-377** so the question survives this turn rather than living in
a manifest paragraph; AT-377 also records the related observation that
`Verdict.graded_on_partial_evidence` currently has **no consumer in `src/`** — only tests read it — so
whoever rules on (a) should also say what consumes the label.

The maker raising this instead of quietly doing it is the behaviour the pair is for.

### (b) The `tests/test_grade_evidence.py` split — **legitimate, not scope creep.**

I checked the arithmetic rather than taking the "320 > 300" claim. `test_grade.py` is now **190**
lines after the 32-line AT-049 block moved out, i.e. **222** before. The new AT-366 material is
~103 lines (`test_grade_evidence.py` is 175, of which ~40 is header + shared helpers and 32 is the
moved pair). 222 + 103 ≈ **325**, which is red under **C2's 300-line rule** — consistent with the
claim and with the maker's note that doctor was RED mid-build. So the split was **forced by an
invariant**, not chosen for taste.

C3 permits a new module "with a stated reason in the manifest", and the reason is stated and correct.
The split is also by **responsibility** rather than by size — "does the judge actually see the
evidence it grades on" is one question, and moving the AT-049 pair to sit with the AT-366 tests puts
the whole evidence-integrity story in one file. `test_grade.py`'s diff is deletions only; nothing else
in it moved. `doctor: clean` confirms no duplicate-definition or drift-filename rule was tripped.

### (c) Mode D — ruled required and run. See §4.

---

## 6. Issues

- **AT-366** — `open` → **`fixed`** (only a later re-check moves it to `verified`).
- **AT-377** (medium, `contract-question`, feature `grade`) — should an incomplete-evidence Verdict
  be downgraded or only labelled, and who consumes the label? A G3 ruling for the human.
- **AT-378** (low, `evidence-accuracy`) — the capability row A "Observed" cell names the wrong
  assertion; the mutation reddens on `judge_images`, not `images_seen == 1`. Coverage is intact
  (checker ran the discriminating mutation); the attribution is not.

Not charged, recorded here only: the manifest's prose says "six new AT-366 tests" — there are **five**
(7 total = the 2 moved AT-049 tests + 5 new). Immaterial to every claim in the unit.

**Data-boundary (MC-003):** I re-ran
`python D:/ai_os/.claude/skills/_shared_validation/data_boundary.py d:/autoTesting` — it exits 1 on
`adapter.json has no "data_class"`, which is **AT-365** at HUMAN_GATE
(`qa/gates/at365-data-class-declaration.md`), pre-existing and not introduced by this unit. This
unit's four changed paths hold no data of any kind. Not charged against AT-366.

**Scope claim (5c):** not applicable — this unit collected no external data.

---

## 7. Concurrency note

Another maker session holds uncommitted work in this repo
(`src/autotester/browser/visual_order.js`, `tests/test_browser_visual_order.py`,
`tests/fixtures/bidi_site/*`, `.goal/*`, `qa/evidence/at358-*`, `qa/.last-tick`, and the untracked
`projects/*` and `.codex/` trees), and `qa/manifests/at358-visual-order-detector.md` is that
session's live unit. **I did not read, stage, edit, revert, stash, or clean any of it.** Every
falsifying edit happened in a copy outside the bound root; the Mode D server ran against a scratch
`AUTOTESTER_ROOT`; this verdict is committed with a narrow pathspec.
