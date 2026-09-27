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
