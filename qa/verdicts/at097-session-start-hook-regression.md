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
