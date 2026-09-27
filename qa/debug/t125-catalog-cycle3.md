# Stall diagnosis — t125-catalog, cycle 3

**Purpose:** the independent root-cause report the maker skill requires before a `STALLED` stop, so
the stall is diagnosed rather than merely stamped.
**Open me when:** deciding `qa/gates/t125-stalled-at-cycle-cap.md`, or before anyone starts a cycle 4.

**Written:** 2026-09-27. **By:** a fresh `senior-software-engineer` subagent, read-only, dispatched
by the maker orchestrator after the cycle-3 FAIL (`a27f9794`). One dispatch, not looped on itself.
**Question asked:** is this failure on the *specification* side or the *execution* side, and does
ONE coherent relevance rule satisfy all four fixtures on record?

## Verdict: SPECIFICATION failure. The maker's hypothesis is confirmed.

> "No criterion, and no line of `plan.md` §5A, ever defines which SecretRef key 'belongs to' which
> `CatalogEntry` row once a project has more than one credential-consuming flow."

`qa/contracts/catalog.md:48-54` (CT5) treats "case class needs a SecretRef" as a singular stable
fact and never says what happens when two flows need two different keys for the same case class —
which the AT-588 OAuth pack **structurally guarantees**. `docs/plan.md:521-523`, the only worked
example D-039 authorizes, says "an unset secret … naming the key": singular, spec-wide, never plural.
**The ambiguity was baked in at the plan/D-039 level, before any maker touched the file.**

## Three independent parties converged, from different angles

Not just the maker's self-serving read — both *fresh* checkers hit the same wall and both ruled it
out of their own blast radius rather than filing it:

- `qa/verdicts/t125-catalog.md:132-146` (cycle-3 checker, Attack #5): "with exactly one row per
  `CaseClass` (CT2) … there is no 'this row's own flow' to scope to … a genuine contract-shape
  question … noting it here so it is not lost."
- `qa/verdicts/t125-catalog.md:340-343` (cycle-2 checker): "I am not filing this as a new blocking
  issue … `_entry_for()` has no per-flow granularity … genuinely out of ISS-t125-2's blast radius."

Domain-model evidence that the gap is structural, not incidental: `schema/case.py:22` keys the real
generated `Case` artifact by `flow_id`, and `stages/expand.py:55-56,73-74` already computes "does
this flow need auth" **per flow** — but `schema/catalog.py:120-131`'s `CatalogEntry` has no flow
dimension at all, because CT2 mandates one row per `CaseClass` project-wide. `catalog()` is asked to
collapse a per-flow fact the rest of the pipeline tracks, and nothing ever specified the collapse.

## Is there a rule satisfying fixtures (a)–(d)? No — not at the current schema level.

- `InputField.secret_key` exists but `stages/explore_merge.py:50-51` states this repo's own
  discipline: *"`secret_key` is deliberately never inferred — a field is only a secret because a
  human declared a `SecretRef` for it."* Any "password-shaped field" heuristic violates a rule the
  pipeline already lives by.
- `_oauth_signup_flow_ids` (`stages/catalog.py:121-134`) is a narrow Google/OAuth keyword match, and
  the review named **case (e)**: a flow clicking a Google button for an unrelated purpose ("sign in
  with Google to import a Drive file") is misclassified by the exact heuristic cycles 2 and 3 relied
  on. Any keyword/structural flow-purpose classifier fails in the same shape again.
- "Any flow that FILLs a referenced secret is relevant to the generic auth classes" handles (a) and
  (b) but not (c)/(d): nothing distinguishes the product's own login form from an admin-import flow
  that happens to FILL `SFTP_KEY`.

**Only sound fixes are contract-level:** (i) `CatalogEntry`/`PackEntry` gain a flow dimension
(contradicts CT2 as worded), or (ii) a **human-declared** relevance tag on `SecretRef`/`Flow`, so
`catalog()` consumes a declared fact — matching the "never infer, only declare" pattern already used
for `secret_key`. Either is an amendment requiring a decision, not a fourth maker guess.

## This corrects the gate's option B — reverting is NOT the safe fallback

The review diffed `cfc13b0b` rather than trusting the summary, and found:

- `git show cfc13b0b:src/autotester/stages/catalog.py:128` —
  `missing_auth_keys = _missing_keys(project, _auth_secret_keys(spec))`, a **global union with no
  flow scoping**, threaded into `_entry_for`'s **gate** exactly as cycle 3's `blocking` is
  (`stages/catalog.py:267,271`). **Cycle 1 and cycle 3 have the IDENTICAL gate defect** — ISS-t125-5
  is present in cycle 1 too. Cycle 3 differs only in scoping the *wording*, and even that re-leaks
  the union through the `or blocking` fallback in exactly the ISS-t125-5 fixtures.
- **`cfc13b0b` was never a passing state.** The manifest itself records it "carried no evidence
  manifest, so the maker/checker handshake had never seen it" (`qa/manifests/t125-catalog.md:23`),
  and the cycle-1 check failed it on CT5 and CT6 (`qa/verdicts/t125-catalog.md:563-576`).
  **There is no "last good git state" in this function's history** — every version ever checked has
  failed.

So reverting buys nothing on correctness and loses wording precision. The standing regression rule
assumes a good state exists to return to; here it does not, and the gate said otherwise. Corrected.

## Least-harmful ranking (unchanged conclusion, firmer evidence)

**cycle 3 ≈ cycle 1 (tied; both over-block, cycle 3 marginally cleaner wording) ≪ cycle 2.**
Cycle 2 is uniquely unsafe: the only version rendering `runnable=True` while a required secret is
unset. Over-blocking never lets a broken case through; under-blocking defeats the tool's purpose —
and per CT7 (`catalog.md:64-70`) the `Catalog` is consumed by T-152/T-166, so a false green could
propagate into an automated dispatcher, not merely a human reading a page.

## Is CT2 the real constraint? Yes — confirmed structurally.

`CatalogEntry` carries `case_class` and nothing identifying a flow; `Catalog` has no per-flow index;
`PackEntry` is one row per `StandardPack` project-wide and shares the identical defect (verdict
Attack #2). **Once a project has more than one credential-consuming flow — the AT-588 modal case —
"which secret does this row need" has no single correct answer at CT2's granularity.** Every
implementation must choose safe-but-broad (1/3) or unsafe-narrow (2). No third option exists in the
current shape.

## What the review recommends

Not a fourth guess. Either (a) a scoped exception cycle fixing ISS-t125-5 **only after a decision
entry states the actual relevance rule**, or (b) a contract-shape decision first (flow dimension on
`CatalogEntry`, or a declared-relevance field on `SecretRef`), then re-open the unit against the
corrected contract. **Explicitly: do not let a cycle 4 attempt a keyword heuristic** — case (e)
shows it fails in the shape cycles 2 and 3 already did.

**Verdict returned: Block.** Not on the maker's execution alone, but because the contract as written
cannot currently be satisfied by any implementation once a project has two credential-consuming flows.
