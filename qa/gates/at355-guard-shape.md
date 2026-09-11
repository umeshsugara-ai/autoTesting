# HUMAN_GATE — the credential guard's SHAPE, after three failed fix cycles

**Opened:** 2026-09-11 · **Status: OPEN** · **Approver:** Umesh
**Blocks:** AT-355 (high) and any further work on the credential guard.
**Do NOT reopen `at345-346-fold-coverage`** — it is STALLED, and the diagnosis says reopening it
repeats the loop rather than ending it.

## The question, in one line

Should the guard keep **subtracting** unreadable characters before comparing (deny-list), **re-shape**
to canonicalising into an allow-list of readable characters, or **declare this class out of scope**?

## Why it is a gate and not a build task

Three fix cycles, three independent checker FAILs, all on one line of `fold_credential`. Execution
was not the problem and got *better* every cycle: 1145 tests green, 10/10 mutations killed with
attribution hand-verified, 11/11 false-positive probes accepted, `doctor` clean, and every earlier
fix re-verified closed. A loop where build quality rises monotonically while the score stays pinned
at 0/2 is not failing on execution.

## What broke the pattern

The first three findings could be read as "another character family nobody enumerated". AT-355
cannot. `U+202E` + the credential **written backwards** renders as 21 plain-type glyphs in the
correct reading order, and it leaks **because the guard strips it**:

```
fold("ZEBRA_QUILT_APIKEY_31")      -> zebraquiltapikey31
fold("‮" + its reverse)        -> 13yekipatliuqarbez
```

Every earlier fix was monotone — subtract more, see more. This one inverts it: the subtraction
destroys the evidence of the attack, so **widening the deny-list makes this class strictly worse.**

## The options

| | Action | What it costs and buys |
|---|---|---|
| **A** | **Refuse bidi controls outright** instead of stripping them | Smallest change, closes AT-355, leaves the shape unchanged. The next class of this kind will still find the same seam. |
| **B** | **Re-shape to an allow-list** of readable characters, comparing what a reader would see | The cycle-3 checker's recommendation and the maker's. But the debugger found an edge neither examined: an allow-list is **also unbounded, with the sign flipped** — its failure mode is false positives on legitimate input, and this repo already has two precedents (AT-078, AT-086) where the guard made a real project uneditable. "The scripts the product actually stores" is the unbounded phrase, in a product that ingests arbitrary third-party web apps. It fails closed and visibly, which is the better trade — not an escape. Needs a written character inventory. |
| **C** | **Declare the class out of scope** in the contract | Honest and bounded. `qa/contracts/ui.md` U8/U9 pin a **byte-for-byte** property that none of AT-345/351/353/355 actually violates — the cycle-1 checker said so and filed rather than charged on exactly that reading. |

## The finding underneath all three

**The contract never said what this guard promises.** U8/U9 pin byte-for-byte reassembly; what was
actually enforced across three cycles was an *unwritten* rendering-equivalence standard, and its
edge **moved during the cycles** — cycle 3 promoted one arm of the filed-only AT-352 to a charged
AT-355 on a fresh measurement. A loop whose acceptance line the judge redraws mid-cycle cannot
terminate, whatever the maker builds.

## What the first unit should be, whichever option you pick

Not a code change. A **`/checker` contract amendment** adding **U11** to `qa/contracts/ui.md`: the
enumerated spelling threat model, plus the rule that *moving a class from filed to charged is an
amendment, not a measurement*. And **port the `visualOrder` detector into the repo** — glyphs
sorted by screen x, the only instrument that caught AT-355, currently living in a checker's scratch
directory. Code changes come after that.

## How to answer

Reply `A`, `B`, or `C` (or name a different scope). Append
`Answered: <ISO date> — <choice> — <where>` below before anything acts on it.

**Answered:** _(not yet)_

## Also surfaced by the diagnosis, not blocking

- `qa/issues.jsonl` has **two rows with id `AT-355`** (one `ui`/high, one `ingest`/medium) — issue-id
  allocation is not collision-safe across concurrent units.
- The maker has made **three** "no mutation can reach this" claims in this repo and all three were
  refuted by a checker. The debugger's read: that is the maker's reasoning, not the instrument
  (independently re-read against all five C7 clauses by two checkers and sound) and not the contract
  (which already forbids the move by name, citing AT-315 and AT-321). Proposed durable fix: an
  unreachability claim must paste a failed mutation attempt reported INCONCLUSIVE per C7 clause 2,
  turning a belief into an artifact a checker can judge.
