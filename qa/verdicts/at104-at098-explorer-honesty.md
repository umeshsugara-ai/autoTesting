# Verdict — at104-at098-explorer-honesty

**Date:** 2026-09-08
**Cycle checked:** 1
**Manifest:** `qa/manifests/at104-at098-explorer-honesty.md` (Fix cycle: 1 of max 3)
**Contracts:** `qa/contracts/explore.md` (X7, X13 named in the dispatch; X1/X2/X10/X12/X16
re-verified because `explore.py` changed) + `qa/contracts/ui.md`
**Unit under check:** commit `5d99520`, the parts touching `src/autotester/ui/` and
`src/autotester/stages/explore.py`. The AT-106 hook half of that commit is **not** this unit and
was not judged here (it belongs to `at097-session-start-hook-regression`, checked concurrently).
**Bound to:** `d:/autoTesting`. Every path read or written is inside it.
**Mode:** A (unit check). Adapter: `qa/adapter.json`, `kind: shell`.

```
VERDICT: PASS
SCOREBOARD: 9/9 criteria met, 4/4 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: AT-108 (new, low) · AT-098 open→fixed · AT-104 open→fixed
EXPLANATION: Both fixes make a system that already KNEW something actually SAY it, and both
are defended by tests that bite in both directions — I proved that by breaking each fix three
different ways rather than by reading the diff. All four verify commands are green on my own
re-run, including scripts/explore_proof.py 10/10 (B3 re-proven, explore.py changed). I counted
the suite myself under -rA because -q suppresses the summary here: 560 passed, 1 skipped, 0
xfailed — exactly the maker's claim. The AT-102/AT-103/AT-105 deferral is honest and none of
the three is load-bearing for T-145 (reasoning below). One residual of the same shape as AT-098,
one level down in `return_to`, is filed as AT-108 rather than charged against this unit.
```

---

## 1. What I re-ran myself (nothing pasted was trusted)

All inside the running container, `docker compose exec -T autotester`:

| Command | My result | Manifest claim | Match |
|---|---|---|---|
| `uv run pytest -q` | **560 PASSED, 1 SKIPPED**, 0 FAILED/XFAIL/XPASS (561 outcome lines, counted with `-rA \| sort \| uniq -c`) | 560 passed, 1 skipped, 0 xfailed | ✅ |
| `uv run ruff check src tests scripts` | `All checks passed!` — exit 0 | `All checks passed!` | ✅ |
| `uv run autotester doctor` | `doctor: clean` — exit 0 | `doctor: clean` | ✅ |
| `uv run python scripts/explore_proof.py` | `10/10 invariants held` (finished-not-hung, ≥4 screens, `/students/{id}` collapsed, no sentinel reached, 6 destructive controls denied, external link refused, first-party 404 reported, console error reported, analytics never reported, unnamed control skipped) | `10/10 invariants held` | ✅ |

The count matters because this repo suppresses pytest's summary line under `-q`; I did not read a
number off the maker's message. `-rA` outcome lines: `560 PASSED`, `1 SKIPPED`, nothing else.

Working-tree note: `git diff 5d99520 -- src tests` was **empty** before I started, so the files I
judged are byte-identical to the commit under check.

## 2. AT-104 — does the crawl page actually tell the human?

**Yes, and the warning means something.** `ui/routes_crawls.py:99-102` renders
`crawl_view.review_line(spec)` at the top of the "Against the FlowSpec" card — the card the merge
button lives in and the page `POST …/merge` redirects to (`RedirectResponse` →
`crawl_page`). `crawl_view.py:139-153` prints the FlowSpec version, a toned review pill, the
review note, and the explicit "**This FlowSpec is not approved.** It drives no test expansion
until a human approves it again." only when `status != "approved"`.

I did not take the manifest's word for the warning being load-bearing. **Three sabotages, all
restored:**

| Sabotage | Result | What it proves |
|---|---|---|
| Delete `crawl_view.review_line(spec)` from the route (`routes_crawls.py:100`) | **BOTH** UI tests FAIL — `test_the_merge_button_tells_the_user_it_un_approved_the_flowspec` (`assert 'draft' in …`) and `test_an_approved_flowspec_is_not_falsely_warned_about` (`assert 'approved' in …`). The other 10 tests in the file still pass. | The route wiring is defended, and the second test is a real test, not a tautology — it fails on the positive half too |
| Change `if status != "approved"` to `if True` (warning printed unconditionally) | `test_an_approved_flowspec_is_not_falsely_warned_about` **FAILS**; the merge test still passes | This is the harder half the dispatch asked about: **a fix that just prints the warning always would not pass this suite.** The warning is meaningful, not decorative |
| (control) restored file | all 12 pass | restoration verified |

X13 is untouched by this unit and still holds: `merge_screens` still resets `Review` to DRAFT and
`test_merge_writes_the_screens_into_the_flowspec_and_resets_review` still passes. AT-104 was never
about the gate — it was about the gate being invisible. It is now visible on the surface most
likely to be used, which is the whole point before T-145.

`spec is None` is handled separately (`routes_crawls.py:106-112`, "This project has no FlowSpec
yet") so the new call cannot raise on a fresh project — and that path creates a DRAFT spec anyway,
so no gate is re-armed silently there either.

## 3. AT-098 — is a security refusal distinguishable from an outage, in BOTH directions?

**Yes, both directions, and both are tested.** `stages/explore.py:106-110` binds the cause:
`NavigationRefused` → `refused by the domain guard: <detail>`; anything else →
`<ExceptionType>: <detail>`. `run_crawl:193` carries it into
`Crawl.stop_reason` as `could not open base_url -- <cause>`.

**Two sabotages, both restored:**

| Sabotage | Result |
|---|---|
| Restore `except Exception: return None` in `_seed` | **BOTH** explorer tests FAIL — both stop reasons collapse to `'could not open base_url -- cause not recorded'`. The other 15 tests in the file pass |
| Make the generic branch *also* say `refused by the domain guard: …` | `test_an_ordinary_failure_at_seed_names_its_exception_type` **FAILS** (`assert 'refused by …domain guard' not in 'could not o…on timed out'`); the refusal test passes |

The second one is the direction that actually matters for a live crawl: **the timeout case cannot
claim a domain refusal.** A fix that labelled everything a refusal would be caught. Note the
fallback string `'cause not recorded'` in `run_crawl` is honest — it says the cause is missing
rather than inventing one.

X7 itself (the post-action host re-check, the SECURITY refusal) is unchanged and intact:
`explore_node.py:111-115` still re-checks `check_destination(current_url())` after every action
and produces an `OFF_DOMAIN_REFUSED` edge plus a `NAVIGATION` issue, and `try_action` already
separates `NavigationRefused` from a generic exception (`:103-107`). This unit closed the same
honesty hole at seed time that X7's path already had at action time.

## 4. Contract criteria judged

**`explore.md` (7/7 in scope)**

- **X1** — `grep -n run_case src/autotester/stages/explore.py`: one call site, `:87` inside
  `_bootstrap_login`. `execute.py` and `execute.md` absent from the commit's diff. ✅
- **X2** — `grep -rn 'import playwright|from playwright|\.page\.' src/autotester --exclude browser/`
  → nothing. ✅
- **X7** — re-verified above; unchanged by this unit and now consistently reported at seed too. ✅
- **X10** — `grep -n 'fill|select_option|upload' src/autotester/stages/explore*.py` → nothing. ✅
- **X12** — no provider reference in `explore.py` outside its docstring; `explore_proof.py` runs
  provider-free and passed 10/10. ✅
- **X13** — a crawl still proposes and never approves: merge still resets to DRAFT (test passes),
  and the reset is now *reported* rather than only performed. ✅
- **X16** — the crawl page still gives `stop_reason` equal billing (`summary_stats`,
  `test_the_crawl_page_names_why_the_crawl_stopped` passes) and still lists every refused/skipped
  edge; AT-105 remains its tracked gap, unchanged. ✅

**`ui.md` (2/2 in scope)**

- **U2** — the crawl page still reads `store.load_flowspec()` live on every request; `review_line`
  renders that live object and caches nothing. ✅
- **U5** — every user-derived value in `review_line` is escaped: `escape(status)` and
  `escape(spec.review.note)`; `spec.version` is `int` (`schema/flowspec.py:140`) and
  `review.status` is a `ReviewStatus` enum (`:120`), so neither can carry markup.
  `theme.pill` documents "text must already be escaped" and is given escaped text.
  `test_crawl_page_escapes_injected_text` passes. ✅

**Core invariants (4/4 in scope)** — **C2** (`doctor: clean`: file ≤300 lines, function ≤50,
module docstrings — `crawl_view.py` grew 23 lines and still passes), **C3** (`review_line` and
`_REVIEW_TONE` each defined exactly once, `crawl_view.py:136/139`; no second copy anywhere in
`src/`), **C4** (repo root clean; my own sabotage backups went to the session scratchpad, never
into the repo), **C5** (the new render path touches no `SecretStore` and no `.env`; it renders
only `project.json`/`flowspec.json` data).

## 5. The deferral — is it honest? (AT-102, AT-103, AT-105)

**Honest, and none of the three is load-bearing for T-145.** I checked this against the actual
on-disk state rather than reasoning from the titles:

- **AT-102** (same-name re-discovery becomes a silent duplicate) and **AT-103** (a later crawl
  files a false `Conflict` on an SPA pattern an earlier crawl merged) both fire only through
  `explore_merge.by_pattern`, which is built **from the pre-existing spec**
  (`explore_merge.py:99-100`). I verified that **no project in this repo has a `flowspec.json` at
  all** (`erp`, `pathlynks`, `regression-demo`, `vidysea-erp` — all four have none). T-145's first
  live crawl therefore merges into an empty or newly created spec, where `by_pattern` is empty and
  neither issue can fire. They are second-merge problems, exactly as the manifest says, and they
  are genuinely FlowSpec-merge semantics rather than honesty-of-reporting — the right home is
  Track A / T-135.
  **One thing the maker should carry forward, not a defect here:** AT-103 *will* fire the moment
  someone presses "Explore again" on the ERP after a first merge, and a false `Conflict` on every
  SPA state is noise a live-crawl operator would be reading. It fails safe (both screens kept,
  nothing overwritten), so it is a queue-priority note, not a T-145 blocker.
- **AT-105** (low — noise counts reach the workbook only) is recorded inside X16 as a tracked gap
  and the audit trail does exist (`Noise` sheet). "We ignored it" stays auditable for anyone who
  downloads the report. Not a blocker.
- Related and worth stating because it is the one issue that *did* gate T-145: **AT-093** (the
  punctuation-separated logout labels) is `verified`, closed 2026-09-07 at
  `explore_safety.normalise_label`. The gate the contract names in X6 is shut. Nothing this unit
  deferred re-opens it.

## 6. New finding — AT-108 (low, filed not charged)

`explore_node.return_to()` (`:135-138`) does `except Exception: _recover(rt); return False` — the
exception is never bound. This is the *same shape* AT-098 just fixed, one level down: a
`NavigationRefused` hit while returning to a node is indistinguishable from a timeout, and the
first call site (`visit_node:182`) marks the node `ABORTED_ERROR` with **no reason string at
all**. Not charged against this unit: AT-098's scope as filed is `_seed`, no criterion requires a
`return_to` reason, and it fails safe (the node is marked, the crawl continues). Filed as **AT-108
(low)** so the residual AT-098's own evidence flagged is not lost when AT-098 closes.
Deliberately **not** flagged: `explore_node.py:33` (`capture`'s "never fatal" swallow, documented
B7 behaviour) and `_recover`'s own inner `except Exception: pass` (last-ditch recovery whose
caller returns `False` regardless).

## 7. Working-tree hygiene (AT-101 discipline)

A second checker was working concurrently on `.claude/hooks/` and
`tests/test_session_start_hook.py`. I used **no `git stash`, no `git checkout`, no `git restore`**
and touched nothing outside this unit. Each sabotage was: copy the file to the session scratchpad
→ patch in place → run → copy the backup back. After the last restore,
`git status --porcelain src tests` is **empty** and `git diff 5d99520 -- src tests` is **empty** —
every sabotaged file is byte-identical to the commit under check. `qa/` was clean before my
ledger write, so my ledger edit cannot have clobbered a concurrent one.

## 8. Ledger

- `AT-104` open → **fixed** (2026-09-08), verdict referenced.
- `AT-098` open → **fixed** (2026-09-08), verdict referenced.
- `AT-108` **new**, low, open.
- `AT-102`, `AT-103`, `AT-105` stay **open**, correctly, per section 5.
- No matching `.goal` task exists for this unit (the manifest's "Goal task: none" is accurate —
  I checked all 45 tasks), so nothing was closed there.
