# Verdict — t135-coverage-merge-expand

**Cycle checked: 1**
**Date:** 2026-09-11
**Checker:** /checker Mode A + Mode D, fresh subagent, no maker context (checkerA — primary verdict
file; T-135 is `criticality: critical` in `.goal/goal.json` and the manifest declares `Dual check:
required`, so a second, independent checker is expected at `t135-coverage-merge-expand.b.md`. This
file was written without reading any `.b.md`.)
**Bound to:** `D:/autoTesting` — every path read or written resolves inside it.
**Contracts judged:** `qa/contracts/ingest.md` (I6 + the no-fire list deferring "merging into an
existing FlowSpec" to A6) · `qa/contracts/coverage.md` (V1, V3, V6) · `qa/contracts/expand.md` (X6)
· `qa/contracts/review-gate.md` (R1)

```
VERDICT: FAIL
SCOREBOARD: 5/5 contract criteria met, 5/5 invariants hold — but the unit's OWN declared
            verify command does not reproduce, and its own live door leaks (see FAILURES)
FAILURES:
- [verify] sev: high · `uv run autotester doctor` returns TWO violations, not the "exactly one"
  the manifest names as its expected output; the second one is caused by this unit ·
  trim/route one line out of docs/ARCHITECTURE.md so the new stage row fits the budget ·
  issue: AT-288
- [V6-drift] sev: high · the UI's own "Merge these screens into the FlowSpec" button covers the
  gap and leaves the answered VideoRequest OPEN — resolve_requests is wired to the CLI door only ·
  call resolve_requests from ui/routes_crawls.py's merge route, as queue_requests is called from
  both entry points · issue: AT-289
- [judgement 4] sev: medium · AT-287's "blast radius, measured rather than assumed" is false:
  three video-derived host-ful url_patterns are already mangled on disk and on screen ·
  backfill them or correct the row; do not ship the claim as written · issue: AT-290
- [judgement 3] sev: medium · url_template is still not idempotent for a dotless host, and the
  new heuristic silently drops a dotted first path segment under keep_host=False, while the
  docstring's promise was strengthened to "in either mode" · narrow the claim or stop inferring
  host-ness from the string · issue: AT-291
LIVE-BROWSER: qa/evidence/browser-t135-coverage-merge-expand-2026-09-11-checkerA/report.json
ISSUES-WRITTEN: AT-288, AT-289, AT-290, AT-291 (+ corrected the checker_note on the
                maker-filed AT-287)
EXPLANATION: The engineering here is good and the merge seam is real — I re-derived both
sabotages myself and the fix is load-bearing in each. It fails on two things a maker cannot
self-certify past: the doctor baseline it declares is not the baseline it produces (its own
ARCHITECTURE.md row pushed the repo over its C2 line budget), and the loop it exists to close is
only closed on the CLI path — I clicked the product's own merge button, watched the gap go to
zero, and read the ask back still OPEN. The AT-287 fix is correctly on the critical path and is
NOT scope creep; what does not survive is its blast-radius paragraph.
```

---

## What I re-ran myself (nothing below is read from the manifest)

| Command | Manifest claimed | I got |
|---|---|---|
| `uv run pytest -q` | exit 0, 2 skips | exit 0 ✅ |
| `uv run ruff check src tests scripts` | "All checks passed!", exit 0 | identical ✅ |
| `uv run autotester doctor` | **exit 1, exactly 1 violation (AT-283 AGENTS.md)** | **exit 1, 2 violations** ❌ |
| `check_deliverable.py --exists …` | "OK 2 deliverable(s) present", exit 0 | identical ✅ |
| `pytest tests/test_merge_flowspec.py tests/test_coverage.py -q` | "27 passed", exit 0 | **28** passed, exit 0 (13 + 15 collected) — green, but the pasted number is one stale |

The doctor delta is not ambient:

```
root-clutter: AGENTS.md — scratch and evidence belong in .work/, not the repo root
architecture-too-long: docs/ARCHITECTURE.md — 151 lines > 150; move detail to a routed doc
2 violation(s)                                                          exit=1
```

`git show HEAD:docs/ARCHITECTURE.md | wc -l` = **150**; working tree = **151**; the diff is
`1 insertion / 0 deletions`, and that insertion is this unit's own `merge_flowspec` concept→file
row. The manifest states the unit "adds none". It adds one. `doctor.py::check_architecture_budget`
against `ledger.render.ARCHITECTURE_MAX_LINES` is the repo's own C2 gate, so the unit that
documents itself is the unit that broke it. This is a one-line fix, but it is exactly the kind of
"my pasted output says otherwise" that Mode A exists to catch. **AT-288.**

## Sabotage — isolation used, and how I know it was real

**Isolation: a copy of the WORKING TREE, not a `git archive`.** Most of this unit is uncommitted
(`merge_flowspec.py`, `request_store.py`, both new test files are `??`), so an archive of HEAD
would not contain the code under test. I copied `src/ tests/ scripts/ pyproject.toml docs/ qa/` to
`C:/Users/Lenovo/AppData/Local/Temp/claude/sb-t135`, **outside the repo**, and ran everything from
there with `PYTHONPATH=<copy>/src`. Verified before trusting any result:

```
import autotester → C:\...\sb-t135\src\autotester\__init__.py
import autotester.stages.merge_flowspec → C:\...\sb-t135\src\autotester\stages\merge_flowspec.py
```

The live tree was never edited.

**(a) `_split` reverted to a bare `urlsplit(url)`** (anchor matched exactly once; source re-read
back through `inspect.getsource` to confirm the patch landed). Baseline in the copy: 4/4 green.
After the revert — exactly the three named tests, and only those:

```
FAILED tests/test_urls.py::test_templating_a_templated_url_is_a_no_op_in_both_modes
FAILED tests/test_urls.py::test_a_host_ful_pattern_and_a_fresh_url_agree_on_the_path
FAILED tests/test_coverage.py::test_a_screen_learned_from_a_video_is_not_a_permanent_gap
```

The coverage failure is the real one: `Left contains one more item: CoverageGap(... '/students/{id}'
... "observed '/students/{id}' but no screen in the FlowSpec has this url_pattern")`. The fix is
load-bearing. ✅

**(b) `resolve_requests`' body replaced with `return []`** (467 chars of body removed; re-read
through `inspect.getsource`). **5** tests fail:

```
FAILED tests/test_merge_flowspec.py::test_a_request_the_merged_spec_now_answers_is_closed
FAILED tests/test_merge_flowspec.py::test_resolving_twice_does_not_rewrite_an_already_closed_request
FAILED tests/test_merge_flowspec.py::test_the_full_loop_closes_a_gap_end_to_end
FAILED tests/test_merge_flowspec.py::test_an_id_bearing_route_is_answered_by_a_templated_pattern
FAILED tests/test_merge_flowspec_cli.py::test_the_cli_merge_closes_the_request_that_asked_for_the_recording
```

Load-bearing, and more strongly than claimed. One correction to the manifest's prediction: it
says "**the two** CLI door tests plus `test_a_request…`". Only **one** CLI door test fails.
`test_the_cli_merges_into_an_approved_spec_instead_of_refusing` correctly stays green — it tests
merging, not resolving, and it *should* survive this sabotage. The prediction was over-claimed;
the property is proven. Noted, not filed.

## Mode D — my own browser, gated on changed paths

No file under `ui/` changed, so this could have been waved through as "not a UI unit". It is one:
`core/urls.py` changes what `stages/coverage.py` reports and `ui/routes_crawls.py:145-152` renders
that in the "Against the FlowSpec" card. I started **my own** uvicorn on **my own** port (64114,
picked by binding port 0) and drove **my own** Playwright Chromium. I did not open the maker's
`report.json` or any of its screenshots, and I did not substitute `curl`.

Five pages, **0 console errors on every one** (AT-248's old permanent favicon-404 baseline is
genuinely gone, so a real error would not hide in noise).

**The interaction, and the finding it produced.** On
`/projects/checkerdemo/crawls/crawl_01M22B474QM5956JR0ZQA8M9M4` the card first read
*"FlowSpec v1 · review: NEEDS_EDIT … 1 screen(s) the FlowSpec cannot name: /"*. I clicked **Merge
these screens into the FlowSpec**. It re-rendered *"FlowSpec v2 · review: DRAFT — 1 screen(s)
added … 0 screen(s) the FlowSpec cannot name: none"*, and on disk `flowspec.json` went
v1→v2, 0→1 screens, `needs_edit`→`draft`. Clicking it a second time changed nothing (still v2) —
the merge seam is idempotent live, as its docstring claims. All good.

Then I read `requests.jsonl` back. `req_bb8e26317632` — the **only** OPEN `VideoRequest` this
system has ever produced, the one asking for a recording of `/` — is **still `open`**. And it is
not unanswerable: probing directly,

```
merge_flowspec._answered_gap_ids(store.load_flowspec()) ∋ gap_2a0765d4adf2   →  answered = True
```

The merged spec covers the gap. `resolve_requests` would close it. It is simply never called:
`cli_video.py::_merge_into_reviewed` calls it, `ui/routes_crawls.py`'s merge route does not.

This is coverage.md **V6's own rule** turned on the closing direction — *"called from **both** real
entry points, so the run path and the crawl path cannot drift apart"*. The manifest's declared gap
#2 anticipates the objection and misses it: it says *"the UI has no ingest route at all … there is
no second call site to wire, unlike coverage.md V6's two."* True of **ingest**. But the crawl-merge
route is a real second **merge** call site — it merges screens into the reviewed spec and closes
coverage gaps — and it is the only door a non-CLI operator has, against T-100's explicit
"full onboarding → report without touching the CLI". The unit's stated reason for existing is that
"every request the system ever made stayed OPEN for life"; on the UI path, it still does. **AT-289.**

*Disclosed:* this mutated `projects/checkerdemo/`. I backed up `flowspec.json` and `requests.jsonl`
first and restored them byte-for-byte afterwards (verified back to v1 / 0 screens / `needs_edit`).
A checker that mutates project data says so and puts it back.

I also drove the unit's own CLI door refusal:
`autotester ingest run checkerdemo src_nonexistent --merge --replace` →
*"--merge and --replace are opposites: merge keeps the reviewed spec, replace discards it. Pick
one."*, exit 2 — and note it refuses **before** touching the store, so a bad flag pair never
reaches a source lookup. Correct ordering. ✅

## Criteria, judged on my own evidence

**ingest.md I6 + the A6 deferral — MET.** `persist_ingest` is untouched; the approved-spec refusal
still stands and `--merge` is a genuinely separate path, not a way around it. `merge_flowspec`
never modifies or replaces an existing `Screen`/`Flow` (`_new_screens`/`_new_flows` filter on id;
the copy is `[*existing, *added]`), so a human's correction survives a later recording. The
no-fire list's A6 deferral is now honoured by a real module, and `Conflict` detection came with it.

**coverage.md V1 — MET, with AT-291 open against its edges.** Both sides still go through
`url_template`, and the unit *strengthens* V1 by making the normaliser survive its own output.
Sabotage (a) proves it. The residual is that "survives its own output" is not yet true for every
host shape.

**coverage.md V3 — MET.** `add_request` moved verbatim into `RequestStoreMixin`; idempotence on
content-addressed id is unchanged and the full suite is green through the move. `update_request`
is a genuine gap being closed — a `VideoRequest` had no status-transition path at all — and it uses
`upsert_jsonl`, matching `update_issue`, so `add_request` stays append-only. Public API unchanged.

**coverage.md V6 — MET as written** (`queue_requests` and both of its call sites are untouched by
this unit; the gap direction is still wired at both, and `unreached_screens` is still never queued).
The **closing** direction is what drifts, and that is AT-289 above rather than a V6 violation, since
V6's text governs `queue_requests`. If the maker's fix does not wire the UI route, V6 should be
amended by a checker to name the closing direction too — I am not amending it inside a pending
verdict.

**expand.md X6 — MET.** `expand`'s two doors are untouched. As a *principle* applied to this unit,
`merge_flowspec` does have a door (`ingest run --merge`), so it is not an unreachable stage — but
see AT-289 for the door it does not have.

**review-gate.md R1 — MET, and this is the nicest part of the design.** A merge that added anything
resets `review.status` to `DRAFT` with a note naming what landed, so the gate is **re-armed**
rather than bypassed — verified live (the card and the FlowSpec page both flipped to DRAFT and
said "This FlowSpec is not approved. It drives no test expansion until a human approves it
again"). Equally important and easy to get wrong: an *empty* merge returns `existing` unchanged,
so it does **not** reset the review — a merge that re-armed the gate on every call would make the
loop permanently un-closeable. `ingest_video` still never sets `review.status`.

---

## Rulings on the four judgements the manifest offered

### 1. Fixing AT-287 inside T-135 — **on the critical path. Not scope creep. Upheld.**

I did not take this on the manifest's argument; I traced it. `resolve_requests` →
`_answered_gap_ids` → `url_template(s.url_pattern, keep_host=False)` over the *stored* pattern,
compared against a `content_id("gap", …)` minted from an *observed* path. `stages/ingest.py:99`
stores that pattern **host-ful** (I7). Pre-fix, re-templating `demo.test/students/{id}` yields
`/demo.test/students/{id}`, which mints a different gap id than `/students/{id}` — so
`resolve_requests` could never close a video-answered gap, i.e. the headline deliverable of this
unit would have been dead on arrival. Sabotage (a) fails
`test_a_screen_learned_from_a_video_is_not_a_permanent_gap`, which is the coverage-level proof.
Splitting it out would have shipped an A6 that cannot do the one thing A6 is for.

The cost was underestimated, though — not the scope. The ARCHITECTURE row this unit owed itself is
what broke the C2 gate (AT-288).

### 2. `_disagreement` → `disagreement` — **behaviour genuinely identical. Approved.**

Verified rather than accepted. The diff is exactly two identifiers: the function name and the
`crawl_id` → `source_id` parameter. `_conflict_for`'s and `disagreement`'s bodies are otherwise
byte-unchanged (`if clash is None or clash.name == incoming.name or _is_structural(clash): return
None`), the sole in-module call site passes `crawl_id` positionally so the parameter rename cannot
bind differently, the full suite is green, and — the part reading a diff cannot settle — I drove
the crawl merge path **in a live browser**, which is the code that calls it, and got the correct
result (1 screen added, 0 conflicts, idempotent on a second click). The reason given is also the
right one: `merge_flowspec._conflicts_for` now calls it, so the video seam and the crawl seam
share one rule instead of growing two (C1).

The genuine loose end was documentary: `qa/contracts/explore.md:164` named `_disagreement`, a
symbol that no longer exists. As the contract's single writer I have applied that as a **routine,
non-weakening naming correction** with an amendment-log entry — no criterion touched.

### 3. `_LOOKS_LIKE_HOST` — **attacked successfully. The heuristic has a real hole and a real leak.**

The maker offered `v1.2/foo` and judged it absent from this system. I went looking for a worse one
and found it in the opposite direction: **the heuristic requires a `.` or a `:`, so a dotless host
is not recognised at all** and AT-287 is simply *unfixed* there:

```
url_template('http://localhost/students/1')  -> 'localhost/students/{id}'
url_template('localhost/students/{id}')      -> '/localhost/students/{id}'    idem = False
url_template('http://erp/trainers')          -> 'erp/trainers'
url_template('erp/trainers')                 -> '/erp/trainers'               idem = False
```

`localhost` on port 80 and any single-label intranet host produce exactly the defect AT-287
describes, and the docstring — which this unit *strengthened* to promise idempotence "in either
mode" — is still false. A promise made stronger than the code is worse than the promise it
replaced.

And the maker's own shape is worse than "misread": under `keep_host=False` the misread segment is
silently **deleted**.

```
url_template('v1.2/foo',          keep_host=False) -> '/foo'
url_template('release-1.0/notes', keep_host=False) -> '/notes'
url_template('index.html',        keep_host=False) -> '/'
```

Both filed as **AT-291** (medium). Neither blocks the unit's own tests; both mean the fix bought
idempotence for the dotted-host case and not for the general case the docstring now advertises.

### 4. AT-287 filed by the maker — **severity right, blast-radius claim wrong.**

*Severity `high`:* upheld. If anything it is generous-to-correct — the row calls the defect
"latent but armed", and it has in fact already fired.

*"Blast radius, measured rather than assumed":* **false, and this is the finding I would defend
hardest.** It was measured over the wrong artifact. The row checks `projects/*/flowspec.json` and
concludes no project carries a video-derived host-ful pattern. But a video's screens land in
`screenmap.json` via `stages/product_map.py::_new_screen`, which calls `url_template(screen.url)`
with `keep_host` at its **default True**. And on disk right now:

```
projects/erp/screenmap.json → 3 of 8 screens carry  url_pattern = "/vidysea.com/erp/trainers"
    visits: [{source_id: "src_c6bb964cfff8", t_start: 0.0, t_end: 32.0}]
    frame_ref: "sources/src_c6bb964cfff8/frames/00000000.png"
```

That leading slash in front of a host is the AT-287 signature and nothing else can produce it — a
schemeless address-bar reading (`vidysea.com/erp/trainers`, which is precisely what a vision model
sees, since browsers hide the scheme) templated pre-fix. It is video-derived by its own `visits[]`
and `frame_ref`. And it is not hypothetical or buried: **I read it off the live page** —
`/projects/erp/product-map` renders *"Trainers … URL /vidysea.com/erp/trainers"* to a human today.

So *"Do not read this row as 'existing projects have corrupt coverage'; read it as 'the next one
would have'"* is exactly backwards, in a **checker-owned** ledger row.

Compounding it: **the fix does not heal what is already stored.** `/vidysea.com/erp/trainers`
starts with `/`, so `_split` short-circuits to plain `urlsplit` and re-templating is a no-op,
while the fresh URL reduces to `/erp/trainers`. No backfill is offered. Filed as **AT-290**
(medium — the code fix is right; the false claim and the missing migration are the defect), and
AT-287's own row now carries a `checker_note` recording the correction.

## Notes that are not failures

- The maker rewrote 5 pre-existing ledger rows (AT-244…AT-248) from compact to spaced JSON. I
  diffed the ledger **semantically**, old vs new, parsed: 280 → 281 rows, `added: ['AT-287']`,
  `removed: []`, `semantically changed: []`. Whitespace only, nothing lost. The ledger is
  checker-owned and a maker should not be reformatting rows it did not file, but no harm was done
  and it is not worth a fix cycle.
- `qa/.last-tick` was stamped and AT-286's remedy ("submit a T-135 manifest at ready-for-check")
  is satisfied by this manifest. AT-286 itself stays `open` — it is a governance finding about
  liveness, not about this unit, and closing it is a sweep's call.
- The manifest's declared gap #1 (no live vision-provider run, no suitable recording in-repo) is
  an honest gap and I did not count it against the unit; the CLI door's happy path is evidenced by
  tests plus sabotage (b) rather than by a live model call, and that is stated, not hidden.
- `.goal/goal.json` T-135 stays `pending`. A FAIL never closes a goal task.

## What the next cycle needs

1. **AT-288** — one line out of `docs/ARCHITECTURE.md`, then `doctor` back to the AT-283-only
   baseline the manifest declares. Cheapest of the four and the one that makes the manifest true.
2. **AT-289** — call `resolve_requests` from `ui/routes_crawls.py`'s merge route. Then re-drive the
   button and read `requests.jsonl` back; the same one-click reproduction I used is the check.
3. **AT-290** — decide: backfill the stored `screenmap.json`/`flowspec.json` patterns, or leave
   them and correct the claim. Either is fine; the current row is not.
4. **AT-291** — narrow the docstring to what the heuristic delivers, or carry the host / host-less
   distinction explicitly instead of re-inferring it from the function's own output.

None of these is a rewrite. The merge seam itself is sound and I would pass it on cycle 2 with
1 and 2 closed and 3/4 either fixed or explicitly deferred with a reason.

---
---

# Verdict — t135-coverage-merge-expand · CYCLE 2

**Cycle checked: 2**
**Date:** 2026-09-11 · **Checker:** checkerA (primary verdict file) · **Bound to:** `D:/autoTesting`
(Appended below the cycle-1 verdict, which is left byte-intact — it is the record of a different
cycle, not a competing judgement of this one. Written without reading `t135-coverage-merge-expand.b.md`.)
**Contract:** `qa/contracts/ingest.md` (I6, I7, no-fire list deferring merge to A6) ·
`coverage.md` (V1, V3, V6) · `expand.md` (X6) · `review-gate.md` (R1)
**Manifest:** `qa/manifests/t135-coverage-merge-expand.md` (Fix cycle: 2, ready-for-check)
**Isolation:** `git archive HEAD` (191be93) extract; `autotester.__file__` confirmed to resolve to
the extract before ANY sabotage or probe result was trusted. The live tree was never sabotaged and
never written to by the browser (verified: `projects/checkerdemo/requests.jsonl` in `D:/autoTesting`
still reads `status=open` after two merge clicks in the extract-served app).

```
VERDICT: FAIL
SCOREBOARD: 6/7 criteria met, 6/7 invariants hold
FAILURES:
- [I7] sev: high · The cycle-2 fix does not fix AT-287. `url_template` still swallows the host of a
  SCHEMELESS url, which is exactly what a vision model reads off an address bar and what this repo's
  only real video data contains, so the video seam and the crawl seam STILL produce different
  patterns for one screen — I7's stated purpose is unmet and the loop still cannot close for a
  video-learned screen. · Stop inferring host-ness; normalise the observed url at the ingest
  boundary so `url_template` is only handed a url whose host position is known, and make the
  defending test feed the video side a schemeless url. · issue: AT-294 (AT-287 reopened)
LIVE-BROWSER: qa/evidence/browser-t135-coverage-merge-expand-2026-09-11-checkerA-c2/report.json
ISSUES-WRITTEN: AT-294 (high, new) · AT-295 (medium, new) · AT-296 (low, new) · AT-287 REOPENED
  (fixed -> open) · AT-293 ruled (fixed) · AT-288/289/290/291 each given a `checker` discriminator
EXPLANATION: Everything cycle 1 charged is genuinely repaired and I verified each one myself: all
four pasted outputs reproduce exactly, all four sabotage checks are load-bearing, and the AT-289 UI
seam really does close the request now — I clicked the button in my own browser and read the closed
request back off disk. But the strategy change at the centre of cycle 2 does not hold. The maker
correctly identified that the two seams stored different shapes and correctly deleted an unwinnable
heuristic; it then concluded the root cause was the `keep_host` disagreement. It was not. Running
`build_screen_map` — the exact function the Analyze button calls — against projects/erp's REAL
analyses with cycle-2 code regenerates the very `/vidysea.com/erp/trainers` corruption the maker
hand-repaired, so the fix and the data repair contradict each other and AT-287's original symptom
is still live on real data.
```

---

## 1. The manifest's own pasted outputs — RE-RUN, all four reproduce

Cycle 1 failed partly because they did not. They do now.

| Command | Manifest claim | My re-run |
|---|---|---|
| `uv run pytest` | 1032 passed, 2 skipped, exit 0 | **1032 passed, 2 skipped, 1 warning in 88.52s — exit 0** OK |
| `uv run ruff check src tests scripts` | exit 0 | **All checks passed! — exit 0** OK |
| `uv run autotester doctor` | exit 1, EXACTLY ONE violation (AGENTS.md, AT-283) | **`root-clutter: AGENTS.md` · `1 violation(s)` · exit 1** OK |
| `check_deliverable --exists …` | exit 0 | **OK 2 deliverable(s) present — exit 0** OK |
| `pytest test_merge_flowspec.py test_coverage.py` | 24 passed | **24 passed** OK |

AT-288 (both rows) is genuinely closed: the ARCHITECTURE row was folded into the coverage row and
`doctor` is back to its certified AT-283-only baseline.

*One note for the maker, not a finding:* `pyproject.toml` sets `addopts = "-q"`, so the literal
command `uv run pytest -q` is `-qq` and pytest 9 **suppresses the summary line entirely** — the
`1032 passed, 2 skipped…` line the manifest pastes cannot have come from the command the manifest
names. The numbers are right; the command that produces them is `uv run pytest`.

## 2. The four sabotage checks — all load-bearing

Each run in the extract, each anchor asserted to match exactly once, each file confirmed changed,
each restored from `git show HEAD:` before the next.

| # | Sabotage | Manifest predicts | Measured |
|---|---|---|---|
| 1 | `ingest.py` back to the host-ful `url_template(observed.url)` | the 2 named tests fail | **exactly those 2 fail** OK |
| 2 | `resolve_requests` body → `return []` | 5 tests fail | **8 relevant tests fail** across `test_coverage_wiring`, `test_merge_flowspec_cli`, `test_merge_flowspec_requests` — under-predicted, i.e. better defended than claimed OK |
| 3 | delete the `resolve_requests` call in `routes_crawls.py::merge_crawl` | `test_the_merge_button_closes_the_request_the_crawl_answers` fails | **exactly that test fails**, 7 pass OK |
| 4 | `_learned_url_patterns` → `{}` | `test_a_re_recording_teaches_a_url_pattern_the_spec_lacked` fails | **that one plus `test_learning_a_url_pattern_closes_the_request_that_asked_for_it`** OK |

Control on sabotage 2's ninth failure: `tests/test_ui_sources.py::test_uploaded_recordings_are_gitignored`
fails at **baseline** in a `git archive` extract (no `.git`), so it is extract noise, not a finding.

## 3. Point 1 — the AT-287 replacement. SAFE IN ONE DIRECTION, UNSOUND IN THE OTHER

### 3a. Does anything READ `url_pattern` expecting a host? **No.** Every consumer grepped.

`coverage._known_paths` / `unreached_screens` re-template host-lessly (idempotent on the new shape);
`explore_merge._new_screens` and `merge_flowspec._conflicts_for` key a dict on the raw string and
only ever compare like to like; `crawl_view.py:184`, `routes_learn.py:105`,
`routes_product_map.py:45` only display it. No consumer parses a host back out. **Clean.**

### 3b. Is there STORED data still holding host-ful patterns? **No — the repair is complete and its VALUE is right.**

Scanned every `projects/**/*.json` and `*.jsonl` for `url_pattern`: exactly one artifact carries any
(`projects/erp/screenmap.json`, 3 rows), and all three now read `/erp/trainers`. No `flowspec.json`
in the repo has a `url_pattern` at all. Confirmed **in the browser** on `/projects/erp/product-map`:
3 × `/erp/trainers`, zero occurrences of the mangled string. `.work/screenmap.json.bak` holds the
pre-repair values and the raw source `url: vidysea.com/erp/trainers`. Crawl artifacts store
`url_example`, not `url_pattern`, and are unaffected.

**Two caveats the maker should own:** `projects/erp/screenmap.json` is **untracked in git**, so the
repair is not in history and one `git clean` takes it; and the repaired value does not match what
the code produces (below).

### 3c. Was I7's purpose DEFEATED before this change? **The maker's claim is UPHELD — independently verified.**

At `c3da666`: `ingest.py:99` and `product_map.py:40,60` used the default `keep_host=True`;
`explore_merge.py:73` and `screen_identity.py:53` used `keep_host=False`. For every screen with a
visible URL the two seams produced different strings, so I7's "collapse to one row instead of two"
could not happen — for the entire life of the criterion. I7 asserted each side *calls* the
templater and never that they *agree*, which is precisely why nothing caught it. This is a
significant contract finding and I have written it into `ingest.md`'s amendment log so it does not
live only here.

### 3d. **THE FAILURE.** The replacement does not discharge I7 either.

Executed in the extract, import verified:

```
url_template('vidysea.com/erp/trainers',         keep_host=False) -> '/vidysea.com/erp/trainers'
url_template('https://vidysea.com/erp/trainers', keep_host=False) -> '/erp/trainers'
```

Canonicalising all four producers removes the disagreement between the **flags**, not between the
**outputs**. The host still lands in `.path` whenever the string has no `//` — and a schemeless
string is exactly what a vision model transcribes, because browsers hide the scheme. This is not
hypothetical: `projects/erp`'s real analyses record `url: vidysea.com/erp/trainers`.

I then ran `stages/product_map.build_screen_map(ProjectStore('erp'))` — **the exact function
`POST /projects/{slug}/sources/{id}/analyze` calls** — against those real on-disk analyses with
cycle-2 code:

```
Trainers                    -> /vidysea.com/erp/trainers
Trainers List               -> /vidysea.com/erp/trainers
Trainers List - Edit Drawer -> /vidysea.com/erp/trainers
   currently stored (maker's cycle-2 repair): ['/erp/trainers']
```

So: **the cycle-2 code regenerates the corruption the cycle-2 data repair removed.** The repair is
right about the answer and unreachable from the code, and any operator who re-analyses an erp
recording silently undoes it. Downstream, `coverage._path_of` is idempotent, so a stored
`/vidysea.com/erp/trainers` never matches an observed `/erp/trainers`: the video-learned screen
stays invisible, the gap stays open, and `resolve_requests` cannot close it — AT-287's original
symptom, for the real data, unfixed.

The new cross-seam test cannot see any of this: it feeds **both** sides the same scheme-ful
`https://demo.test/trainers/123?tab=2`, so it proves one function is deterministic, not that the
seam agrees. Filed **AT-294** (high); **AT-287 reopened**; `ingest.md` I7 tightened (routine,
non-weakening) to require a schemeless video-side input in the defending test.

*On the maker's cycle-1 judgement #1 (scope creep?):* not scope creep — it is on the critical path
exactly as argued, and it must stay in this unit. Judgement #2 (`_disagreement` → `disagreement`):
upheld as correct; the contract prose is what is stale (AT-292, filed by checkerB, still open for a
sweep). Judgement #3 (`_LOOKS_LIKE_HOST`): moot, the heuristic is gone — correctly, and for the
right reason.

## 4. Point 2 — attacking `_learned_url_patterns`

- **Can it overwrite a human's value?** **No.** `lacking` is filtered on falsy `url_pattern`, so only
  a `None` is ever filled. Held under probe.
- **Idempotence (merge twice)?** **Holds.** Second merge returns the *same object*
  (`again is merged` True), version 4 → 4, review not re-armed. Confirmed again through the UI:
  clicking the Merge button twice left flowspec at v2 and `requests.jsonl` byte-identical.
- **Can it introduce a duplicate pattern or an unrecorded conflict?** **YES — finding.**
  `_conflicts_for` iterates only `added_screens`; the patterns learned onto *existing* screens never
  pass through `disagreement`. Probe: existing spec has `scr_B 'Staff Directory' = /trainers`
  (source `src_human`) and `scr_A 'Trainers' = None`; a recording of `scr_A` supplies `/trainers`.
  Result: **both screens carry `/trainers`, `merged.conflicts == []`** — while calling
  `_conflicts_for` on the same pair directly *does* return a real `Conflict`. The module's own
  docstring states the rule it routes around. Knock-on: `_answered_gap_ids` uses `setdefault`, so
  with two screens on one path the first in spec order wins the attribution — re-admitting AT-291's
  shape through the AT-290 fix. Filed **AT-295** (medium).

## 5. Point 3 — AT-291 attribution

Correct by construction for the case it was filed for: attribution comes from the answering screen's
own `source_ref`, and `test_a_no_op_merge_does_not_credit_an_unrelated_recording` fails under
sabotage 2, so it is load-bearing. Two reachable residual paths, neither strong enough to charge
separately (recorded here as questions, not failures):

1. `answered[gap] or source_id` still falls back to the merged recording when the answering screen
   has **no** `source_ref` — `Screen.source_ref` is `| None` and a hand-edited `flowspec.json` (the
   documented review/edit workflow) produces exactly that. Narrower than AT-291 was, but the same
   false statement.
2. Where AT-295's duplicate patterns exist, `setdefault` picks by spec order, which is arbitrary.

Fixing AT-295 removes (2); (1) is one `if` away from being provably safe.

## 6. Point 4 — Mode D, my own browser (D-024)

**In scope by CHANGED PATHS:** this cycle edits `src/autotester/ui/routes_crawls.py` directly.

My own uvicorn on my own free port **62436**, serving the **extract**, driven by my own Playwright
Chromium. The maker's screenshots were not read; `curl` was not substituted for a click.

- 5 pages, **0 console errors, 0 console warnings** in total.
- **AT-289 verified live and CLOSED:** on
  `/projects/checkerdemo/crawls/crawl_01M22B474QM5956JR0ZQA8M9M4` the card read *"1 screen(s) the
  FlowSpec cannot name: /"* with `req_bb8e26317632` OPEN. Clicked **"Merge these screens into the
  FlowSpec"** → card went to *"0 screen(s) … none"*, flowspec v1→v2 (review `needs_edit`→`draft`,
  screen at `/`), and **read back off disk**: `status=fulfilled`,
  `fulfilled_by_source=crawl_01M22B474QM5956JR0ZQA8M9M4`. The cycle-1 defect does not reproduce.
- **Idempotence through the button** (my own addition): second click → v2 unchanged, request
  byte-identical, 0 conflicts.
- `/projects/erp/product-map` renders `/erp/trainers` ×3 — AT-290(checkerA)'s human-visible defect
  is gone from the screen.
- **Declared gap (a SKIP is a stated gap, never a pass):** the Analyze button that regenerates
  `screenmap.json` needs a live vision provider with credentials and cost, so it was not clicked; I
  executed `build_screen_map` directly against the same real data instead (§3d). Nothing else was
  substituted.

Report: `qa/evidence/browser-t135-coverage-merge-expand-2026-09-11-checkerA-c2/report.json`.

## 7. Criteria scoreboard

| Ref | Judgement |
|---|---|
| ingest.md **I6** + its A6 deferral | **MET** — `merge_flowspec` lands the answer without rewriting a reviewed screen or flow, re-arms review to DRAFT, and is idempotent. Load-bearing (sabotage 2, 4). |
| ingest.md **I7** | **NOT MET** — §3d. AT-294; AT-287 reopened. |
| coverage.md **V1** | MET — both sides still normalise through `url_template(..., keep_host=False)`; `_path_of` unchanged and idempotent on the new stored shape. |
| coverage.md **V3** | MET — one request per gap, and closing is idempotent (`status is not OPEN` guard; verified twice through the button). |
| coverage.md **V6** | MET — the closing half is now wired at BOTH entry points exactly as `queue_requests` is, proven by sabotage 3 **and** by a real click. |
| expand.md **X6** | MET — `autotester ingest run --merge` is a real door with a `--merge`/`--replace` mutual-exclusion refusal; the crawl-merge button is the second. |
| review-gate **R1** | MET — a merge that changed anything returns `ReviewStatus.DRAFT`, so EXPAND re-blocks rather than inheriting an approval; observed live (`needs_edit`→`draft`, "not approved … drives no test expansion"). |

## 8. Ruling on AT-293 — id collision in the dual check (I own the ledger)

1. **The eight existing rows are NOT renumbered.** Two cycle-1 verdicts and this unit's manifest
   already cite those ids by number; rewriting them would destroy exactly the audit trail the dual
   check exists to create. Instead each colliding row now carries a **`checker`** discriminator
   (`checkerA` / `checkerB`) plus an `id_collision` pointer, so a reader can tell AT-290(A) from
   AT-290(B) without archaeology. Applied.
2. **Forward rule: the second checker suffixes its ids with `b`** (`AT-294b`). It mirrors the
   `<slug>.b.md` verdict convention this project already runs, is self-describing in the ledger, and
   needs no coordination between two checkers who are supposed to be blind to each other.
3. **`tools.reserve_id` is REJECTED for this purpose.** An atomic reservation requires the two
   checkers to share a resource, which is the one thing independence forbids; it also fails open the
   moment one checker runs in a sandbox that cannot reach it. Drop it or document it (AT-296).
4. AT-293 marked **fixed**; **AT-296** (low) filed to carry the suffix rule into the dual-check
   dispatch text, since a convention nobody can read on disk gets rediscovered by collision.

## 9. What the maker must do for cycle 3

One thing, and it is the only blocker: **AT-294**. The reasoning that killed the heuristic was right
— you cannot infer host-ness from a schemeless string — but the conclusion drawn from it was half
the answer. Do not make the parser guess; make the *input* unambiguous at the ingest boundary, so
`url_template` is never handed a string whose host position is unknown. The defending test must then
feed the video seam a **schemeless** url and the crawl seam a scheme-ful one, because that asymmetry
IS the seam. Use `build_screen_map` on `projects/erp` as the acceptance check: it must produce
`/erp/trainers`, matching the repaired data instead of contradicting it. AT-295 is a should-fix in
the same file and cheap while you are there. Everything else in this unit stands.
