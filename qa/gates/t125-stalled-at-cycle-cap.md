# HUMAN_GATE — T-125 has burned all three fix cycles; how should it proceed?

**Opened:** 2026-09-27 by the maker, on the cycle-3 checker verdict (`a27f9794`): **FAIL, 5/8,
unit STALLED at its 3-cycle cap.**
**Decider:** Umesh. **Status:** OPEN — asked once, then written here.
**Blocks:** T-125 only. Nothing else in the backlog waits on this, and **nothing broken has
shipped** (see "Blast radius").
**Related gate, still open:** `qa/gates/t125-ct6-tiered-dispatch-vs-ru3.md` — CT6 is a *second,
independent* reason this unit cannot reach 8/8. Answering this gate does not answer that one.

## Blast radius — read this first, because it is the reassuring part

**`src/autotester/stages/catalog.py` does not exist on `master` at all.** The entire T-125 catalog
stage, and both regressions described below, live only on the unmerged branch `wave/t125-catalog`.
No shipped behaviour is affected, no operator has ever seen a wrong catalog row, and reverting
costs nothing that is in production. This is a decision about how to finish a feature, not an
incident.

## What happened, without softening it

Three cycles, three different answers to one question, each fixing the last and breaking something
new — all inside `stages/catalog.py::catalog()`:

| Cycle | What it did | What the checker found | Failure mode |
|---|---|---|---|
| 1 (`cfc13b0b`) | one global missing-key list; every blocked row named the **union** of every unset secret | `auth_wrong_creds` told the operator to set a sign-up-only token — one of its two named actions is always a no-op (**ISS-t125-2**) | misleading, but **visible** |
| 2 (`72f71aa1`) | scoped the key list per flow — and used the narrowed list for the blocked/runnable **decision** as well as the wording | one flow that both clicks "Sign up with Google" *and* fills the product's own password was read as OAuth-only, so its unset key vanished from the auth rows and they rendered a green `runnable` pill (**ISS-t125-3**, high) | **invisible** — ships a case that fails for real at run time |
| 3 (`513a08c7`) | separated them: the gate never narrows (every declared key), only the wording is scoped. **This genuinely fixed ISS-t125-3** — the checker verified it live | a login flow whose own password is set is now **wrongly blocked** because an unrelated flow (an OAuth sign-up, or even an admin-import flow) has an unset secret of its own (**ISS-t125-5**, high) | **false positives**, on any spec with more than one credential-consuming flow |

Both cycle-2 and cycle-3 defects are mine. Cycle 2's was the dangerous one and I reported it as a
fix; the checker caught it because I asked it to attack the rule, and caught cycle 3's the same way.

## The diagnosis, which is the actual decision you are being asked about

**No criterion in `qa/contracts/catalog.md` ever defines which secret key "belongs to" which
catalog row.** CT5 and CT8 judge the blocked state and its `unblock_action`, so a checker can prove
an answer *wrong* without the contract ever saying what is *right*. Each cycle was therefore a guess
at unwritten ground truth, and a fourth guess is not obviously better than the third. An independent
read-only root-cause review is running to confirm or refute exactly that, and to say whether a single
coherent relevance rule even exists that satisfies all four fixtures on record — including the one
where a flow is legitimately relevant to **both** the auth rows and the OAuth pack, which is what
broke cycle 2.

There is also a live question of whether the answer is expressible at all under **CT2**, which
mandates exactly one row per `CaseClass` for the whole project: if a project has three
credential-consuming flows, "which secret does *the* `auth_wrong_creds` row need" may have no
correct answer, only less-wrong ones.

## The options, with the cost of each

| | Option | What it costs |
|---|---|---|
| **A** | **Specify relevance first, then one scoped exception cycle.** The checker amends `catalog.md` to define which flows a row is about (it owns the contracts); the maker then builds once against a written rule instead of guessing. | Breaks the 3-cycle cap, which is a real discipline and exists precisely to stop this pattern. The justification would be that the cap assumes the maker is failing at a *specified* task, which the diagnosis says is not the case — fixing the specification changes the conditions rather than buying another guess. **Maker's recommendation, conditional on the root-cause review confirming the contract is silent.** |
| **B** | **Revert cycles 2 and 3** (`513a08c7`, `72f71aa1`) back to `cfc13b0b` and re-open T-125 with a corrected design from the start. | This is what your own standing rule says to do — *"on a regression, REVERT to the last good git state — do NOT stack a new fix"* — and cycle 1's failure mode is the least harmful of the three (visibly over-named actions, no false greens, no false blocks). Costs the ISS-t125-3 hybrid fix and its regression test, which are genuinely correct work, and leaves CT5/CT8 failing exactly as they did at cycle 1. |
| **C** | **Ship the catalog without a credential gate at all** — the rows report applicability and blocked-for-write-policy, and say nothing about whether secrets are set. | Honest: the system stops making a claim it has no specified rule for. An operator then discovers a missing credential when the case runs and fails, with a clear error, instead of beforehand. Costs a real feature that AT-588 asked for, and CT5/CT8 would need amending to match — so it is also a contract change, not just a deletion. |
| **D** | **Amend CT2 to allow more than one row per `CaseClass`** (per-flow or per-screen), so "which secret" becomes answerable by construction, then build. | Addresses the root shape rather than its symptom. Costs the catalog's best property — a fixed-length table an operator can scan — and is much the largest change of the four. |

**The maker is not choosing.** A and D both amend checker-owned ground truth; B and C give up
shipped scope. Each is a decision about what the product promises, not an implementation detail.

## Until this is answered

- `wave/t125-catalog` stays **unmerged**. Nothing is reverted yet either — reverting pre-empts A and
  D, and merging would ship ISS-t125-5.
- `ISS-t125-5` (high) and `ISS-t125-1` stay `open`; `ISS-t125-3` is `verified` (genuinely fixed).
- **No cycle 4 will be started without an answer here.** The cap is respected rather than quietly
  exceeded, which is the whole point of having one.
- T-125 stays `pending` in `.goal/goal.json`. The rest of the backlog continues; this gate blocks
  only this unit.
