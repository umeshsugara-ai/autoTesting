# Manifest — t124-consent-gates
**Contract:** **`qa/contracts/consent.md` does not exist yet — this unit requests it.** The
criteria I built against (CN1–CN7) plus a no-fire list are filed verbatim in
`qa/feedback-inbox.md` (2026-09-08 entry) for the checker to author; contracts are checker-owned
and the maker never writes one. Until it exists, judge against `qa/contracts/core-invariants.md`
(C1, C2, C3, C6) and `qa/contracts/explore.md` **X1–X16, which this unit must leave intact**.
**Goal task:** T-124
**Date:** 2026-09-08
**Fix cycle:** 1 of max 3
**Dual check:** no
**Plan:** plan.md §5A "T-124 — the two-gate consent model", authorised by **D-018**
**Issues addressed:** **AT-100** (T-145's `done_check` could never fail)

## Why this unit exists
The explorer is about to be pointed at a live production ERP, and `T-145`'s `done_check` was
`{"cmd": "true"}` — a check that cannot fail, on the highest-risk task in the plan. Consent was a
habit: `write_policy` defaults and gate files that a careful operator honoured. This makes it a
file a human writes once and a runner checks every time.

## What changed
- **New** `schema/approval.py` — `RunApproval(Artifact)`: target, scope, bounds, `granted_by`,
  `granted_at`, `expires_at`, `production`. Id is content-addressed over **every bound field**;
  `note` is deliberately outside the payload so a human may annotate without re-granting.
- **New** `core/consent.py` — `require_approval(...)` and `ApprovalRequired`. Exact matching on
  (project, kind, target); intact + unexpired + at least as wide as the run.
- `stages/explore.py` — `_require_consent` called **before the crawl envelope, the browser
  navigation and the screenshot directory exist**. At the seam, not in each caller.
- `schema/enums.py` `ApprovalKind`; `core/paths.py` `approvals`; `store/project_store.py`
  `add_approval`/`list_approvals`.
- `cli_crawl.py` — `autotester approve`; `explore` exits 2 with the refusal instead of a
  traceback. `ui/routes_crawls.py` — the refusal is a **403**, not a 500: it was refused on
  purpose.
- **New** `scripts/check_crawl_approval.py` — **T-145's real `done_check`**, and `.goal/goal.json`
  updated to use it. It asserts a finished crawl on disk **and** an approval covering its bounds.
- Tests: **new** `tests/test_consent.py` (17), `tests/test_explore.py` +2 (the gate refuses and
  writes nothing / a run wider than its approval refuses), and `scripts/explore_proof.py` gains a
  **new first invariant**.

## Two things found by running it, not by reasoning about it
1. **The refusal's own suggestion did not work.** The first message printed a grant command with
   no bounds — and `--max-actions` defaults to 0, which every real crawl exceeds. An operator who
   pasted it verbatim would have been refused a second time. A suggestion that does not work is
   worse than none, because it spends the reader's trust on the way to the same dead end. The
   command now carries the bounds of the run it is refusing, and two tests pin it.
2. **The new `done_check` fails today, correctly** — `FAIL  no finished crawl on disk for 'erp'`,
   exit 1. That is the point: unlike `true`, it can fail.

## The trade I made deliberately — please judge it
The gate applies to **every** crawl, including local fixture crawls in the test suite, rather than
being conditional on the target being remote. That cost an update to four test entry points and
the proof script. I chose it because *"is this localhost?"* is a heuristic that fails **open** on a
misconfiguration, and because a guard only the production callers pass through is a guard tested
nowhere — every crawl test now also exercises the gate's happy path. If the checker disagrees, the
alternative belongs in the contract rather than left implicit.

## Live proof (real browser, no credentials) — pasted, not summarised
```
$ docker compose exec -T autotester uv run python scripts/explore_proof.py
PASS  no approval => nothing runs, nothing written  (refused, no crawl dir created)
PASS  finished, did not hang  (stop_reason=frontier empty)
...
11/11 invariants held
```
The first line is the new one, and it is proven **at the transport**: it attempts a real ungated
crawl and asserts no crawl directory was created — not that the code looks like it would refuse.

## How to verify (commands + expected)
- `docker compose exec -T autotester uv run pytest -q` → **582 passed, 1 skipped** (563 before)
- `docker compose exec -T autotester uv run ruff check src tests scripts` → `All checks passed!`
- `docker compose exec -T autotester uv run autotester doctor` → `doctor: clean`
- `docker compose exec -T autotester uv run python scripts/explore_proof.py` → `11/11`
- `docker compose exec -T autotester uv run python scripts/check_crawl_approval.py erp` →
  **exit 1** with `no finished crawl on disk` (this is the expected state until T-145 runs)

## Adversarial checks worth making
1. **Prove the gate is not decorative:** delete the `_require_consent` call and confirm
   `explore_proof.py`'s first invariant FAILS and the two new explorer tests fail.
2. **Prove tamper detection is real:** hand-edit `max_actions` in an `approvals.jsonl` row on disk
   and confirm the crawl refuses with "edited after it was granted" rather than honouring it.
3. **Prove exactness:** grant for `https://host/a` and confirm a run against `https://host/a/b` is
   refused. A prefix match would defeat the whole gate.
4. **Prove the suggestion works:** take the command from a refusal, run it, re-run the crawl, and
   confirm it now proceeds. If it refuses twice, finding (1) has regressed.

## What this unit does NOT do (deliberately)
Revoking an approval (expiry only, for now); gating `ingest`/`expand`/`run_case` (T-122's live-case
gate is its own unit); a UI grant form (CLI only — the credentials page is the right home and is
not built here); org-level approvals; any auto-granting path whatsoever.

## Status: ready-for-check
