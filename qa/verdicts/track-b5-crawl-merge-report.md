# Verdict — track-b5-crawl-merge-report

**Date:** 2026-09-08 · **Mode:** A (unit check) · **Cycle checked: 1** (manifest `Fix cycle: 1`)
**Bound to:** `d:/autoTesting` · **Unit:** commit `f731983`, goal task **T-144** (Track B5)
**Contracts:** `qa/contracts/explore.md` (X1–X12 pre-existing, **X13–X16 authored in this check**),
`qa/contracts/coverage.md` (**V1 amended, V5 added**), `qa/contracts/ui.md` (U1–U9)
**Dual check:** no.

```
VERDICT: PASS
SCOREBOARD: 20/20 criteria met, 12/12 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-102, AT-103, AT-104, AT-105 (all residuals/gaps, none a criterion violation)
```

---

## What I re-ran myself (nothing below is the maker's pasted output)

All commands executed by me in the project's own container (`docker compose exec -T autotester`),
per `qa/adapter.json`.

| Command | Result I obtained | Manifest claimed | Match |
|---|---|---|---|
| `uv run pytest -q` | exit 0 — **549 passed, 1 skipped** (counted from the progress marks; this repo's pytest suppresses the summary line) | 549 passed, 1 skipped | ✅ |
| `uv run ruff check src tests scripts` | `All checks passed!` | same | ✅ |
| `uv run autotester doctor` | `doctor: clean` | same | ✅ |
| `uv run python scripts/explore_proof.py` | exit 0 — **10/10 invariants held** (all ten PASS lines re-read) | 10/10, B3 not regressed | ✅ |
| `uv run pytest tests/test_explore_merge.py tests/test_crawl_report.py tests/test_ui_crawls.py tests/test_coverage.py -q` | exit 0 — **39 passed** | 33 passed | ⚠️ see note |

**Note on the last row:** the manifest says 33; I counted **39** (11 + 6 + 10 + 12). The manifest
under-reports its own test count. Not a defect — nothing is missing, the extra six are the
`test_coverage.py` additions the manifest itself lists as "+6" — but the number in "How to verify"
is wrong and a later checker re-running it would see a mismatch. Recorded here, not filed.

`.goal` T-144's own `done_check` is exactly that command; it passes.

## The four adversarial checks — performed independently

I wrote my own end-to-end script (container `/tmp/checker_b5.py`, never in the repo); the maker's
was deliberately not committed and I did not reconstruct it. Real Chromium, real local fixture
site, `READ_ONLY`, no credentials.

```
CRAWL: 7 screens stop=frontier empty denied=8 issues=15
PRE-MERGE review: approved v 1
POST-MERGE1 review: draft v 2 screens 8
IDEMPOTENT byte-identical: True  d98bee5b0886 / d98bee5b0886   (sha256 of flowspec.json, twice)
existing screen preserved: Reports
PATTERNS: ['/', '/dialog.html', '/reports.html', '/settings.html', '/students', '/students/{id}']
any host in pattern: []
CONFLICTS: [('/reports.html', ["existing screen 'Reports' (scr_known)",
                               "crawled screen 'Crawl Demo - Reports' (node_aad4e2d1169b)"])]
GAPS after merge: []   UNREACHED after merge: []
SHEETS: ['Summary', 'Screens', 'Edges', 'Denied & Skipped', 'Issues', 'Noise']
Summary stop: frontier empty | policy: read_only
REFUSED rows: 8 · refused rows missing reason: 0
NOISE rows: [('cdn.unknown-third.test', 3)]   ISSUES rows: 15 · third-party issues: []
EDGE OUTCOMES: {'navigated': 17, 'off_domain_refused': 1, 'denied_policy': 6, 'same_screen': 2,
                'skipped_unnamed': 1, 'dialog': 1}  → 8 refused edges, 8 refusal rows in the report
```

### 1. The merge cannot launder an approval — **and the gate is NOT decorative**

The one that mattered most. I seeded a spec at `APPROVED`, merged a 7-screen crawl, and got
`DRAFT` at `v2` with the pre-existing human-named screen (`Reports`) byte-preserved.

Then I sabotaged the reset itself. In `stages/explore_merge.py::merge_screens` I replaced
`status=ReviewStatus.DRAFT,` with `status=spec.review.status,` — the exact "forgot to reset" bug —
and re-ran the suite:

```
FAILED tests/test_explore_merge.py::test_new_screens_are_added_and_review_resets_to_draft
  assert <ReviewStatus.APPROVED: 'approved'> is <ReviewStatus.DRAFT: 'draft'>
1 failed, 10 passed
```

A test fails. The human approval gate is real. (`tests/test_ui_crawls.py::test_merge_writes_the_
screens_into_the_flowspec_and_resets_review` defends the same reset on the UI route, so the gate
has two independent guards.) The file was restored from a backup immediately and
`git status --porcelain -- src/autotester/stages/explore_merge.py` is empty — the working tree is
byte-unchanged by this check.

*Method note for future checkers:* `PYTHONPATH` does **not** win over `/app/src` under this repo's
pytest (`sys.path` = `['/app/tests', '/app/src', …]`), so a sabotage in a copied tree is silently
never loaded and every test passes — which reads exactly like "the gate is decorative". I hit that
false negative first and chased it down. The mutation has to happen on the real file, backed up
and restored.

### 2. Idempotence is not vacuous

Merged the same crawl twice and compared the **persisted `flowspec.json` bytes**, not the version
number: identical sha256. No version bump, no second review reset, no duplicate conflict row.

### 3. The coverage fix is real

Reverted `stages/coverage.py::_path_of` to `urlsplit(url).path` (the pre-T-144 behaviour) and
re-ran `tests/test_coverage.py`:

```
FAILED tests/test_coverage.py::test_an_id_bearing_route_no_longer_looks_unknown
FAILED tests/test_coverage.py::test_a_crawled_screen_matching_a_templated_pattern_is_not_a_gap
FAILED tests/test_coverage.py::test_two_crawled_ids_of_one_screen_produce_at_most_one_gap
3 failed, 9 passed
```

Restored; tree clean. `/students/1` + `/students/2` collapsing to one `/students/{id}` screen, and
`gaps=0 unreached=0` after the merge, are the same fix seen end to end.

### 4. X10 — nothing was taught to type

`grep -n 'fill\|select_option\|upload'` over `stages/explore*.py`, `stages/crawl_report.py`,
`stages/coverage.py`, `core/excel.py`, `cli_crawl.py`, `ui/routes_crawls.py`, `ui/crawl_view.py`
returns **nothing**. The merge and report paths introduced no typing.

## X1–X12 re-verified (this unit must not regress the crawl)

- **X1** — `execute.py` and `execute.md` are absent from the commit's diff; `grep -n run_case
  src/autotester/stages/explore.py` = one call site, at `:86` inside `_bootstrap_login`. ✅
- **X2** — `grep` for `playwright` imports / `.page.` across `src/autotester/` outside `browser/`
  returns nothing. ✅
- **X3–X9, X11, X12** — `scripts/explore_proof.py` **10/10**, re-run by me because `coverage.py`
  and `cli.py` both changed: `/students/{id}` collapsed to one screen, no sentinel page reached,
  destructive controls all denied, external link refused, first-party 404 reported, analytics never
  reported, unnamed control skipped-not-clicked, stop reason named, crawl provider-free. ✅
- **X10** — above. ✅

## Contract work done in this check (checker is the single writer)

Authorized by **D-015** (`Changes-authorized`: `qa/contracts/explore.md`, and "coverage.md V1 after
B5"). Both amendments are **routine** — they add criteria and tighten one; nothing is softened.

- **`explore.md` X13–X16 added.** I did not rubber-stamp the maker's wording:
  - **X13** gained a mandatory sabotage clause — the DRAFT reset must be defended by a test that
    fails when the reset is removed. A gate no test defends is decorative, and this contract now
    says so rather than trusting that someone will think to check.
  - **X14 — the exception is RIGHT, and I have upheld it.** Two screens found by the *same* crawl
    sharing a `url_pattern` must not raise a `Conflict`. X3 requires two states at one URL with
    different controls to be two screens; a single source correctly modelling an SPA is not two
    sources disagreeing. Raising a conflict there would file a false one on every SPA in every
    product — and the fixture already proves it fires immediately (7 screens over 6 patterns).
    A `Conflict` means *sources disagree*, not *patterns collide*; I re-stated the criterion in
    those terms so the exception reads as the rule's meaning rather than as a carve-out. The
    maker's own account is corroborated: he hit the false-positive by running it, not by reasoning,
    and pinned it with `test_two_spa_states_at_one_url_are_two_screens_not_a_conflict`.
    **Two residuals of the implementation are recorded inside the criterion** rather than left
    implicit — AT-102 and AT-103 below. The exemption is right; its *scope* is one crawl where it
    should be one source.
  - **X15** kept, with the reason (`coverage.py` compares paths, `node.url_template` carries a
    host) written into the criterion.
  - **X16 tightened** — stop-reason and every refused edge with its reason on *both* surfaces;
    third-party noise auditable in the workbook and never an issue; and the honest gap (the page
    omits noise) recorded as tracked **AT-105** instead of letting the criterion read clean.
  - The maker's offered no-fire list is folded in.
- **`coverage.md` V1 amended + V5 added.** V1 now names `core.urls.url_template(..., keep_host=
  False)` as the one normaliser and requires **both sides** to use it, plus a load-bearing-fix
  clause (revert it and tests must fail — executed, 3 fail). V5 pins the crawl-sourced twins and
  states that `unreached_screens` is **not** a gap and must never become a `VideoRequest` — a
  bounded crawl seeing less than the spec describes is expected, and turning that into a video ask
  would be the "coverage means the script ran" failure in reverse. V2–V4 byte-unchanged and
  re-verified.

The `qa/feedback-inbox.md` 2026-09-08 entry is folded by these two amendments.

## `ui.md` U1–U9 — unaffected, spot-re-verified

The new routes go through `ProjectStore` only, with no parallel store (U1); read live per request
and 404 an unknown slug via `_load_project_or_404` (U2); import no `SecretStore` and touch no
`.env` (U3); add no run/report logic (U4); and escape every user-derived value in `crawl_view.py`
— confirmed by `test_crawl_page_escapes_injected_text` and by reading the module: every
interpolation is `escape(...)`, `crawl_id` additionally passes `_require_safe_id`, and the
path-traversal probe on `report.xlsx` is refused (U5). U6–U9 untouched by this diff.

## Design rules (`core-invariants.md`)

`doctor: clean` covers the caps. Worth naming because the manifest claims it: **C3 (one concept,
one place) is genuinely honoured** — `grep -rn 'def autosize_columns\|def _reserved_temp_path'
src/autotester` returns exactly one definition each (`core/excel.py:13`, `ui/helpers.py:201`),
so the second exporter and the third download route reuse rather than copy. `explore` was *moved*
into `cli_crawl.py`, not duplicated. C4 holds: the maker's end-to-end script stayed in `.work/`
and out of the commit — which is why I wrote my own, as he asked.

## Issues written (`qa/issues.jsonl`)

None of these is a violation of a criterion as authored; all four are residuals or gaps, recorded
so a later unit can close them.

| id | sev | what |
|---|---|---|
| **AT-102** | medium | The conflict test is `clash.name != incoming.name`, so a screen re-discovered at a known pattern under the **same** name is a silent duplicate — two identically-named screens on one pattern, no `Conflict` explaining it. Probed live. |
| **AT-103** | medium | The (correct) SPA exemption is scoped to one **crawl**, not one **source**: the identical SPA pair gives `conflicts 0` merged in one call and `conflicts 1` merged as crawl c1 then c2. A project that re-crawls (the UI has an "Explore again" button) accumulates false conflicts. Fails safe — noise, not loss. |
| **AT-104** | medium | The UI merge button re-arms the human gate **silently**: it sends the spec to DRAFT and redirects to a page that renders no review status (`grep -n review` over both crawl UI modules returns nothing). The CLI names it explicitly and its docstring says exactly why it matters. |
| **AT-105** | low | Third-party noise counts reach the workbook only; the crawl page never shows the X9 "we counted it and did not report it" trail. Tracked inside X16. |

## Explanation

Every criterion is evidenced by output I produced myself, and the two claims that could have been
theatre are not: sabotaging the `Review(...)` DRAFT reset fails a test, and reverting `_path_of`
fails three — so neither the human approval gate nor the coverage fix is decorative. The unit does
what it says (7 real screens merged into an APPROVED spec send it back to DRAFT at v2, a second
merge is byte-identical, the workbook carries the stop reason and all 8 refusals with reasons), it
regresses nothing (549/549, `explore_proof` 10/10, X1/X2/X10 greps clean), and its judgement call
on X14 is correct — a single crawl correctly modelling an SPA is not a disagreement, and treating
it as one would file a false `Conflict` on every SPA. The four issues filed are the seams that
judgement leaves behind: the exemption is scoped to a crawl rather than to the crawler as a source
(AT-103), the clash test keys on a name string rather than on identity (AT-102), and the gate this
unit correctly arms is invisible on the surface most people will use (AT-104). None blocks the
PASS; AT-104 is the one I would fix before T-145 points this at a real product, because a user who
merges a live crawl and is not told the FlowSpec is now unapproved will believe it still is.
