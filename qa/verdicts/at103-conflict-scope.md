# Verdict — at103-conflict-scope

**Date:** 2026-09-08
**Cycle checked:** 1
**Manifest:** `qa/manifests/at103-conflict-scope.md` (Fix cycle: 1 of max 3)
**Contract:** `qa/contracts/explore.md` — **X14** ("sources disagree, not patterns collide") and
**X3** (two SPA states at one URL with different controls are two screens); `core-invariants.md`
C2/C3/C4/C5.
**Unit under check:** commit `ef881b9` — `src/autotester/stages/explore_merge.py` (+37/-3),
`tests/test_explore_merge.py` (+40).
**Bound to:** `d:/autoTesting`. Every path read or written is inside it.
**Mode:** A (unit check). Adapter: `qa/adapter.json`, `kind: shell`.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met, 4/4 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: AT-109 (new, medium) · AT-103 open→fixed
EXPLANATION: The fix works and it is not decorative — I reproduced the predecessor's probe on
BOTH the pre-fix module (extracted with `git show`, never checked out) and HEAD: conflicts went
1 → 0 with screens staying 2, while the one-crawl control stayed 0 in both. All three sabotages
land exactly as the manifest claims, including the one that matters: making `_is_structural`
return True — the lazy "just stop filing conflicts" fix that would also make AT-103's symptom
vanish — fails three tests, so this unit is earning its PASS rather than suppressing a symptom.
The new rule is right on its merits, but it is not free, and the maker did not write the test for
the case that costs: a GENUINE product change at a URL an earlier crawl already claimed is now
silently two screens and no Conflict. That is a real disagreement made unreportable. It is not a
FAIL — the contract's own AT-103 residual paragraph prescribed exactly this widening, nothing is
overwritten or lost, and a Conflict was always the wrong instrument for "this screen went away" —
but it is a hole, so it is filed as AT-109 and written into X14 rather than left implicit.
```

---

## 1. What I re-ran myself (nothing pasted was trusted)

All inside the running container, `docker compose exec -T autotester`:

| Command | My result | Manifest claim | Match |
|---|---|---|---|
| `uv run pytest -q` | **563 PASSED, 1 SKIPPED**, nothing else (counted with `-rA \| awk \| sort \| uniq -c`; `-q` suppresses the summary in this repo) | 563 passed, 1 skipped | ✅ |
| `uv run ruff check src tests scripts` | `All checks passed!` — exit 0 | `All checks passed!` | ✅ |
| `uv run autotester doctor` | `doctor: clean` — exit 0 | `doctor: clean` | ✅ |
| `uv run python scripts/explore_proof.py` | `10/10 invariants held` — exit 0 (real browser; 7 screens, `/students/{id}` collapsed, 6 destructive controls denied, off-domain refused, first-party 404 reported, analytics never reported, unnamed control skipped) | `10/10` | ✅ |

The 563 count is +3 on the 560 I verified at the previous unit, and the commit adds exactly 3
tests. Working-tree note: `git status --porcelain src tests` and `git diff ef881b9 -- src tests
scripts` were both **empty** before I started, so the files I judged are byte-identical to the
commit under check.

## 2. Does the fix actually fix it? — the probe, re-derived on both sides

I did not trust my predecessor's numbers either. I extracted the **pre-fix** module with
`git show a195fbf:src/autotester/stages/explore_merge.py` into `.work/` (no `stash`, no
`checkout`, no `restore` — AT-101 discipline) and loaded it under a separate module name
alongside the real package, so both versions ran against the same schema in the same interpreter.

| Merge shape | pre-fix (`a195fbf`) | HEAD (`ef881b9`) |
|---|---|---|
| SPA pair, **two crawls** (`sig_plain` as crawl_1, then `sig_filters` as crawl_2) | screens=2 **conflicts=1** | screens=2 **conflicts=0** ✅ |
| SPA pair, **one crawl** (control) | screens=2 conflicts=0 | screens=2 conflicts=0 |

`conflicts 1 → 0`, `screens` unchanged at 2, and the intra-crawl behaviour the contract already
upheld is untouched. The defect reproduces on the parent commit and is gone at HEAD — the fix is
real, and it is the fix for *this* defect rather than a coincidence of the suite.

## 3. Sabotage — three, all restored

| Sabotage | Result | What it proves |
|---|---|---|
| **Revert to the crawl-scoped exemption** (drop `or _is_structural(clash)` from `_disagreement`) | `test_spa_states_found_by_two_separate_crawls_still_do_not_conflict` **FAILS** — and only it, in that file | The new test is load-bearing; it fails on exactly the old behaviour |
| **The LAZY fix** — `_is_structural` → `return True`, i.e. never file a conflict at all (which also makes AT-103's symptom vanish) | **THREE FAIL** across the full suite: `test_a_name_clash_on_the_same_url_keeps_both_and_records_a_conflict`, `test_the_same_conflict_is_not_recorded_twice_on_re_merge`, `test_a_human_authored_claim_is_still_contradicted_by_a_crawl` | **This is the one that matters.** A "fix" that suppressed conflicts wholesale does NOT pass this suite, so the unit is not decorative. X14's positive half is defended |
| **Change the pinned prefix** — `content_id("node", …)` → `content_id("scrn", …)` in `schema/screen_graph.py:73` | `test_a_real_screen_node_id_carries_the_structural_prefix` **FAILS** (`'scrn_f8417a9609e9'` does not start with `node_`), and the SPA test fails alongside it | The coupling fails **loudly at its own name**, not silently. A prefix change cannot quietly turn every structural screen back into a conflict — the pin genuinely bites |

Restoration verified after each: `git status --porcelain src tests` empty, `git diff ef881b9 --
src tests scripts` empty. My scratch lived in `.work/checker-at103/` and is deleted.

The prefix pin is well-founded beyond the one test: `content_id` is `<prefix>_<12-char hash>`
(`core/ids.py:35`) and the prefixes are disjoint per type — the crawler is the **only** producer
of `node_` ids (`schema/screen_graph.py:73`), while human/ingested screens are `scr_`
(`stages/ingest.py:31`, `schema/case.py:104`). So `_is_structural` is a genuine
namespace discrimination, not a string coincidence. It is also more robust than the fix direction
AT-103 itself proposed (`source_ref.source_id`), because `Screen.source_ref` is `| None`
(`schema/flowspec.py:96`) while `id` never is.

## 4. Is the new rule right, or merely convenient? — and the case with no test

**Right on its merits, and it is what the contract asked for.** X14's residual paragraph says in
so many words: *"The exemption is right; its scope is one crawl rather than one source."*
`_is_structural` implements exactly "one source" — the crawler as a source class, versus a human's
or an ingested video's claim which asserts a URL and nothing more. X3 requires two states at one
URL with different controls to be two screens; two structural ids at one pattern *are* that, by
construction, however many crawls found them. `_disagreement`'s docstring carries that reasoning
next to the code that implements it, which is the right place for it.

**But I probed the case the maker did not write a test for, and it is a hole.** Genuine product
change: crawl 1 finds `/settings` (`sig_v1`, "Settings"); the product ships a redesign; crawl 2
finds `/settings` (`sig_v2`, "Account settings") and the v1 state no longer exists. Run live:

```
PRODUCT CHANGE screens=2 conflicts=0
    node_1adc40552 'Settings'         /settings  src=source_id='c1'
    node_bc8e052c9 'Account settings' /settings  src=source_id='c2'
review: draft | 1 screen(s) added by crawl c2 — needs review | version 3
```

Two crawls of the same product at different times **are** two sources with distinct `source_id`s,
and their claims genuinely differ. Pre-fix that filed a `Conflict`; now it is silent, and the
FlowSpec keeps a stale screen forever with nothing marking it stale. The human is told only
"1 screen(s) added — needs review", which is byte-identical to what an innocent SPA re-crawl says.
**So yes: a real disagreement has been made unreportable, and I am saying so.**

Why it is nonetheless not a FAIL of this unit, at >80% confidence:

- **The trade is forced, and the maker took the right side.** At the merge layer an SPA re-crawl
  and a product change are *the same shape* — same pattern, different signature, different name,
  different crawls — so no rule here can separate them. Pre-fix fired a false positive on every
  SPA state on every re-crawl (high frequency, pure noise, and it is the intended workflow: the UI
  has an "Explore again" button); post-fix it misses a lower-frequency real change that fails safe.
- **X14's core survives intact.** Its rule is "kept, never resolved". Both screens survive, nothing
  is overwritten, the version bumps and `Review` resets to DRAFT. What is lost is *reporting*, not
  data.
- **A `Conflict` was always the wrong instrument for this.** It would only ever have caught a
  product change that (a) kept the URL and (b) changed the name; a screen that simply vanished, or
  moved, was never reported by it at all. The right instrument is last-seen/staleness on `Screen`
  ("not seen by the latest crawl of this project"), which does not exist anywhere in this repo —
  that is a new mechanism, not a line in `_disagreement`.
- **The contract pre-authorized precisely this widening**, so the unit built what was asked.

Filed as **AT-109 (medium)** and written into X14 as a tracked residual — the same treatment
AT-102/AT-103/AT-105 got — so it cannot quietly become the new normal.

## 5. Contract criteria judged

- **X3** — untouched by this unit and still honoured *by* it: two states at one URL remain TWO
  screens in every probe above (2 in one crawl, 2 across two crawls, 2 on a product change), and
  `explore_proof.py` re-proved the live half (`/students/{id}` collapsed to 1, 7 screens over 6
  patterns). ✅
- **X14** — "a disagreement between SOURCES is kept, never resolved". Kept: every probe keeps both
  screens; nothing is rewritten. Never resolved: the merge still picks no winner. Recorded: a
  human-authored claim IS still contradicted by a crawl
  (`test_a_human_authored_claim_is_still_contradicted_by_a_crawl` passes and fails under the lazy
  sabotage), the name clash still files a `Conflict`, and it is still not recorded twice on
  re-merge. The exception now reads on identity rather than on crawl id, which is what the
  criterion's own residual paragraph prescribed. ✅ — with the scope change and its cost recorded
  in the contract by this check (§7).
- **X13** — unchanged and re-verified: `merge_screens` still never rewrites an existing screen,
  still resets `Review` to DRAFT with a version bump when it adds anything, and still returns the
  spec untouched when it adds nothing (`test_merge_writes_the_screens_into_the_flowspec_and_resets_review`
  and the idempotence test pass; the lazy sabotage did not disturb them). ✅
- **X15** — untouched: `url_pattern` is still the host-less path (`/settings`, `/` and
  `/students/{id}` in my own probes, all leading `/`). ✅
- **X1 / X10** — `explore_merge.py` is not the explorer, but re-checked because the merge changed:
  `grep -n 'fill\|select_option\|upload' src/autotester/stages/explore*.py` returns nothing;
  `run_case` still has one call site, in `_bootstrap_login`. ✅
- **X12** — the merge takes no provider and the proof ran provider-free, 10/10. ✅

**Core invariants (4/4)** — **C2** `doctor: clean`; the manifest's note is accurate and the right
call: extracting `_disagreement` rather than trimming its explanation is how you keep a 50-line cap
from deleting a reason. **C3** `_is_structural`, `_disagreement` and `_STRUCTURAL_ID_PREFIX` are
each defined exactly once, all in `explore_merge.py`; no new module, no `*_v2.py`. **C4** repo root
clean, `.work/` used for my scratch and deleted after. **C5** the merge touches no `SecretStore`
and no `.env`; it moves `Screen`/`Conflict` data only.

## 6. Issues addressed vs the ledger

- **AT-103** — genuinely fixed by this unit, verified against the pre-fix module rather than
  asserted. `open → fixed`.
- **AT-102** and **AT-105** stay **open**, correctly: AT-102 is the same-name silent duplicate,
  which this unit does not touch and does not worsen (`clash.name == incoming.name` still
  short-circuits first); AT-105 is the crawl page's missing noise counts, untouched. **AT-108**
  (`return_to` swallows its cause) stays open — the manifest's plan to fix it as a sweep of every
  `except` in `stages/explore*.py` rather than another one-line patch is the better call, and I
  am recording it as an intention, not crediting it.
- **AT-109** — new, medium, filed by this check (§4).

## 7. Contract amendment made by this check (routine)

`qa/contracts/explore.md` X14: the deliberate exception now reads on **structural identity**
rather than on "the same crawl", its residual list drops AT-103 (closed) and gains **AT-109**, and
the amendment log records the change with its cost. This is routine, not a softening decided to
pass a failing artifact: the criterion's own residual paragraph, written on 2026-09-08 before this
unit existed, prescribed the widening. Criteria are added and recorded; none is removed.

## 8. Working-tree hygiene (AT-101 discipline)

No `git stash`, no `git checkout`, no `git restore`. History was read with `git show <commit>:<path>`
into `.work/checker-at103/` (gitignored). Each sabotage was: copy the file into `.work/` → patch in
place → run → copy the backup back. After the last restore, `git status --porcelain src tests
scripts` is **empty** and `git diff ef881b9 -- src tests scripts` is **empty**; the scratch
directory is deleted.

## 9. Ledger + goal

- `AT-103` open → **fixed** (2026-09-08), this verdict referenced.
- `AT-109` **new**, medium, open.
- `AT-102`, `AT-105`, `AT-108` stay **open**, correctly.
- `.goal/goal.json` has no task matching this unit (`grep -ci at103|conflict-scope` → 0), so the
  manifest's "Goal task: none" is accurate and nothing was closed there.
