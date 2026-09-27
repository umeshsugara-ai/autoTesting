# GATE — AT-674: two acts only Umesh can do, and they are ONE action with a hard prerequisite

**Filed:** 2026-09-28 (maker, tick wave 33) · **Severity:** high · **Ledger:** `AT-674`
**Blocks:** T-122 (the Pathlynks user-account login case — the unit Umesh named first), and T-145.
**Related, and part of the same conversation:** `AT-654`/D-029 (dev-only vs production), `AT-659`.
**Independently verified by the checker** (commit `9ab15717`) on all three counts.

## The situation in one paragraph

Today a UI case run checks **no** approval — that *is* defect `AT-570`, currently being fixed. The
moment that fix lands, case runs fail closed, and **nothing on disk can authorize a Pathlynks run.**
So our own fix blocks the unit Umesh asked for first. This is a sequencing cost, not a disagreement:
the fix is right, and it needs one human action in front of it.

## Why nothing on disk works (measured read-only; no secret value was printed)

`projects/pathlynks/approvals.jsonl` holds 3 rows. All three fail, for reasons that stack:

| Row | `run_kind` | expires | `production` | signature |
|---|---|---|---|---|
| `appr_333a83b240ce` | crawl | 2026-09-10 (expired) | false | **absent** |
| `appr_7ffa35808cf0` | crawl | 2026-09-24 (expired) | false | **absent** |
| `appr_d89c9e3c61fd` | crawl | 2026-12-12 | false | **absent** |

1. **No row carries a `signature` field at all** — the key is absent from the parsed key union, not
   merely empty.
2. **None is `run_kind=live_case`.** `schema/enums.py:165-172` defines `ApprovalKind.LIVE_CASE`; it
   has been defined and never used. A crawl approval cannot cover a case run.
3. **`AUTOTESTER_APPROVAL_KEY` is absent from the repo-root `.env`.** `core/ids.py:31-47` raises
   `SigningKeyMissing` from **both** `sign_payload` and `verify_payload`.

**The precise firing reason, kept separate on purpose.** `schema/approval.py:119-128` returns `False`
at `if not self.signature` **before** `verify_payload` is reached, and its docstring says it never
raises for an empty signature because *"no key configured"* and *"this row has no signature"* are
different problems an operator must be able to tell apart. So what fires today is
`consent.py:79-83` — **"no signature — re-grant it"** — *not* the AT-110 `"cannot verify"` branch.
The missing key is latent on read and fires on **create**.

## Why this is ONE action, not a to-do list

`approve_cmd` calls `candidate.sign()` and **exits 1 before writing any row** when the key is
missing. So the key is not a preference about ordering — **you cannot grant until it exists.**

## What to do — and you should NOT hand-write the bounds

`--max-actions`, `--max-probes` and `--wall-clock` all default to **0**, and `consent.py::_shortfalls`
refuses any run exceeding the approved bound — so a grant written without them produces a row that
refuses everything. **This is already solved and you do not need to work it out:** every refusal ends
with `Grant one with:` followed by a pasteable command carrying the correct bounds for that exact run
(`consent.py:129-133` → `_grant_command`, tested at `tests/test_consent.py:195,209`). The docstring
records that an earlier version omitted the bounds and *"an operator who followed the printed command
verbatim got a second refusal"* — that was fixed.

**So the sequence is:**

1. **Provision `AUTOTESTER_APPROVAL_KEY`** in the repo-root `.env`. This is a secret; no agent should
   generate, choose or write it, and none has.
2. Let `AT-570` land (in flight).
3. **Start the Pathlynks case run.** It will refuse and print the exact `uv run autotester approve …`
   command — correct `--kind live_case`, correct bounds, and `--production` if the target needs it.
4. **Paste that command**, with `--granted-by umesh`. Granting is an authorization act; every existing
   row reads `granted_by: umesh`.
5. Re-run.

## The one decision inside this that is genuinely yours

Step 3's printed command includes `--production` only if the run is against a production target — and
**whether Pathlynks is treated as production is exactly the open `AT-654`/D-029 question.** All three
existing rows are `production=false`, which is why these two gates are one conversation: D-029's
dev-only condition and the grant's production flag are the same decision wearing two labels. Answer
`AT-654` (options in `qa/gates/at654-d029-dev-only-vs-production-pathlynks.md`) and this follows from
it — the maker picks neither.

**`AT-659` (low, checker) is a wording trap on the same command,** and worth knowing only so it does
not mislead you: `--production`'s help says *"required for an adversarial run against production"*, but
`consent.py:87` applies the production check to **every** kind. The printed command in step 3 is
generated from the run's actual `production` flag and is kind-independent, so **following the printed
command is immune to this**; reading the flag help instead is what would mislead. The three existing
`production=false` rows are exactly what someone who read that help would produce.

## What the maker did and did not do

Filed, measured and sequenced it — and deliberately ran this check **while the `AT-570` build was in
flight**, so the ordering cost surfaced before the merge rather than after. **Not done, and not an
agent's to do:** no key was generated or written, no `approvals.jsonl` row was created, edited,
signed or backfilled, and the build agent was instructed in writing not to weaken the guard, add a
bypass flag or a dev-mode escape to make T-122 runnable — that would reinstate the fail-open defect
the unit exists to remove. If it judges the unit cannot be both fail-closed and T-122-compatible
without one, it must say so in Disclosures and leave it here.
