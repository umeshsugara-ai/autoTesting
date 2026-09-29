# GATE — a finished, falsified implementation has nowhere legal to live

**Filed:** 2026-09-28 (maker) · **Severity:** high · **Blocks:** AT-710, and the same wall will stop
AT-697 and anything else that adds a check.
**Rule in force:** repo `CLAUDE.md` — file ≤ 300 lines, *"No `*_v2.py` / `*_new.py` — edit in
place"*, one concept one place, enforced by `uv run autotester doctor`. A new module is a human gate.

## The question in one line

`check_decision_citations` is built, validated and falsified, and every file it could live in is
full. Does it get a new module — `src/autotester/ledger/citations.py` — or does something else move
first?

## Why this is a gate and not a judgement call

The design rules exist because `d:/erp` shipped without an upfront schema and became unreadable to
humans and expensive for agents. Those rules are cheap now and unaffordable later, and "just make a
new file" is exactly the erosion they prevent. So a builder does not get to grant itself the
exception — which is why two independent build subagents, on different days, each stopped here
rather than creating the file.

## The measurement, verified by the maker rather than taken on report

| Candidate home | Lines | Headroom | Why not |
|---|---|---|---|
| `src/autotester/ledger/checks.py` | 288 | **12** | The conceptual home — it hosts the closest sibling check |
| `src/autotester/doctor.py` | 279 | **21** | Where the CLI surfaces it |
| `src/autotester/ledger/evidence_specs.py` | 156 | 144 | Room, but thematically wrong — considered and rejected |
| `src/autotester/ledger/render.py` | 300 | **0** | At the cap |
| `tests/test_doctor.py` | 300 | **0** | At the cap |

The implementation is **131 lines plus 110 lines of tests**. It fits none of the available headroom,
and the two files with the most headroom are the two it does not belong in.

## What is actually already built (so the cost of saying no is visible)

- Written against `qa/contracts/living-ledger.md` **L9**, a checker-owned criterion that already
  exists for this exact unit — this is not a speculative feature.
- Validated across the live repo: **643 files, ~1406 `D-NNN` occurrences**, finding **exactly 7 real
  dangling citations**, all `D-056`, in `at654-d029-dev-only-vs-production-pathlynks.md` (:8, :18,
  :63) and `pathlynks-user-account-first.md` (:31, :35, :38, :67) — matching L9's own named fixture.
- All 5 capabilities falsified by breaking the exact production line and confirming the named test
  went red; 9/9 tests green.
- It also found a previously-undocumented case at `write-policy-tier.md:103`.

This is the check that would have caught the D-056 mess **before** seven citations went from
visibly dangling to silently wrong. Nothing on disk checks that a cited decision id resolves.

## The options

- **(A) Authorize `src/autotester/ledger/citations.py`** (plus `tests/test_citations.py`). Precedent
  exists: the `checks.py` / `evidence_specs.py` split under AT-506 is the same shape. Cost: one more
  module, and the rule bends once with a written reason. **Recommended.**
- **(B) Refactor first, then land it in place.** Split `checks.py` or `render.py` to free headroom,
  as its own unit, then add the check with no new concept. Costs a refactor of files that are at or
  near the cap, i.e. the riskiest edit available, before any of the value lands.
- **(C) Raise the 300-line cap.** Cheapest keystroke, worst idea — it weakens the rule everywhere to
  solve one case, and the rule is the thing keeping this repo legible.
- **(D) Don't build it.** Accept that dangling and wrong-subject decision citations stay undetected.
  Honest, and it leaves the known 7 unresolved with nothing to stop the next 7.

My recommendation is **(A)**, and the reason is narrow rather than convenient: the check is a
genuinely distinct concept from what `checks.py` does, so putting it there would violate "one
concept, one place" even if the lines fit. The cap is not the real argument for a new file here —
the concept boundary is. (B) is the defensible answer if you would rather spend the refactor than
the exception.

**Scope note:** answering this authorizes the module for AT-710 only. AT-697 will reach the same
wall separately; if you want a standing rule instead of a per-case gate, say so and it becomes a
DECISIONS entry rather than a repeat of this file.

## Answer

<!-- Append one line when answered:
Answered: <ISO date> — <A|B|C|D> — <where/verbatim> -->

Answered: 2026-09-29 — A — "A: new ledger/citations.py (Recommended)", AT-710 only (standing-rule variant not chosen); Umesh via AskUserQuestion in session autotesting-23, re-confirmed to the maker session; recorded as D-057
