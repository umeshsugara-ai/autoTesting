# GATE — AT-673: the session-start hook seam has hit its round cap on the 4th visit

**Filed:** 2026-09-28 (maker) · **Severity:** high · **Rule:** D-014 round cap (AIOS delivery gate)
**Blocks:** cycle 2 of `at673-sessionstart-unclosed-detector` — i.e. the fixes for AT-713, AT-714
and AT-715, which are all correct and all currently unfixed by deliberate choice.
**Does not block:** the cycle-1 check already in flight. A round-1 verdict is information either way.

## The question in one line

The session-start hook seam has 3 prior PASSes and a non-security cap of 2. Do we accept this
fourth round and close it, or withdraw the unit and take its findings as *file-don't-fix*?

## Why this reached you instead of being decided here

The rule offers three ways past the cap, and two of them are honestly unavailable:

- **(a) Security class** — the cap never applies to tenancy, auth, cross-tenant reads, data writes
  or credential handling. This hook prints a directive and reads manifest/verdict/ledger state. It
  is an **enforcement path**, which is adjacent to that class and is not in it. Stretching
  "enforcement path" into "security class" to escape a cap is exactly the rationalisation the cap
  exists to stop, so I am not making that claim.
- **(b) A waiver** authorized by a DECISIONS entry carrying `Approved-by` — no such entry exists,
  and the append is classifier-blocked for both the maker and the checker seat. I have not
  attempted it and will not route around it.
- **(c) Withdraw and file the finding** — taken, pending your answer.

## The evidence, which argues FOR the cap rather than for an exception

Four visits: `at097-session-start-hook-regression`, `at383-sessionstart-loop-status`,
`t005-living-ledger`, and this unit. Inside this one unit alone the seam produced four defects:

| Defect | Found by | What it was |
|---|---|---|
| Anchored `^## Status:` read | me, by measuring | would have silently skipped ~37 of 263 manifests — worse than the bug it fixed |
| `Fix cycle` pattern | me, by measuring | broke on `**Fix cycle:** 2` (colon inside the bold), producing a false pending row |
| AT-713 | checker | last-wins is an LS6 rule about **manifests**; verdicts order history the opposite way, so one file in 280 reads its cycle as 1 when it is 2 |
| AT-714 | checker | the cycle boundary admits a bare space, so an unquoted prose mention counts — a sweep table cell returns 3 |

A seam that yields four defects while being fixed once is the shape this cap is named for. My own
instinct was to open cycle 2 and fix all three residuals; the count says that instinct is the
problem, not the backlog.

## What is true about the current state, so the choice is made on facts

- Cycle 1 is built, committed (`ed26fb16`, suite line at `a30ff712`), and the full suite is green:
  2172 passed, 6 skipped, 14 xfailed, exit 0, unpiped.
- It is a **real** fix: the old read flagged `t182-viewport-locale` (whose manifest merely keeps
  superseded history) and missed `at483-orphaned-running-crawl` (a real cycle-2 PASS never flipped).
  The count stayed 1→1; the set inverted.
- AT-713/714/715 are **open and attributed**, not hidden. AT-713 and AT-714 both resolve to one
  change — read `max` instead of `last`, and drop the bare-whitespace alternative — which is small,
  but small is not the same as free on a capped seam.
- The enforcement-path authorization is still missing and still disclosed.

## The options

- **(A) Accept round 4 and close.** The unit stands as built, AT-713/714/715 stay open as filed
  debt against a capped seam, and nobody edits this hook again without a waiver. Cheapest today;
  leaves a known-wrong cycle read on one verdict file in 280.
- **(B) Accept round 4 AND authorize one bounded cycle 2** for AT-713/714 only (the `max` fix), via
  a DECISIONS entry with `Approved-by`. Costs the entry — which is currently classifier-blocked, so
  it needs your hand, not mine. Leaves the seam correct.
- **(C) Withdraw the unit**, revert `ed26fb16`, and file the whole thing as *file-don't-fix*. Most
  faithful to the cap. Costs a real, verified fix and returns the hook to over-reporting `t182`
  forever while missing genuine dangling handshakes.

I recommend **(B)** and note the conflict of interest in recommending it: it is also the option
that lets my own work stand and be finished. (A) is the defensible default if you would rather not
spend a decision entry on a hook.

## Answer

<!-- Append one line here when answered:
Answered: <ISO date> — <A|B|C> — <where> -->
