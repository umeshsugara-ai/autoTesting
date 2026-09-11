# HUMAN_GATE — the credential guard's SHAPE, after three failed fix cycles

**Opened:** 2026-09-11 · **Status: ANSWERED** · **Approver:** Umesh
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

---

**Answered: 2026-09-11 — C, plus the narrow half of A — decided by the maker, delegated by Umesh
("take the best decision as per the goal and keep going").**

## The reasoning, against the north star

The north star is that an expert human tester and AutoTester get the same material and the same
build, and **AutoTester wins on bugs found, false-positive rate, and time**. The credential guard
is not the product; it is the boundary that lets the product use real credentials on a real portal
without publishing them. Every cycle spent on Unicode exotica is a cycle not spent on the thing
being measured.

**Who is the adversary?** `CLAUDE.md` says why this boundary exists: `cases.jsonl` and
`project.json` are git-tracked in a public repo, values must never reach a prompt, a log or a
screenshot. The realistic failure is **a hurried human pasting a credential into a text box, or an
agent writing one into a tracked file**. It is not someone who deliberately reverses a credential
and prefixes `U+202E`.

And that distinction is decisive, because **anyone who can construct the AT-355 spelling already
holds the credential.** They read it out of `.env` to reverse it. A guard cannot protect a secret
from a party that already has it — this is AT-110's "tamper evidence, not tamper proofing" posture
wearing a different costume, and the same answer applies.

**What that means for the four findings.** The classes already closed — case, separators,
percent-encoding, zero-width, control characters — are exactly the transforms that arrive *by
accident*: a paste out of a terminal or a PDF carries stray marks, a user re-types with different
punctuation. Those stay closed and they work. The remaining classes (AT-355 bidi, AT-352
base64/hex/entities, AT-349 exotic homoglyphs) each require deliberate construction by someone
holding the value. Those are declared **out of scope, by name**.

## So why do the narrow half of A as well

Leaving a *charged, reproduced, high-severity rendering leak* open while writing "out of scope"
would be using the threat model to excuse the one finding that prompted it. Two facts make the
narrow fix cheap and safe, and they are why this is not a fourth patch in the same shape:

- The attack needs a **bidi OVERRIDE** (`U+202D`/`U+202E`), which forces direction character by
  character regardless of content. The embeddings and isolates do not reverse a pure-ASCII run.
- `U+200E`/`U+200F` (LRM/RLM) are **legitimately used in Hebrew and Arabic text** and are NOT
  touched. That is the false-positive risk the debugger warned about, and the override pair sits
  entirely outside it: no project name or case title has a legitimate use for one.

So: **refuse `U+202D`/`U+202E` outright rather than stripping them.** Refusing is the operation
that does not destroy the evidence — which was the actual defect, not the missing character.

## What is NOT done, deliberately

**Option B is rejected.** The debugger is right that an allow-list is unbounded with the sign
flipped, and its failure mode — refusing legitimate input — is the one this product cannot afford:
`false-positive rate` is a term in the north star, and AT-078 and AT-086 are two prior occasions
when this guard made a real project uneditable. A guard that blocks real work loses on the metric
being optimised.

## Order of work, as the diagnosis prescribed

1. The threat model goes to `qa/feedback-inbox.md` for **/checker** to fold into `qa/contracts/ui.md`
   as U11 — the maker never edits a contract. It must carry the rule the diagnosis identified:
   *moving a class from filed to charged is an amendment, not a measurement.*
2. The narrow override refusal ships as its own unit, `at355-refuse-bidi-overrides`.
3. The `visualOrder` detector is ported into the repo regardless of any of this — it is the only
   instrument that caught AT-355, and a product whose job is reading other people's rendered pages
   should own a glyph-order detector on its own merits.

`at345-346-fold-coverage` stays STALLED and is not reopened.

## Also surfaced by the diagnosis, not blocking

- `qa/issues.jsonl` has **two rows with id `AT-355`** (one `ui`/high, one `ingest`/medium) — issue-id
  allocation is not collision-safe across concurrent units.
- The maker has made **three** "no mutation can reach this" claims in this repo and all three were
  refuted by a checker. The debugger's read: that is the maker's reasoning, not the instrument
  (independently re-read against all five C7 clauses by two checkers and sound) and not the contract
  (which already forbids the move by name, citing AT-315 and AT-321). Proposed durable fix: an
  unreachability claim must paste a failed mutation attempt reported INCONCLUSIVE per C7 clause 2,
  turning a belief into an artifact a checker can judge.
