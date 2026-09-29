# Contract — permission-surface (what can this account actually DO, and was it all tried?)

**Status:** **DRAFT** (authored by /checker 2026-09-28 under **D-054**, `Approved-by: Umesh`).
Goes **ACTIVE** on T-171's first checker PASS, the same way every prior contract batch landed.
**Feature:** T-171 — exercise every reachable control the supplied account is entitled to use, under
`write_policy` + a valid `RunApproval`, and account for the ones it did not.
**Code:** does not exist yet (T-171 `pending`, depends on T-165).
**Tests:** none yet.
**Grounding:** D-040 (which names PS1 and PS2 verbatim) · AT-638 (this capability had zero checkable
criteria) · `coverage.md` V7 · `consent.md` CN1/CN9 · D-016 (deny-list contents) · D-018 and
`qa/gates/write-policy-tier.md` (the tier is Umesh's switch, already thrown).

## Why it exists

A tester that will not press the button cannot report what the button does. The whole point of
T-171 is to convert "the account has these rights" into "these rights were exercised, and here is
what happened" — and, for anything not exercised, a **named reason** rather than silence. The
failure this contract refuses is an incomplete report that reads like a clean one (intent O4).

**The boundary is the supplied account's own permissions and that is Umesh's to set** — see
`qa/gates/write-policy-tier.md`, answered and re-confirmed. This contract does not narrow it, and a
unit judged against these criteria must not either.

## Criteria

### PS1 — Every reachable control is exercised, or blocked with a reason [D-040 verbatim]

Under a `write_policy` permitting action plus a valid `RunApproval`, every reachable control ends up
either exercised or carrying a named reason from `coverage.md` V7(b)'s **closed** reason set.

T-171 **calls through `consent.md`'s existing gate** — CN1 (nothing outward-facing starts without an
approval) and CN9 (the gate is unconditional). It does not build a second approval mechanism. This
is the same shape `adversarial.md` AD1/AD2 already use: extend the existing gate, never parallel it.

**Verify:** a fixture role with N reachable non-destructive controls, exercised under a granted
approval → all N are exercised or reason-tagged. A run with **no** approval, or an expired one,
touches zero controls and is CN1-shaped: no run directory, no navigation.

### PS2 — Destructive actions are ordered last [D-040 verbatim]

Every destructive action's position in the exercise sequence is after every non-destructive one.

**This criterion is `[D-040 verbatim]` and is not arguable** (carried into D-054 for whoever authors
this file). A unit may not re-scope or soften it; changing it needs a superseding decision.

**Verify:** a fixture mixing deny-list-shaped destructive controls (D-016) with non-destructive ones
→ assert the ordering. This is a C7-class guard, so it needs its own **failing-first** sabotage:
reordering the sequence must be shown to fail a named assertion, not merely to look different.

### PS3 — A blocked control never counts as covered — and the counting stays in `coverage.md` V7

`coverage.md` V7(a)–(c) already owns the arithmetic: `controls_discovered`, `controls_exercised`,
reason-tallied gaps, and the book-balance
`controls_exercised + sum(unreached by reason) == controls_discovered`.

**T-171's obligation is to supply the exercise pass V7 counts over, not to count.** Under an
action-permitting tier with approval, a control landing in `policy:<rule>` must be **genuinely**
deny-listed or off-domain — never merely un-attempted.

This is deliberately *not* written as a new V7 clause. Restating the mechanism here would give one
concept two ground truths in two contracts, which is the mistake `ai-target.md`'s checker corrected
on the AI3/AI4 filing. **One concept, one place** (C3).

**Verify:** a fixture with a reachable, non-deny-listed control left unexercised under an
action-permitting tier with approval and no bound / off-domain / login-wall reason → V7(c)'s
book-balance test **fails**.

### PS4 — No second, disagreeing coverage number [hardening, not from D-040's text]

If T-171 ships any report surface of its own beyond the existing V7 surfaces (crawl page, workbook,
`crawl.json`, CLI), that surface must not compute an independent coverage percentage that could
disagree with V7's book-balanced figure.

**This criterion is offered pre-emptively and is explicitly droppable.** T-171 does not exist yet.
If it adds no new surface, PS4 is **vacuously satisfied and must be recorded as such** in the unit's
verdict — stated, never silently dropped.

**Verify:** no second coverage-percentage computation exists outside `coverage.py`'s V7 arithmetic.
If no new surface exists, say so explicitly.

## No-fire list

- Building T-171 itself.
- The concrete deny-list contents — D-016's territory, `schema/crawl.py`.
- A UI page for permission-surface results — not asked for by D-040.
- T-165's traversal mechanics — `crawl-traversal.md`'s job, per its own no-fire list.
- Re-litigating the write-policy tier. It is decided (`qa/gates/write-policy-tier.md`); a unit
  reports what a run actually did.

## Amendment log (append-only; git history is the version)

- 2026-09-28 · init · authored by /checker under D-054 from the criteria filed in
  `qa/feedback-inbox.md` (2026-09-27, `at638-remainder`), which a prior checker judged sound and
  buildable as worded. Cause: AT-638 — T-171 had **zero** checkable contract criteria, so the pair
  could not build it at all. D-054's carried caveat is honoured: PS2 is marked `[D-040 verbatim]`
  and not arguable. DRAFT until T-171's first PASS. **Changes-authorized:** this file (named by
  D-054). No enforcement-path file touched. **Links:** AT-638; D-040; D-054; T-171.
