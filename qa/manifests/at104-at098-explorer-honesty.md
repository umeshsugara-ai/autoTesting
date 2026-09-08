# Manifest — at104-at098-explorer-honesty
**Contract:** `qa/contracts/explore.md` (X7 the host re-check is a SECURITY refusal; X13 a crawl
proposes screens and never approves them) + `qa/contracts/ui.md`.
**Goal task:** none (issue-fix batch)
**Date:** 2026-09-08
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** **AT-104** (medium), **AT-098** (medium) — both filed as "before T-145",
the live logged-in ERP crawl

## Why these two together
Both are the same failure shape: **the system knew something and did not say it.** One re-armed a
human approval gate without telling the human; the other collapsed a security refusal and a
network timeout into one indistinguishable string. Neither is a crash, and neither would ever
appear in a passing test suite — which is exactly why they matter on a live production crawl.

## AT-104 — the merge button silently un-approved the FlowSpec
`POST /projects/{slug}/crawls/{id}/merge` sends an APPROVED FlowSpec back to DRAFT (correctly — a
crawl may propose screens, never approve them) and then redirected to a page that rendered **no
review status anywhere**. `grep -n review src/autotester/ui/routes_crawls.py
src/autotester/ui/crawl_view.py` returned nothing. The CLI path says it explicitly; the UI path
did not, so a human could re-arm their own gate and never learn of it.

- `ui/crawl_view.py` — new `review_line(spec)`: FlowSpec version, a toned review pill, the review
  note, and an explicit "**This FlowSpec is not approved.** It drives no test expansion until a
  human approves it again." when the status is anything but approved.
- `ui/routes_crawls.py` — rendered at the top of the "Against the FlowSpec" card, which is the
  card the merge button lives in and the page the merge redirects to.

## AT-098 — a security refusal read exactly like an outage
`stages/explore.py::_seed` did `except Exception: return None`, so every distinct startup failure
became the single string `"could not open base_url"`. Detection was never lost — the crawl aborted
and said so — but the diagnosis was: an operator watching the live ERP crawl could not tell whether
the ERP was down or whether **the crawl had been refused by its own domain guard**, which is the X7
security boundary.

- `_seed` now binds the cause, and `NavigationRefused` is caught separately and reported as
  `refused by the domain guard: <detail>`; anything else reports `<ExceptionType>: <detail>`.
- `ExploreRuntime.seed_error` carries it into `Crawl.stop_reason`.

## Tests, and the sabotage that proves they bite
- `tests/test_ui_crawls.py` +2: approved-then-merged shows DRAFT **and** the "not approved"
  warning; a still-approved spec is **not** falsely warned about (the warning has to mean
  something when it appears). Removing `review_line` from the route fails **both** — the second is
  what stops a fix that just prints the warning unconditionally.
- `tests/test_explore.py` +2: a `NavigationRefused` at seed yields a stop reason containing
  `refused by the domain guard` **and** the offending host; a `TimeoutError` names `TimeoutError`
  and must **not** say "refused by the domain guard" — the two must stay distinguishable in both
  directions, which is the entire point of the issue.

## How to verify (commands + expected)
- `docker compose exec -T autotester uv run pytest -q` → **560 passed, 1 skipped, 0 xfailed** (556 before this batch: 555 passed + the
  AT-106 xfail, which became a live pass when D-020 corrected the hook path in the sibling unit)
- `docker compose exec -T autotester uv run ruff check src tests scripts` → `All checks passed!`
- `docker compose exec -T autotester uv run autotester doctor` → `doctor: clean`
- `docker compose exec -T autotester uv run python scripts/explore_proof.py` → `10/10 invariants
  held` — `explore.py` changed, so B3 must be re-proven.
- Sabotage worth running yourself: delete `crawl_view.review_line(spec)` from the route (both UI
  tests must fail), and restore `except Exception: return None` in `_seed` (both explorer tests
  must fail).

## Not done here
AT-102, AT-103 (the conflict-scope residuals the T-144 checker recorded inside X14) and AT-105
remain open — they are FlowSpec-merge semantics, not honesty-of-reporting, and belong with the
Track A merge work (T-135) that shares the same shape.

## Status: checked-PASS

Verdict: `qa/verdicts/at104-at098-explorer-honesty.md` (**Cycle checked: 1**, PASS, 9/9 criteria,
4/4 invariants). **AT-104 and AT-098 close.** The checker broke each fix three different ways
rather than reading the diff, and confirmed the both-directions property that was the whole point:
an approved spec is not falsely warned, and a timeout does not claim a domain refusal.

**It also found the same defect one level down: AT-108 (low, new).**
`explore_node.return_to()` discards the cause of a failed return, exactly as `_seed` discarded the
cause of a failed start. I fixed the instance the issue named and did not look for its siblings —
the honest lesson is that "the cause was swallowed" is a *shape*, not a location, and the sweep for
it should have been part of this unit rather than a follow-up. Queued with AT-102/AT-103/AT-105.

The deferral of AT-102/AT-103/AT-105 to T-135 was judged honest: they are FlowSpec-merge semantics
rather than honesty-of-reporting, and none is load-bearing for T-145.
