# Verdict — at147-at148-grant-boundary

**Cycle checked: 1** · **Date:** 2026-09-08 · **Checker:** /checker Mode A, bound to `D:/autoTesting`
**Manifest:** `qa/manifests/at147-at148-grant-boundary.md` (commit `4164547`, HEAD `0bed142`)
**Contract:** `qa/contracts/consent.md` CN4–CN7 · **Adapter:** `qa/adapter.json` (coding)

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 9/9 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-149 (medium), AT-150 (low) — both fresh findings on new code, neither a
  criterion failure. AT-147 and AT-148 flipped open → verified.
```

## What I re-ran myself (nothing below is the maker's pasted output)

| Command | My result | Manifest claimed |
|---|---|---|
| `uv run pytest` | **641 passed, 2 skipped** in 68.88s | 641 / 2 ✔ |
| `uv run ruff check src tests scripts` | `All checks passed!` exit 0 | clean ✔ |
| `uv run autotester doctor` | `doctor: clean` exit 0 | clean ✔ |

Docker down, `uv` native, bare `pytest` as instructed.

## AT-147 — re-probed through the real CLI, not the test suite

Fresh `AUTOTESTER_ROOT` scratch project, `base_url=https://demo.test/app`:

| `--expires` | exit | message |
|---|---|---|
| `2026-09-07` (yesterday) | **1** | "is already in the past" |
| `2026-09-08` (**today**) | **1** | "is today — consent expires at the START of the named day, so a run today needs tomorrow's date" |
| `2026-09-09` (tomorrow) | 0 | granted |
| `2026-09-10` (+2) | 0 | granted |
| `2030-01-01` (far) | 0 | granted |
| `notadate` | 1 | "must be YYYY-MM-DD" |

The AT-147 defect is gone: the exact date an operator granting same-day production consent for
T-145 would type is now refused at the grant instead of being granted and then refused at the run.

**The deeper property, probed independently of the maker's test.** I loaded every approval the
CLI accepted above and asked the real `RunApproval.is_expired(datetime.now())`: all three
`False`. So every expiry `approve` accepts is one `require_consent` honours — the rule holds, not
just the two comparisons.

**Boundaries I attacked, beyond the ones the manifest names:**

- **Midnight.** Expiry `2026-09-09`, evaluated at `2026-09-08 23:59:59` → not expired;
  `2026-09-09 00:00:00` → not expired; `00:00:01` → expired. The boundary is exact and the
  comparison is `>` not `>=`, so the instant of midnight is still honoured. No off-by-one left.
- **Timezone.** `_validate_grant` uses `date.today()` (naive local) and `consent.require_approval`
  defaults to `datetime.now()` (naive local) — the **same clock**, so they cannot disagree by a
  UTC offset. `explore.py` uses `datetime.now(UTC)` only for *stamping* artifacts, never for the
  expiry comparison. Checked at `src/autotester/core/consent.py:99`.
- **A tz-aware `expires_at`.** `is_expired` strips `tzinfo` when `now` is naive, comparing wall
  clocks rather than instants — off by the offset if the row ever carried a foreign zone. It
  **cannot be reached**: `approve` refuses anything that is not bare `YYYY-MM-DD`, and a
  hand-written tz-aware row fails `is_intact` (I confirmed: `intact=False`). Only a forger who
  recomputes the id could get there, which is the documented, contract-recorded AT-110 boundary.
  Not a finding.

## AT-148 — re-probed, then attacked much harder

`base_url = https://demo.test/`. Warned (correct) unless noted:

| target | result | right? |
|---|---|---|
| `https://demo.test/` | silent | ✔ exact base |
| `https://demo.test/admin/users` | silent | ✔ genuine sub-path, no wolf-crying |
| `https://demo.test.evil.com/` | **WARN** | ✔ **the AT-148 case, now caught** |
| `https://demo.test-evil.com/` | WARN | ✔ |
| `http://demo.test/` | WARN | ✔ scheme differs → CN5 exact match would refuse it |
| `https://demo.test:8443/` | WARN | ✔ netloc differs → a different target |
| `https://demo.test./` | WARN | ✔ trailing-dot host is a different string to CN5 |
| `https://DEMO.TEST/` | WARN | ✔ CN5 says host case is a deliberately different target |
| `https://demo.test@evil.com/` | WARN | ✔ **userinfo trap: the real host is evil.com** |
| `` (empty) | WARN | ✔ |
| `not a url` | WARN | ✔ |
| `//demo.test/x` | WARN | ✔ no scheme |
| `https://evil.com/https://demo.test/` | WARN | ✔ |

Every one of these is *correctly* warned, and for the right reason: the warning's promise is "a
crawl of this will not match this approval", and CN5 matches the target string EXACTLY, so each
of the port / scheme / case / trailing-dot / userinfo variants genuinely is a different target.
The warning and CN5 now say the same thing, which is the whole point.

**But I found the same defect one line below the fix — filed as AT-149 (medium).** The maker
fixed the host half and left the path half naive. With `base_url = https://demo.test/app`:

```
https://demo.test/app              silent   (correct)
https://demo.test/app/users        silent   (correct)
https://demo.test/apple-secrets    silent   <-- WRONG: not under /app
https://demo.test/appliance/admin  silent   <-- WRONG: not under /app
https://demo.test/other            WARN     (correct)
```

`base.path.startswith(want.path.rstrip("/"))` at `cli_crawl.py:187` is AT-148's bare-prefix bug in
the path component. Bounded identically to AT-148 — CN5 is exact at run time, so no approval
widens and nothing unsafe runs — so it is a **fresh finding on new code, not an unmet criterion**,
and it does not block this PASS. It is the same class the unit was filed to kill, which is why it
is medium rather than low.

**AT-150 (low):** the refusal says the operator needs "tomorrow's date" but never prints
`2026-09-09`. The manifest claims the refusal "names the date to use instead"; it names the
*word*. The unit's own test asserts only `"tomorrow" in result.output`, so the word passes it.
CN6 already demands that a refusal leave the operator able to proceed; this is that principle one
level up, and it is one `timedelta` away.

## Sabotages Q and R — reproduced, not read

Per AT-101: `git archive HEAD` into a scratch tree, repo `.venv` interpreter, live tree untouched
(no `stash` / `checkout` / `restore`).

```
BASELINE  tests/test_approve_cli.py                     11 passed
SABOTAGE Q  `<=` reverted to `<`                        1 failed, 10 passed
            FAILED test_approve_refuses_an_expiry_of_today
SABOTAGE R  back to target.startswith(base_url)         1 failed, 10 passed
            FAILED test_a_lookalike_host_is_flagged_not_silently_accepted
```

Both counts confirmed at **exactly 1**, on the named test, as claimed. Each sabotage is caught by
the test written for it and by nothing else — the tests are load-bearing, not decorative.

I also read the property test rather than trusting its name: it drives the **real CLI grant** and
then calls the **real `require_consent`**, so it cannot pass by asserting on its own fixture.

## The file split — audited, nothing lost

`tests/test_crawl_real_cli.py` at `4164547^` vs the pair after:

- Test names: **14 before → 18 after**, `comm` shows **zero lost**, four added (the four new tests).
- Bodies: I AST-parsed both sides and compared every function body. **17 of 17 identical**
  (14 tests + 3 helpers). Nothing was renamed away, trimmed, or silently weakened in the move.
- The stated reason for the split — deny half vs grant half — is borne out by the contents.

## Adversarial: can an approval be written that bypasses `_validate_grant`?

Traced every caller of `store.add_approval` in the repo:

- `src/autotester/cli_crawl.py:231` — the **only** production path, and `_validate_grant` runs on
  line 230, immediately before it. Covered.
- `scripts/explore_proof.py:71`, `tests/crawl_fake.py:153`, `tests/test_consent.py:149`,
  `tests/test_explore_live.py:50` — proof/test fixtures constructing state, not operator grants.
  CN9 requires exactly this (tests grant a real approval rather than bypassing the gate).

**On the UI grant surface named in the dispatch: there is none.** I enumerated every `POST` route
in `src/autotester/ui/` — onboard, cases, explore, merge, env, edit, secrets, run, providers. None
creates a `RunApproval`; `add_approval` and `RunApproval` appear nowhere in `src/autotester/ui/`.
The consent contract's "Out of scope" says so explicitly ("A UI grant form. CLI only"). So this
fix covers **100% of the shipped grant surface**, not merely the CLI half of two. If a UI grant
form is ever built, `_validate_grant` is the function it must call — worth stating here because
the seam-vs-caller lesson of CN2 applies to the grant exactly as it does to the run.

## Ruling on the design question the manifest put to me

**Should `is_expired` treat the named day as INCLUSIVE (end of day)?**

**The maker's refusal is SOUND, not over-cautious, and I uphold it.** The reasoning it gave is
precisely the criticality gate in my own skill: adopting end-of-day would lengthen **every
`RunApproval` already on disk by up to 24 hours**, retroactively, with nobody re-consenting. That
is "weakening a safety invariant" and "widening a boundary" in one move, on the gate standing in
front of a live production ERP. A maker that had quietly made that change on its own judgement
would be a **more serious finding than either defect this unit fixed**. Refusing to widen a
security boundary and escalating instead is the behaviour I want, and the manifest escalated it in
the right direction — to the contract's owner, with the alternative fully argued rather than
buried.

**Do I prefer end-of-day? On the merits, yes — but I may not adopt it either.** "Expires on the
9th" means *through* the 9th to every human who has read a passport or a coupon, and start-of-day
leaves a live sharp edge the maker did not name: **a grant issued at 23:50 with `--expires
<tomorrow>` is accepted with a green line and is dead ten minutes later.** That is AT-147's shape
again, narrower, and no current test would catch it. But my own rule is that a CRITICAL amendment
goes to the human and is decided away from a pending verdict — so I have not decided it, and this
PASS does not depend on it.

**What I did instead, all within the routine gate:**

1. **Amended CN4 (tightening, auto-applied)** to record the measured semantics — a bare date means
   the START of the named day — and to promote the maker's rule to a criterion in its own right:
   *every expiry `approve` accepts must be one `require_consent` honours*, and a refusal at the
   grant must name what to type instead. AT-145 and AT-147 were one defect twice; writing the
   property into the contract is what stops a third.
2. **Raised `qa/gates/at147-expiry-end-of-day.md`** as a HUMAN_GATE for Umesh with three options.
   My recommendation there is **(C)**: store new grants as an explicit `<date>T23:59:59` timestamp
   at grant time and leave bare-date rows reading as midnight. That buys the intuitive meaning
   with **zero retroactive widening** — it is the option neither the maker nor the binary framing
   of the question considered, and it costs one line in `approve_cmd`.
3. Recorded that if Umesh picks end-of-day, the conservative refusal is **REPLACED, not layered
   on**, exactly as the maker asked.

## Criteria

| | Judgement |
|---|---|
| **CN4** (consent never open-ended; grant↔runtime agree) | **MET** — probed across yesterday/today/tomorrow/+2/far/garbage plus the midnight boundary to the second; the two comparisons agree on every expiry the CLI accepts. |
| **CN5** (approval does not transfer; exactness) | **MET / untouched** — the warning now agrees with CN5's exactness on all 13 variants I probed, including the userinfo and trailing-dot traps. No matching logic was changed. |
| **CN6** (bounds checked; refusals teach) | **MET** — the grant refusal now teaches instead of merely stopping; AT-150 is the residual (it teaches in words, not in a date). |
| **CN7** (adversarial/production) | **MET / untouched** — no change to the production field or its handling. |
| Invariants | 9/9 — full suite green, ruff clean, doctor clean, no file over 300 lines, CN9's unconditional gate intact, no production write, live tree never stashed. |

**Both AT-147 and AT-148 as filed are fixed, evidenced by my own probes and by sabotage.** Ledger
rows flipped `open → verified`.
