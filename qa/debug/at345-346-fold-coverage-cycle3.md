# Stall diagnosis — at345-346-fold-coverage (cycle 3)

**Skill:** `/agent-debugger`, Phases 1–2 only (failure capture + root cause). Read-only toward
code, tests, contracts and the manifest. Nothing outside this file was written.
**Bound to:** `D:/autoTesting`
**Date:** 2026-09-11
**Dispatched by:** `/maker` on `Status: STALLED` (fix cycle 3 of 3, three independent checker FAILs)

---

## Phase 1 — Failure capture

```
Session / task      : close AT-345/AT-346 — the credential-spelling transforms the AT-339 fold
                      still let through — under qa/contracts/ui.md U8/U9 and core-invariants C2/C7.
Goal in progress    : cycle 3's fix (U+0000 / category Cc added to the ignorable strip, predicate
                      renamed _is_invisible -> _is_ignorable) being judged by a fresh checker.
Error               : not an exception. Three consecutive checker verdicts of
                      `VERDICT: FAIL / SCOREBOARD: 0/2 criteria met, 2/2 invariants hold`,
                      each charging U8 + U9 at sev high on a NEW character class, each reproduced
                      live in the checker's own Chromium against its own uvicorn.
Last successful step: every mechanical gate passed, every cycle, including cycle 3 —
                      pytest 1145 passed / 2 skipped, ruff clean, `doctor: clean`,
                      10/10 mutations killed with kill-attribution hand-verified by the checker,
                      11/11 false-positive probes accepted. Prior cycles' fixes all re-verified
                      as still closed (AT-345, AT-346, AT-351, AT-353).
Last failed "call"  : `POST /onboard` name = U+202E + "13_YEKIPA_TLIUQ_ARBEZ" -> HTTP 200,
                      `projects/atk18/project.json` written; home index renders 21 glyphs in
                      visual order `ZEBRA_QUILT_APIKEY_31`. Same spelling accepted by the case
                      form on `title` / `step_value` / `step_expected`; `cases.jsonl` carries 7
                      `\u202e` escapes. Filed AT-355 (ui, high).
Repeated pattern    : four cycles, one line — `redact.py::fold_credential` / `_is_ignorable`.
                      AT-339 case  -> fix -> AT-345 six transforms -> fix -> AT-351 Mn invisibles
                      -> fix -> AT-353 Cc controls -> fix -> AT-355 bidi override.
                      Each fix ADDS a subtracted character family. Each FAIL names a family the
                      previous fix did not subtract — except the last, which names one it does.
Environment checked : branch `master`; `redact.py` 215 lines, inside the 300-line cap;
                      no environment, tooling, provider, network or harness failure appears in
                      any of the three verdicts. The mutation harness (`scripts/mutation_check.py`)
                      was independently re-read against all five C7 clauses by two different
                      checkers and holds.
```

**My own discriminating check** (the only command I ran; read-only, no file touched):

```
$ uv run python -c "from src.autotester.core.redact import fold_credential as f, _is_ignorable; ..."
plain      -> zebraquiltapikey31
rlo+rev    -> 13yekipatliuqarbez
rev only   -> 13yekipatliuqarbez
ignorable(U+202E) = True
equal? True
```

The checker's central claim is confirmed at the unit level from a cold start: `_is_ignorable`
returns `True` for U+202E, the strip deletes it, and `fold_credential` then compares a string
that is not the credential. **The guard leaks because it strips, not because it misses.**

---

## Phase 2 — Root-cause diagnosis

### 1. Which side is this on — LOOP DESIGN, not execution

**Verdict: LOOP DESIGN. Specifically, the contract. Not execution, not tooling, not environment.**

Taking a position, with the evidence:

- **Execution is clean and improving.** Nothing in three cycles failed for a tooling, flake,
  environment or context reason. Every verify command in `qa/adapter.json` passed every cycle.
  The mutation instrument was audited from the outside twice and holds all five C7 clauses.
  Cycle 3 is, in the cycle-3 checker's own words, "the best of the three" — and it still scored
  0/2. A loop where the maker's work quality rises monotonically while the score stays pinned at
  0/2 is not failing on execution.
- **The adapter and verify step are fine.** They measure what they claim to measure. They are
  simply orthogonal to the criterion being charged: no amount of green pytest/ruff/doctor/mutation
  output has any bearing on "does a fifth character class exist".
- **The contract is where it breaks.** `qa/contracts/ui.md` U8/U9 pin a **byte-for-byte** property:
  "a raw `.env` value in any one of those fields is refused (400)… their **concatenation** is
  checked too, so a value split across two or more rows cannot reassemble **byte-for-byte**".
  None of AT-345, AT-351, AT-353 or AT-355 is a raw value. The first checker in this thread said
  so explicitly and **filed rather than charged** AT-345 on exactly that reading. Three cycles
  later, the same class of finding is being **charged at sev high** against the same criterion
  text, which has not been amended.

  What is actually being enforced is a different, unwritten criterion that appeared in the
  verdicts and evolved between them:

  | cycle | operative standard used to charge | where it is written |
  |---|---|---|
  | 1 | "renders pixel-identical to a plain-credential control" | nowhere |
  | 2 | "needs no decoding step the reader must deliberately take" | nowhere |
  | 3 | same standard, **re-measured**, moving RTL-reversal out of the filed-only AT-352 into a charged AT-355 | nowhere |

  Cycle 3 states this move plainly: AT-352 "does name RTL-override reversal", was filed not
  charged on a premise the checker then found "factually wrong", and so one arm of it was promoted
  to a charge in the final cycle. That is a criterion boundary being **re-drawn during the fix
  cycles, by the judge, on the basis of a fresh measurement**. That is not misconduct by the
  checker — the finding is real and severe — but it is a loop with no fixed acceptance line, and
  a loop with a moving acceptance line cannot terminate. The maker cannot pass a criterion whose
  edge is discovered by the next probe.

- **Second loop-design defect, smaller but real: the unit had no exit rule other than the cycle
  counter.** The manifest's own closing line says it: "The limit is not why it should stop — the
  fourth finding is." The loop stopped because it ran out of cycles, and the decision that it
  *should* stop was reached by prose reasoning inside the manifest, not by any gate. A unit whose
  completion is "the checker stops finding things" is unbounded by construction.

- **Third, a ledger defect the loop produced along the way (mechanical, worth one line):**
  `qa/issues.jsonl` now contains **two rows with `"id": "AT-355"`** — one `feature: ingest`
  (VisionOptions.thinking_level, medium) and one `feature: ui` (the bidi override, high). Verified:
  `grep -c '"AT-355"' qa/issues.jsonl` → 2. Issue-id allocation is not collision-safe across
  concurrent units. Not the stall's cause; file it.

### 2. Coverage problem or shape problem? — **Shape. The maker and the cycle-3 checker are right, and I reach it by a different route than they do.**

Their argument is the enumeration count: 1,107,659 code points defeat the fold when interleaved,
the strip set covers ~4,200. That argument is **true but not decisive** — a deny-list can be
sound if the complement is provably harmless, and cycle 2's DI audit (4174 DI code points, zero
under-inclusion against Unicode 14 data) is exactly the kind of proof that would make a
deny-list respectable.

The decisive evidence is the one I re-derived above, and it is qualitative, not numeric:

> **AT-355 is a character the guard already handles, and it leaks *because* the guard handles it.**

Every earlier fix was monotone — subtracting one more family could only make the comparison see
*more*. AT-355 breaks monotonicity: the subtraction itself destroys the attack's evidence. Widening
the deny-list makes this class **strictly worse**, because each newly-stripped format character is
another character whose layout effect the comparison becomes blind to. A coverage problem gets
better as you add cases; this one gets worse. That is the definition of a shape problem.

**Is the proposed allow-list itself unbounded? Yes — and that is the part neither the maker nor the
cycle-3 checker examined, so I will state it as the gating risk on their recommendation.**

The checker's own scoping words are "letters, marks and digits of **the scripts the product
actually stores**". That phrase is the unbounded edge. Concretely:

- **A legitimately non-ASCII credential breaks it in the wrong direction.** The allow-list's job
  is to refuse *unrenderable input*, not to decide what a credential looks like — so the failure
  mode is not "a Cyrillic credential sails through", it is a **false positive**: a real project
  name, base URL, CSS selector, XPath, or expectation text containing a character outside the
  permitted set is refused with "unrenderable input" when nothing is wrong. This product's own
  U9 history is a cautionary tale here: AT-078 and AT-086 are both cases where the guard made a
  legitimate project **uneditable with no fix the user could express**. The cycle-2 checker's 44
  probes and cycle-3's 11 (Hindi, Arabic with shadda, Thai, Hebrew with niqqud, Khmer, Korean,
  five emoji forms with U+FE0F and ZWJ, multi-line `expect`, tabs, CRLF, CSS/XPath/JWT/semver)
  are exactly the population an allow-list will start biting.
- **So the allow-list is unbounded on the false-positive axis instead of the leak axis.** That is
  a better trade for a security guard — it fails closed and each refusal is visible, actionable
  and reported by a user, whereas a deny-list gap fails silently into a public git repo. But it is
  a trade, not an escape, and it needs an explicit, enumerated, *written* script/character
  inventory to be bounded at all. "The scripts the product actually stores" is not yet that
  inventory; the product ingests arbitrary third-party web apps.
- **The confusable half does not go away.** Homoglyph attacks (AT-349) are attacks *inside* the
  allow-list — Cyrillic `а` is a letter in a script the product may well store. An allow-list
  addresses invisibility and layout; it does nothing for confusability. The existing fold's case /
  separator / confusable / percent-escape work survives and is still needed, which the cycle-3
  checker correctly says.

So: **shape problem, the recommended direction is right, and it must ship with a written
character inventory or it recreates the same unbounded loop with the sign flipped.**

### 3. Was the unit mis-scoped from the start? — **Yes, and a threat model in `qa/contracts/ui.md` would have terminated it at cycle 1.**

The mis-scoping is visible in the title. The unit is named `at345-346-fold-coverage` — *coverage*.
It was framed as "close the transforms AT-339 missed", which presupposes a finite, enumerable
missed set. It was in fact an open-ended adversarial hardening exercise against an adversary
(the checker) who is free to search a million-code-point space and is *rewarded* for finding one
more. Under that framing no fix can be final, because the unit's completion condition is the
negation of an existential the checker is actively trying to satisfy.

Two structural tells confirm it was mis-scoped rather than merely hard:

1. **No completion criterion was ever written.** The manifest's "How to verify" section lists five
   mechanical commands, all of which passed at every cycle. Not one of them can answer the question
   the unit is actually judged on.
2. **The scope boundary was declared inside the code, by the maker, and then repeatedly overruled
   by the judge.** AT-349's docstring bound ("this map is curated, not UTS #39") was accepted;
   AT-352's bound was accepted at cycle 1 and 2 and then partially revoked at cycle 3. A boundary
   the author declares and the judge can revoke mid-cycle is not a boundary.

**Would an explicit threat model in `qa/contracts/ui.md` have terminated it? Yes — with one
caveat.** A criterion of the shape:

> **U11 — Credential-spelling threat model.** The guard must refuse: (a) exact values,
> (b) case/separator/percent-escape/whitespace reversals a human performs mentally, (c) spellings
> that a conforming renderer displays as the credential with no reader-side decoding —
> enumerated as: zero-width/default-ignorable interleaving, control-character interleaving, bidi
> reordering. Everything else — homoglyphs beyond the curated map (AT-349), base64/base32/hex/HTML
> entities/double-encoding (AT-352), visible combining marks (AT-356) — is **declared out of
> scope**; a finding in those classes is FILED, never CHARGED, and moving a class in or out is a
> contract amendment under the criticality gate, **not a cycle-3 measurement**.

…would have converted cycles 2 and 3 into a *contract amendment* (a deliberate, gated, one-time
decision) rather than three fix cycles. Note that clause (c) is exactly the standard the three
checkers used — the problem is not that the standard is wrong, it is that it lived in verdict prose
rather than in the contract, so its edge moved. Critically, **AT-355 would still have been charged
under that clause** (bidi reordering is in it), but it would have been charged *at cycle 1*,
alongside AT-351, as one enumerated list to close in one fix — not discovered one family per cycle.

**The caveat:** a threat model written by enumeration is itself a deny-list, and it inherits the
deny-list's weakness — the next class nobody enumerated is a contract amendment rather than a FAIL,
which is better but not free. The durable version is clause (c) expressed as a **positive
detector**, which the loop already built and then left in a scratch directory: the cycle-3
checker's `visualOrder` probe (per-character `Range` rects, glyphs sorted by screen x, compare
against the credential) is the only instrument in this entire thread that caught AT-355, and it
answers the right question — *"does this text, rendered, read as the credential?"* — without
enumerating anything. It belongs in the repo.

### 4. The smallest recovery action

The smallest action that **changes the diagnosis surface** is not a fifth patch and is not the
allow-list rewrite (which is a design decision, correctly gated to Umesh). It is to fix the thing
that made the loop non-terminating: write the acceptance line down.

**One `qa/QUEUE.md` row:**

> **HUMAN_GATE — `at345-346` shape decision, then contract first.** Umesh picks: **(A)** narrow —
> refuse bidi controls (`U+202A`–`U+202E`, `U+2066`–`U+2069`, `U+200E`/`U+200F`, `U+061C`) outright
> instead of stripping them, closing AT-355 and leaving the deny-list shape unchanged; **(B)**
> re-shape — NFKC then require every character to be in a **written** allow-list inventory, bidi
> refused by its own rule, keeping the case/separator/confusable/percent-escape fold intact; or
> **(C)** defer both and declare the classes out of scope. Whichever is chosen, the **first** unit
> is a `/checker` amendment adding **U11** to `qa/contracts/ui.md` — the enumerated spelling threat
> model plus the "filed, never charged, moving a class is an amendment not a measurement" rule —
> and porting the checker's `visualOrder` detector out of
> `qa/evidence/browser-at345-346-fold-coverage-2026-09-11-checker/` into the repo as the positive
> test. Code change is the unit **after** that, judged against U11. Do not re-open
> `at345-346-fold-coverage`; it is correctly STALLED.

Rationale for that ordering: U8/U9 currently cannot fail the way three checkers failed them, and
until that is repaired, any successor unit inherits the same non-terminating loop.

### 5. Process observation — three refuted unreachability claims: property of the **maker**, not the instrument or the contract

The claims, all three refuted on the checker's first attempt: AT-315, AT-321, and now AT-354
("an acceptance test for Indic/Arabic/emoji names cannot be killed by any mutation of this guard"
— refuted in one line by mutating the strip to `category(ch).startswith("M")`, which folds a Hindi
or Thai name to a stub so the guard refuses *more*, killing the test).

**Attribution: the maker's reasoning.** Ruling out the other two first, because the ruling matters:

- **Not the instrument.** `scripts/mutation_check.py` was independently re-read against all five
  C7 clauses by two different checkers (green-baseline assertion l.241, anchor-matched-once l.248,
  file-actually-changed l.256, `is_kill` requiring `exit_code == 1 and expected <= failures` l.85)
  and holds. It killed 10/10 with hand-verified attribution. The instrument never once failed to
  kill a mutation the maker wrote — the failure is that the maker did not write one.
- **Not the contract.** C7 already carries a clause written for precisely this, naming the two
  prior occurrences by id: *"An unreachability claim is INCONCLUSIVE, never a justification …
  it has been refuted on the first attempt both times it was made here (AT-315, AT-321)."* The rule
  exists, is specific, cites precedent, and was still violated. A contract cannot be strengthened
  its way out of being unread.
- **It is the maker's reasoning, and the mechanism is identifiable.** In all three cases the maker
  reached "no mutation can reach this" by **failing to think of one** and then promoting that
  failure to a proof — which is the exact move C7 names ("the error was stopping at *I could not
  think of a mutation*"). It is an unfalsifiable negative used to close a search, and it is
  *cheaper* than the search, which is why it recurs. The maker's own manifest reaches the same
  conclusion — "The pattern is mine, not the code's" — and I concur independently.

**Therefore it should be handled as a mechanical duty, not a rule to remember.** The durable form
is: a manifest that contains an unreachability claim must paste a **failed mutation attempt**
(the mutation tried, and the run showing 0 failures reported as `INCONCLUSIVE` per C7 clause 2)
— i.e. the claim costs one mutation run, not one paragraph. That converts a belief into an
artifact, which is the only form of it a checker can judge. Worth a `qa/loop.md` step or an
`autotester doctor` grep for unreachability phrasing in `ready-for-check` manifests; that is a
separate small unit, not this recovery row.

---

## Summary

| Question | Answer |
|---|---|
| Loop design vs execution | **Loop design — the contract.** U8/U9 pin byte-for-byte reassembly; three cycles charged high-sev FAILs on a rendering-equivalence standard that is written nowhere and whose edge moved between cycles. Execution, adapter and instrument are clean. |
| Coverage or shape | **Shape.** AT-355 leaks *because* the strip handles it — the fix operation is non-monotone, so widening makes it worse. Allow-list is the right direction **but has its own unbounded edge on the false-positive axis** and needs a written character inventory to be bounded at all. |
| Mis-scoped from the start | **Yes.** Framed as finite "coverage", judged as open-ended adversarial hardening, with no completion criterion and a boundary the judge could revoke mid-cycle. An enumerated threat model in `qa/contracts/ui.md` would have collapsed cycles 2–3 into one gated amendment; the durable version is the `visualOrder` positive detector, not a fourth enumeration. |
| Smallest recovery | One `qa/QUEUE.md` HUMAN_GATE row: Umesh picks narrow-vs-reshape; **first unit is the U11 contract amendment + porting `visualOrder` into the repo**, code change second. Do not reopen the unit. |
| Three refuted unreachability claims | **The maker's reasoning.** Instrument verified sound twice; C7 already forbids it by name citing AT-315/AT-321. Fix is mechanical: an unreachability claim must paste a failed mutation attempt, not a paragraph. |

**Result:** blocked — escalate to human (design decision is Umesh's by the manifest's own reading and mine).
**Token/time burn risk if not gated:** high. A fourth cycle would pass every mechanical gate and score 0/2 again; the search space is ~1.1M code points and the judge is incentivised to search it.
**Preventive change to encode later:** (1) U11 spelling threat model in `qa/contracts/ui.md` with the "filed, never charged; class moves are amendments" rule; (2) unreachability claims must carry a pasted failed-mutation run; (3) issue-id allocation is not collision-safe — `qa/issues.jsonl` currently holds two `AT-355` rows (ui + ingest).
