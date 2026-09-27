# GATE ANSWERED — write_policy tier for live runs

**Asked by:** checker session (Mode B), 2026-09-27
**Answered by:** Umesh, 2026-09-27. Asked once; this file is the record so it is never asked again.
**Authority:** D-018 (`docs/DECISIONS.md:225`) — *"write_policy is enforced ... as an INNER guard inside
Umesh's outer boundary (the test account's own permissions) ... **ALLOW_WRITES is Umesh's switch.**"*
This file records the switch being thrown. It does not create a new policy.

## The question

Which of the three declared tiers applies to live runs, and on which targets?
`READ_ONLY` (deny-list on, no submits, no typing) · `TEST_ACCOUNT` (deny-list on, submits + typing)
· `ALLOW_WRITES` (deny-list **off**, submits + typing).

## The answer

**`ALLOW_WRITES`, on every target, production included.**

Umesh's standing position, consistent across four records and unchanged:

- `qa/gates/at052-bfs-video-corpus-grill.md:43` — *"this will all dependent on the account of which
  credentials provided. jo jo uss account mai access hoga vo krr lengee"*
- `docs/DECISIONS.md:860` — *"jo account mai dunga usme jitni permission hogi utni tho testing ho hi
  jaani chaiyee"*
- `qa/gates/at110-approval-forgery.md:38` — the real boundary is the test account's own permissions
  plus the per-run approval
- 2026-09-27, this gate — *"jis acccount k credentials diyee hongee usko jo jo right honge vo sabb
  action test aand validate krr skta hai"* and *"production prr bhi agar jo user creditials diya hai
  agar uss user ko koi write krna allos hai tho write krr skta hai"*

**The boundary is the account's own permissions.** Whatever the supplied test account is entitled to
do, AutoTester may do and validate.

## Asked with the consequences stated, and reaffirmed

The checker put the specific consequences to Umesh in the question itself before he chose, naming
that at `ALLOW_WRITES` the 19-term deny-list goes off, so on production the crawler may click
`Delete` on a real record, `Send` (a real email to a real person), and `Pay` (real money) — and that
an account having the *right* to do something is not the same as the action being reversible. He
chose `ALLOW_WRITES` everywhere with that in front of him. **It is his decision, recorded, not
re-litigated.** A future session must not reopen this gate; it may only report what a run actually did.

## What this does NOT waive — unchanged, and NOT part of the answer

1. **Per-run approval still applies.** D-018 gate 2 governs every outward-facing run. The maker's
   D-052 states it directly: *consent gate 2 existing is not permission to use it.* This gate sets
   the ceiling; each run still needs its own `RunApproval` naming target and scope.
2. **Logout/sign-out is never clicked at any tier** — `DEFAULT_NEVER_CLICK_PATTERNS`,
   `schema/crawl.py:41`. Not a policy setting.
3. **Real user accounts are never used** — test accounts only (D-018; test accounts carry no 2FA,
   Umesh 2026-09-07).
4. **`T-154`/`T-155` stay held** — see below. `ALLOW_WRITES` plus adversarial is not authorized.
5. **The tier is still a per-project config value.** The checker does not flip
   `projects/*/project.json`; that is the maker's surface and needs its own DECISIONS entry.

## Residual the checker is obliged to record (not a re-ask)

Two deny-list terms are outward-facing to **third parties**, which differs in kind from mutating the
product's own data: `send` reaches a real person's inbox and `pay` moves real money. Neither is
undone by any write policy, a per-run approval, or a rollback. This is recorded so that if it ever
happens it was foreseen and authorized, not discovered. The mitigation available without changing
the tier is the per-run `RunApproval` scope (point 1) — a run may be approved with a narrower scope
than the tier permits.

## T-154 / T-155 (adversarial pass + its report)

**HELD.** Umesh 2026-09-27: *"Pehle proof run ho, phir kholenge"* — the T-169 proof run happens
first, he reviews the comparison, and only then is the adversarial pass opened. This gives the
open-ended morning hold a condition. Track C builds through C3 only.

## Links

`AT-651` (prepod has no environment of its own; the `_host_matches` suffix match makes production
secrets fill-eligible on `dev-new.vidysea.com`) · `AT-281` (T-169 acceptance) · `AT-653` (ground-truth
ordering) · `T-145` · `T-171` (permission surface — the tier is what makes it reachable) · D-018 · D-052
