# Contract — loop-status (is the maker-checker loop alive?)

**Status:** ACTIVE (authored by /checker 2026-09-26 under D-047). LS1, LS2 and LS4 describe behaviour already shipped and tested. LS3's pinning test shipped with unit at610-strict-out-of-order-pin (checked-PASS, merged 11f1d4ea/37aaa375).
**Feature:** `autotester loop-status [--strict] [--hours N]` reads `qa/.last-tick` read-only. It enumerates the gaps, classifies each one (explained by `qa/.paused`, or SLEEP), and reports anomalies in the log.
**Code:** `src/autotester/loop_status.py` (logic plus `report_lines`) · `src/autotester/cli_loop.py` (the terminal only).
**Tests:** `tests/test_loop_status.py`, `tests/test_loop_status_integrity.py`.
**Grounding:** AT-368 (a 4.85-day silent outage), AT-399 and AT-424 (anomalies computed but not shown), AT-592 (strict missed an all-future log), AT-610 plus the at610 gate (write-order corruption).

## Why it exists

Nothing in this repo runs while the app is closed. So this command does not keep the loop alive. It makes a silence **legible afterwards**, and `--strict` gives a caller something to key an alarm off.

## Criteria

### LS1 — What `--strict` exits non-zero for

`--strict` exits non-zero exactly when `LoopStatus.strict_unhealthy` is true. That is either of two cases:
- the loop is silent **right now** and nothing on disk explains it, meaning the open gap is at or over the threshold and no `qa/.paused` exists (`asleep_now`);
- ticks exist but **none is credible**, meaning every stamp is dated after now (`ticks > 0` and `last_tick is None`).

In every other state `--strict` exits 0. Without `--strict` the command always exits 0, whatever it prints. A historical (closed) gap never fails `--strict`: it says the loop once slept, not that it is sleeping. (AT-368, AT-592)

### LS2 — Every structured anomaly is rendered, not only counted

When the log has at least one tick, `report_lines` renders:
- a `CORRUPT` row for future-dated stamps, which are excluded from the gap arithmetic;
- a `CORRUPT` row for ticks written out of chronological order;
- a `last: none credible` row when no tick survives.

An all-future log is never rendered as "no ticks recorded", and never also claims "no gaps". Only a log with zero parsed ticks says "no ticks recorded". (AT-399, AT-424)

### LS3 — Write-order corruption is report-only (Umesh, at610 gate answer A, 2026-09-26)

Ticks written out of chronological order (`out_of_order > 0`) always get their LS2 `CORRUPT` row. They never, on their own, make `--strict` exit non-zero. With `out_of_order > 0` and a credible recent tick, `--strict` exits 0.

Liveness is judged only from the sorted credible ticks, never from file order. So write-order corruption cannot hide an outage: an asleep loop with out-of-order lines still fails LS1.

Making out-of-order lines gate `--strict` needs a new gate answer. It is not a fix.

### LS4 — Not part of doctor, and read-only

`loop-status` is never wired into `autotester doctor` or the adapter's verify chain. A stale loop must not fail every unit's verification, because a liveness signal that breaks the build is worse than the silence it replaces (AT-368). It never writes, repairs or re-sorts `qa/.last-tick`.

### LS5 — The session-start consumer is bounded and cannot block or break session start (at383, AT-622/AT-624)

`qa/hooks/mc-sessionstart.ps1` calls `loop-status` once, with a timeout (default 15000 ms). On timeout it kills the **whole process tree** (`taskkill /T /F`), not only the `uv` process. No `uv`-launched python grandchild may survive a timed-out call.

Any failure (timeout, missing `uv`, missing `taskkill`, non-zero exit) prints one skip line with a stderr tail and lets the hook continue with exit 0. The call sits inside an outer try whose catch prints that skip line. A test asserts this structure, not merely that `try {` and `catch {` appear somewhere in the file.

A behavioural test drives a real grandchild through the same path and asserts it is dead after the timeout.

### LS6 - The handshake DECLARES which line carries authority; history is never swept
**CORRECTED 2026-09-28, hours after it was written, on the maker's counter-evidence. The first
version of this criterion would have destroyed records.** It called for "exactly one line per
manifest" and for the fix to be made in the data. Re-derived: 12 manifests carry more than one
status-shaped line (not the 6 my narrower pattern found), and the extra lines are **legitimate
append-only history** - `t133-ensemble-and-issues.md:117` and `at206-guards-that-guard.md:88` both
read `## Status: superseded by cycle 2`, and `at576-577-serial-runs.md:491` records cycle 1 above the
live cycle-2 line. Canonicalising to one line deletes those. In a project whose discipline is that
history is append-only, that is not hygiene; it is history loss to make a grep correct.

- **One line is DECLARED authoritative, going forward.** The handshake names which line a reader may
  key on. The defect was never that writers were careless - every shape on disk is defensible - it is
  that nothing ever said which line counts, so every writer picked one and every reader wrote its own
  matcher. `at575-orchestrator-caller` did not drift; it was always *able* to drift.
- **Every historical and per-cycle line stays exactly as it stands.** A superseded-cycle record is
  evidence. No sweep, no migration, no rewriting a PASSed manifest to satisfy a pattern.
- **New manifests are checked against the declaration, not old ones.** `uv run autotester doctor`
  judges manifests written after the declaration. Forward-looking and reversible, so it needs no
  enforcement-path change and no gate.
- **This does NOT clear the t182 count, and claiming it did was the first version's second error.**
  `t182-viewport-locale.md:13` is PROSE explaining the rule - *"handshake - `Status: ready-for-check`
  is written last)"*. A declaration about fields never touches prose. Clearing t182 through data would
  mean deleting a manifest's own explanation of the handshake so a detector stops matching it.
  **So anchoring the detector (AT-673) remains the only route for anything whose match lives in
  prose, and that gate is not optional.** Until it is taken, the hook's `PASS not closed out: 1` is a
  known constant and must be reported as one wherever it is read - it keeps AUTO-CONTINUE armed every
  session (AT-657).
- **Verify:** a manifest created after the declaration carries the authoritative line in the declared
  shape, and `doctor` names any that does not; no commit deletes or rewrites an existing status line.
  **Links:** AT-662; AT-673; AT-657; core-invariants C12.

## No-fire list

- Historical gaps rendered as SLEEP (the `retro_blind` note explains why).
- A CORRUPT row alongside exit 0 for out-of-order lines. That is LS3 working as decided.

## Amendment log (append-only; git history is the version)

- 2026-09-26 · init · contract authored by /checker under D-047. It codifies at399, at424 and at592 (all checked-PASS and merged), and records the at610 gate answer A as LS3. No prior contract named loop-status; the at592 manifest asked for this decision. Nothing amended.
- 2026-09-27 · tighten · added LS5, which codifies at383 cycle 2 (checked-PASS, verdict df909e05, merged 0f503612): a bounded session-start call, a whole-tree kill on timeout, and a structural try/catch assertion. The out-of-scope bullet "where `--strict` is called from: gate at383" is replaced, because that gate was answered and is now LS5; AT-623 is named as the remaining out-of-scope call. Only tightening, so no DECISIONS entry is needed.
- 2026-09-27 · tighten (routine, Mode B sweep) · LS3's header changed from present tense ("pinning test arrives with unit at610-strict-out-of-order-pin") to past tense, since at610 has since merged and PASSed (11f1d4ea/37aaa375) — the pinning test is shipped, not pending. No criteria text changed; a status correction, not a new rule.
- 2026-09-28 - routine (add) - LS6 added: the handshake state a detector reads has one canonical
  machine-readable line. Cause: AT-662, measured in the overdue Mode B sweep. Eight spellings of
  `Status` across 261 manifests, nine files matching none of the common shapes, six carrying two -
  and the hook's standing `PASS not closed out: 1` turns out to be a PROSE sentence in
  t182-viewport-locale.md:13 that quotes the phrase, while that unit's real close-out uses a
  spelling the detector cannot see. LS6 deliberately routes the fix to the DATA rather than to the
  hook, because the hook is an enforcement path needing Approved-by: Umesh and canonical manifests
  make its existing literal test correct without touching it. Additive; no criterion weakened.
  **Changes-authorized:** qa/contracts/loop-status.md LS6 + Amendment log (this entry). No
  enforcement-path file touched. **Links:** AT-662; AT-673; AT-657.
- 2026-09-28 - CORRECTION (narrow) - LS6 rewritten the same day it was added, on the maker's
  counter-evidence (autotesting-52, 31fe9ec0), and the correction is load-bearing: as first written it
  called for one status line per manifest and for the fix to be made in the data, which would have
  DELETED the superseded-cycle records at t133:117, at206:88 and at576-577:491. Re-derived its
  premise myself: 12 manifests carry more than one status-shaped line, not 6, and the extras are
  append-only history plus two prose lines and one block of quoted command output. No manifest is
  unreadable by a human; the whole variance is in whether a PATTERN can read it. LS6 is now a
  forward-looking DECLARATION of which line carries authority, checked by doctor on new manifests
  only, with history explicitly untouched. Also withdrawn: the claim that canonicalising data clears
  the t182 false positive. t182's match is prose explaining the handshake, so a field declaration
  never reaches it, and the AT-673 detector-anchoring gate stays the only route. My first version
  would have traded records for a clean grep - the shape of error this contract exists to catch.
  **Changes-authorized:** qa/contracts/loop-status.md LS6 + Amendment log (this entry). No
  enforcement-path file touched. **Links:** AT-662; AT-673; AT-657.
