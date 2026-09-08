# Verdict — at116-criticality-vocabulary

**Date:** 2026-09-08
**Cycle checked:** 1
**Contract:** `qa/contracts/core-invariants.md` (C6; **C9 added by this check** — see Contract ruling)
**Bound root:** `D:/autoTesting`
**Commit under check:** 1fb89c9
**Checker:** fresh Mode A subagent, read-only toward code/artifacts/manifest

```
VERDICT: PASS
SCOREBOARD: 6/6 claims evidenced, 9/9 invariants hold (C1–C9; C9 authored by this check)
FAILURES: none
ISSUES-WRITTEN: AT-118 (medium, upstream), AT-119 (low, hardening)
ISSUES-CLOSED: AT-116 open→fixed, AT-100 open→fixed (second half)
EXPLANATION: Computed rather than read — imported classify() from the shared classifier and ran it
over the live goal.json; T-145 and T-154 both derive 'critical', and the computed pending
distribution matches the stored field exactly, so monitor.py's output is not stale. Sabotage
reproduces (2 failed in 0.20s in a git-archive copy). The NORMAL→low mapping is correct on
evidence stronger than the maker's own argument: monitor.py:40 treats 'low' and 'medium' as one
auto-advance lane, so the two are behaviourally identical and 'medium' would have bought nothing.
The T-135 false positive and the silent fallback are real defects but genuinely upstream; the
boundary call was right and the remainder is now filed durably as AT-118 rather than living in
manifest prose.
```

## What I re-ran myself

| Command | Result |
|---|---|
| `uv run pytest -p no:warnings` | **586 passed, 2 skipped in 64.47s**, exit 0 — matches the claim |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `pytest -q -rs` (skip reasons) | verified, not accepted: `tests/test_db.py:93` live-Mongo opt-in; `tests/test_ui.py:163` POSIX permission bits don't apply on Windows. Both expected on this host. |
| `classify()` over live `.goal/goal.json` | see below |
| Sabotage in `git archive HEAD` scratch copy | both tests fail |

Docker daemon down as stated; everything ran natively.

## 1. Computed, not read

Imported `classify`, `base_criticality`, `_ORDER` from
`D:/ai_os/.claude/skills/goal/scripts/criticality.py` and executed them against the live
`.goal/goal.json` (45 tasks):

```
unrecognised base_criticality: []          # 0 of 45 rows outside _ORDER
T-145  base=critical  status=pending  computed=critical  stored=critical
T-154  base=critical  status=pending  computed=critical  stored=critical
computed pending: {critical: 4, high: 6, low: 7}
stored   pending: {critical: 4, high: 6, low: 7}
```

**Confirmed.** Both target rows derive `critical`, so `maker/SKILL.md` step 7b now fires the dual
check on them.

One thing the manifest did not claim and I checked anyway: **computed and stored agree on every
pending row.** That matters because the test asserts on the *stored* `criticality` field, which
would be worthless if `monitor.py` had not been re-run. It had been. The 22 rows where stored and
computed differ are all `status: done` — exactly the `monitor.py` behaviour the maker's
self-correction #1 describes, and I confirm that correction is accurate: my uniform
`classify()`-over-all-45 run reproduces the maker's "wrong" pre-build simulation
(`{critical: 8, low: 12, medium: 7, high: 18}`) **exactly**. The simulation was not miscomputed;
it was mis-scoped by including completed work. Reporting that rather than dropping it was right.

## 2. Ruling on `NORMAL → low` — the one judgement call

The maker's count is exact. At `1fb89c9^` the vocabulary was
`{HIGH: 20, NORMAL: 12, MEDIUM: 7, LOW: 3, CRITICAL: 3}`, and of the 12 `NORMAL` rows **11 carry
`user_value: normal`**; the single exception is T-125 (`user_value: high`). Verified against the
parent commit, not the manifest.

But the maker argued this from *intent*, which is the weaker argument. The decisive evidence is in
the consumer:

```python
# monitor.py:40
if crit in ("low", "medium"):
    ...  actions.append({... "action": "auto-advance"})
```

**`low` and `medium` are the same lane.** Nothing in the pipeline distinguishes them — only `high`
and `critical` gate anything (`high` leaves the auto-advance lane; `critical` triggers the dual
check). So the choice between `NORMAL → low` and `NORMAL → medium` is behaviourally inert today,
and "safer" is not available as a property of `medium`. `low` is the faithful mapping.

Two things that make this robust rather than lucky, both checked:

- `base_criticality` is a **floor, not a ceiling**. `classify()` re-derives from live signals every
  tick, so a `NORMAL` row that becomes genuinely dangerous re-escalates regardless of its floor —
  T-135 demonstrates this happening in practice.
- The riskiest `NORMAL` rows (T-132 host media prep, T-152 AI check registry, T-155 report) are
  build tasks with no outward-facing side effect. None is a T-145-shaped row that needed a floor.

The maker chose a uniform mapping where AT-116's own fix direction said "per row". Uniform was the
better call and it stated its reasoning — I would have rejected a per-row mapping made silently.

## 3. Ruling on T-135 — an unearned dual check

`classify(T-135)` → `critical` from `base_criticality: low`, via `"merge"` in
`SIDE_EFFECT_KEYWORDS` matching "coverage/**merge**/expand loops" (a FlowSpec merge).

**The decision to leave it is upheld. The reasoning is only half right.**

Upheld because it fails safe in the correct direction and because suppressing it here has no clean
mechanism: you would either edit a shared skill from inside one project, or reword a task title to
dodge a keyword — data bending to fit a broken reader, which is precisely the defect class this
unit exists to fix.

Half right because "keyword false positive" understates it. I executed the keyword list:

```python
[k for k in SIDE_EFFECT_KEYWORDS if k == k.strip()]
# ['commit', 'publish', 'delete', 'payment', 'deploy', 'email', 'transfer', 'merge']
```

Three keywords (`' send'`, `' push'`, `' drop '`) carry deliberate space-anchoring; **eight do
not.** This is not one unlucky word — the substring guard is applied inconsistently across the
list, so `"commit"` hits "commitment", `"delete"` hits "deleted", and every project using this
classifier inherits it. That is not something to tolerate silently. **Not tolerated: filed as
AT-118.** Correct not to fix from here; incorrect to let it rest in manifest prose.

## 4. Sabotage — reproduced, plus the drift question

In a `git archive HEAD` extract (no `stash`/`checkout`/`restore`, AT-101 respected), I restored the
uppercase vocabulary across all 45 rows and reset derived values to `low`:

```
sabotaged rows: 45
FAILED test_every_base_criticality_is_a_value_the_classifier_recognises
FAILED test_the_highest_risk_pending_work_actually_derives_critical
2 failed in 0.20s
```

Both tests fail as claimed. The second failed on `- critical / + low` for T-145 — the exact
consequence the unit is about.

**On duplicating `_ORDER` instead of importing it:** the no-hard-dependency reasoning is accepted.
This suite must not break on a machine without the AIOS checkout, and importing across roots would
be a real coupling defect. But the maker framed it as a binary, and it is not one. A third test can
`importlib`-load `criticality.py` from the known path, `pytest.skip` when it is absent, and
otherwise assert `CLASSIFIER_VOCABULARY == set(criticality._ORDER)`. That keeps the suite green
everywhere and makes divergence loud where it can be detected — strictly better than a comment,
with no dependency added.

Filed as **AT-119 (low)**, not a FAIL: the shipped tests do what the manifest claims, and no
criterion required the guard. Duplicating-with-a-comment was defensible; it is simply not the best
available option, and the maker presented it as though it were.

## 5. Ruling on the scope boundary — discipline, not evasion

**Correct discipline.** `criticality.py` is outside the bound root. A unit that edited it would have
been `CONTRACT_MISMATCH` on arrival, and a project-local session changing a classifier that ten
other products depend on is how a local fix becomes a fleet-wide incident. The maker also picked
the half of AT-116's stated fix direction that stays inside its own root, which was the right half.

The evasion risk was never the refusal — it was **where the refusal was recorded.** "Filed as
out-of-scope" was, in fact, two paragraphs in a manifest that gets archived; nothing on any queue,
no ledger row, nothing a sweep or a human would ever surface again. The real bug would have stayed
live for the next project exactly as the question suspects, not because the maker declined to fix
it but because the record would have evaporated.

That is the checker's surface, not the maker's, so I closed it myself: **AT-118** now carries the
silent fallback and the unanchored keywords with executed evidence, and it will keep appearing in
sweeps until a human carries it to `D:/ai_os`. With that row on disk, the boundary call is complete.

## 6. Regressions

- **586 passed, 2 skipped** — counted myself, matches exactly (584 before + the 2 new tests).
- `.goal/goal.json` consumers checked: `autotester doctor` → `doctor: clean`;
  `monitor.py` re-derives cleanly and its written values match my independent computation;
  the dashboard reads the same file and was regenerated in the same commit.
- `git status --porcelain src tests scripts .goal` → **empty** before and after this check.
- No file in the live tree written except this checker's own surfaces
  (`qa/verdicts/`, `qa/issues.jsonl`, `qa/contracts/core-invariants.md`).

## Contract ruling (the manifest's open question)

The manifest correctly noted no contract governed this and asked me to rule. **`.goal/goal.json`
does not get its own feature contract** — one file's vocabulary is too narrow to govern separately,
and a contract per config file is the kind of machinery that stops being read.

The gap is real but broader than the manifest framed it. This is the **third** instance of one
shape: AT-100 (a `done_check` of `true` that cannot fail), AT-115, and now AT-116 (a floor silently
downgraded). C1's `extra="forbid"` makes an unknown *key* raise; nothing covered an unknown *value*
being quietly replaced by a **weaker** default. So I added **C9 — a declared control value is
honoured or rejected, never silently ignored** to `core-invariants.md`, with its own verify command.
Tightening only, weakens nothing → routine gate, applied and committed with this verdict.

C9 is also what makes AT-118 enforceable rather than advisory: it states the standard the upstream
classifier currently fails.

## Ledger

- **AT-116** open → **fixed** (verified by execution; `verified` awaits a later re-check per protocol)
- **AT-100** open → **fixed** — second half closed by this unit. It was open across two cycles solely
  because T-145 sat at `criticality: low`; it now computes `critical`. Both halves closed.
- **AT-118** new, medium, open — upstream silent fallback + unanchored keywords (needs a human for `D:/ai_os`)
- **AT-119** new, low, open — test drift guard for `CLASSIFIER_VOCABULARY`

## Note to the maker

This is the second consecutive unit where the manifest's self-corrections were accurate and
checkable, and it is why this check was fast. Correction #1 reproduced to the digit. Keep doing
that. The one habit to adjust: when you decline to fix something outside the root, put a row in the
ledger in the same turn — prose in a manifest is not a filing surface, and AT-118 is a row you could
have written yourself.
