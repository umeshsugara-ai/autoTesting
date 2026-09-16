# HUMAN_GATE — live-crawl-target: which real, post-login product may AutoTester crawl end to end?

**Opened:** 2026-09-16 by `/checker` (Mode B sweep #6) · **Status: OPEN** · **Approver:** Umesh
**Blocks:** the live acceptance run of `explore.md` X17/X18 and `coverage.md` V7 (the fixture proves
the mechanism; only a real product proves "the whole product is mapped"). Does NOT block building
X17/X18/V7 against local fixtures.
**Evidence:** `qa/feedback-inbox.md` 2026-09-16T22:25+05:30 · every crawl on disk stopped at or before
login (saucedemo 1 screen / 0 actions, checkerdemo ×2 the same, pathlynks `login_failed` 0 screens).
**Related, not duplicated:** `erp-credentials.md` (ERP test account, still OPEN) · `at110-approval-forgery.md`.

## The question, in one line
Which target should the first live post-login end-to-end crawl run against, under which
`write_policy`, and with which credentials?

## Why it matters
The contracts can require that a crawl passes login and reports coverage, but "each possible route"
is only measurable on a real product with a real login. The checker will not choose a target,
a credential, or a write policy — each is outward-facing.

## Options (the checker does not recommend a credential; it lists what is decidable)
- **(a)** A public practice site that publishes its own demo login (e.g. `saucedemo.com`, whose login
  page lists demo usernames and a shared password). `projects/saucedemo/` already exists (untracked).
  Needs: your OK to use the published demo login as a `SecretRef` in that project's `.env`, the
  `allowed_domains`, and a `write_policy` (`READ_ONLY` maps navigation only; `TEST_ACCOUNT` lets it
  submit forms such as add-to-cart/checkout on a site built for that).
- **(b)** Pathlynks with a dedicated test account (the existing `pathlynks` project; its last crawl
  was `login_failed`). Needs a test account and per-run approval — never a live user's credentials.
- **(c)** The ERP, once `erp-credentials.md` is answered.
- **(d)** Fixtures only for now; no live target.

Also answer: the bounds for that run (defaults 30 screens / 200 actions / 600 s), or "defaults".

## How to answer
Reply in chat, e.g. `live-crawl a TEST_ACCOUNT defaults`, or `live-crawl d`. The maker appends
`Answered: <ISO> — <choice> — <where>` below before acting.

Answered: (pending)
