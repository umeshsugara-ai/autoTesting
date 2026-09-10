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


---

# Verdict — t135-coverage-merge-expand · CYCLE 2 (SECOND INDEPENDENT CHECKER, dual check)

**Checker:** checkerB — the `.b.md` lane. `qa/verdicts/t135-coverage-merge-expand.md` was **not
read, not appended to, not overwritten**. Formed from evidence this checker produced itself.
**Date:** 2026-09-11
**Cycle checked: 2**
**Bound to:** `D:/autoTesting`
**Adapter:** `qa/adapter.json` — coding; verify = shell; isolation = worktree-copy; done = audit-pass.
**Isolation:** `git archive HEAD` (191be93) extracted outside the repo; `autotester.__file__`
printed and confirmed to resolve to the extract before any sabotage result was trusted.
**Contracts judged:** `ingest.md` I6 · I7 (+ the no-fire list deferring "merging into an existing
FlowSpec" to A6) · `coverage.md` V1, V3, V6 · `expand.md` X6 · `review-gate.md` R1.

```
VERDICT: FAIL
SCOREBOARD: 6/7 criteria met, 6/7 invariants hold
FAILURES:
- [I7] sev: high · A screen learned from a video and the same screen found by a crawl STILL do not
  collapse to one row: url_template swallows the host of a SCHEMELESS url, and a schemeless address
  bar is exactly what this repo's only real video data contains · fix direction: stop handing
  url_template a string whose host position is unknown - normalise at the ingest boundary (prepend a
  scheme, or record schemelessness on ObservedScreen); the defending test must use a schemeless url
  on the video side and a scheme-ful one on the crawl side · issue: AT-294 (re-derived
  independently here; already open, filed by checkerA)
- [I6/A6-merge] sev: medium · merge_flowspec._learned_url_patterns can fill a None url_pattern that
  an existing screen already claims, producing two screens at one pattern with NO Conflict, because
  _conflicts_for iterates only `added` · fix direction: pass the learned-pattern fills through
  `disagreement` before applying them · issue: AT-295 (re-derived independently here; already open)
- [manifest claim] sev: medium · The manifest lists AT-290 as addressed, but the
  projects/erp/screenmap.json repair is an UNTRACKED, unreproducible hand-edit with no migration -
  the code regenerates the corruption it removed, so AT-290 is not durably fixed and stays open ·
  fix direction: a committed, idempotent, tested migration under scripts/, run AFTER the AT-294
  producer fix; raise a HUMAN_GATE rather than edit real project artifacts in-flight · issue: AT-297b
LIVE-BROWSER: qa/evidence/browser-t135-coverage-merge-expand-2026-09-11-checkerB-c2/report.json
ISSUES-WRITTEN: AT-297b
EXPLANATION: Every pasted output in the manifest reproduces exactly, all four declared sabotages are
load-bearing, and the AT-289 fix is confirmed live through the product's own button on my own port
with my own browser and zero console errors. The unit still fails because cycle 2's strategy change
fixed the producer DISAGREEMENT without fixing the defect: canonicalising to keep_host=False makes
both seams call the same function, but on a schemeless url - the only url shape this repo's real
recorded data actually contains - the host is still swallowed into the path, so I7's stated purpose
is unmet and the maker's hand-repair of the affected artifact is one `analyze` away from being
undone. The new _learned_url_patterns path also bypasses the conflict rule this same unit
centralised.
```

---

## 1. The manifest's pasted outputs — all reproduce exactly

| Command | Manifest claims | I measured | |
|---|---|---|---|
| `uv run pytest -q` | 1032 passed, 2 skipped, exit 0 | junitxml `tests="1034" failures="0" errors="0" skipped="2"`, exit 0 → **1032 passed / 2 skipped** | OK |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 | `All checks passed!`, exit 0 | OK |
| `uv run autotester doctor` | exit 1, **exactly one** violation (AGENTS.md) | `root-clutter: AGENTS.md …` → `1 violation(s)`, exit 1 | OK |
| `check_deliverable.py --exists …` | exit 0 | `OK 2 deliverable(s) present`, exit 0 | OK |
| `pytest tests/test_merge_flowspec.py tests/test_coverage.py -q` | 24 passed | 24 passed, exit 0 | OK |

AT-288 is genuinely closed: doctor is back to the single certified AT-283 baseline, and the cycle-1
"27 vs 28" and "2 violations" discrepancies are gone.

## 2. The four declared sabotages — all load-bearing

Run in the `git archive HEAD` extract, never the live tree; anchor-hit count asserted `== 1` before
each edit; the file restored from a pristine copy after each.

1. `stages/ingest.py` `keep_host=False` → `True`: **2 fail** —
   `test_an_observed_url_is_templated_the_same_way_the_crawler_templates_it` and
   `test_a_video_screen_and_a_crawled_screen_of_one_url_produce_one_pattern`
   (`AssertionError: assert 'demo.test/trainers/{id}' == '/trainers/{id}'`). As claimed.
2. `resolve_requests` body → `return []`: **8 fail** across `test_coverage_wiring.py`,
   `test_merge_flowspec_cli.py`, `test_merge_flowspec_requests.py`. The manifest predicted 5; the
   real number is higher, not lower.
3. Delete the `resolve_requests(...)` call at `ui/routes_crawls.py:252`: **1 fail** —
   `test_the_merge_button_closes_the_request_the_crawl_answers`. As claimed.
4. `_learned_url_patterns` → `{}`: **2 fail** —
   `test_a_re_recording_teaches_a_url_pattern_the_spec_lacked` and
   `test_learning_a_url_pattern_closes_the_request_that_asked_for_it`. As claimed.

**Environmental, not a defect:** `tests/test_ui_sources.py::test_uploaded_recordings_are_gitignored`
fails in the extract *baseline* with no sabotage applied — the extract has no `.git`. Green in the
repo. Recorded so nobody charges it to the maker.

## 3. Data correctness and migration — where cycle 2's strategy change actually costs

**The stored-shape sweep is complete, and I did not take the maker's word for it.**
`grep -rl url_pattern projects/` over all **989** files under `projects/` returns exactly two:
`projects/erp/screenmap.json` (the 3 repaired rows) and `projects/checkerdemo/requests.jsonl`
(prose inside a request prompt, not a stored pattern). No `flowspec.json`, no `crawl/**`, no
`cases.jsonl`, no `runs/**` carries a `url_pattern` at all. **The maker's "3 rows is the complete
set" claim is correct** — that part I uphold.

**No code path writes a host-ful `url_pattern` any more, and there is no lookalike templater.**
All four producers pass `keep_host=False` (`ingest.py:99`, `explore_merge.py:73`,
`product_map.py:40` and `:60`, `screen_identity.py:53`). `schema/screen_graph.py`'s
`ScreenNode.url_template` is a *field* holding a browsing identity, and `explore_merge.py:65-73`
deliberately re-derives the pattern from `url_example` rather than reusing it. That much is clean.

**But `keep_host=False` is not the same as host-less.** Measured in the extract:

```
url_template('vidysea.com/erp/trainers',         keep_host=False) -> '/vidysea.com/erp/trainers'
url_template('https://vidysea.com/erp/trainers', keep_host=False) -> '/erp/trainers'
```

`urlsplit` has no `//` to key on, so the host lands in `.path` and survives as a path segment.
Idempotence now holds for every input I probed — that much cycle 2 did fix — but **the two seams
still disagree**, which is I7's entire point. This is not a hypothetical shape: all three
`projects/erp/sources/*/analysis.json` records carry `url: 'vidysea.com/erp/trainers'`, schemeless,
because a browser hides the scheme and the vision model transcribes what it sees. The new defending
test picks `https://demo.test/trainers/123?tab=2` — the one input shape where the seam agrees.

**The repair is undone by the code that is supposed to have been fixed.** I ran
`stages/product_map.build_screen_map(ProjectStore('erp'))` read-only (it returns a `ScreenMap`; the
caller persists) against the real on-disk analyses with committed cycle-2 code:

```
REGENERATED (current code, real erp data)          ON-DISK (maker-repaired)
  Trainers                    -> '/vidysea.com/erp/trainers'   '/erp/trainers'
  Trainers List               -> '/vidysea.com/erp/trainers'   '/erp/trainers'
  Trainers List - Edit Drawer -> '/vidysea.com/erp/trainers'   '/erp/trainers'
```

**Was rewriting stored project data inside a unit cycle appropriate? No.** Three reasons, each
verified rather than argued:

- `git ls-files --error-unmatch projects/erp/screenmap.json` → *"did not match any file(s) known to
  git"*. The repaired artifact is **untracked**; `git show --stat d21440c` lists 18 files, none
  under `projects/`. The maker's own proposed isolation, `git archive HEAD`, does not contain the
  repair — so the change under review and the change that was made are not the same change.
- The backup `.work/screenmap.json.bak` sits under `.gitignore` line 10. The edit and its undo are
  both one `git clean -xdf` from gone.
- The value written is one the code cannot produce, and nothing tests it. This is a migration
  wearing a unit's clothes. It needed a committed, idempotent, tested script under `scripts/`,
  sequenced **after** the producer fix so it writes the value the code produces — or a HUMAN_GATE.
  AT-290 is therefore not durably fixed. Filed as **AT-297b**.

Consequence for this unit specifically: `coverage._path_of` is idempotent, so a stored
`/vidysea.com/erp/trainers` will never match an observed `/erp/trainers`; the video-learned screen
stays invisible, the gap stays open, and `resolve_requests` still cannot close it. That is AT-287's
original symptom, alive for real data.

## 4. `_learned_url_patterns` vs `_conflicts_for` — the gap is real

`_conflicts_for(existing, added_screens, source)` (`merge_flowspec.py:71`) iterates **only**
`added_screens`. Patterns that `_learned_url_patterns` writes onto screens that already exist never
pass through `disagreement`. Executed in the extract:

```
existing (APPROVED): scr_a 'Trainers List' url_pattern='/erp/trainers'
                     scr_b 'Trainers Grid' url_pattern=None
incoming recording : scr_b 'Trainers Grid' url_pattern='/erp/trainers'  (same id -> not "added")

merged screens  : [('Trainers List','/erp/trainers'), ('Trainers Grid','/erp/trainers')]
DUPLICATE       : ['/erp/trainers']
merged.conflicts: []            <-- GAP CONFIRMED
```

`disagreement` returns a real `Conflict` for that same pair when called directly (different names,
non-structural clash), so the rule this unit deliberately centralised — one concept, one place — is
bypassed by the very path cycle 2 added. `by_pattern` is also built from `existing.screens` before
the fill, so ordering cannot save it.

## 5. Idempotence end to end after the learning change — holds

```
in-process, re-recording that only teaches a pattern:
  merge #1: version=2 screens=2 review=draft (changed)
  merge #2..#4: the identical object is returned; version stays 2, review not re-armed

in-process, genuinely new screen:
  merge #1: version=2 screens=2 ; merge #2..#4: unchanged

live UI (my own browser, port 8791):
  click #1: version=2, 1 screen, review=draft, request -> fulfilled
  click #2: version=2, 1 screen, review=draft, request stays fulfilled
  click #3: version=2, 1 screen, review=draft, request stays fulfilled
```

The `_learned_url_patterns` fill is self-limiting (`lacking` no longer contains the screen once it
has a pattern), so the second merge is a genuine no-op. R1 holds: a real change re-arms the review
gate to DRAFT, a no-op does not.

## 6. Mode D — my own port, my own browser, my own sandbox

`qa/evidence/browser-t135-coverage-merge-expand-2026-09-11-checkerB-c2/report.json`

Real `uvicorn` on **port 8791** (verified free before launch, killed after), pointed by
`AUTOTESTER_ROOT` at a **copy** of `projects/` in scratch so no real artifact was written by this
check. Own `playwright.chromium` instance — not the shared MCP browser, not the maker's PNGs.
**7 pages, 0 console errors, 0 page errors in total.**

The interaction that matters — AT-289, the only door an operator has:

```
requests BEFORE : req_bb8e26317632  gap_2a0765d4adf2  status=open  fulfilled_by=null
  -> clicked the real "Merge these screens into the FlowSpec" button
requests AFTER  : req_bb8e26317632  gap_2a0765d4adf2  status=fulfilled
                  fulfilled_by_source=crawl_01M22B474QM5956JR0ZQA8M9M4
flowspec AFTER  : v2, 1 screen, review=draft, url_patterns=['/']
```

**AT-289 is genuinely fixed** — cycle 1's finding (gap closes, ask stays OPEN) does not reproduce.
`fulfilled_by_source` correctly falls back to the crawl id because a crawl-merged screen carries no
`source_ref`; that is the honest answer, not the AT-291 false attribution.

Also visited: `/`, `/projects/checkerdemo`, `/projects/checkerdemo/crawls`, the crawl detail (the
"Against the FlowSpec" coverage card renders), `/projects/checkerdemo/requests`, and both
product-map pages. `/projects/erp/product-map` renders `/erp/trainers` today (screenshot in the
evidence dir) — which is precisely the AT-297b problem: **the human-visible surface looks repaired
while the generator that feeds it disagrees with it.**

## 7. The CLI door (X6) — exercised live, not read

```
$ autotester ingest run --help
  --replace   overwrite an APPROVED FlowSpec, discarding its review
  --merge     fold into the existing FlowSpec instead of replacing it, and close
              the video requests this recording answers

$ autotester ingest run checkerdemo <src> --merge --replace
  --merge and --replace are opposites: merge keeps the reviewed spec, replace discards it. Pick one.
  exit=2
```

A refusal that exits non-zero with a message naming the choice, writing nothing. The manifest's
declared gap (no UI ingest route) is honest — `persist_ingest`/`ingest_video` appear only in
`cli_video.py` — and the crawl-merge button covers the seam that does exist.

## 8. Criterion-by-criterion

| Criterion | Verdict | Evidence |
|---|---|---|
| **I6** — persistence; APPROVED never silently overwritten; merge is where the answer lands | MET | full suite green incl. `test_ingest_persist.py`; `--merge`/`--replace` refuses with exit 2; live merge kept the reviewed rows and added only new ones |
| **I7** — one templater; video and crawl collapse to ONE row | **NOT MET** | `'vidysea.com/…'` → `/vidysea.com/erp/trainers` vs `'https://vidysea.com/…'` → `/erp/trainers`; regenerating the real erp data reproduces the corruption (AT-294) |
| **V1** — both sides normalised by `url_template(keep_host=False)` | MET (mechanism) | `coverage.py:30`; idempotent for every input probed. Its *purpose* is defeated upstream by I7 |
| **V3** — exactly one `VideoRequest` per gap, idempotent | MET | 3 live merge clicks left exactly one request row |
| **V6** — wired to BOTH entry points, closing side included | MET | sabotage 3 (UI seam) and sabotage 2 (both seams) fail as required; confirmed live through the button |
| **X6** — the stage has a door; refusals write nothing | MET | `autotester ingest run --merge` live; mutual-exclusion refusal exits 2 |
| **R1** — a changed spec is unreviewed and blocks | MET | live: review → `draft` after a real merge; a no-op merge does not re-arm |

## 9. Judgements the manifest asked for

1. **Was fixing AT-287 inside this unit correct, or scope creep?** Correct — `resolve_requests`
   cannot close a video-answered gap while the two seams produce different patterns, so it is
   genuinely on the critical path. The problem is not that it was fixed here; it is that it is
   **still not fixed**.
2. **`_disagreement` → `disagreement`.** Fine. Behaviour identical, the one-place rule preserved,
   and it is what lets the video seam and the crawl seam share the rule. The stale `explore.md` X14
   prose is already tracked as AT-292 — a contract edit, not a code defect.
3. **The `_LOOKS_LIKE_HOST` heuristic.** Moot — deleted in cycle 2, and deleting it was right.
   Inferring host-ness from a schemeless string is unwinnable; the residual defect is that the
   system still *feeds* `url_template` schemeless strings.
4. **AT-287 filed by the maker.** Acceptable as a one-off given the id is cited in shipped code
   comments. Not charged.
5. **(unasked, ruled anyway) The screenmap repair.** Not appropriate as an in-unit edit — see
   AT-297b. Ruled: it needed its own migration unit, sequenced after the producer fix.

## 10. Note on independence

I did not open `qa/verdicts/t135-coverage-merge-expand.md`. I did read `qa/issues.jsonl` (protocol
step 5 requires checking the manifest's claimed `Issues addressed` against the ledger) and found
that checkerA had already filed **AT-294** and **AT-295** for two of the three defects above, with
evidence matching mine. I reached both independently — from the schemeless-url probe and from the
`_conflicts_for` iteration respectively — before reading those rows, and I have **not** allocated
duplicate ids for them, per AT-293's ruled `b`-suffix convention. Two blind checkers converging on
the same two defects is the dual check working, not a wasted cycle. My third finding, **AT-297b**
(the repair's durability and the propriety of rewriting real project data inside a unit cycle), is
new.

---

# Verdict — t135-coverage-merge-expand · CYCLE 3 (SECOND INDEPENDENT CHECKER, dual check)

**Cycle checked: 3**
**Date:** 2026-09-11
**Project root:** `D:/autoTesting` (bound)
**Commit under test:** `cc00e9b`
**Contracts:** `qa/contracts/ingest.md` (I6, I7, no-fire list) · `qa/contracts/coverage.md` (V1, V3,
V6) · `qa/contracts/expand.md` (X6) · `qa/contracts/review-gate.md` (R1)
**Independence:** this checker did NOT read `qa/verdicts/t135-coverage-merge-expand.md`, the maker's
browser evidence, or checker A's browser evidence. Its own port, its own uvicorn, its own Chromium.
New issue ids carry the `b` suffix per AT-293's ruling.
**This was the LAST fix cycle.**

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, 7/7 invariants hold
FAILURES: none at criterion level
LIVE-BROWSER: qa/evidence/browser-t135-coverage-merge-expand-2026-09-11-checkerB-c3/report.json
ISSUES-WRITTEN: AT-298b (high), AT-299b (medium) — neither is a criterion failure
```

## 1. The core promise, driven end to end by this checker

The unit's promise is a closed loop, so I drove the loop rather than judging its parts.

| Step | How it was driven |
|---|---|
| an unknown route is observed by a run | results + run written to a real on-disk store, then **`ui/routes_runs.py::_ask_for_what_it_did_not_recognise`** — the production function the run route calls after `save_run`. Queued one request on gap `/erp/trainers/{id}`, status OPEN. (The HTTP POST itself was not driven: it launches a real browser session against a live product. Declared gap.) |
| a human records the answer | `register_source` on a real file, real sha256 |
| the recording's observed url is **SCHEMELESS** | `ObservedScreen.url = "demo.test/erp/trainers/7"` — the only shape `projects/erp/sources/*/analysis.json` actually contains |
| INGEST + MERGE | **`autotester ingest run demo <src> --merge` through the real typer CLI app.** Only `providers.get` was stubbed; the command function, the store, `merge_flowspec`, `resolve_requests` and every write ran for real. Exit 0. |
| the answer lands without destroying the review | on disk: the hand-reviewed screen survives **verbatim** (`scr_signin`, `/signin`); the recording's screen is **added** as `/erp/trainers/{id}`; v3→v4; review **APPROVED→draft** (R1 re-armed, not bypassed) |
| the request closes | `status=fulfilled`, `fulfilled_by_source=src_a3fe7abeef64` — the **answering screen's own** source, not the merge's fallback (AT-291/checkerB) |
| the gap stops being reported | `diff_coverage(spec, results)` → `[]` |
| merging the same recording twice | version unchanged, `0 request(s) closed`, review not re-armed |

**And the other door, in a real browser, by hand:** on
`/projects/checkerdemo/crawls/crawl_01M22B474QM5956JR0ZQA8M9M4` I clicked *"Merge these screens into
the FlowSpec"*. The coverage card went `1 screen(s) the FlowSpec cannot name: /` → `0 … none`, and
`requests.jsonl` went `open` → **`fulfilled`** (`fulfilled_by_source=crawl_…`). A second click
changed nothing. **AT-289 — the cycle-1 finding that the loop was closed on the CLI path only — is
fixed and verified through the product's own button, not through a helper call.** 0 console errors
on every page.

The loop is closed. That is what the two previous cycles left open, and it is now true.

## 2. Criterion by criterion

- **ingest I6** — `--merge` reaches an APPROVED spec without `--replace` and without discarding the
  review; `persist_ingest`'s refusal path is untouched, and the CLI refuses `--merge --replace`
  together (exit 2, message naming the tradeoff, nothing written). **MET.**
- **ingest I7** — `url_pattern` comes from `url_template`, is set only when a url was observed, and
  the defending cross-seam test now feeds the **video side a schemeless url and the crawl side a
  scheme-ful one**. *Load-bearing, re-derived:* in a `git archive cc00e9b` extract (import verified
  to resolve to the extract before any result was trusted) I reverted `absolute_url` to the identity
  — `test_a_video_screen_and_a_crawled_screen_of_one_url_produce_one_pattern` **fails, and nothing
  else does**. The vacuity charged in cycle 2 is gone. **MET.**
- **ingest no-fire list** — "merging into an existing FlowSpec" is deferred to A6, which is this
  unit. No scope violation. **MET.**
- **coverage V1** — both sides of every diff go through `url_template(..., keep_host=False)`;
  `coverage.py` was not touched this cycle. **MET.**
- **coverage V3** — one request per gap, idempotent across store calls: verified on disk through two
  identical CLI merges and two identical button clicks. **MET.**
- **coverage V6** — the opening direction stays wired at both entry points, and the **closing**
  direction now is too (`cli_video.py::_merge_into_reviewed`, `ui/routes_crawls.py:252`).
  *Load-bearing:* `resolve_requests` body → `return []` fails **exactly 8 tests**, including one per
  door. **MET.**
- **expand X6 (the door rule)** — the stage has a reachable door and its refusal writes nothing.
  **MET.**
- **review-gate R1** — a merge that changes anything returns the spec to DRAFT so EXPAND is blocked
  until a human re-approves; a no-op merge does not re-arm it. Observed on disk both ways. **MET.**

## 3. `absolute_url` — I attacked the assumption

The assumption is *"the caller knows the string is absolute because it came out of an address bar."*

It is **correct for every address-bar shape I could construct**: schemeless host, scheme-ful,
`host:port`, protocol-relative `//host/x`, an already-rooted `/path`, a query, a fragment, and the
elided `…/` prefix a browser renders. And it **is** grounded in the prompt —
`src/autotester/prompts/ingest_video_v1.md` says *"Record the URL only when the address bar is
legible on screen. Copy it exactly … A guessed URL is worse than none."*

But nothing **enforces** it. `schema/observation.py` declares `url: str | None` with no pattern, no
validator, no format, and `_to_screen` passes it straight through. So a model that answers with a
hostless path or with prose is refused nowhere, and the new code handles those *worse* than cycle 2
did: `'erp/trainers'` → `/trainers` (first segment silently eaten; cycle 2 produced the correct
`/erp/trainers`), `'students/1'` → `/{id}`, and `'Sign in page'` → **`/`** — a false claim that the
site root is covered, where the old code produced harmless junk.

**Ruling: not a criterion failure.** I7 governs the schemeless address-bar case and that case is now
correct end to end; the assumption is far narrower and better grounded than AT-287's deleted
`_LOOKS_LIKE_HOST`, which had to tell `settings.json` from `example.com`; and the limit is documented
on the function. Filed as **AT-299b (medium)** with a cheap non-guessing remedy: if the templated
result is `/` while the raw url was not root-shaped, store `None` — I7 already makes `None` the
normal, honest outcome, and "no pattern" beats a false claim on the root.

## 4. Stored-shape sweep — repeated from scratch

I re-derived every `url_pattern` / `url_template` / `url_example` value in every `.json` and `.jsonl`
under `projects/`: **9 values, 1 distinct**, and the only value the new code mis-compares is
`/vidysea.com/erp/trainers` in **`projects/erp/screenmap.json` (3 rows)**. That is the only one.
Alongside it, confirmed:

- the maker **did revert** the cycle-2 hand-edit — the file is back to its real, corrupt state
  (`git diff cc00e9b~1..cc00e9b` touches no file under `projects/`), and the corruption renders live
  on `/projects/erp/product-map` in my own browser;
- **leaving it is genuinely harmless beyond that display.** `screenmap.json`'s `url_pattern` is read
  in exactly one place — `ui/routes_product_map.py:45`, as escaped display text. `attach_screenshots`
  matches on screen *name*; `routes_flow_diagram` reads journeys/stops. `projects/erp` has **no
  `flowspec.json`**, so the value cannot reach coverage, merge or `resolve_requests`;
- **the producer really is fixed:** I ran `build_screen_map(ProjectStore('erp'))` myself against the
  real analyses — `['/erp/trainers', …]`, mangled **False**. It heals on the next Analyze.

## 5. `scripts/migrate_url_patterns.py` judged as production code — AT-298b (high)

Good: dry run by default; idempotent (a second run says "nothing to repair"); a missing root exits 2;
unreadable/invalid JSON is skipped; the `"screens": 1` count guard is real. Driven with `--write`
against a **sandbox copy** of the real tree it repaired exactly the 3 intended rows, was idempotent,
and changed exactly 36 bytes — no wholesale reformat.

**But its central safety claim is false, and it reproduces:**

    repair('/v1.2/foo')      -> '/foo'        # first segment silently deleted
    repair('/index.html')    -> '/'
    repair('/settings.json') -> '/'
    repair('/sitemap.xml')   -> '/'

`_MANGLED` anchors on *any* dotted label pair in the first segment — which a genuine path segment
has. Three documents assert the opposite: the module docstring (*"a genuine path segment carrying a
dot (`/v1.2/foo`) is NOT matched"*), the manifest's cycle-3 AT-297b paragraph, and
**`qa/gates/t135-url-pattern-data-migration.md`, the document a human decides on** (*"it refuses to
touch a first path segment that merely contains a dot"*). And
`test_a_real_path_segment_containing_a_dot_is_not_treated_as_a_host` asserts only
`/v1/release-1.0/notes` and `/docs/settings.json` — **deeper** segments, which the anchored regex
could never match. The test's name states a property the test cannot see, and it passes while the
property is false. That is the same shape this project has charged twice already.

Undo: `projects/` is **untracked** in git, the script takes no backup, and `apply()` rewrites the
whole document — so a false-positive repair is not recoverable by git and, on a file not already
`indent=2`, not even locatable by diff. Remaining production concerns are minor and do not bite at
`--root projects`: `sorted(rglob)` materialises the tree, pathlib swallows permission errors during
traversal, and `rglob` on Python 3.11 will descend a directory symlink.

**Why an issue and not a FAIL.** It is governed by no criterion of the four contracts; it is dry-run
by default; it has not been run against real data; and on today's real data there is **no**
false-positive value to hit — I checked every one. **One condition, and it is not optional:
`qa/gates/t135-url-pattern-data-migration.md` must not be answered with option A until AT-298b is
fixed or the three false claims are struck.** A human approving an irreversible write to untracked
data on the strength of a safety claim that is false is the worst shape this ledger records. Option B
(re-run Analyze) is unaffected and remains the better answer.

## 6. Regression risk on the other three `url_template` callers — clean

`absolute_url` is called from exactly two places, both vision boundaries: `stages/ingest.py:99` and
`stages/product_map.py:40,61`. The other three callers — `stages/coverage.py:30`,
`stages/explore_merge.py:73`, `stages/screen_identity.py:53` — are **untouched**, confirmed by grep
and by `git diff cc00e9b~1..cc00e9b --stat`, which lists none of them. `url_template`'s body is
byte-unchanged this cycle; only a docstring and a new sibling function were added.

## 7. Verify commands — all re-run by me, all reproduce

| Command | Claimed | Mine |
|---|---|---|
| `uv run pytest -q` | 1042 passed, 2 skipped, exit 0 | exit **0**; 1044 collected, 2 skipped ⇒ **1042 passed, 2 skipped** ✓ |
| `uv run ruff check src tests scripts` | exit 0 | `All checks passed!` exit **0** ✓ |
| `uv run autotester doctor` | exit 1, exactly one violation (AGENTS.md) | `root-clutter: AGENTS.md` · `1 violation(s)` · exit **1** ✓ |
| `uv run pytest tests/test_merge_flowspec.py tests/test_coverage.py` | 25 passed | **25 passed** ✓ |
| `uv run python scripts/migrate_url_patterns.py` | 3 rows, 1 file, writes nothing | 3 rows in `projects\erp\screenmap.json`; `would repair 3 … across 1 file(s)`; exit 0; **file byte-unchanged** ✓ |

Sabotage (all in a `git archive cc00e9b` extract whose `autotester` import was verified to resolve to
the extract before any result was trusted): **#1** → 1 test fails, the right one · **#3** → 1 test
fails, the right one · **#5** → **exactly 8**, both doors among them. The maker's cycle-3 sabotage
predictions are accurate for the first time in three cycles.

## 8. Ledger

Appended **AT-298b** and **AT-299b** only. My own evidence independently supports the `fixed` claims
on AT-287, AT-288, AT-289, AT-290 (both rows), AT-291 (both rows), AT-294, AT-295 and AT-297b, but I
have **not** flipped those rows to `verified`: the primary checker is their writer, `qa/issues.jsonl`
is being appended to by two checkers, and a lost update on eight rows is worse than a deferred flip.
AT-296 (low — the `b`-suffix convention is not written anywhere the next second-checker will read it)
stays open; I complied with the ruling by reading it here rather than by being told.

## 9. The judgements the maker offered

1. **AT-287/AT-294 fixed inside this unit — scope creep?** No. `resolve_requests` can never close a
   video-answered gap while the pattern a recording teaches does not match the path the request was
   raised on. My end-to-end drive is the proof: with the schemeless url the loop closes; with
   `absolute_url` reverted the cross-seam assertion fails.
2. **`_disagreement` → `disagreement`.** Accepted. Behaviour identical, and the rename exists so the
   video seam and the crawl seam share one rule — which is what C1 asks for. Explore's contract prose
   naming the private form is a docs nit, not a defect; not filed.
3. **The `_LOOKS_LIKE_HOST` heuristic.** Moot — deleted in cycle 2. Its successor assumption is
   attacked in §3.
4. **AT-287 filed by the maker, not the checker.** Left standing rather than re-filed: the id is
   cited in shipped code and in two verdicts, and renumbering would destroy the audit trail, exactly
   as AT-293 ruled.

## What this PASS does and does not certify

It certifies that the self-extension loop closes **end to end on the data shape this repo actually
contains**, through **both** doors, with a human's review preserved and re-armed. It does **not**
certify `scripts/migrate_url_patterns.py --write` against any tree other than today's `projects/`
(AT-298b), and it does **not** certify `absolute_url` against a vision answer that is not an
address-bar transcription (AT-299b).

*Written by /checker (checker B) after re-running every verify command, three sabotages, a full
end-to-end drive of the loop, and its own Mode D browser session. Read-only toward code, artifacts
and real project data throughout: every interaction ran against a sandbox copy, and
`D:/autoTesting/projects` was confirmed unchanged afterwards.*
