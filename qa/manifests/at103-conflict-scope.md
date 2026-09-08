# Manifest — at103-conflict-scope
**Contract:** `qa/contracts/explore.md` **X14** ("sources disagree, not patterns collide") and
**X3** (two SPA states at one URL with different controls are two screens).
**Goal task:** none (issue-fix unit)
**Date:** 2026-09-08
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** **AT-103** (medium)

## Why this one, now
The checker that PASSed `at104-at098-explorer-honesty` left a forward note rather than a blocker:
**AT-103 fires the first time someone presses "Explore again"** on the ERP after a merge — a false
`Conflict` per SPA state, i.e. noise a live-crawl operator would be reading during T-145, the run
Umesh watches. It is cheap to fix and it degrades exactly the demo it would appear in.

## The defect
`merge_screens` built `by_pattern` from the **pre-existing spec only**, and screens added during
the current merge went into `known_ids` but never into `by_pattern`. That is precisely what made
the intra-crawl SPA exemption work — and it scoped the exemption to **one crawl** rather than to
**identity**. Probed by the checker: the same SPA pair (`/`, signatures `sig_plain` /
`sig_filters`) gives `screens=2 conflicts=0` merged in one call, and `screens=2 conflicts=1`
merged as crawl 1 then crawl 2. The UI's "Explore again" button makes re-crawling the intended
workflow, so a project accumulated a false conflict per SPA state on every re-crawl.

## The fix — at the principle, not at the symptom
A `Conflict` means **two sources disagree**, not that two patterns collide. Two screens that both
carry a *structural* identity are by definition structurally different screens at one URL — an
SPA, which X3 requires to be two screens — so they never conflict with each other, however many
crawls found them. Only a claim with **no structural identity** (a human's or an ingested video's
screen, which asserts a URL and nothing more) can be contradicted by a crawl.

- `stages/explore_merge.py` — `_is_structural(screen)` and `_disagreement(clash, incoming, crawl_id)`,
  which carries the reasoning next to the code that implements it. (`merge_screens` hit doctor's
  50-line function cap once the explanation was in its docstring — extracting the rule was the
  right answer rather than trimming the reason for it.) The
  crawl-scoped `by_pattern` construction is unchanged; it is no longer load-bearing for the
  exemption, which now rests on identity.
- The coupling `_is_structural` depends on (`ScreenNode` ids come from `content_id("node", …)`) is
  **pinned by its own test**, so if that prefix ever changes this fails loudly instead of silently
  turning every structural screen into a conflict.

## Sabotage — both directions, and the lazy fix is the one that matters
```
=== revert to the crawl-scoped exemption ===
FAILED test_spa_states_found_by_two_separate_crawls_still_do_not_conflict

=== "_is_structural -> return True" (the lazy fix: just stop filing conflicts) ===
FAILED test_a_name_clash_on_the_same_url_keeps_both_and_records_a_conflict
FAILED test_the_same_conflict_is_not_recorded_twice_on_re_merge
FAILED test_a_human_authored_claim_is_still_contradicted_by_a_crawl
```
The second block is the point: a "fix" that suppressed conflicts wholesale — which would also make
AT-103's symptom disappear — does **not** pass this suite. `git status --porcelain src` clean
after restoring.

## How to verify (commands + expected)
- `docker compose exec -T autotester uv run pytest -q` → **563 passed, 1 skipped** (560 before)
- `docker compose exec -T autotester uv run ruff check src tests scripts` → `All checks passed!`
- `docker compose exec -T autotester uv run autotester doctor` → `doctor: clean`
- `docker compose exec -T autotester uv run python scripts/explore_proof.py` → `10/10` — B5's
  merge changed, and the proof is the only end-to-end that runs a real browser.
- Worth doing yourself: reproduce the checker's original probe (merge one SPA state as crawl 1,
  the other as crawl 2) and confirm `conflicts=0` where it was 1.

## Still open, deliberately
**AT-102** (the clash test keys on the name string, so a same-name re-discovery is a silent
duplicate) and **AT-105**. AT-102 is a *different* failure — it under-reports rather than
over-reports — and it cannot fire on T-145's first merge either. **AT-108** (`return_to` swallows
its cause, the sibling of AT-098) is queued: the honest lesson from that check was that "the cause
was swallowed" is a shape rather than a location, so it wants a sweep of every `except` in
`stages/explore*.py`, not another one-line patch.

## Status: ready-for-check
