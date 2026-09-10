# Verdict — t135-coverage-merge-expand (SECOND INDEPENDENT CHECKER, dual check)

**Date:** 2026-09-11
**Cycle checked:** 1
**Bound to:** `D:/autoTesting`
**Role:** checker **B** of a deliberate dual check (`.goal/goal.json` T-135 `criticality: critical`).
`qa/verdicts/t135-coverage-merge-expand.md` was **not read** — this verdict is formed from evidence
this checker produced itself. Any agreement or disagreement with checker A is coincidental.
**Contracts judged:** `qa/contracts/ingest.md` (I6 + the no-fire list deferring "merging into an
existing FlowSpec" to A6) · `qa/contracts/coverage.md` (V1, V3, V6, and V5 as an attack surface) ·
`qa/contracts/expand.md` (X6, the door rule) · `qa/contracts/review-gate.md` (R1) ·
`qa/contracts/core-invariants.md` C2 (reached through the manifest's own `doctor` verify command).

---

## VERDICT: **FAIL**

**SCOREBOARD: 6/6 named contract criteria met, 5/6 invariants hold** (the sixth is core-invariants
C2, broken by this unit's own `docs/ARCHITECTURE.md` edit and asserted-but-not-reproducible in the
manifest).

This is a *narrow* FAIL. The merge semantics — the thing this dual check exists to attack — are
correct, idempotent, and non-destructive under every attack I could construct. The failing item is
one line of documentation that puts a repo-wide gate in the red and makes the manifest's own
pasted evidence false.

---

## FAILURES

- **[core-invariants C2 / manifest verify #3]** sev: **high** · `uv run autotester doctor` reports
  **2** violations, not the "exactly one" the manifest claims: the pre-existing `root-clutter:
  AGENTS.md` (AT-283) **and** `architecture-too-long: docs/ARCHITECTURE.md — 151 lines > 150`,
  introduced by this unit's own single-line addition to `docs/ARCHITECTURE.md`. · Fix: move one row
  of ARCHITECTURE detail to a routed doc (or shorten the new row) and re-paste the real output ·
  issue: **AT-288**

Nothing else rises to a FAILURE line. AT-289/290/291/292 are filed as follow-on work, not as
charges against this cycle — see "Findings that are not failures".

---

## What I re-ran myself (never trusting the pasted outputs)

| Command | Manifest claimed | I got |
|---|---|---|
| `uv run pytest -q` | exit 0 | **exit 0**, full suite green (1 skip visible in tail) ✔ |
| `uv run ruff check src tests scripts` | exit 0 | **`All checks passed!`, exit 0** ✔ |
| `uv run autotester doctor` | exit 1, **exactly one** violation | **exit 1, TWO violations** ✘ (AT-288) |
| `uv run python scripts/check_deliverable.py --exists …` | exit 0 | **`OK 2 deliverable(s) present`, exit 0** ✔ |
| `uv run pytest tests/test_merge_flowspec.py tests/test_coverage.py -q` | exit 0 | **28 passed, exit 0** ✔ |

The `doctor` regression is deterministic, not environmental: `git show HEAD:docs/ARCHITECTURE.md |
wc -l` = 150, working copy = 151, `git diff --stat` = 1 insertion (the `merge_flowspec` concept→file
row). `doctor.py:145-156` counts with `splitlines()`, so CRLF plays no part.

### Sabotage — both re-derived, not read

Run in an isolated worktree copy under the scratchpad, with `autotester` confirmed to resolve to the
copy (`.../scratchpad/sab/src/autotester/core/urls.py`) before trusting any result:

1. `core/urls.py::_split` reverted to a bare `urlsplit(url)` →
   `test_templating_a_templated_url_is_a_no_op_in_both_modes`,
   `test_a_host_ful_pattern_and_a_fresh_url_agree_on_the_path` and
   `test_a_screen_learned_from_a_video_is_not_a_permanent_gap` **all three FAIL**, exactly as
   claimed. The AT-287 fix is load-bearing.
2. `resolve_requests`' body replaced with `return []` → **5 FAIL**:
   `test_a_request_the_merged_spec_now_answers_is_closed`,
   `test_resolving_twice_does_not_rewrite_an_already_closed_request`,
   `test_the_full_loop_closes_a_gap_end_to_end`,
   `test_an_id_bearing_route_is_answered_by_a_templated_pattern`, and the CLI door test
   `test_the_cli_merge_closes_the_request_that_asked_for_the_recording`. The manifest predicted
   three of these; the real count is higher, which is stronger, not weaker.

---

## The attacks I was asked to press

### 1. Can a merge LOSE or MUTATE a human-reviewed screen or flow? — **No.**

Probed against production code, not tests:

- **Same id, different content (screen).** Existing `('scr_1','Login',url_pattern=None)` +
  incoming `('scr_1','Login',url_pattern='/login')` → `merge_flowspec` returns the **existing object
  itself** (`m is existing`). The human's row is untouched; the incoming row is dropped whole.
  Nothing reviewed is mutated. (The *other* consequence of that drop is AT-290, below.)
- **Flow whose id collides / entry_screen collides.** Existing `flow_1 'Checkout' → scr_x`, incoming
  `flow_1 'Checkout' → scr_y` with 1 step → the existing flow survives **byte-identical**
  (`m.flows[0] == existing.flows[0]`), `scr_y` is added as a new screen, the incoming flow (and its
  step) is dropped. No dangling reference either way: an incoming flow whose `entry_screen` names a
  brand-new screen resolves because that screen is added in the same copy, and one naming an
  existing id resolves to the existing screen. `FlowSpec.screen(flow.entry_screen)` returned
  non-`None` in every case I built.
- **End-to-end, through the production door** (`cli_video::_merge_into_reviewed`, throwaway
  `AUTOTESTER_ROOT`): an APPROVED spec with a hand-corrected `Login` screen and a `Sign in` flow,
  merged with a video-derived spec → after three merges the human's flow list is `==` its original
  and `scr_login` is byte-identical to the original object, while the new screen is appended.
- **Visible in a real browser too:** after driving the UI merge, `/projects/checkerdemo/flowspec`
  still lists the human's `Sign in` flow (4 steps) beside the newly added screen.

Verdict on this attack: **I6 holds, and holds by construction** — `model_copy(update=…)` only ever
appends to `screens`/`flows`/`conflicts`.

### 2. Is the idempotence claim real, and is the review gate ever re-armed forever? — **Yes real; no permanent block.**

- Merging the same spec **4×**: version `v1→v2` on the first call and **frozen at v2** thereafter;
  screens stay 2; the review note is written once. Second and later calls return the existing object.
- **Specs that differ only in conflicts**: incoming `conflicts` are ignored entirely and the merge
  is a no-op (`m3 is h3`). A conflict already recorded is never re-recorded — a genuine conflicting
  screen merged 3× produced `conflicts=1`, not 3.
- `resolve_requests` called 2nd and 3rd time → **0** closed, and `requests.jsonl` stayed at exactly
  the original row count (it is an `upsert_jsonl`, not an append) — no row duplication, no re-write
  of an already-`fulfilled` request.
- **The R1 denial-of-service scenario does not occur.** After a merge re-arms the gate to `DRAFT`,
  I re-approved through `stages/review.approve` and merged the *same* spec again: the spec stayed
  **`approved`**, and `require_reviewed` did not raise. The gate is re-armed exactly once per
  genuinely-new learning, so EXPAND is never permanently blocked.

### 3. Can `_answered_gap_ids` close a request it should not? — **No; it errs strictly safe.**

Built a store with six real requests via `queue_requests(request_for(gap))` and resolved against a
spec covering `demo.test/students/{id}` (host-ful, the I7 shape) and `/reports`:

| gap | closed? |
|---|---|
| `(project=p, kind=route, /students/{id})` | **fulfilled** ✔ (correct — and this is the AT-287 payoff: a host-ful stored pattern matched a host-less gap path) |
| `(p, screen, /reports)` | **fulfilled** ✔ correct |
| `(p, **field**, /students/{id})` | **left OPEN** ✔ |
| `(p, **class**, /students/{id})` | **left OPEN** ✔ |
| `(**q**, route, /students/{id})` — another project | **left OPEN** ✔ no cross-project leak |
| `(p, route, /billing)` — genuinely unanswered | **left OPEN** ✔ |

The hardcoded `_GAP_KINDS = ("route","screen")` against a schema documenting `route | screen | field
| class` is therefore **conservative, not dangerous**: the un-listed kinds can only ever fail to
close, never wrongly close. It is also unreachable today — `diff_coverage` only ever mints `route`
and `diff_crawl` only `screen`; nothing in `src/` constructs a `field` or `class` gap. Cross-project
safety comes free: `spec.project` is part of the hashed payload.

**Path collision after templating:** a stored pattern `/orders/12345` templates to `/orders/{id}`
and closes an `/orders/{id}` ask. That is `coverage.md` V1's own rule applied symmetrically — the
request is judged answered by exactly the normaliser that judged it unanswered — not a defect.

**Idempotence of `url_template` itself, re-derived over 17 inputs × both `keep_host` modes:**
`T(T(T(u))) == T(T(u)) == T(u)` in **every** case, including `demo.test`, `http://demo.test`,
`a.b:8080/x/2026-01-02/`, `//demo.test/x`, `/a//b/`, `''` and `'/'`. Zero non-idempotent inputs.
The `_LOOKS_LIKE_HOST` heuristic the maker flagged (judgement #3) does mis-read a *relative* path
whose first segment carries a dot — `url_template('v1.2/foo', keep_host=False)` → `'/foo'` — but
every `url_pattern` this system stores is either absolute (`/…`, from `explore_merge`) or host-ful
(from `ingest`), and both are handled correctly. **Ruled acceptable and correctly disclosed.**

### 4. Does anything write `RequestStatus.DISMISSED`? — **No. Still dead.**

`grep -rn DISMISSED src/ tests/` → only the enum definition (`schema/enums.py:169`) and a docstring
in `store/request_store.py`. `update_request` *could* carry it; nothing does. This is unchanged by
the unit and violates no criterion — recorded here so the next sweep does not re-discover it as new.
`FULFILLED` and `fulfilled_by_source`, by contrast, are now genuinely written (confirmed on disk).

### 5. Can `unreached_screens` become a `VideoRequest` (coverage.md V5)? — **No.**

`grep -rn unreached_screens src/` → two hits only: its definition in `stages/coverage.py:119` and
`ui/routes_crawls.py:150`, where it is passed to `crawl_view.coverage_card` for **rendering**.
`queue_requests` has exactly two callers, `routes_runs.py:141` (`diff_coverage`) and
`routes_crawls.py:234` (`diff_crawl`) — both the gap direction. This unit opened no new path;
`merge_flowspec.py` does not import `unreached_screens` at all. **V5 and V6 both hold.**

---

## LIVE-BROWSER

`qa/evidence/browser-t135-coverage-merge-expand-2026-09-11-checkerB/report.json`

Mode D run by this checker on its **own** port (8791) with its **own** Playwright Chromium. The
maker's `report.json` and screenshots were not opened. The unit is UI-touching **indirectly**:
`core/urls.py` changes what `stages/coverage.py` reports and `ui/routes_crawls.py:150` renders
exactly that.

- **4 pages, 0 console errors, 0 console warnings** (all levels, whole session). Note that AT-248's
  permanent favicon error is gone, so a real error would not be lost in a baseline of one.
- **Interaction 1 — clicked "Merge these screens into the FlowSpec"** on the checkerdemo crawl page.
  This is the seam whose helper the unit renamed (`_disagreement` → `disagreement`). Asserted state
  change on disk: `flowspec.json` v1→v2, screen `node_81feb20` added at `url_pattern '/'`, review
  `needs_edit → draft`, `conflicts: []` (correct — no existing screen claimed `/`). The renamed
  function is live on the real UI path and behaves identically.
- **Interaction 2 — reloaded and re-read the coverage card**: it flipped from "1 screen(s) the
  FlowSpec cannot name: `/`" to "0 … none", and "0 known screen(s) this crawl never reached". The
  surface AT-287 feeds renders correctly and is unregressed.
- **Interaction 3 — followed "Add a recording"** from the FlowSpec page: it lands on
  `/projects/{slug}/sources`, which registers and uploads recordings and offers **no ingest action
  at all**. This independently confirms the manifest's declared gap #2 — the CLI is this stage's
  only door — rather than taking the maker's word for it.
- **Real subprocess CLI:** `autotester ingest run … --merge --replace` → exit 2 with the refusal
  text and **zero writes** (the guard is the first statement in `run_cmd`, before `ProjectStore` is
  even constructed) — X6's "every refusal behind the door writes nothing". `ingest run --help`
  documents `--merge` as a real option.
- **Cleanup:** `projects/checkerdemo/flowspec.json` was restored byte-for-byte from a pre-interaction
  snapshot. `requests.jsonl` was never modified — which is itself finding AT-289.
- **Disclosed gap (a SKIP is a stated gap, never a pass):** no live vision provider was called; no
  suitable recording exists in-repo and `--provider mock` has no queued `see_video` response. The
  observation half is stubbed. Everything this unit *owns* — `merge_flowspec`, `resolve_requests`,
  `open_requests`, the CLI door, `urls._split` — was executed for real against a real on-disk store.

---

## Rulings on the four judgements the maker offered

1. **Was fixing AT-287 inside this unit correct, or scope creep? — CORRECT, not scope creep.**
   I verified the causal claim rather than accepting it: `_answered_gap_ids` normalises with
   `url_template(..., keep_host=False)`, and `stages/ingest.py` stores `url_pattern` host-ful (I7).
   With the old `_split`, `'demo.test/students/{id}'` re-templates to `'/demo.test/students/{id}'`,
   which hashes to a different `CoverageGap.id` than the `'/students/{id}'` the request was raised
   on — so `resolve_requests` could **never** close a video-answered gap. The unit's deliverable is
   unreachable without it. Filing it as its own id and defending it with three tests is the right
   shape.
2. **`_disagreement` → `disagreement`. — Ruled CORRECT; do not revert.** A second seam
   (`merge_flowspec._conflicts_for`) now calls it, and a cross-module private is worse than a public
   name; the rename is what stops the video seam and the crawl seam drifting apart (C1). Behaviour
   is unchanged and I confirmed that through the live UI, not by reading the diff. What is stale is
   the *contract prose*: `explore.md` X14 line 164 still names `_disagreement` — filed as **AT-292**
   for a routine amendment by the primary checker or the next sweep. I deliberately did not edit
   `qa/contracts/` myself: two checkers are writing this project's `qa/` concurrently and a contract
   is not worth a lost write.
3. **The `_LOOKS_LIKE_HOST` heuristic. — Accepted, and the assumption is sound.** Attacked directly
   (see §3 above): the failure shape requires a *relative* path whose first segment contains `.` or
   `:`, and every `url_pattern` in this system is absolute or host-ful. Zero non-idempotent inputs
   across my 34 probes. Correctly disclosed rather than hidden.
4. **AT-287 filed by the maker, not the checker. — Accepted as filed, not re-worded.** The id is
   cited in shipped code comments; leaving it unfiled would dangle a reference. The row's substance
   matches what I reproduced. I have left its status at `fixed` rather than promoting it to
   `verified`, because the unit it belongs to is FAILing this cycle — it should move to `verified`
   at the close-out re-check, which is the normal `fixed → verified` transition.

---

## Findings that are not failures (filed, not charged)

- **AT-289 (medium)** — the closing half of the loop is wired to **one** seam. The UI's crawl-merge
  button folds in the answering screens and leaves the request that asked for them **OPEN**;
  `resolve_requests` is imported only by `cli_video.py`. Measured live: the coverage card correctly
  went to 0 gaps while `requests.jsonl` stayed `status: open`. This is precisely the asymmetry
  `coverage.md` V6 was written to prevent, now reappearing on the closing side. Not charged, because
  no criterion in the four contracts I was given names the crawl-merge seam — but it is the single
  most valuable follow-on unit here.
- **AT-290 (medium)** — `Screen.id` is content-addressed on `(name, signals)` only, so a
  re-recording of a screen the FlowSpec already names can never teach its `url_pattern`: the row is
  dropped whole and no `Conflict` is raised (`_conflicts_for` iterates only `added`). Since I7 makes
  `url_pattern=None` the *normal* outcome for a video with no visible address bar, this is a common
  shape, not a corner — and in it the recorded answer lands but the gap stays open. Not silent
  (`open_requests` prints "still unanswered"), which is why it is a finding and not a failure.
- **AT-291 (low)** — a merge that taught **nothing** still closes requests and stamps
  `fulfilled_by_source` with that unrelated recording's id. Reproduced. Closing may be right; the
  attribution is a false statement about which video answered the ask.
- **AT-292 (low)** — contract staleness, `explore.md` X14 (see ruling 2).
- **Observation, not filed:** the ledger contains a pre-existing duplicate id (`AT-282` ×2) — present
  at `HEAD`, not introduced here. This unit's ledger diff is semantically **only** the AT-287
  addition; the AT-244…AT-248 lines in `git diff` are pure JSON whitespace reformatting with
  byte-identical content, which I verified by parsing both revisions and diffing the sorted objects.
  Harmless, but the maker should not be rewriting checker-owned rows even cosmetically.

---

## EXPLANATION

I re-ran all five verify commands and both sabotages myself; four commands reproduce exactly, and
the second sabotage is stronger than claimed (5 failures, not 3). The merge semantics survived every
attack in the dispatch: no reviewed screen or flow can be lost or mutated (`model_copy` only ever
appends), idempotence is real over 4× repeats and holds for `resolve_requests`' upsert as well, the
review gate re-arms once per genuine learning and re-approval survives a re-merge — so there is no
silent denial-of-service on EXPAND — `_answered_gap_ids`' hardcoded kinds err strictly toward
leaving requests open and never leak across projects, nothing writes `DISMISSED`, and no path was
opened from `unreached_screens` to `queue_requests`. Mode D on my own port and browser found 0
console errors over 4 pages and 3 asserted interactions.

The FAIL is one line: this unit's own `docs/ARCHITECTURE.md` addition put the file at 151 lines and
turned `autotester doctor` red on a second violation, while the manifest asserts and pastes "exactly
one". Two things are wrong there and only one of them is the doc — a manifest that pastes an output
the checker cannot reproduce is the failure mode the re-run rule exists to catch, and the maker
should re-paste real output next cycle rather than the output of an earlier tree state. Fix the line
budget and this unit is a PASS on my reading; nothing in the merge logic itself needs to change.
