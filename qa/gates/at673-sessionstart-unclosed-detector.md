# GATE — AT-673: the session-start "PASS not closed out" signal is stuck ON

> **Read this before either mechanism below: a partial fix here is worse than no fix.** The hook has
> two defects with one root — nothing in it is anchored to the field it claims to read — and they fail
> in **opposite** directions. `AT-673` over-reports (prose counted as state, so `t182` shows as an
> unclosed PASS forever); `AT-669` under-reports (a prose cycle number silences a manifest that really
> is awaiting a check). Anchoring only the visibly-wrong pattern makes the spurious `1` disappear —
> which removes the one symptom that motivates fixing the silent half. Whichever option you pick, it
> has to cover `:14`, `:16`, `:18` and `:21` together. *(This framing is the checker's; it asked that it
> be the first thing you read, ahead of either row's mechanism, and it is right.)*


**Filed:** 2026-09-28 (maker, tick wave 32) · **Severity:** medium · **Ledger:** `AT-673`
**Why this is a gate and not a fix:** `qa/hooks/*` is an **enforcement path**. Changing it needs a
`docs/DECISIONS.md` entry carrying `Approved-by: Umesh` (project CLAUDE.md, Lab Protocol). The maker
filed the defect and stopped; it did not edit the hook.

## What is wrong, in one paragraph

`qa/hooks/mc-sessionstart.ps1` decides a unit is "PASS not closed out" like this:

```powershell
:14  if (-not (Select-String -Path $m.FullName -Pattern 'Status: ready-for-check' -Quiet)) { continue }
:23  if (Select-String -Path $v -Pattern 'VERDICT:\s*PASS' -Quiet) { $unclosed += $m.BaseName }
```

The manifest (`$m`) is **never re-examined for `checked-PASS`**. The block's own comment at `:8-9`
promises it detects *"a PASS verdict whose manifest was never flipped to checked-PASS"* — the code
contains no flip check. And the gate at `:14` is an **unanchored substring** match, so it fires on the
phrase wherever it appears, including inside a sentence *about* the handshake.

## The measurement (by construction, not by reading)

| | before this tick | after |
|---|---|---|
| hook's `PASS not closed out` | **2** | **1** |

- **The one that was real** — `qa/manifests/at621-exit-call-aliases.md:125` genuinely still read
  `## Status: ready-for-check` while `:127` recorded `checked-PASS … merged c679ad89`. Verified the
  close-out was true before flipping it: verdict `14f13a22` is a real cycle-1 PASS, merge `c679ad89`
  is an ancestor of `HEAD`. The maker flipped the heading. It dropped out of the count.
- **The one that cannot be cleared** — `qa/manifests/t182-viewport-locale.md` is closed out
  **correctly**: heading `## Status` at `:199`, value `checked-PASS (cycle 1, 4c6b7f6)` at `:201`,
  flipped by `fb4f398e`, merged `219c4383`. It is counted anyway, because `:13` says:

  > `` `Status: ready-for-check` is written last ``

  That sentence is **true documentation of the handshake**. It cannot be deleted to satisfy a
  validator, and no close-out action will ever clear the count.

## Why it matters more than one wrong digit

`$unclosed.Count` being non-zero is **by itself** enough to trigger the `AUTO-CONTINUE REQUIRED`
directive (`:39`). So every session in this repo is now told it has pending maker-checker state on
the strength of one prose sentence. **A signal that is stuck ON is a signal that stops being read** —
which is precisely the class this project exists to refuse, and the same class as `AT-656` with the
polarity reversed: there the crude line-regex was *truthful* because it built no index; here the
crude substring match is the *defect*, because it cannot tell a claim from a quotation of a claim.

## Options (the maker picks none)

**A — anchor the gate and add the flip check (recommended).** Gate on `'^##\s*Status'` and read the
value that follows; before counting a unit unclosed, actually test the manifest for a terminal
status, which is what the comment already promises. Smallest change that makes both halves honest.
Cost: one DECISIONS entry with `Approved-by: Umesh`, ~5 lines of PowerShell, plus the C12(b)
construction tests below.

**B — anchor only.** Fixes t182 (its prose stops matching) and leaves the missing flip check. Cheaper,
but the signal still cannot detect the thing it is named after: a manifest whose heading is stale AND
that never mentions the phrase elsewhere is caught, while the comment's promise stays unimplemented.

**C — leave it, and write the false positive down.** Accept "PASS not closed out: 1" as a permanent
floor and teach every reader to subtract one. Cheapest today, and the maker recommends against it:
the count is also what arms `AUTO-CONTINUE REQUIRED`, so the repo loses its only automatic signal
that a real close-out was missed.

**Either way, C12(b) applies to the measurement itself** (as the peer widened it on 2026-09-28 —
*verify by construction, not inspection*): build a manifest that is correctly closed out **and** quotes
the phrase in prose, and assert the hook does **not** count it; build one whose heading is genuinely
stale, and assert it **does**.

## Not in scope of this gate

`AT-656` (id-keyed status collapse in `ledger/checks.py::_status_by_id`) is a different instrument and
a different defect; the two only share the lesson about where an index loses information. Neither is
on `T-122`'s path.

---

## Addendum, 2026-09-28 — the directive has a SECOND unconditional arm (AT-657, checker)

Filed by the checker and verified against the same file: **fixing AT-673 alone does not restore the
signal.** Line 38's condition is an OR over five terms, and one of them is `($sweepAge -gt 120)` —
true on any session opened more than two hours after the last sweep, which is most of them. At the
session start that prompted this gate, the line read `Last sweep: 416 min ago`, so that term was
independently true at the same moment `$unclosed` was.

So `AUTO-CONTINUE REQUIRED` has **no OFF state for two unrelated reasons**, and they must be decided
together. If Umesh approves option A or B for the close-out detector alone, the directive stays
unconditional and nothing observable changes. **This is one gate decision, not two.**

The checker also withdrew a reading of its own before sending it, and it is recorded because the
correction matters: it first took `$n -gt 0` (the open-issue count) to be a third unconditional arm.
It is not — `$n` reaches line 38 only through `$asleep`, which *also* requires a stale tick. The two
genuinely unconditional arms are `$unclosed` and `$sweepAge`.

## Addendum, 2026-09-28 — withdrawal of this gate's disk-urgency framing

The `qa/.last-tick` line for wave 32 said AT-672 was *"degrading ~30 MB/hr … ~11h to zero"*.
**That claim is withdrawn by the maker.** It rested on two spot samples (0.37 then 0.34 GB) read as a
trend. Measured properly on 2026-09-28 with three instruments sampled at the same instants, they
**agree exactly** — `Get-PSDrive` = `Get-CimInstance Win32_LogicalDisk` = `df -h /c` = 9.6–9.77 GB —
and C: free space had gone 0.34 → 2.37 → 6.59 → 9.77 GB inside about twenty minutes. It was rising,
not falling, and the volume churns at GB scale per minute.

The apparent 7x disagreement between the two sessions' figures (0.34 vs 2.373) was therefore **time,
not instrument**. Both numbers were correct when taken.

**The lesson is the same invariant this gate is about, and it caught the maker rather than the code:
a spot sample has no representation for a rate.** Two readings of a churning quantity cannot
distinguish a trend from noise, exactly as `dict[id]` cannot represent two rows and an unanchored
substring cannot represent the difference between a claim and a quotation of a claim.

**What survives, restated honestly:** the ENOSPC hazard is real but it is not a runway — free space
*dips*, and it was observed at 0.34 GB, which is below what a full suite needs. So a suite can still
be poisoned by a transient dip rather than by a march to zero, and an ENOSPC red would be
indistinguishable from a real one on the instrument both the maker and the checker sign verdicts with.
The hold was right; the reason given for it was not.

## Addendum — ledger id block 670–679 is RETIRED, not reserved

The checker flagged that `AT-673` was allocated from the block `qa/QUEUE.md` reserves for
`wave/t191-video-reachable`. Checked: that wave **merged** at `8f577aef` and its remap to 670/671/672
is already on master, so no further ids are coming from it and 673+ were free. Verified `AT-673` is
unique on master. The reservation table should now read the block as retired — the checker's caution
was correct in form, and the block being live is the only thing that made it not a collision.


## Addendum (maker, tick wave 33i) — a proposal to route this fix to the DATA, re-measured

The checker filed `AT-662`/LS6 proposing that the manifests be canonicalised to one status line
each, which would make the hook's existing literal correct without editing an enforcement path, and
would therefore make this gate optional rather than blocking. It reported **eight spellings across
261 manifests**, nine matching none of the common shapes and six carrying more than one.

**261 manifests confirmed. The rest does not survive re-measurement, and the remedy would do damage.**

Counting every line whose start looks like a status field
(`^[-* ]*\**#*\s*Status`), **twelve** files carry more than one, not six — and then almost all of
the multiplicity turns out to be either legitimate or not a status line at all:

- **Cycle history, which the repo is supposed to keep.** `t133:117` and `at206:88` read
  `## Status: superseded by cycle 2` above their `## Status: checked-PASS`; `at576-577:491` reads
  `## Status (cycle 1, superseded by cycle 2 below)` above `:497`. **Canonicalising to one line per
  manifest deletes the superseded record** — in a project whose entire discipline is that history is
  append-only. The remedy is not ours to take as described.
- **Prose that begins with the word.** `t060:83` (*"Status line updated, naming the real remaining
  limit…"*), `ui-settings-providers:63` (*"Status pills genuinely reflect the real `.env`…"*), and
  `at015-at028:121` — where `## Status` is a line of **quoted command output** listing another file's
  headings. None is a status field. This is the same false-positive class as `t182:13`.
- **Agreement, not ambiguity.** `at575` and `at621` each carry two lines that now say the same thing,
  because the maker reconciled them today (`f3a2014b`, `57b1f161`).

**Filtering to lines that genuinely disagree leaves exactly one file: `at438`.** Its `:404` says
`## Status: STALLED — 3 of 3 fix cycles spent` and its `:439` says
`**Status: checked-PASS for U14(b)**`. Even there a reader is not actually stuck, because `:8` states
the resolution — *checked-PASS for U14(b) only, cycle 3 re-ruled under D-048/D-049*. It is ambiguous
to a **matcher** and coherent to a **reader**.

**So the measured state is: no manifest is genuinely unreadable by a human, and the variance is
entirely in whether a pattern can read it.** That inverts LS6's premise. This is not data hygiene
needing a 261-file sweep; it is that the handshake never **declared** which line carries authority,
so every writer chose a defensible shape and every reader wrote its own pattern.

**And LS6 does not clear `t182` either.** `t182`'s false positive comes from `:13`, a **prose**
sentence explaining the handshake — ``handshake — `Status: ready-for-check` is written last)``.
Canonicalising status *fields* does not touch it. Clearing `t182` by editing data means rewriting a
passed manifest's own explanation of the rule so that a grep stops matching it — deleting an
explanation to satisfy a detector. That is the wrong direction whatever it costs to ask.

**What this addendum changes about the question below:** nothing about options A/B/C, and one thing
about urgency. The safe, non-destructive, ours-to-take part of LS6 is *forward-looking*: declare one
authoritative line, let historical and per-cycle lines stay exactly as they are, and let
`autotester doctor` check new manifests against it. That is worth doing and does not need this gate.
What still needs this gate is `t182` and anything else whose match lives in prose — because the only
fix for a detector that reads prose as state is the detector.


## Addendum (maker, tick wave 33j) — two more enforcement-path findings, both verified first-hand

The checker's sweep closed with two findings that belong in **this** conversation rather than their
own, because both are enforcement paths and therefore need `Approved-by: Umesh`. The maker verified
each against the files before putting it in front of him.

### `AT-668` (high) — the guard does not guard the maker-checker hooks

`.claude/hooks/decisions-append-guard.ps1:92-94` decides what counts as an enforcement file:

```powershell
$isEnforcement = ($relL.StartsWith(".claude\hooks\")) -or
                 ($relL -eq "scriptsppend_decision.ps1") -or
                 ($relL -eq ".claude\settings.json")
```

`qa\hooks\` is **not in that list** — and `.claude/settings.json` wires exactly those hooks, at
`:37` (`qa/hooks/mc-sessionstart.ps1`) and `:58` (`qa/hooks/mc-precommit.ps1`). The project
`CLAUDE.md` names `qa/hooks/*` as an enforcement path in policy. **So the policy covers those files
and the mechanism does not:** an edit that widened, weakened or deleted the AUTO-CONTINUE detection
passes with no ask, while the identical edit one directory over is correctly gated. Confirmed by
reading both files; the checker's account is exact.

This is the finding that hides the others. Every other item on this gate is about a detector
reporting the wrong state; this one is about whether a change to a detector gets noticed at all.

### `AT-669` (medium) — the same hook also fails toward SILENCE, and that pairs with the defect above

`qa/hooks/mc-sessionstart.ps1:16-20`:

```powershell
$a = Select-String -Path $m.FullName -Pattern 'Fix cycle[:*\s]+(\d+)' | Select-Object -First 1
$b = Select-String -Path $v -Pattern '(Cycle checked|Fix cycle judged)[:*\s]+(\d+)' | Select-Object -First 1
if ($vc -lt $mc) { $pending += $m.BaseName; continue }
```

Neither pattern is anchored to a field, and each takes the **first** match in the document. A prose
line mentioning a cycle number ahead of the real field therefore sets `$mc` too low (or `$vc` too
high), `$vc -lt $mc` comes out false, and a manifest genuinely awaiting a check is **not reported**.
AUTO-CONTINUE never fires for it.

**Stated honestly: this is reachable by construction and is not firing today.** The block is gated at
`:14` on the literal `Status: ready-for-check`, and only one manifest in 261 matches that literal —
`t182`, via prose. So the hook currently has exactly one file flowing through this code, and that
file is the *other* defect.

**Why the pairing is the point, and why fixing one is worse than fixing neither.** The same hook
over-reports in one direction (`AT-673`: prose read as state, `t182` counted forever) and
under-reports in the other (`AT-669`: prose read as a cycle number, real pending state silenced).
They share a single root — **no pattern in this hook is anchored to the field it claims to read** —
and they fail in opposite directions. Anyone asked to "fix the hook" will naturally anchor the
pattern that is visibly wrong, see the spurious `1` disappear, and ship with the silent direction
intact. **Option B below (anchor the patterns) must anchor all of them, `:14`, `:16`, `:18` and `:21`,
or it fixes the noise and keeps the silence.**

That is the seventh instance today of one instrument, two states, one representation — and the first
where the two halves of the pair point opposite ways in the same file.


## Addendum (maker, tick wave 33p) — `AT-696`: the same hook, both directions, in ONE printed line

The headline at the top of this gate said a partial fix is worse than none, because the hook
over-reports in one place and under-reports in another. That was two defects in two predicates.
**It is now demonstrated in a single line of the hook's own output**, and the maker verified it
first-hand:

```
git ls-files qa/manifests/ | grep -i 570      ->  nothing
grep -c worktree qa/hooks/mc-sessionstart.ps1 ->  0
mc-sessionstart.ps1:11-12                     ->  Get-ChildItem 'qa/manifests'   (current checkout)
```

The at570 manifest exists only at
`.claude/worktrees/agent-ac0c11769db9a7239/qa/manifests/at570-live-case-approval.md`, with
`**Fix cycle:** 1 of max 3` at `:22` and `## Status: ready-for-check` at `:424`. It is genuinely
awaiting a check right now. The hook prints:

| printed | reality | direction |
|---|---|---|
| `PASS not closed out: 1` | that is `t182`, whose match is **prose** explaining the handshake | false positive — fails toward **alarm** |
| `Checks pending: 0` | at570 is pending and has been for an hour | false negative — fails toward **silence** |

**Both numbers in one line, both wrong, in opposite directions.**

**This one is not the pattern problem, and that is why it is here.** `## Status: ready-for-check`
would satisfy the substring test at `:14` perfectly — the file simply is not in the directory being
enumerated. **So no amount of anchoring the patterns (option B) touches it.** It is also distinct
from `AT-643`, which is about finished but unjudged *commits* sitting in worktrees; this is the
ready-for-check *signal*, one step earlier in the handshake.

**Why it matters more than a miscount.** Today the loop survives this because the maker dispatches
its own checker straight at the worktree, so the invisible pending state has a live owner. That is a
property of *a maker being alive*, not of the mechanism. The hook exists precisely for the case
where one is not — and in that case it reports `Checks pending: 0` and a session starts on something
else. That is the `AT-641` scenario, and it has already happened once in this project.

**Direction only, not a fix — and a correction to what an earlier version of this addendum said.**
It claimed "one change to this hook answers `AT-673`, `AT-669`, `AT-696` and `AT-643`." **That was
wrong, and it contradicted a sentence two paragraphs above it** — the same addendum had just
explained that anchoring the patterns does not touch `AT-696` at all. Both cannot be true. The
checker caught it before this reached you. It is **one file and one decision, but three changes at
three sites**, and the row sets are disjoint:

| site | what is there now | rows it answers |
|---|---|---|
| `:11-12` | `Get-ChildItem 'qa/manifests'` — the current checkout only | `AT-696`, `AT-643` — **enumeration** |
| `:14, :16, :18, :21` | `'Status: ready-for-check'` unanchored; `Fix cycle` / `Cycle checked` / `VERDICT:\s*PASS` taken as first match | `AT-673`, `AT-669` — **anchoring** |
| `:30, :38` | the `$backlog` / `$asleep` arming condition and the directive it emits | `AT-657` — **the arming condition** |

**This makes the warning at the top of this gate stronger, not weaker.** With three sites, a partial
landing is *more* likely than with one, and each partial leaves a different thing broken:

- **Anchoring alone** leaves the hook **silent** on any manifest living in a worktree — which is
  where every in-flight unit's manifest lives.
- **Enumeration alone** leaves the `t182` **false alarm**, and therefore leaves `AT-657` armed
  forever, because `$unclosed.Count` is one of its two permanently-true terms.

So an approval of the form *"fix the hook"* is not enough on its own; the answer needs to cover all
three sites, or say explicitly which ones it covers. `AT-668` is the reason none of them can be made
without you at all, since the guard that should ask before a `qa/hooks/*` edit does not cover
`qa/hooks/*`. **That is the fourth reason this is one conversation rather than five.**

*(The `ready-for-check` pattern is at `:14`. Both sessions wrote `:13` earlier today; the substantive
claim — that `:11-12` is the enumeration and the pattern would match fine if the file were
enumerated — is unaffected.)*
