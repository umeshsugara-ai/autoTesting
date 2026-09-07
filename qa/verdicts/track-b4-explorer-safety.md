# Verdict — track-b4-explorer-safety

**Manifest:** qa/manifests/track-b4-explorer-safety.md
**Contract:** qa/contracts/core-invariants.md (C1, C2, C3)
**Goal task:** T-142
**Cycle checked: 2**

## Verdict: PASS

## What I verified myself (fresh context, re-run not re-read)

### 0. Staleness + bind-mount guard

Container `autotesting-autotester-1` started `2026-09-07T16:32:26.88Z`. Newest source mtime in
the touched files (`tests/test_explore_safety.py`) is `2026-09-07T16:33:20Z` — nominally after
container start. `docker-compose.yml` mounts `D:\autoTesting` → `/app` as a live bind mount (not
a baked image), so the running container reads the current filesystem on every invocation; the
mtime ordering has no staleness implication here. Confirmed by re-running every check live
against the current tree, not trusting any pasted output.

### 1. AT-092 reproduced against the fix — genuinely closed

Cycle 1's crashed checker found: `policy_for(project, never_click_patterns=[])` produced a
`SafetyPolicy` under which `deny_reason` let a "Log out" control through, contradicting the
original manifest's claim that no policy setting could do this.

I reproduced the exact probe myself inside `docker compose exec autotester`:

```
policy = policy_for(p, never_click_patterns=[])
el = ElementRef(role='button', name='Log out', selector='#x')
deny_reason(el, policy) -> "never-click pattern (logout/sign-out)"
```

Not `None`. The fix holds: `deny_reason` (`src/autotester/stages/explore_safety.py:38-64`)
checks the module-level `DEFAULT_NEVER_CLICK_PATTERNS` tuple (imported directly from
`schema/crawl.py`) unconditionally, in an `or` with `policy.never_click_patterns` — the baseline
does not depend on the policy object at all.

### 2. My own adversarial bypass attempt via SafetyPolicy construction — failed to find one

Per the dispatch, I did not just re-run the maker's own tests. I read `deny_reason`'s full
source and tried to construct a `SafetyPolicy` a different way than `policy_for` uses, to see if
the guard could still be disarmed:

```
sp = SafetyPolicy(write_policy=WritePolicy.ALLOW_WRITES, never_click_patterns=[])
deny_reason(el, sp) -> "never-click pattern (logout/sign-out)"
```

Still denied. Because the check reads `DEFAULT_NEVER_CLICK_PATTERNS` from the module, not from
any field on the policy instance, there is no construction path — `policy_for(**overrides)` or
`SafetyPolicy(...)` directly — that can remove the baseline. Only editing
`DEFAULT_NEVER_CLICK_PATTERNS` itself (a code change, exactly as the manifest claims) would. I
could not find a bypass.

### 3. Widening still works — the extension point is not removed

```
sp2 = policy_for(p, never_click_patterns=['\bfoo-custom-logout\b'])
deny_reason(ElementRef(name='Foo Custom Logout', ...), sp2) -> "never-click pattern (logout/sign-out)"
```

A project-supplied pattern not present in the default set still denies. The fix removes only the
ability to narrow the baseline below the hardcoded floor, not the ability to add to it — matches
the manifest's stated design intent exactly.

### 4. My own adversarial control names beyond the maker's list — found a genuine new gap

I tried names the maker's cycle-1 re-probe didn't cover, focused on punctuation separators
instead of word gaps:

| name | denied? | expected |
|---|---|---|
| `Log-Out` | **not denied** | should be denied |
| `Sign-Out` | **not denied** | should be denied |
| `LOG_OUT` | **not denied** | should be denied |
| `Log.Out` | **not denied** | should be denied |
| `Logout Now` | denied | correct |
| `Please Log Out` | denied | correct |
| `sign  out please` | denied | correct |
| `checkout` | not denied | correct (no false positive) |
| `workout tracker` | not denied | correct (no false positive) |
| `about us` | not denied | correct (no false positive) |
| `output settings` | not denied | correct (no false positive) |

`DEFAULT_NEVER_CLICK_PATTERNS` uses `[\s\w]{0,10}` (word gap) or a literal `" ?"` (single
optional space) between the two halves — neither class matches `-`, `_`, or `.`. A real button
labelled `Log-Out` or `LOG_OUT` (plausible: kebab-case design-system captions, or CSS
`text-transform` over a snake_case id) walks straight through the "never disarmable" guard via a
punctuation variant, not via policy manipulation. This is a genuine false negative in the
baseline pattern itself, distinct from AT-092 (which was about disarming via configuration) —
AT-092's fix is unaffected and correct. I found no false positives in either the maker's original
adversarial set or my own additions; word-boundary discipline holds. Filed as **AT-093**
(medium — plausible in real UIs, not yet exploitable since T-143's crawler doesn't exist).

This does not fail C1–C3 (it's a functional-safety gap, not a schema/readability/anti-drift
violation), consistent with how AT-092 itself was logged despite the same scoping note, and
consistent with the manifest's own stated "documented limit" framing — but it is a real gap
beyond what was tested, worth closing before T-143 wires a live crawl through this guard.

### 5. AT-092 status in qa/issues.jsonl — genuinely "fixed", now moved to "verified"

The ledger entry said `status: "fixed"`, `verified_date: null` — accurate, not overclaimed (the
maker never claimed more than "fixed", and correctly left verification to the checker). I
appended my verification evidence to the entry and flipped it to `status: "verified"`,
`verified_date: "2026-09-07"`. Also appended a new entry **AT-093** for the punctuation-gap
finding above (§4), `status: "open"`. Ran a JSONL well-formedness check over the whole file after
editing — every line parses.

### 6. Standard verify — all green, re-run live

```
docker compose exec autotester uv run pytest tests/test_explore_safety.py   -> 38 passed in 1.44s
docker compose exec autotester uv run pytest -q                             -> 472 passed, 1 skipped, 1 warning
docker compose exec autotester uv run ruff check src tests scripts          -> All checks passed!
docker compose exec autotester uv run autotester doctor                     -> doctor: clean
```

All match the manifest's claimed expected output exactly (38 = 27 original + 11 from the cycle-1
fix; 472/1 up from 434 after T-141).

## Scoreboard

SCOREBOARD: 3/3 criteria met (C1, C2, C3), 0 invariant violations
FAILURES: none
ISSUES-WRITTEN: AT-093 (new, open, medium) · AT-092 (updated fixed → verified)

## Push / commit state

`git log origin/master..HEAD` and `git log HEAD..origin/master` both empty before this verdict —
`cf684b9` (the AT-092 fix) and `d7e176d` (ledger status update) are both already on
`origin/master`. The only uncommitted changes in the working tree (`.goal/dashboard.html`,
`.goal/goal.json`) predate this unit and are outside this manifest's scope — left untouched.

## EXPLANATION

The AT-092 fix is real and complete for the reported defect: I reproduced the original crash-time
probe, tried my own independent bypass via direct `SafetyPolicy` construction, and confirmed
widening still works — no configuration path disarms the baseline. Cycle 2's own second fix (the
`Log me out` word-gap widening) also holds under my adversarial re-probing with no new false
positives. I did find one new genuine gap that the maker's testing didn't cover — exactly what the checker's
job of independent adversarial probing exists to catch (AT-093, punctuation-separated logout
labels) — but it doesn't
implicate the C1–C3 contract this unit is judged against, so the unit PASSes with AT-093 filed
for a future cycle (T-143 or a small follow-up).
