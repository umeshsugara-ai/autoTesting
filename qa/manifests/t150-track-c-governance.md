# Manifest — t150-track-c-governance

**Contract:** none owned by this unit — `qa/contracts/ai-target.md` and `qa/contracts/adversarial.md`
do not exist yet; they are checker-owned deliverables this unit proposes criteria for (D-017/D-018).
**Goal task:** T-150 — "Track C governance: register C tasks, file ai-target.md and adversarial.md
criteria for the checker" (`.goal/goal.json`).
**Date:** 2026-09-27
**Fix cycle:** 1 of max 3
**Dual check:** no
**Persona walk:** skip — governance only. No screen, route, component, schema, or stage changed;
nothing a rendered page reads is different. `plan.md`'s own row for this unit also says "skip
(governance)".
**Issues addressed:** AT-638 (Track C portion only — see "What this unit does NOT close" below).
**Executor:** a `/maker` **build subagent** (Sonnet default, own git worktree), dispatched by the
orchestrator. **Corrected by the orchestrator before check:** the subagent's own draft of this line
claimed it was "the maker orchestrator, inline. No build subagent dispatched" — that was false, and
in a pair whose whole point is that the record says who did what, a manifest misreporting its own
author is a defect in the evidence rather than a typo. The real rationale for delegating: the unit
needs no test runs and holds no port, DB or browser, so it ran in parallel with the t125-catalog
cycle-3 full suite instead of queueing behind it.
**Orchestrator's review before dispatch:** read the criteria and both manifests; the substance is
accepted as filed. The corrections made were this Executor line and the registration note below.

## What changed

- `qa/feedback-inbox.md` — one dated entry appended (2026-09-27, "maker (T-150, Track C
  governance)"), filing two groups of **proposed** contract criteria for the checker:
  - **`qa/contracts/ai-target.md` — AI1–AI7**, covering T-151 (C1, discovery), T-152 (C2, check
    registry), T-153 (C3, behavioural checks).
  - **`qa/contracts/adversarial.md` — AD1–AD7**, the bound a HELD capability (T-154/T-155) must
    satisfy *before* it may be built.
  Each criterion is tagged `[D-017]` / `[D-018]` (reasoned directly from the authorizing decision)
  or `[maker]` (my own judgement, freely arguable) so the checker can tell which claims carry
  Umesh's authority and which are mine to attack. No other file was touched.

## Why this shape

D-017 and D-018 (`docs/DECISIONS.md`) already name `qa/contracts/ai-target.md` and
`qa/contracts/adversarial.md` as checker-owned deliverables, so no new DECISIONS entry was needed
or written (per this unit's brief). `qa/contracts/*.md` is checker-owned territory (`CLAUDE.md`
maker-checker discipline block: "Ground truth lives in `qa/contracts/` — maker never edits it");
the maker's job is to file the criteria into `qa/feedback-inbox.md` in the format the inbox already
uses, which is exactly what `consent.md`'s own provenance line documents happened for T-124
("CN1–CN7 folded verbatim from `qa/feedback-inbox.md` 2026-09-08"). I matched that entry's shape
(pattern statement, individual criteria with a `**Verify:**`-equivalent, a no-fire list, an
"applies next" line) and additionally tagged each criterion's authority source, which the T-124
entry did not need to do (T-124 had one clean source, D-018; this unit draws on both D-017 and
D-018 plus some of my own extensions).

## How I chose the id prefixes

`AT-` is already this repo's *issue* ledger prefix (`qa/issues.jsonl`); every existing contract-id
prefix (checked via `grep -ohE '^### [A-Z]+[0-9]+' qa/contracts/*.md`) is one of `AL, B, C, CN, CR,
D, E, F, G, I, K, L, LC, LS, ML, O, P, R, RE, RP, U, V, VL, X` — none free to reuse and none reads
as "AI-target" or "adversarial" on its own. I chose **`AI`** for `ai-target.md` and **`AD`** for
`adversarial.md`: both are free, and both read unambiguously next to an `AT-NNN` issue id rather
than being confused with one. The checker may of course pick different prefixes when it actually
authors the files — this is a proposal, not a claim of authority over naming.

## What this unit cannot do, stated plainly

- **This unit cannot make T-150's own `done_check` pass**, and does not try to. T-150's check is
  `uv run python scripts/check_deliverable.py --exists qa/contracts/ai-target.md
  qa/contracts/adversarial.md && uv run autotester doctor` — both files are checker-owned
  deliverables. Creating them here to turn the check green would be the maker writing its own
  ground truth, which `scripts/check_deliverable.py`'s own docstring names as the exact failure
  mode T-150 already produced once (AT-100/AT-115/AT-141: T-126, T-135, and **T-150 itself** all
  previously carried a `done_check` that could pass without the guarded work existing). Filing the
  criteria is what this unit does; **the checker authoring the two contract files from those
  criteria is what actually closes T-150.**
- **AT-638 is broader than this unit and stays `open`.** AT-638 names five ungoverned capabilities:
  T-166, T-167, T-168, T-171, and Track C (T-150..T-155). This unit answers only the Track C
  portion. T-166/T-167/T-168/T-171 have no criteria filed here and need their own governance unit —
  I am not claiming AT-638 closed, and the checker should not close it on this manifest alone.
- **T-154 (bounded adversarial pass) and T-155 (its report) are not built here, and no probe was
  sent.** Umesh's decision this session (also recorded in `plan.md`'s "Held / blocked" table): build
  C1–C3, hold the adversarial pass for a separate approval, no probe traffic without a fresh
  decision. Authoring AD1–AD7 — the criteria that would *bound* a future T-154 build — is governance
  and is explicitly in scope per this unit's brief: it records the constraints before anyone builds
  the capability, which narrows the eventual build rather than widening what is allowed today.
  Building T-154, or sending even one probe request to test AD1–AD7 for real, would be out of scope
  and was not done. No network call, no probe, no script execution beyond the two verify commands
  below was made by this unit.
- **No code, no tests.** Zero lines of `src/`, `tests/`, or `scripts/` changed. `qa/contracts/`
  itself was not touched — only `qa/feedback-inbox.md` and this manifest.
- **The "register the C tasks" half of T-150's title was already satisfied and this unit adds
  nothing there** — stated because a reader comparing the title to the diff would otherwise be
  right to ask. T-150..T-155 have existed in `.goal/goal.json` since `2026-09-08T00:46:52`, each
  with its deps, `note` and `done_check`; `docs/plan.md` rows 15/20/24/25, `target.md` M11 and
  `docs/spec.md` R30 all carry them too. So T-150's remaining work is exactly the criteria filing,
  which is what AT-638 actually complained about: the tasks were registered, the *criteria* to judge
  them by were not.

## How to verify (commands + expected)

- `uv run ruff check src tests scripts` → expect exit 0, `All checks passed!` (no source changed,
  included because the adapter runs it on every unit regardless).
- `uv run autotester doctor` → expect exit 0, `doctor: clean` (this unit touched no `docs/` file,
  so the router-row / Purpose / Open-me-when check has nothing new to verify against, but the
  command still asserts the design-rule and doctor checks stay green).
- **No pytest run** — explicitly, not left unexplained: this unit adds and changes no code, so
  there is nothing for the test suite to exercise that the two commands above don't already cover.
- `git diff --stat` → expect exactly one file, `qa/feedback-inbox.md`, `+139` (no deletions, no
  other path touched). The commit carries **two** files — `git diff` shows only tracked ones and
  this manifest was new at that point; `git show --stat 25f1e403` is the complete picture.

## Actual outputs (pasted, real — this worktree, 2026-09-27)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ git status --short
 M qa/feedback-inbox.md

$ git diff --stat
 qa/feedback-inbox.md | 139 +++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 139 insertions(+)
```

## Capability coverage

Not applicable in the usual (falsification-per-claim) sense — `core-invariants.md`'s mutation duty
applies to a unit that **adds or rewrites a test**; this unit adds none. The "capability" delivered
is a filed proposal, and its correctness is judged by the checker reading the criteria against
D-017/D-018 and the ground-truth files listed below, not by a red/green test pair. I am stating
this explicitly rather than fabricating a falsification table for prose.

## Gaps stated, not hidden

- **These are proposals, not contracts.** The checker may accept, reword, split, drop, or add to
  any of AI1–AI7 / AD1–AD7. Nothing here binds anyone until the checker writes the actual contract
  files.
- **AD6 and AD7 are scope calls, not derivations.** I flagged both explicitly in the inbox entry as
  my own additions beyond what D-018's text asks for (an absolute probe ceiling on top of the
  approval bound, and a durable refusal audit log). The checker or Umesh may judge either as
  unwanted scope creep onto a HELD capability, or as reasonable defense-in-depth consistent with
  D-016's inner-guard-inside-an-outer-boundary pattern for the crawler. I do not have a strong
  opinion either way and said so in the inbox entry.
- **AI2's "adversarial-string kind" clause extends D-017's text rather than quoting it.** D-017
  says a model may never *choose* which checks run; I read that as also covering a poisoned-context
  attempt to *steer* the choice via a fabricated kind string, which D-017's own text does not
  explicitly address. Flagged in the inbox entry as a place the checker may want to split the
  criterion into a D-017-verbatim half and a separate hardening half.
- **No ground truth surprise found that contradicts the plan.** I checked `docs/plan.md` (the
  numbered unit table and the "Held / blocked" section), `target.md` M11, `docs/spec.md` R30/R31,
  `qa/issues.jsonl` AT-638, and `docs/DECISIONS.md` D-017/D-018/D-039/D-040 against this unit's
  brief and found them consistent with each other and with the brief — no contradiction to report.
  One thing worth naming even though it isn't a contradiction: `docs/spec.md` R30 covers only
  "read-only discovery, deterministic signals, a check registry, behavioural checks graded by the
  existing judge" (T-150–T-153) — it does not mention T-154/T-155 at all, which matches the HELD
  status but means AD1–AD7 have no spec requirement row backing them yet; they rest on D-018 alone
  until R30/R31 is amended or a new row is added when T-154 is unblocked.

## Live browser evidence

Not UI-touching — no surface changed. `qa/feedback-inbox.md` and this manifest are the only paths
touched; neither renders anywhere in the product.

**Status: checked-PASS** — /checker cycle 1, verdict `qa/verdicts/t150-track-c-governance.md`
(`Cycle checked: 1`), verdict commit `a3d04cd2`, merged into master. T-150 marked `done` in
`.goal/goal.json`; `docs/FEATURES.jsonl` row **F-060** (`live`, `track-c-governance`).

**What the checker did that closed this unit, and what it changed about the proposals:**
- **Authored both contracts** — `qa/contracts/ai-target.md` (AI1–AI8) and
  `qa/contracts/adversarial.md` (AD1–AD7). T-150's `done_check` now genuinely passes on master:
  `check_deliverable.py --exists …` → `OK 2 deliverable(s) present`, `doctor: clean`, ruff clean.
  It could only ever be closed this way round — the maker creating those files would have been the
  maker writing its own ground truth.
- **Split my AI2** into AI2 (the D-017-verbatim table-mapping claim) and AI3 (the poisoned/
  out-of-table "kind" hardening), tagging the latter `[maker]` so it is independently attackable.
  That was the right call: I had fused an authorized claim with my own extension, which would have
  let my judgement inherit D-017's authority.
- **Refused to refile my AI3** (one `Catalog`, not a second) as a new criterion, because
  `catalog.md`'s CT7 already extends to Track C's catalog code by path — folding it in as a
  cross-reference instead, so one concept does not get two ground truths in two contracts. This is
  the "one concept, one place" rule applied to contracts, and I had missed it.
- **Accepted AD6/AD7** (my own additions: an absolute probe ceiling independent of the approval's
  bound, and an audit row on a refused attempt), tagged `[maker's addition, accepted]` rather than
  `[D-018]`, reasoned against D-016's real inner-guard-inside-an-outer-boundary precedent. Judged
  narrowing-only, so within checker authority and no gate opened — **flagged in the verdict so
  Umesh can reverse it**, since D-018 designs the approval as the sole control point.
- **Corrected a false claim in my filed criteria.** My AI3 draft asserted its own `Verify`
  (`grep -rn "class Catalog" src/autotester/schema/`) would return exactly one definition; run for
  real it returns **zero** — `schema/catalog.py` does not exist yet and T-125 is still pending. The
  checker documented it as the expected pre-T-125 state rather than a defect, but the draft stated
  as fact something it had not run.
- **Added a `Landing note` to every forward-declared criterion**, because a `grep` against a
  not-yet-existing Track C stage file **exits 2, not "no match"** — so a future checker could read
  "file not found" as "criterion satisfied". That is the AT-218 vacuous-guard trap one level up, and
  closing it was the most valuable thing this check did.

**Carried forward as open debt:** `ISS-t150-1` (low, spec-coverage-gap) — `docs/spec.md` R30 has no
requirement row for T-154/T-155, so AD1–AD7 rest on D-018's `Changes-authorized` alone.

**Still open, deliberately: `AT-638`.** It names five ungoverned capabilities; this unit answered only
Track C. **T-166, T-167, T-168 and T-171 still have zero checkable criteria** and need their own
governance unit, which must match the prefix and `Landing note` conventions the checker set here.

**A process gap of mine, recorded rather than hidden:** `autotester ledger relitigation` is supposed
to run *before* a unit is picked; I ran it after the PASS. It returned `no gate — no retired
features (rule)`, so nothing was revived and no harm followed, but the gate was checked in the wrong
order and that is worth the honesty.
