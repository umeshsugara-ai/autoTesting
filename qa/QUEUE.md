# qa/QUEUE.md — checker sweep queue (top-3 recommended next units)

Refreshed by `/checker sweep` **2026-09-09T02:15Z** (bound to `D:/autoTesting`). Prior sweep
2026-09-08T20:00Z, ~6h and 17 commits ago. Everything the prior sweep recorded was treated as
stale and re-derived from disk.

Docker not used; every command below ran natively under `uv`. Baseline was **bare `uv run pytest`**
(`addopts = "-q"` is already set, so a command-line `-q` gives `-qq` and hides the summary).

## Concurrency note (AT-101, respected)

No `git stash`, `git checkout` or `git restore` ran in the live tree. All three sabotages ran in a
`git archive HEAD` extract under the session scratchpad with `PYTHONPATH` pinned to the extract's
`src/`. Nothing was regenerated in the live tree — `git status --porcelain` is empty apart from the
files this sweep owns.

**A unit checker on `at206-guards-that-guard` was live for this entire sweep.** Its manifest, its
verdict and `qa/contracts/core-invariants.md` were **read but never written**; it moved
AT-210…AT-213 to `verified` mid-sweep and that is its call, not this sweep's. This sweep wrote only
`qa/issues.jsonl` (five new rows, appended), this file, and `qa/.last-sweep`.

---

## TOP-3 FROM THE BUSINESS-TRUTH CAMPAIGN (2026-09-09, verdict `qa/verdicts/business-truth-campaign-2026-09-09.md`)

These outrank the sweep list below. They are not contract violations -- every contract passed. They
are places where the shipped product does not do what the north star says, found by driving
AutoTester's own UI in a real browser and onboarding a product it had never seen.

1. **AT-241 + AT-239 + AT-240 -- reconnect the pipeline to a human.** `expand` (the repo's own
   "differentiator") and the whole coverage/VideoRequest loop have **zero production callers**; a
   newly onboarded product's only route to runnable is hand-writing cases. T-135 already exists for
   the reconnection -- this raises it to the top and adds the UI half: an operator needs a route to
   add a recording, review the FlowSpec, and generate cases without the CLI. T-100's own acceptance
   note ("full onboarding -> report without touching the CLI") is currently false.

2. **AT-242 -- a crawl that learned nothing must not report `completed`.** On an unseen login-gated
   product the crawler recorded 1 screen, 0 actions, 3 refusals in 3.4s and returned a success
   state. Needs a terminal state meaning "could not act", and -- once AT-240 is fixed -- an
   escalation (ask for a video / credentials) instead of a silent success.

3. **AT-243 -- re-check the UI units live.** Mode D has never run in this repo: 86 verdicts, zero
   `LIVE-BROWSER:` lines, `qa/evidence/` absent until this campaign. Every UI-touching PASS was
   granted without independent browser validation. **T-100 must be flipped back to `pending`** --
   handed over rather than done by the checker because a concurrent maker session was writing
   `.goal/goal.json` at the time.

Also open from this campaign: AT-244 (raw JSON 403 from a UI button), AT-245 (unknown run id renders
a fabricated pending run), AT-246 (unknown crawl id returns 200), AT-247 (UI hardcodes crawl
bounds), AT-248 (favicon console error on every page), AT-249 (**AT-229's evidence is misattributed
-- it blames `uv run pytest` for artifacts this campaign created; re-verify or withdraw**).


---

## Measured state

| | Prior sweep | **Measured now** |
|---|---|---|
| Ledger | 140 verified / 65 open / 0 fixed | **157 verified / 61 open / 0 fixed** (3 high, 22 medium, 36 low open) |
| Manifests / verdicts | 84 / 83 | **85 / 84** (the one gap is at206 cycle 2, live) |
| Goal tasks | 30/45 done (66.7%) | **31/45 done (68.9%)** — T-133 closed; matches disk |
| Test suite | 797 passed, 2 skipped | **818 passed, 2 skipped**, 0 `FAILED` |
| `ruff` | clean | **clean** |
| `doctor` | clean | **RED — 1 violation, `stale-generated: docs/SNAPSHOT.md`** (AT-214) |
| Ledger row coverage | — | `autotester ledger check`: every closed high-value task has a row (F-039 for T-133) |

## THE HEADLINE — the rate did not move. Say it plainly.

Seven issues have been filed since the last sweep (AT-207…AT-213). `found_by` is `checker-unit`
on **all seven**. **Maker self-caught: 0 of 7. Cumulative: 0 of 23.**

The at206 unit is the sharpest case and it is worth naming exactly, because that unit existed
*only* to remove vacuity from the AT-176/AT-178 guard. Its cycle-1 check produced four fresh
instances of the same class **inside the countermeasure**: AT-210 (the replacement assertion pins
nothing into existence — a `@parametrize` over collected sites, so a deleted site stops being a
test case rather than failing), AT-211/AT-212 (the hole reporter's exemptions are wide enough to
exempt what it exists to catch), AT-213 (the media guards assert ffmpeg's argument order but never
`argv[0]`). Fourth generation: fix → guard → guard-of-guard → guard-of-guard-of-guard, each
vacuous in a new way.

It did not move. That is the finding, not a softened version of it.

## The two countermeasures, judged

**The `&&` verify chain — it broke this round, by scope.** The last sweep called it "the only
countermeasure that has not yet produced an instance of the class inside itself." It has now.
`doctor` is RED on the committed tree at HEAD: commit `1e33584` appended D-021 and committed
`.claude/settings.json` + `docs/DECISIONS.md` without regenerating `docs/SNAPSHOT.md`. The chain
is a habit the maker applies to *unit* commits; its own *governance* commits sit outside it, and
nothing enforces it. A countermeasure whose coverage is decided per-commit by the actor it
constrains is the same recognition-without-prevention shape as the rest. Filed as **AT-214**
(high). Fourth doctor-red commit in this repo's history.

**C7's INCONCLUSIVE clause — it is holding, and it is worth keeping.** It fired twice in the at206
cycle: on the maker's own hole-detector sabotage, and (per the cycle-1 verdict) on the *checker's*
own harness — a null result that came back 823-passed, six *more* cases than baseline, correctly
reported INCONCLUSIVE rather than "the guard is vacuous", then re-run as a true revert of the fix
hunk and caught. This sweep reproduced the discipline independently on three fresh sabotages
(below) and all three discriminated first try.

But be precise about what it prevents. **C7 prevents a false accusation of vacuity; it does not
prevent vacuity.** It makes the checker's evidence honest, which is why the class keeps being
*found* rather than *avoided*. It is the same kind as before — better recognition, no prevention —
and it is doing that job well. AT-210…AT-213 are the proof of both halves at once.

## Sabotages run this sweep (C7-compliant: anchor matched exactly once + file re-read as changed)

In a `git archive HEAD` extract, over the contract criteria that landed with T-133's PASS:

| Sabotage | Criterion | Result |
|---|---|---|
| Drop `prompt_name` from the ensemble sort key | VL4 (AT-197's fix) | **CAUGHT** — 1 failure, `test_order_still_does_not_matter_with_TWO_prompts_per_chunk` |
| Key the observation cache by prompt NAME, not content digest | VL2 (AT-200's fix) | **CAUGHT** — 1 failure, `test_editing_a_prompt_invalidates_its_cached_answers` |
| `worst()` returns the first severity instead of the worst | I-VL5 | **CAUGHT** — 2 failures |

Zero INCONCLUSIVE. **VL2, VL4 and I-VL5 are genuinely exercised and non-vacuous** — the contract
text the t133 checker authored has teeth, and this is the first independent confirmation of it.

## Contract coverage

- **VL1c — the measured-placement half still has NO test. Third consecutive sweep, unchanged.**
  The maker's claim that AT-170 closed it does not hold, and I verified this independently rather
  than taking the ledger's word: `tests/test_media_shellout.py:61` and `:82` monkeypatch
  `subprocess.run` and assert `-ss` comes after `-i` plus the literal argument string. VL1c says in
  as many words that the argument order "is not itself the criterion" and that a future change "is
  judged against the measured property, not against the comment." Nothing runs a real ffmpeg and
  measures that the first frame IS the second named. **AT-170 itself is correctly `verified`** —
  its four degrade behaviours *are* guarded, and the at206 cycle-1 checker's S7–S10 produced 6
  failures against them — so this is filed separately as **AT-215** rather than as a reopen.
- **C9's `approved` is still unpinned (AT-156, open, unchanged).** `grep -c '"approved"'
  .goal/goal.json` → 0; the field exists in no goal task, so the honour-or-reject property is
  untested on both sides. The criterion discloses this in its own Verify clause, which is the
  honest posture, but it has not moved in three sweeps.
- **VL2–VL6 / I-VL5 / I-VL6 are committed and real.** Three of them proven non-vacuous above; VL6's
  scope note and I-VL6's provider-free clause read consistently against `stages/adjudicate.py` and
  `stages/issues.py` (no provider import in either).
- **C7 and C4** re-confirmed; C7 earned its keep twice more this cycle.

## Bypass detection — clean

All 17 commits since the last sweep accounted for. Code commits: `ac2a4b7` (T-133 cycle 2 →
manifest `t133-ensemble-and-issues` cycle 2 → PASS verdict `c4a28a5` → closed out `a8e1079`),
`9351387` + `eabc638` (at206 cycles 1 and 2 → manifest at both cycles; cycle-1 FAIL verdict
`fb5f734`; cycle-2 verdict live). `1e33584` touches `.claude/settings.json`, an enforcement path,
and carries its own authorizing entry — see below. Everything else is tick stamps, dashboard
refreshes and verdicts.

## `.claude/settings.json` — checked, and the finding does NOT stand

The maker asked this sweep to file it as an enforcement path modified without an authorizing
`docs/DECISIONS.md` entry carrying `Approved-by: Umesh`. Re-derived from disk: it does not stand.
**D-021 (2026-09-09, type: fix, status: ACTIVE)** exists, its `Changes-authorized` names
`.claude/settings.json (permissions block only; the hooks block is untouched)`, and its
`Approved-by` records Umesh answering an AskUserQuestion on 2026-09-09 with the breadth option
chosen. The working tree was dirty when the sweep was dispatched and is clean now — the entry and
the change landed together in `1e33584` during this sweep. Recorded here because a finding
withdrawn on evidence is worth as much as one filed on it.

One residual, stated not filed: the entry landed in the *same commit* as the change rather than
before it, so for the window in which the permissions were live the enforcement path was
unauthorized on disk. No harm resulted and the protocol's substance (a written, approved,
append-only reason) is met.

## Handshake, liveness, gates

- 85 manifests / 84 verdicts. The single gap is `at206-guards-that-guard` cycle 2 — **live**, its
  checker was mid-run for this sweep and moved AT-210…AT-213 to `verified` while the sweep ran.
  Not a dispatch gap.
- `t133-ensemble-and-issues`: manifest `checked-PASS`, verdict cycle 2 PASS, goal task `done`,
  ledger row F-039 present. Clean close-out.
- Historic `at015-at028` STALLED, unchanged and correctly so.
- `qa/.last-tick` fresh (this session), no `qa/.paused`. **Maker alive.**
- **Three gates open, none answered off-disk**, re-verified by grepping every verdict, manifest,
  tick entry, DECISIONS body and commit message since the last sweep for `23:59`, "end of day",
  "forgery", `ERP_EMAIL`/`ERP_PASSWORD`: `at110-approval-forgery`, `erp-credentials`,
  `at147-expiry-end-of-day` (its `**Answered:**` line is present but empty — a template stub, not
  an answer). `projects/erp/` still has no `.env`. `at106` and `at052` correctly carry real
  `Answered:` lines.
- Loop spec `qa/loop.md` present with all seven terminal states and a Human-gate line consistent
  with the adapter. No stall without a diagnosis.

## Silent-failure hunt (over code PASSed since the last sweep)

One finding, **AT-216** (medium): `src/autotester/stages/analyze_video.py:68-71` —
`try: Transcript.from_sidecar(...) except Exception: return None`, reached only when the sidecar
already `exists()`. A malformed transcript sidecar is collapsed into the same `None` as "never
transcribed", the cause is discarded, and the chunk is analysed with no narration while nothing
in the analysis, the coverage fields, or any log names the loss. VL1b treats narration as ground
truth, so this is not VL1's contract-mandated degrade (a *missing tool* producing a smaller
result) — it is a *present but broken* artifact read as absent. Exactly the AT-108/AT-114 class.

Also filed: **AT-217** (low) — `_repo_fingerprint` watches `docs/DECISIONS.md`, which the pair's
own `append_decision.ps1` rewrites, so a concurrent governance commit makes
`test_running_every_command_leaves_the_repository_untouched` report a **false** failure. This
sweep reproduced it by accident and exactly: a baseline run overlapping `1e33584` returned
`1 failed, 817 passed`, blaming the CLI for a write the CLI did not make; the settled re-run was
818 passed. Same shape as AT-189, but on a path that sits in the verify command every tick.

---

- GRILL: what to do about the vacuous-guard class — three consecutive sweeps have reported it unchanged across 20+ units, self-caught is 0 of 23, and every countermeasure so far is maker-authored, so the checker cannot settle it (AT-218)

## TODO — top 3 recommended next units

| # | Unit | Why now |
|---|---|---|
| 1 | **AT-214** (high) — regenerate `docs/SNAPSHOT.md` and put governance commits inside the verify chain | `doctor` is RED on HEAD right now. Smallest possible fix for the red; the durable half is making the chain something other than a habit the maker chooses to apply. |
| 2 | **T-136** (high) — Track A acceptance: erp1/2/3 scored against `ERP_Issues_Trainers.xlsx` with recall/FP numbers in the manifest | The maker's own stated next unit, and the first time the north star's actual scoreboard produces numbers. Fold in AT-207 (coverage reaches no reader) and AT-208 (`expected=None` declares a fragment complete) — both are in the surface it will touch. |
| 3 | **AT-215 + AT-216** (medium) — VL1c's measured-placement test, and bind the swallowed sidecar cause | AT-215 is a HIGH-criticality contract criterion uncovered for a third sweep, and every downstream issue timestamp rests on it. AT-216 is one `except` clause in the same subsystem. |

Open HUMAN_GATEs, which must not idle any of the above: `at110-approval-forgery`,
`erp-credentials` (blocks T-122/T-145), `at147-expiry-end-of-day`.
