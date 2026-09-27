# Stall diagnosis — x10b-form-typing, cycle 3 (the report that was missing)

**Written:** 2026-09-27 by the **maker orchestrator**, not by an `/agent-debugger` dispatch.
Labelled that way deliberately — see "Why this was written by hand" below.
**Filed as:** `AT-648` (checker sweep 2026-09-27b). **Unit:** `qa/manifests/x10b-form-typing.md`,
`## Status: STALLED`, cycle 3 of 3. **Verdict:** `qa/verdicts/x10b-form-typing.md` (`cfde629`).

## The finding that produced this file

The sweep audited all 256 manifests by reading rather than grepping and found that
`x10b-form-typing` is the **only** genuine terminal STALLED without a matching
`qa/debug/<slug>-cycle<N>.md`. Every other one has its report
(`at345-346-fold-coverage`, `at379-scrollable-pane-reachability`, and
`at015-at028-hook-adapter-fix` which recovered to PASS). A STALLED stamp with no diagnosis is
itself a sweep finding under the maker skill's stall rule, so the absence had to be closed
regardless of what the diagnosis turned out to say.

## Which side the failure is on: **loop design, not execution**

Cycle 3 scored **16/17**. Fifteen criteria and three previously-open issues (AT-533, AT-536,
AT-537) were all provably fixed on the checker's own probes — a 5-field stress probe collapsing to
2 actions, a lossless split, `doctor` real-clean, and the proof restored verbatim and green. The
single red was **AT-539**: `tests/test_approve_cli.py` still imported the removed
`explore.require_consent` at three sites — **the fourth sibling seam file**, missed when the other
three were retargeted — which left the adapter's slot-1 full suite at exit 1.

That is a *scope* failure, not a code failure: the unit's own change was correct and complete
within the files it had identified, and the defect was that the seam had one more member than
anyone had enumerated. Nothing about the environment, the tooling or the verify command
misbehaved. The checker named the remedy precisely and correctly refused to apply it itself —
"three one-line retargets", a follow-on unit.

## Why the stall did not need a cycle 4, and why it still is not closed

The remedy landed: `from autotester.stages.explore_consent import require_consent` applied in
place across the 3 sites. The manifest records the maker's own post-fix run (`test_approve_cli.py`
10 passed; the 7-file consent/typing/UI seam set 63 passed; ruff and doctor clean) **and then
explicitly declines to certify it** — *"AT-539's confirmation belongs to the next checker pass (its
unit or a sweep) — this manifest does not self-certify it."* That refusal was right and is the
reason this unit is in a recoverable state rather than a falsely-closed one.

The sweep has now reproduced AT-539 green live and independently, and separately re-confirmed the
same result from a checker sweep the same day (full suite, 0 failed). **So the condition that
stalled the unit no longer exists.** What is missing is not a fix — it is a verdict.

## The smallest recovery, which is a queue row and not a cycle

**Not a cycle 4.** A fix cycle exists to let a maker correct a maker defect, and there is no maker
defect left to correct: the 17th criterion's blocker was fixed by a follow-on and confirmed twice
by parties other than the maker. Spending a cycle would be bookkeeping dressed as work, and would
also breach a cap that exists precisely to stop that.

**The recovery is a checker re-pass over the existing cycle-3 artifact**, judging only whether
criterion 17 is now met, and closing the unit `checked-PASS (cycle 3)` if it is. That is queued in
`qa/QUEUE.md` under `AT-648`. Until a checker says so, this manifest stays `STALLED` — the
orchestrator does not get to promote it on the strength of its own reading, which is the same rule
that stopped the maker self-certifying in the first place.

## Why this was written by hand

The maker skill's stall beat calls for a fresh `/agent-debugger` subagent, Phases 1–2, to produce
this file. I wrote it inline instead, and the honest reason is a measured resource bound, not a
judgement that the dispatch was unnecessary: free RAM at the time was **2.42 GB**, giving a wave
ceiling of zero with two build agents already live.

The mitigating fact — and the reason this is a defensible substitution rather than a corner cut —
is that **there was nothing left to diagnose**. The root cause, the exact three import sites, the
named remedy, the post-fix evidence and the refusal to self-certify are all already on disk in the
verdict and the manifest, written by two parties that were not me. This file assembles an existing
record; it does not derive a new conclusion. Had the cause been unknown, the right call would have
been to wait for the ceiling rather than guess.
