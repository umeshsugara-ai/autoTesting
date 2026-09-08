# Verdict — at097-session-start-hook-regression

**Date:** 2026-09-08
**Cycle checked:** 1
**Unit:** commit `b9fa94b` (closes AT-097 high, AT-029 medium; authorized by D-019)
**Contract:** `qa/contracts/core-invariants.md` + the Lab Protocol section of `CLAUDE.md`
**Bound to:** `d:/autoTesting`
**Mode:** A (unit check), fresh context, read-only toward the artifact

```
VERDICT: FAIL
SCOREBOARD: 5/6 criteria met, 3/3 invariants hold
```

---

## Part 1 — the approval question: the maker's reasoning HOLDS

I was asked to judge this adversarially and not to wave it through. I read D-008, D-010, D-011,
D-013 and D-019 myself. **The reasoning holds on all three sub-questions.** This is *not* where
the unit fails.

### (a) Do D-008 and D-010 authorize these exact two values? — YES

- **D-008** (ACTIVE, `Approved-by: Umesh` — batch answer "Yes, approve both", 2026-09-03).
  `Changes-authorized:` `.claude/hooks/lab-session-start.ps1` (ARCHITECTURE excerpt filter only).
  Its `Result` names the change from the inclusion allowlist `^## (1|2|3|6)[\.\s]` to *exclusion of
  the one generated section*. That is exactly the filter now on disk.
- **D-010** (ACTIVE, `Approved-by: Umesh`) authorizes the cap `-ge 100` → `-ge 150` and the label
  text, naming the specific line. **D-011** (ACTIVE) then supplies the *verbatim, cap-specific,
  fresh* approval exchange — Question: "Approve this specific cap change?" → Answer: **"Yes,
  approve the cap change."**

Both values are named, both entries are ACTIVE, both carry Umesh's approval. Confirmed by reading
the entries, not the manifest's summary of them.

**The strongest counter-argument, which I checked and rejected:** this repo's own checker has
already FAILED a unit twice (AT-030, AT-031) precisely for treating an earlier batch approval as
covering a change by extension. That precedent is *satisfied* here, not violated — it demanded that
the authorization **name the specific change** rather than be assumed. D-008 names the filter;
D-011 names the cap verbatim. D-019 is not stretching an approval onto a value Umesh never saw; it
points at approvals of these exact values.

### (b) Was 051303e's revert unintended, or does D-013 legitimately supersede? — UNINTENDED

D-013's own text disclaims the effect:

- **What:** "JSON output is now ASCII-escaped before it is written. **Behaviour otherwise
  unchanged.**" — false as executed.
- **Why:** entirely about OEM-codepage `0x1a` bytes breaking the JSON payload. Not one word about
  the excerpt filter or the cap.
- **Result:** "The session-start snapshot and the append-guard reply are accepted as JSON." Nothing
  about ground-truth content.
- No `Supersedes:` line for D-008 or D-010.

Nowhere does D-013 argue that the numbered-heading allowlist is *desirable* — an allowlist D-008
had already proven matches zero headings in this repo. Reading D-013 as a legitimate supersession
would mean Umesh knowingly approved re-breaking a bug he had approved fixing twice, inside an entry
that tells him behaviour is unchanged. An approval cannot silently carry authority that its own
text disclaims. The `byte-identical to the AIOS template` clause in `Changes-authorized` is the
mechanism by which the revert happened, not evidence that the revert was the decision.

**Therefore restoring D-008/D-010's values creates no new authority and needs no fresh human gate.**

### (c) Was declining `Supersedes: D-013` correct? — YES

The `Supersedes` primitive in this repo is **entry-level and machine-consumed**: I read
`lab-session-start.ps1:137-142`, which computes `SUPERSEDED (by D-NNN)` into the decision index
injected at every session start. Marking D-013 SUPERSEDED would print, in every future session,
that a live and load-bearing ASCII-escaping fix is discardable. There is no partial-supersession
primitive, and D-013 cannot be edited (append-only).

This repo also already has the correct, checker-endorsed pattern for exactly this: **D-011** narrows
and corrects D-010's authorization record while stating "D-010 itself is never edited" and "is NOT
re-litigated" — with no `Supersedes` line. D-019 follows that precedent, states the narrowing
explicitly in both `What` and `Why`, and links D-013. **The protocol does not require the line
here.**

**One accuracy note (not a failure):** D-019's claim that it "creates NO new authority" is slightly
overstated. Its item (4) — the standing policy that this file is *deliberately not* byte-identical
to the AIOS template — narrows a clause of D-013's `Changes-authorized` that Umesh did approve.
That is a small new policy, not covered by D-008/D-010. It is documented prominently and was
flagged to Umesh in the tick report, so it is a wording note, not a violation.

---

## Part 2 — the substance: the fix changes code the hook never executes

**The unit FAILS here, and it fails hard.**

### The finding

`.claude/hooks/lab-session-start.ps1:118` reads:

```powershell
$archPath = Join-Path $root "ARCHITECTURE.md"
```

`$root` is the repo root (`D:\autoTesting`, resolved by the `.git` walk at lines 40-48 — I checked).
**This repo's architecture document lives at `docs/ARCHITECTURE.md`.** The same hook correctly uses
`docs\DECISIONS.md` (line 50) and `docs\archive\INDEX.md` (line 145) — only this one path omits
`docs\`.

There is no root `ARCHITECTURE.md`, and there never has been:

```
$ ls ARCHITECTURE.md            → No such file or directory
$ git log --all --diff-filter=A -- ARCHITECTURE.md
(empty — never added in this repo's entire history)
$ git log --oneline --diff-filter=A -- docs/ARCHITECTURE.md
a5ffcec P0: design lock — schema, core, provider seam, enforcement
```

So `Test-Path -LiteralPath $archPath` is `$false` and the hook takes the **`else`** branch. The
whole filter block — the code D-008, D-010 and now D-019 have changed three times — **has never
executed once.**

### Proof: I ran the live hook, post-fix

```
$ powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/lab-session-start.ps1
root line     : === LAB PROTOCOL ACTIVE (root: D:\autoTesting) ===
label present : False        # no "--- ARCHITECTURE.md (all sections except ...) ---"
WARN present  : True         # "[WARN] ARCHITECTURE.md missing at repo root -- ... Run /init-lab repair."
arch headings injected: 0
root ARCHITECTURE.md exists: False
```

**Zero lines of architecture ground truth reach the session, after the fix.**

### What this means for the two issues this unit claims to close

- **AT-097** — the record/disk divergence is repaired and D-019 is a correct authorizing entry. But
  the defect the row is *about* — "every session start injects an empty ground-truth block" — is
  **not fixed**. It stays `open`.
- **AT-029** — "the cap fires before Design rules / Commands / Status." Those sections still do not
  reach the session; nothing does. **Not fixed.** Stays `open`.
- The manifest's "Design rules, Commands and Status now reach the session" and D-019's Result "the
  session-start hook injects real ground truth again" are both **false as executed**.
- The bisection narrative is also wrong about *impact*: the block was empty during the
  "authorized fix" window (`f9e3456`) too, and during `5f83bdb` before it — not "since 2026-09-05".
  The path has never resolved.

### The tests reproduce the exact flaw the maker claims to have eliminated

`tests/test_session_start_hook.py:22`:

```python
ARCHITECTURE = REPO / "docs" / "ARCHITECTURE.md"
```

The tests parse the **excluded-heading pattern** and the **cap** out of the live `.ps1` — that part
is genuine and I verified it works (below). But the **path is hardcoded**, so `apply_filter` runs
the real filter against a file the hook never opens. All 6 tests pass while the live hook injects
nothing. `test_the_excerpt_is_not_effectively_empty` asserts `len(kept) > 100` and passes at 140,
while the actual injected excerpt is **0 lines plus a WARN**.

This is the maker's own stated failure mode — "quietly simulating a filter the hook no longer
contains" — surviving one axis over: simulating a *file* the hook never reads. It is what let this
unit reach `ready-for-check` believing itself green.

---

## Part 3 — what I re-ran and re-derived myself

### 1. Manifest verify commands (re-run, not trusted)

| Command | Manifest claim | My result |
|---|---|---|
| `docker compose exec -T autotester uv run pytest -q` | 555 passed, 1 skipped | **matches** — 556 collected, 1 `s`, exit 0 |
| `docker compose exec -T autotester uv run ruff check src tests scripts` | `All checks passed!` | **matches**, exit 0 |
| `docker compose exec -T autotester uv run autotester doctor` | `doctor: clean` | **matches**, exit 0 |

(`docker compose exec` is this project's established convention for the adapter's slot-1 commands —
consistent with at053/at054 and other manifests. Not a mismatch.)

### 2. My own filter probe — old vs repaired, hand-written, not the maker's

Hand-written PowerShell reimplementing each version's loop verbatim from the two blobs, executed
against the real `docs/ARCHITECTURE.md` (150 lines, 11 `## ` headings):

```
OLD filter (051303e / D-013 state, cap 100): kept 1 line, 0 '## ' headings
   |# AutoTester — architecture
NEW filter (b9fa94b / D-019 state, cap 150): kept 140 lines, 10 '## ' headings
   |# AutoTester — architecture
   |## What it does          |## Pipeline              |## Concept → file
   |## Data model            |## Execution model       |## Security
   |## Storage               |## Design rules          |## Commands
   |## Status
```

**The "1 line" and "140 lines / 10 headings" claims are both accurate** — as statements about the
filter. They are not statements about the hook, because the hook never reaches this code.

### 3. Sabotage — I re-applied 051303e's exact revert

Restored the file to `b9fa94b^` (verified byte-exact: `git diff b9fa94b^ -- <file>` empty), ran the
suite, then restored via `git checkout --` and re-confirmed a clean tree.

```
FAILED test_the_numbered_heading_filter_is_not_back
FAILED test_the_excerpt_cap_is_the_authorized_one
FAILED test_every_named_section_survives_the_filter
FAILED test_the_generated_directory_map_is_the_only_thing_dropped
FAILED test_the_excerpt_is_not_effectively_empty
→ 5 of 6 failed; after restore, 6 passed.
```

**Confirmed: 5 of 6, exactly as claimed.** And the committed version *is* genuinely the stronger
one — the parse-driven design is real. `excluded_pattern()`'s `_FILTER_RE` failed to match under
sabotage and took the three behavioural tests down with it (error message: *"Live code line was:
`$inKeep = $false`"*), rather than letting them pass against a hardcoded constant. The maker's
account of its own weaker first attempt (2/6) is credible and the correction is verified.

**The strength stops at the path.** The pattern and the cap are parsed from the `.ps1`; the file
the filter is applied to is not.

### 4. D-013's ASCII-escaping half — UNTOUCHED ✓

`lab-session-start.ps1:191` still carries the full escaper:
`[regex]::Replace($_, "[^\x00-\x7F]", { ... "\u{0:x4}" ... })` with its 2026-09-05 comment. It is
outside the diff hunks entirely. Confirmed.

### 5. Nothing else in the hooks directory changed ✓

```
$ git diff --stat 051303e HEAD -- .claude/hooks/
 .claude/hooks/lab-session-start.ps1 | 14 ++++++++++----
 1 file changed, 10 insertions(+), 4 deletions(-)
```

One file, and the commit's own `--name-only` under `.claude/hooks/` lists only that file. The 10/4
matches the shown diff exactly, so there are no unlisted edits. `decisions-append-guard.ps1` and
every other hook are byte-identical to their 051303e state.

---

## FAILURES

```
- [Issues-addressed] sev: high · The unit does not fix AT-097's or AT-029's actual defect. The hook
  reads `Join-Path $root "ARCHITECTURE.md"` (line 118) but the file is at `docs/ARCHITECTURE.md`;
  a root copy has never existed in this repo's history, so the repaired filter block is unreachable
  and the live hook emits "[WARN] ARCHITECTURE.md missing at repo root" with zero architecture
  lines injected. Verified by executing the committed hook. · Fix direction: correct the path to
  `docs\ARCHITECTURE.md` — but this is an enforcement path and the path value is NOT covered by
  D-008/D-010/D-019, so it needs its own authorizing entry with a fresh Approved-by. · issue: AT-106

- [C7-adjacent] sev: high · tests/test_session_start_hook.py:22 hardcodes
  `ARCHITECTURE = REPO / "docs" / "ARCHITECTURE.md"` instead of parsing the path out of the .ps1
  like it does the pattern and the cap, so all 6 tests pass green while the hook injects nothing.
  This is the maker's own "simulating a fiction" failure mode, one axis over, and it is what let
  the unit reach ready-for-check. · Fix direction: parse the `Join-Path $root "<...>"` argument out
  of the hook and resolve it, so a wrong path fails the suite; add one test asserting the live
  hook's output actually contains the ARCHITECTURE label and >100 lines. · issue: AT-107
```

**ISSUES-WRITTEN:** AT-106, AT-107
**ISSUES KEPT OPEN (claimed fixed, not fixed):** AT-097, AT-029

---

## HUMAN_GATE

**Question for Umesh — asked once, answer written to disk:**

> The session-start hook has been injecting an empty ARCHITECTURE ground-truth block since this
> repo's genesis commit — not since 2026-09-05. The filter that D-008, D-010 and D-019 all fixed
> has never run, because `lab-session-start.ps1:118` looks for `ARCHITECTURE.md` at the repo root
> while this project keeps it at `docs/ARCHITECTURE.md`. Which fix do you approve?
>
> **(A)** Change the hook to `Join-Path $root "docs\ARCHITECTURE.md"` — one line, matches how the
> same hook already resolves `docs\DECISIONS.md`, keeps the repo root clean per C4. Diverges
> further from the AIOS Lab template (already recorded as deliberate by D-019 item 4).
>
> **(B)** Keep the hook aligned with the template and put an `ARCHITECTURE.md` at the repo root —
> requires adding it to `doctor`'s `ALLOWED_ROOT_ENTRIES` and creates a second copy or a link,
> which cuts against C3 (one concept, one place).
>
> Either way the change is to an enforcement path, so it needs its own DECISIONS entry with
> `Approved-by: Umesh`. **This gate is about the remaining fix only — it is not a retroactive
> approval request for D-019, whose reasoning I judged sound above.**

---

## EXPLANATION

The approval judgement the maker asked me to make is **sound and I uphold it**: D-008 and D-010
(with D-011's verbatim exchange) authorize precisely the filter and the cap that were restored;
D-013's revert was a side effect its own text disclaims rather than a decision that supersedes
them; and declining `Supersedes: D-013` was right, because the supersession marker is computed into
every session's decision index and would misreport a live ASCII-escaping fix — with D-011 standing
as this repo's own precedent for partial correction without supersession. No HUMAN_GATE is owed on
that.

The unit nonetheless fails on substance. The hook looks for `ARCHITECTURE.md` at the repo root
while the file lives in `docs/`, so the filter block that four DECISIONS entries have now argued
about has never executed; the live hook emits a `[WARN]` and injects zero lines of ground truth.
Everything the manifest claims about the filter is true and reproducible, and the sabotage really
does fail 5 of 6 — but all of it measures a code path the hook does not enter, because the tests
parse the pattern and the cap out of the `.ps1` and then hardcode the one thing that was wrong. The
verify commands all reproduce exactly (555 passed / 1 skipped, ruff clean, doctor clean), D-013's
ASCII escaping is untouched, and no other hook changed.

---
---

# Verdict — at097-session-start-hook-regression (CYCLE 2)

**Date:** 2026-09-08
**Cycle checked: 2**
**Unit:** commits `b9fa94b` + `afddb87` + `5d99520` (closes AT-097 high, AT-029 medium, AT-106 high,
AT-107 high; authorized by D-019 + D-020)
**Contract:** `qa/contracts/core-invariants.md` + the Lab Protocol section of `CLAUDE.md`
**Bound to:** `d:/autoTesting`
**Mode:** A (unit check), fresh context, read-only toward the artifact

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met, 4/4 invariants hold
```

The cycle-1 FAIL is answered on its own terms: the defect it found — a repaired filter sitting in
code the hook never entered — is fixed, and I confirmed it by running the hook, not by reading the
diff.

---

## 1 — The authorization: HOLDS, and it was gated rather than stretched

**`qa/gates/at106-hook-architecture-path.md`** carries `Status: ANSWERED` and the line:

> **Answered:** 2026-09-08 — **Option 1, approve the one-line path fix** — Umesh, directly in the
> session via an AskUserQuestion presenting all three options with the two-line diff. Recorded here
> before any file was touched, per the gate-record rule. Authorizing entry: **D-020**.

**Ordering, stated precisely rather than generously.** The gate file was created OPEN in `afddb87`
(2026-09-08 01:13:03) — 5h27m before the fix commit `5d99520` (06:40:41). So the question existed on
disk, unanswered, for the whole interval between the cycle-1 FAIL and the change: the maker did not
act first and paper over it afterwards. What git *cannot* independently prove is the ordering
*within* `5d99520`, because the `Answered:` line, D-020 and the code edit all land in that one
commit. I record that as a limitation of the evidence, not as a finding — the protocol requirement
is that the gate be raised before acting and answered by the Approver, and both are satisfied.
(A strictly stronger habit for next time: commit the `Answered:` line by itself, then the change.)

**D-020 exists, is its own entry, and does not stretch an approval.** Verified by reading it in
`docs/DECISIONS.md`, and by confirming the diff to that file in `5d99520` is **additions only**
(8 added lines, 0 removed — the append-only rule holds; no existing entry was touched):

- `**Approved-by:** Umesh -- asked directly 2026-09-08 via an AskUserQuestion presenting three
  options … he chose the path fix.`
- `**Changes-authorized:** .claude/hooks/lab-session-start.ps1 (the $archPath value only; the D-013
  ASCII-escaping and the D-008/D-010 filter and cap are untouched); tests/test_session_start_hook.py.`

That `Changes-authorized` is **narrower than the change is broad** — it names the single value and
excludes the two neighbouring authorized behaviours by name. I checked the actual enforcement-path
diff against it:

```
$ git diff --stat 051303e HEAD -- .claude/hooks/ qa/hooks/ scripts/append_decision.ps1 .claude/settings.json
 .claude/hooks/lab-session-start.ps1 | 18 ++++++++++++------
 1 file changed, 12 insertions(+), 6 deletions(-)
```

One enforcement file, and within `5d99520` exactly two lines of it: `$archPath` and the `[WARN]`
text. Nothing in the authorization is stretched, and D-019 was correctly **not** extended — which is
the move this repo has failed two checks (AT-030, AT-031) for. This was the one thing cycle 1 asked
the maker to get right and it got it right.

---

## 2 — The fix works. I ran the real hook, before and after.

Per AT-101 I did **not** stash or check out anything in the live tree. I extracted the pre-fix hook
with `git show b9fa94b:.claude/hooks/lab-session-start.ps1` to `.work/checkprobe/` (inside the repo,
because the hook's AMD-3 guard makes a copy outside the root exit silently — a probe run from a temp
dir would have produced a false "0 lines" for the wrong reason), and drove both with a real
SessionStart payload.

| | BEFORE (`b9fa94b`) | AFTER (`HEAD`) |
|---|---|---|
| total lines in `additionalContext` | **53** | **193** |
| real `[WARN]` line | **present** — `[WARN] ARCHITECTURE.md missing at repo root -- protocol expects it. Run /init-lab repair.` | **none** |
| `--- ARCHITECTURE.md (...) ---` label | absent | present |
| architecture headings injected | **0** | **10** |

The 10, verbatim from my run: What it does · Pipeline · Concept → file (one concept, one place) ·
Data model (the core five) · Execution model · Security (non-negotiable) · Storage · Design rules
(enforced by `autotester doctor`) · Commands · Status. The generated `## Directory map and schema
summary` is the only `## ` section dropped, which is exactly D-008's rule.

**The manifest's 0 → 10 and "no [WARN]" claims reproduce.** One honest note on the maker's own
numbers: the only string matching `[WARN]` in the AFTER output is inside the injected *text of
D-020 itself*, quoting the old warning. The maker reported "actual [WARN] lines: none", which is the
correct reading; I confirm there is no emitted warning line. (Line totals differ by one from the
manifest's 52/193 — a trailing-newline split artefact of my probe, not a discrepancy in substance.)

Design rules, Commands and Status reach a session for the first time in this repo's history. That is
AT-029's half, and unlike cycle 1 it is now a statement about the hook rather than about a filter.

---

## 3 — The test is no longer vacuous, and the strict xfail is genuinely gone

`tests/test_session_start_hook.py` now parses **all three** load-bearing values out of the live
`.ps1` — nothing about the hook is hardcoded any more: the excluded-heading pattern (`_FILTER_RE`),
the cap (`_CAP_RE`), and now the architecture path (`_ARCHPATH_RE`, matching
`$archPath = Join-Path $root "..."`).

`architecture_path_from_hook()` resolves the parsed value, and
`test_the_hook_reads_the_file_the_project_actually_has` asserts both that it **exists** and that it
**equals** the project's `docs/ARCHITECTURE.md` — so the hardcoded `ARCHITECTURE` constant the other
tests use is pinned to the hook's real path by a live assertion instead of by hope. That is the
correct repair of AT-107.

**The xfail was removed, not relaxed and not deleted with its assertion.** The diff in `5d99520`
drops the whole `@pytest.mark.xfail(strict=True, reason="AT-106: ...")` decorator (and the now-unused
`import pytest` with it), keeps the test, and turns its single
`assert architecture_path_from_hook().exists()` into two asserts — existence *and* identity with the
project's file. The decorator is gone, the test remains, and its assertion got **stronger**.
`grep -n "xfail" tests/test_session_start_hook.py` returns only prose in docstrings, and the full
suite run shows no `x` in the progress line, so no xfail of any strictness survives.

### Sabotage — I reverted the path myself, in isolation

I built an isolated copy under `.work/checkprobe/sab/` (hook + `docs/ARCHITECTURE.md` + the test
file, `REPO` resolving to that copy) and re-applied the exact defect —
`Join-Path $root "docs\ARCHITECTURE.md"` back to `Join-Path $root "ARCHITECTURE.md"`. **The live
tree was never modified** (`git status --porcelain` showed only the pre-existing `.goal/` churn
throughout).

```
$ python -m pytest tests/test_session_start_hook.py -q      # sabotaged copy
F......                                                                  [100%]
FAILED test_the_hook_reads_the_file_the_project_actually_has
E   AssertionError: the hook opens ...\sab\ARCHITECTURE.md, which does not exist

$ python -m pytest tests/test_session_start_hook.py -q      # unsabotaged copy of HEAD
.......                                                                  [100%]
```

**Confirmed: the path defect now fails the suite, and it did not before.** Under `b9fa94b` this same
sabotage was a no-op — all six tests passed while the hook injected nothing. That gap is closed.

---

## 4 — Nothing else regressed

- **D-013's ASCII escaping — untouched.** `lab-session-start.ps1:191` still carries
  `[regex]::Replace($_, "[^\x00-\x7F]", { ... "\u{0:x4}" ... })` with its 2026-09-05 comment, outside
  every diff hunk.
- **D-008's filter — in place.** Line 125: `$inKeep = ($line -notmatch '^## Directory map and schema summary')`.
- **D-010's cap — in place.** Line 128: `if ($keep.Count -ge 150) { ... "capped at 150 lines" ... }`.
- **No other enforcement path touched** — the `--stat` above covers `.claude/hooks/`, `qa/hooks/`,
  `scripts/append_decision.ps1` and `.claude/settings.json`; one file, one line changed in this cycle.
- **Verify commands, re-run by me, not trusted from the manifest:**

| Command | Manifest claim | My result |
|---|---|---|
| `docker compose exec -T autotester uv run pytest -q` | 560 passed, 1 skipped | **matches** — 561 collected, one `s`, exit 0, no `x`/`F` |
| `docker compose exec -T autotester uv run ruff check src tests scripts` | `All checks passed!` | **matches**, exit 0 |
| `docker compose exec -T autotester uv run autotester doctor` | `doctor: clean` | **matches**, exit 0 |

`doctor: clean` carries C2 (file/function caps, `docs/ARCHITECTURE.md` ≤ 150 lines — it is exactly
150), C3 (duplicate-concept + drift filenames) and C4 (root stays clean; my probe artefacts went to
gitignored `.work/`, which is where C4 says they belong).

---

## 5 — Issues

| Issue | Verdict |
|---|---|
| **AT-097** (high) | **CLOSABLE → fixed.** Both halves are now real: the record/disk divergence is repaired under D-019, and the ground-truth block actually reaches the session (0 → 10 headings, verified by running the hook). |
| **AT-029** (medium) | **CLOSABLE → fixed.** Design rules, Commands and Status are present in the injected excerpt; the 150 cap does not truncate before them (140 kept of 150 allowed). |
| **AT-106** (high) | **CLOSABLE → fixed.** Path corrected under its own gate + D-020; the else-branch `[WARN]` no longer fires. |
| **AT-107** (high) | **CLOSABLE → fixed.** The path is parsed from the `.ps1` and pinned by a live assertion; sabotage now fails the suite. |

Ledger rows moved `open → fixed` with today's date; `verified` is left for a later sweep per the
usual rule.

**ISSUES-WRITTEN:** none (no new findings).

---

## Observations — recorded, deliberately NOT failures

Neither of these meets the >80 % bar for a FAILURE line, and neither should burn a fix cycle.

1. **`5d99520` bundles an enforcement-path change with an unrelated unit's product code**
   (`stages/explore.py`, `ui/crawl_view.py`, `ui/routes_crawls.py` for AT-104/AT-098). The
   enforcement diff inside it is exactly the two authorized lines, so nothing is smuggled and D-020
   is not exceeded — but a change to `.claude/hooks/` is the one category where a reviewer most
   wants an isolated commit, and this one has to be read past three other issues to be seen. Worth a
   habit, not an issue. (The AT-104/AT-098 half is another checker's unit; I judged none of it.)
2. **Still no feature contract governs the hook itself** — the manifest flagged this in cycle 1 and
   it is correct. `tests/test_session_start_hook.py` is now doing that job well enough that I would
   not manufacture a contract just to have one; noting it so it stays visible rather than forgotten.

---

## EXPLANATION

The cycle-1 FAIL said the fix was to dead code, and the maker's response is the right shape: it did
not extend D-019 to cover the path, it raised a gate, got Umesh's answer, wrote it to disk, and
authorized the change with its own narrowly-scoped D-020 whose `Changes-authorized` explicitly
excludes the neighbouring approved behaviours. I re-derived the substance rather than reading the
diff: running the real hook from an extracted `b9fa94b` copy and from HEAD gives 0 architecture
headings with a live `[WARN]` before and 10 headings with no warning after, so the ground-truth block
this repo has argued about across four DECISIONS entries is finally reaching a session. The AT-107
repair is genuine — the architecture path is now parsed out of the `.ps1` alongside the filter and
the cap, the strict xfail is deleted with its assertion strengthened rather than weakened, and
sabotaging the path back to the repo root fails the suite in an isolated copy where it previously
passed. D-013's ASCII escaper, D-008's filter and D-010's cap are all untouched, no other
enforcement path changed, and pytest (560 passed / 1 skipped), ruff and doctor all reproduce clean.
AT-097, AT-029, AT-106 and AT-107 all close.
