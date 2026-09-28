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

| Row | `run_kind` | expires | `production` | signature | `max_actions` | `max_probes` | `wall_clock_s` |
|---|---|---|---|---|---|---|---|
| `appr_333a83b240ce` | crawl | 2026-09-10 (expired) | false | **absent** | 40 | **0** | 300.0 |
| `appr_7ffa35808cf0` | crawl | 2026-09-24 (expired) | false | **absent** | 150 | **0** | 600.0 |
| `appr_d89c9e3c61fd` | crawl | 2026-12-12 | false | **absent** | 200000 | **0** | **600000000.0 = 19.01 years** |

**Read that last row across.** The two rows with sensible bounds (40 actions / 300 s, 150 / 600 s) are
the **expired** ones. The only unexpired approval is also the least bounded one: 200 000 actions,
`scope: everything`, and a wall clock of **nineteen years**.

**An earlier version of this gate called that "a granting-practice matter, not a code defect". That was
half wrong, and checking it before it reached you is why this paragraph changed.** The honest split,
measured (`AT-675`):

- **The tool's doing, not yours.** The UI grant form has **no `max_probes` field at all** — its entire
  field set is `expires_at, granted_by, max_actions, note, scope, timezone_offset_minutes,
  wall_clock_s` — so every approval granted through the UI is written `max_probes=0`, and the CLI's
  `--max-probes` defaults to `0` too. Combined with `parallel_run.py:164`'s falsy guard, **no approval
  granted through the UI can ever bound probes.** So `max_probes=0` on all three rows is what the tool
  produces; it is not a lapse by whoever granted them, and it should not be reported as one.
- **Hand-entered.** The form's own defaults are `max_actions` **200** and `wall_clock_s` **600**, both
  required with `min=1` — so the UI **cannot** emit `0` for those two at all, which makes `max_probes`
  the only bound a UI-granted row can zero out. The live row carries **200 000** and **600 000 000** — three orders of
  magnitude off — and `scope: everything` against a required free-text field whose placeholder reads
  *"what this crawl may read and click"*. Those were typed.

**One more measured thing, and it is why step 4 below says *paste the printed command* rather than
*run `approve`*.** `cli_crawl.py:241-243` defaults **all three** bounds of the `approve` command to
`0`, with no `min=1` anywhere — while `cli_crawl.py:60-61`, the command that actually *runs* a crawl,
defaults to `200` and `600.0`. So **the command whose job is to set a bound defaults to unbounded,
and the command it bounds defaults to bounded.** A grant typed by hand without flags writes a row
that is `0` on every axis; only the command the refusal prints carries real numbers. Nothing on disk
was produced that way — all three rows have non-zero actions — but it means the `0` problem is
reachable on every bound through the CLI, not only on `max_probes` through the UI.

**The cleanest statement of it is the checker's, and it is confirmed line by line**
(`cli_crawl.py:232-243`): on `approve_cmd`, **every identity field is required** —
`--kind`, `--target`, `--scope`, `--granted-by`, `--expires` are all `typer.Option(...)` — while
**every bound defaults to void.** *The command whose entire job is to set limits enforces provenance
and not limits.* And the sharpest detail is in the help text of the one field that is required:
`--expires` reads *"YYYY-MM-DD; consent is never open-ended"*. So the command refuses open-ended
consent in **time**, by construction, and hands out open-ended consent in **magnitude**, by default,
in the same signature. That is not a missing `min=`; it is the wrong half of a grant being treated as
the mandatory half.

So one bound was defeated by the code and another by a value chosen at the keyboard. Only the second is
a granting-practice question, and it is the reason step 3 below matters: the command the tool prints
derives its bounds from the run that was actually attempted, so it structurally cannot emit a 19-year
clock or a scope of `everything`.

**One thing deliberately not concluded:** `granted_by` reads `Umesh` on the two disciplined rows and
`umesh` on the live one. Both the UI and the CLI take that field as free text, so the casing does **not**
establish which path produced the row, and it is recorded as a weak signal rather than an identification.

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
refuses any run exceeding the approved bound. **A correction to an earlier version of this gate,
because it mattered:** that does NOT make a `0`-bound row safely useless. `AT-660` (checker, high,
verified first-hand) found `0` means two opposite things — at the gate `consent.py:56`
`if actions > approval.max_actions` has no falsy guard, so `0` is a **zero budget**; but during the
run `parallel_run.py:158,162,164` all read `if approval.max_actions and …`, where `0` is falsy, the
conjunct short-circuits and **no bound is applied at all**. All three bounds behave this way. And
`require_approval` declares `actions/probes/wall_clock_s` as **defaults of 0**, so a caller that
omits them is accepted by a vacuous check and then bounded by nothing. **A second correction, to the correction:** an earlier version of this
paragraph said all three rows carry `0` bounds. They do not — see the table above. `max_actions` is
non-zero on all three, so the falsy-guard inversion is **not** live for actions. It **is** live for
`max_probes`, which is `0` on every row, so probes are unbounded at run time today. And the live
row's `wall_clock_s` of 19 years is the *other* shape: non-zero, so every check passes, and it
constrains nothing — which the `0` fix does not reach. **So the rows are neither harmless nor
uniformly zero: one bound is defeated by the code, another by the value chosen.** The worse of the
two is the 19 years, because `0` at least looks suspicious while `600000000.0` looks like a number
somebody chose. That is being fixed inside the AT-570 unit; it is named here because
this gate previously implied those rows simply refuse everything, and that was half the truth.

**You still do not need to work the bounds out:** every refusal ends
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

---

## UPDATE 2026-09-28 — AT-570 has now LANDED, so the refusal in this gate is live

`wave/at570-live-case-approval` merged at `e303f5e4` on a checker PASS (cycle 1, verdict
`qa/verdicts/at570-live-case-approval.md`, all eleven capability rows independently falsified by the
checker in its own isolated copy). The sequencing cost this gate predicted is no longer a prediction:
**every UI case run is refused today until a signed `live_case` approval exists.** Steps 1-5 above are
now the live procedure, not a plan.

### One new fact that changes the procedure, found by the checker and NOT disclosed in the build's manifest

**`AT-698` (high).** The UI cannot create a `live_case` approval **at all**:
`ui/routes_crawl_approval.py:188` hard-codes `run_kind=CRAWL` on the row it writes, and `:104` filters
the table to `CRAWL`, so a `live_case` row granted by CLI is not even visible in the UI list. F-042
shipped "complete no-CLI crawl approval"; after this merge **the same operator can no longer start a
run without touching the CLI.**

This does not change what you do — step 4 already says to paste the command the refusal prints, and
the refusal renders as a themed HTML page carrying that exact command. It changes what you should
expect: **do not go looking for a grant button in the UI. There isn't one, and the absence is a filed
defect rather than something you have missed.** One edit to `routes_crawl_approval.py` closes AT-698
and AT-675 together, and it is queued.

The checker called the manifest's silence on this *"the one place this manifest fell short of its own
standard"* — it disclosed the narrower `max_probes` field gap and the "CLI is the intended path" note,
and never stated that the no-CLI surface can no longer start a run. That judgement is recorded here
rather than softened, because this gate is where you would have discovered it the hard way.

### A SECOND decision now sitting with you, and it is genuinely open

**Ratify or reverse: `0` means ZERO BUDGET on both sides.** `AT-660` was that `0` meant two opposite
things — a zero budget at the gate (`consent.py:56`, bare comparison) and *no bound at all* during the
run (`parallel_run.py`, truthiness guards, where `0` is falsy and the check short-circuits). The build
closed that by making `0` mean zero budget everywhere, which is the fail-closed direction.

**The build chose that. No human ratified it.** CN10's ratification clause is why the checker said so
out loud instead of letting a PASS imply agreement, and why all three field descriptions in
`schema/approval.py:56-79` carry "ZERO MEANS ZERO" **plus** the sentence that it awaits ratification.

- **Ratify** and `0` stays a zero budget: a bound left at `0` refuses everything, loudly and early.
- **Reverse** and `0` means unbounded: convenient, and it reinstates the shape where the least-bounded
  approval is the one that looks most innocuous — which is exactly how `appr_d89c9e3c61fd` came to
  carry `max_probes=0` and a 19-year clock without anyone noticing.

**The maker recommends ratifying**, for one reason: `0` is what the CLI writes when a bound is
omitted (`cli_crawl.py:241-243`, every bound defaulting to `0` with no `min=`), so under "reverse" the
command whose job is to set limits would grant unlimited consent by default. Under "ratify" the same
omission refuses the run and prints a command with real numbers. **It is your call, and the code is
already in the reversible direction, so either answer is cheap today and neither is cheap later.**

## Answer

Answered: 2026-09-28 -- Umesh, direct instruction. NOT one of the listed options: he rejected the
premise that a human types bounds at all.

Verbatim: "aisa kyu banayenge hum like fix number of counts? hamein thodi pata hai wo product kitna
bada hai. jab auto-test / koi manual tester testing karta hoga to tujhe kya lagta hai uske paas clicks
limited rehte honge? manual tester jab testing karta hoga wo bas kya karega ki login karega id password
se aur jo target URL hai wahan pe jaake uske baad us portal ko explore karega end to end full detail
mein. count permission ya jo chahiye -- bhai jab tere paas id password user ne de diya, wahi sabse badi
permission hai na. jab tool ka purpose hi wo hai to extra permission extra wo kyu daal raha hai tu.
itna complicated mat bana system; system easy to use banana hai hame."

THE RULE THAT REPLACES THE GATE: the provisioned account IS the authorization. Credentials in the
repo-root .env + the target URL + allowed_domains = the grant. Nothing else is typed by a human.

What follows, mechanically:
1. max_actions / max_probes / wall_clock_s stop being consent and become operational safety brakes
   the system sets itself. Defaults generous enough that a full end-to-end explore finishes
   unattended. If a brake stops a run, the report says which -- a truncated run is never reported
   as a completed one.
2. AUTOTESTER_APPROVAL_KEY is generated on first use and written to the repo-root .env by the tool.
   Its job is row integrity (no forged or imported approval), never consent. With authorization
   derived from the account, a human-typed key adds a step and protects nothing.
3. approve_cmd bound defaults go from 0 to real values with min=1, so the void-by-default shape
   this gate measured at cli_crawl.py:241-243 becomes unreachable.
4. Accountability moves to the record. Every field typed with its prior value, every button pressed,
   lands in the run report and trace.jsonl. Verbatim: "tu jo karega wo sab to tu apne system pe
   rakhega na, taaki kal ke din koi tere se kuch bole to tere ko pata ho."

AT-570 is NOT waived by this. Case runs still fail closed; they now have a derivable authorization
to succeed against instead of a human-typed one that nobody can size correctly.

EVIDENCE THIS GATE ITSELF PROVIDES FOR HIS POSITION: the two approvals on disk with sensible bounds
are the EXPIRED ones; the only live one carries 200000 actions and a nineteen-year wall clock. When
a human was forced to guess a number he could not know, he guessed unbounded. The pre-ask delivered
none of its promised safety and still cost a turn.
