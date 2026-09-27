# GATE — AT-673: the session-start "PASS not closed out" signal is stuck ON

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
