# VERDICT — at108-at114-swallowed-causes

**Cycle checked: 1**  ·  **Date:** 2026-09-08  ·  **Checker:** fresh subagent, bound to `D:/autoTesting`
**Manifest:** `qa/manifests/at108-at114-swallowed-causes.md` (Status `ready-for-check`, Fix cycle 1)
**Commit judged:** `6e98487`  ·  **Contract:** `qa/contracts/explore.md` X11/X16, `core-invariants.md` C9

## VERDICT: PASS

## What I re-ran myself (host; Docker daemon down, `uv` native — not a blocker)

| Command | My result | Manifest claim | Match |
|---|---|---|---|
| `uv run pytest -q` | 592 collected, **590 passed, 2 skipped** (counted from the progress dots: 8x72+16 items, two `s`) | 590 passed, 2 skipped | yes |
| `uv run ruff check src tests scripts` | `All checks passed!` | same | yes |
| `uv run autotester doctor` | `doctor: clean` | same | yes |

The 2 skips are the live-Mongo opt-in and the POSIX-only `tests/test_ui.py:163`; the container's 1
skip is explained. Not charged.

## Sabotages — reproduced by me, not read from the manifest

Isolated copy via `git archive HEAD` into the scratchpad with `PYTHONPATH` pinned to the copy's
`src/` (verified: `autotester.__file__` resolves inside the scratch tree, so nothing touched the
live working tree — AT-101 honoured). Each sabotage applied to `explore_node.py`, suite re-run,
file restored between runs.

```
=== SABOTAGE 1 capture() blind except: 1 failing
    FAILED tests/test_explore_error_causes.py::test_a_screenshot_failure_is_recorded_with_its_cause
=== SABOTAGE 2 return_to() cause discarded: 1 failing
    FAILED tests/test_explore_error_causes.py::test_a_lost_screen_reports_why_it_was_lost
=== SABOTAGE 3 _recover() bare pass: 1 failing
    FAILED tests/test_explore_error_causes.py::test_a_failed_recovery_says_so_instead_of_passing_silently
=== SABOTAGE 4 the LAZY fix (EVIDENCE -> NAVIGATION): 2 failing
    FAILED tests/test_explore_error_causes.py::test_a_screenshot_failure_is_recorded_with_its_cause
    FAILED tests/test_explore_error_causes.py::test_a_screenshot_failure_is_not_reported_as_a_product_bug
=== RESTORE: 4 passed
```

**The specific claim holds exactly as written** — 1/1/1/2, each failure landing on the test that
defends that site, and sabotage 4 taking down the second test that exists to defend against the
wrong fix. This is the AT-117 check applied to this unit: the pasted transcript matches a real run.

## Rulings on the two design calls the manifest put to the checker

**1. `IssueKind.EVIDENCE` as a new member of a closed vocabulary — UPHELD.**
The argument is sound, not vocabulary creep. `CrawlIssue` is read as a finding *about the product
under test*; X9 already establishes in this contract that the crawl must not inflate that list with
things that are not the product's fault (third-party noise), and a failure of the crawler itself is
the same shape one step closer to home. Reusing `NAVIGATION` would have made the tool's own death
indistinguishable from the product losing a screen — and the maker's second test pins exactly that,
provably (sabotage 4). **On process:** an *additive* enum member that weakens no criterion, reverses
no goal direction and enables no outward-facing action is a **routine amendment, not a new DECISIONS
entry.** D-015 authorizes the stage, its file layout and `qa/contracts/explore.md`; adding a member
to a vocabulary that decision already owns is maintenance inside its authorization, the same way
widening the deny-list is (X6/D-016). I have recorded it in the contract's amendment log instead,
which is the checker's own surface.

**2. `capture()` staying non-fatal — UPHELD; it does not under-fix AT-114.**
AT-114's evidence names the defect precisely: *"a genuine capture failure is indistinguishable from
a screen that simply has no screenshot."* That is a statement about **silence**, not about survival.
X11 requires a crash-survivable partial graph, and killing a whole crawl over a compositor hiccup
would trade a documented hole for no graph at all — strictly worse against the criterion the unit is
judged on. The distinction AT-036 built into `session.screenshot` (retry the one transient CDP race,
re-raise everything else) is now preserved *as information* rather than as a process exit. Correct
call.

## Adversarial probes — what I tried to break

**Stale-cause hunt (`rt.return_error` is shared mutable state).** I could not construct a path that
reports a previous node's cause as the current one's. `return_to` clears the field on entry before
any branch can set it; `_why` is called only on the two `not return_to(...)` branches in
`visit_node`, i.e. only after a call that just cleared and re-set it; `_recover` has exactly two
callers (`explore_node.py:150,154`), both inside `return_to` after the clear; nothing else in `src/`
reads `return_error`, and it is scratch (never persisted, never exported). The success path runs the
same clear, so no stale value survives a later success either. **No finding.**

**Sweep completeness — verified by grep, not by the manifest's word.**
`grep -rn except src/autotester/stages/explore*.py src/autotester/stages/screen_identity.py`:
`explore_safety.py`, `explore_merge.py` and `screen_identity.py` return **no** matches — the
manifest's claim is true. `try_action` (`explore_node.py:114/116`) already binds its cause into the
edge reason and is correctly left alone. **And the two blocks the manifest did not mention:**
`stages/explore.py:110` and `:113` in `_seed` — I read them; they were **already correct** (bound to
`rt.seed_error`, with `NavigationRefused` split from the generic case, per AT-098). Nothing was
missed. The sweep is complete over the surface it claims.

**Is `_why` honest?** Yes, and I confirmed the exact behaviour rather than reasoning about it. Under
the AT-113 tests' shape (which monkeypatch `return_to` wholesale, so `return_error` is never set) the
issue reads:
`[navigation] could not return to this screen before exploring it — abandoned unexplored: cause not recorded`.
That is **acceptable and not a hidden regression**: the real code path is defended by
`test_a_lost_screen_reports_why_it_was_lost`, which sabotage 2 proves is load-bearing, so the honest
placeholder appears only where a test has deliberately replaced the function that would have set the
cause. An explicit "cause not recorded" is strictly better than the old silence — it tells the reader
the gap is in this crawler, not in the product.

## FINDING (filed, not a FAIL): AT-120 — the separation stops at the enum

The one thing I broke. I ran a real crawl at HEAD with `page.screenshot` always raising:

```
crawl.issues (headline) = 5
issue kinds: {'evidence': 4, 'navigation': 1}
```

**One product issue is reported as five.** `add_issue` (`explore_node.py:53`) increments `rt.issues`
without looking at the kind, and that single total is what `crawl_report.py:42` prints as
**"Issues found"**, what `ui/routes_crawls.py:66` shows in the crawls table, and the Issues sheet
(`crawl_report.py:133`) / the UI Issues card (`routes_crawls.py:125`) list every kind together with
no partition. So the manifest's claim — *"New IssueKind.EVIDENCE keeps a failure of the TOOL out of
the product's issue list"* — **holds at the enum level only**; in every artifact a human actually
reads, the crawler's own failures are still counted as the product's. Before this unit a screenshot
failure filed no issue at all, so this inflation is newly introduced here.

**Why this is a ledger issue and not a FAIL of this unit:** every criterion this unit is judged on is
evidenced by my own execution — the swallowed causes are gone, all three sites record their cause,
the recovery cause is appended rather than replacing the original, and the tests are individually
load-bearing. The leak lives in `crawl_report.py` and `routes_crawls.py`, which this unit does not
touch and whose reporting criterion (X16) is B5 territory; failing the unit would burn a fix cycle on
work whose right home is a separate one. Filed as **AT-120 (high)** with the fix direction: count
EVIDENCE separately, give it its own summary row and its own sheet/partition — mirroring the `Noise`
sheet X9/X16 already require for third-party noise. X16 is **not clean** until that lands, and I have
said so in the contract.

## Ledger

- `AT-108` → **fixed** (2026-09-08) — `return_to` binds its cause; `_recover` appends rather than drops.
- `AT-114` → **fixed** (2026-09-08) — `capture` records the cause it used to discard, still non-fatal.
- `AT-120` → **open, high** — new, above.

Both claimed `Issues addressed` are genuinely addressed by this unit; neither stays open.

## SCOREBOARD

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (X11, X16 as scoped to this unit), 1/1 invariants hold (C9)
FAILURES: none
ISSUES-WRITTEN: AT-120 (high)
EXPLANATION: I re-ran all three verify commands (590 passed / 2 skipped, ruff clean, doctor
clean) and independently reproduced all four sabotages in a git-archive scratch copy — 1/1/1/2
failures, each landing on the test that defends that site, exactly as claimed. Both design calls
are upheld: EVIDENCE is a sound distinction and an additive enum member is a routine amendment
under D-015, not a new decision entry; and keeping capture() non-fatal fixes the silence AT-114
actually named without trading X11's crash-survivable graph for a dead crawl. The sweep is
complete — explore_safety/explore_merge/screen_identity have no except at all, try_action was
already correct, and explore.py's two unmentioned blocks were already bound to seed_error by
AT-098. One real finding, filed rather than failed: the tool/product separation stops at the enum
— crawl.issues, the workbook's "Issues found" row and the crawls UI all still fold EVIDENCE into
the product's total, so a crawl with one product bug and four failed screenshots reports five
issues (AT-120, high).
```
