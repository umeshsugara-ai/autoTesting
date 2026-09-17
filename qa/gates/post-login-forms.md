# HUMAN_GATE — post-login-forms: may the crawler fill forms after login?

**Opened:** 2026-09-17 by `/checker` (Mode B sweep, 10:10 IST) · **Status: OPEN** · **Approver:** Umesh
**Blocks:** any unit that makes the explorer type, select or upload after login (post-login forms,
multi-step flows such as checkout or "create X"). Does NOT block X17/X18/V7, AT-463, AT-467/AT-474,
or mapping every post-login screen reachable by clicks.
**Evidence:** `qa/feedback-inbox.md` 2026-09-16T22:25 fold note: "Not folded: relaxing READ_ONLY after
login (CRITICAL, D-016)". No gate file carried that decision until now, so it lived only in a fold note.

## The question, in one line
Should the explorer be allowed to invent form VALUES after login, and if so under which
`write_policy`, with what data, and against which target?

## Why it is a human decision
- `qa/contracts/explore.md` **X10** ("Nothing is typed": never `fill`, `select_option`, `upload`) and
  **X5** / **D-016** (typing = never, at every policy, including `ALLOW_WRITES`) forbid it outright.
- Changing it weakens a safety invariant, and it becomes outward-facing on any live target. That makes
  it a CRITICAL amendment. The checker will not make it.
- Without it, "each possible route" stays limited to click-reachable screens. Any screen that sits
  behind a submitted form (search results, a created record, the next wizard step) is listed as a V7
  hole. It is never reached.

## Options (listed, not recommended)
- **(a)** Keep X10. Post-login forms are exercised only by human-authored or video-derived cases
  (`run_case`), never by the crawler. V7 lists form-gated screens as holes with reason `policy`.
- **(b)** Allow typing of SYNTHETIC values (a fixed, non-PII generator) under `TEST_ACCOUNT` and
  `ALLOW_WRITES` only, on local fixtures first. A live target still needs `live-crawl-target.md`
  answered. Amends X10, the X5 matrix and D-016 through a new DECISIONS entry.
- **(c)** Like (b), but search/filter forms only (no create/update submits) under `READ_ONLY`.
- **(d)** Defer until the live-crawl-target run shows how many holes are form-gated.

## How to answer
Reply in chat, e.g. `post-login-forms b` or `post-login-forms d`. The maker appends
`Answered: <ISO> — <choice> — <where>` below before acting. Then a DECISIONS entry supersedes the
D-016 typing column, and the checker amends X10/X5 as a critical amendment.

Answered: (pending)
