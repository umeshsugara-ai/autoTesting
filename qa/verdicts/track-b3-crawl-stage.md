# Verdict — track-b3-crawl-stage

**Manifest:** qa/manifests/track-b3-crawl-stage.md
**Contract:** qa/contracts/explore.md (**authored by this check** — X1-X12), plus
qa/contracts/core-invariants.md (C1, C2, C3, C6), qa/contracts/browser-and-secrets.md (B5-B9),
qa/contracts/execute.md E5 (must be untouched)
**Goal task:** T-143
**Cycle checked: 1**

## Verdict: PASS

## Contract authored

`qa/contracts/explore.md` did not exist; this unit requested it. I wrote it from the maker's
filed X1-X11 (`qa/feedback-inbox.md`, 2026-09-07), treating that list as a starting point, not a
specification. Three substantive changes:

- **Added X12** — the crawl is DOM-driven and deterministic; a model never chooses an action and
  may only *name* an already-discovered screen. The maker's list omitted this, yet D-015 both
  authorizes "explore.md **X1-X12**" and rejects vision-guided crawling by name. Restoring it
  makes the contract match the count its own authorizing decision states, and pins the property
  that lets this entire stage be proven without a credential or an API key.
- **Tightened X6** — records the live-verified name-based limitation (accepted per D-016, not a
  defect) AND records AT-093 as an **open gap against the criterion**, so X6 does not read clean
  when it is not.
- **Tightened X11** — bounds the crash guarantee to what the write ordering actually supports
  (see §9 below), rather than the manifest's unqualified "a crash mid-crawl leaves a loadable
  partial graph".

## What I verified myself (fresh context, re-run not re-read)

### 0. Staleness + bind-mount guard

Container `autotesting-autotester-1` started `2026-09-07T17:24:44Z`; the newest `src/**.py` mtime
(`explore.py`, `explore_node.py`) is later. That ordering is meaningless here and I did not rely
on it: `docker-compose.yml` mounts `.:/app` as a live bind mount, so the container reads the
current tree. I confirmed identity directly instead — `md5sum` of `explore.py`, `explore_node.py`
and `crawl_store.py` is byte-identical on host and inside the container. Every result below was
re-run live; nothing pasted in the manifest was trusted.

### 1. The four verify commands — all reproduce

```
docker compose exec autotester uv run pytest -q                     -> exit 0
docker compose exec autotester uv run ruff check src tests scripts  -> All checks passed!
docker compose exec autotester uv run autotester doctor             -> doctor: clean
docker compose exec autotester uv run python scripts/explore_proof.py -> 10/10 invariants held, exit 0
```

The suite's progress dots count 495 tests with exactly one `s` — **494 passed, 1 skipped**, the
claimed number exactly. I separately confirmed the live half genuinely *runs* rather than
silently skipping (the failure mode that would make the whole real-browser claim hollow):
`pytest tests/test_explore_live.py -v` → **8 passed in 59.02s**. Real Chromium, real crawl.

### 2. The adversarial check — the guards are NOT vacuous (the one that mattered)

The manifest invited this and it is the check that separates "the guards work" from "the fixture
never exercised them". I renamed `Delete account` → `Obliterate` in
`tests/fixtures/crawl_site/settings.html` (a name `DEFAULT_DENY_PATTERNS` does not match) and
re-ran the proof:

```
FAIL  no sentinel page ever reached  (reached=['deleted.html'])
FAIL  destructive controls all denied  (denied=['Deactivate','Log out','Remove user','Save','Sign in'])
8/10 invariants held     EXIT=1
```

Screens went 7 → 8: the crawler really did click the button and really did land on the delete
sentinel. So the fixture genuinely drives the guard, the sentinel check genuinely detects a
breach, and the proof's exit code is real. Restored the file and re-verified by hash
(`f89d7472…3c`, `git status` clean) — the proof returns to 10/10, exit 0.

This also demonstrates the accepted D-016 limitation in the open: the deny-list matches on a
control's *name*, so an unnamed destructive verb is clicked. That is a decided design boundary
(the real boundary is the test account's permissions), recorded in X6 — not re-litigated here.

### 3. X7 — the post-action host re-check, read directly

`stages/explore_node.py::try_action` re-checks `check_destination(project, session.current_url())`
**after every action**, not only on navigations: `_perform` branches to `goto` for a safe link and
`click` otherwise, and both fall through to the same re-check. A refusal adds an
`IssueKind.NAVIGATION` issue and returns an `OFF_DOMAIN_REFUSED` edge — it does not silently
continue. Recovery is real: control returns to `visit_node`, which calls `return_to` (back → the
node's own URL → `base_url` via `_recover`), each step verified by *fingerprint*, not by URL
string. Confirmed no node is ever created from an off-domain page — the refusal returns before
`observe`/`node_from`.

One observation, not a finding: if `go_back` fails to leave a third-party page, `return_to`
fingerprints that off-domain DOM before falling through to the on-domain `goto`. It is a read,
never an action, no node or screenshot results from it, and it self-corrects. Noted for the
record only.

### 4. X10 — nothing is typed

`grep -n 'fill\|select_option\|upload' src/autotester/stages/explore*.py` returns exactly one hit:
`type(exc).__name__` in an error string. No typing path exists in the explorer. `run_case` is
called from `stages/explore.py` at exactly one site — `_bootstrap_login` — which is the
human-authored login case. X10 holds.

### 5. X1 / E5 — untouched, verified by history not by reading

`git show --name-only bb4c13c` does not contain `src/autotester/stages/execute.py` at all; its
last change was `640cd92` (Track B1). `qa/contracts/execute.md` was last touched by a prior
checker sweep (`927a097`), not by this unit. E5 is intact and unamended, exactly as D-015
requires. The maker also correctly did not write into `qa/contracts/` — it filed the criteria in
`qa/feedback-inbox.md` (+49 lines in the same commit) and left the contract to me.

### 6. Defect 1 (node status not persisted) — fix is real and the test has teeth

I sabotaged `CrawlStoreMixin.update_node` into a no-op and re-ran the pinning test:

```
assert statuses == {"explored"}
E  AssertionError: assert {'queued'} == {'explored'}
```

It fails with precisely the defect signature the maker described — the test is not vacuous, and
the maker's account of the bug is truthful. Restored; `md5sum` back to `2bc697c6…04`,
`git status` clean.

### 7. Defect 2 (settle_ms) — genuinely fixed, but NOT pinned

The fix is complete rather than partial: all six `session.settle(...)` call sites in the explorer
pass `timeout_ms=rt.bounds.settle_ms` (default 2500ms vs the 8000ms default in
`session.settle`). I independently corroborated the effect — the live file runs in 59.02s, matching
the claimed 300s+ → 59s.

But **no test references `settle_ms` at all**. Dropping `timeout_ms=` from any call site would
silently restore the >5-minute behaviour; only the live suite's wall clock would grow, and no
assertion pins it. Coverage is indirect and incidental (a slow crawl would eventually trip
`wall_clock_s` and perturb the screens-found assertions), not deliberate. Filed as AT-095 — it
does not fail a criterion, since no criterion demanded a timing pin.

### 8. C1 — no schema model duplicated, no dict-shaped domain object

`ExploreRuntime` is a dataclass of live, non-serialisable objects (session, store, clock,
observer, breaker, in-memory node index) plus integer tallies. It defines no persisted shape and
is never written to disk. The one judgement call: `rt.noise` is a `dict[str, int]` host→count
accumulator, and `NoiseCount` is a schema model of `{host, count}`. I judged this acceptable —
it is a mutable counter folded once into `NoiseCount[]` at `_finish`, not a parallel domain
object, and the alternative is O(n) list scans on every failed request. The persisted shape has
exactly one definition. C2 holds (largest new file 202 lines, all under 300; doctor clean), C3
holds, C6 holds.

### 9. X11 — I induced a real crash rather than only reasoning

The manifest asked me to reason about this and say honestly if I could not prove it. I proved it
instead. I monkeypatched `visit_node` to raise `KeyboardInterrupt` on the second node, then loaded
the artifacts from a fresh `ProjectStore`:

```
CRASHED mid-crawl: simulated hard kill mid-crawl
partial graph loaded OK -> 3 nodes, 3 edges
statuses: ['explored', 'queued']
crawl envelope status: running | finished_at: None
frontier: queue=[node_982…, node_1f7…] visited=[node_ef3…] actions_used=2 screens_found=3
```

A genuinely loadable partial graph, honestly self-describing: the finished node is `explored`, the
un-visited frontier is `queued`, the envelope is left `running` with `finished_at: None`. Write
ordering supports it — nodes/edges/issues use `append_jsonl` (never rewrites an earlier line) and
frontier/envelope use `_atomic_write` (tmp + `os.replace`).

**The honest limit, now written into X11:** this proves a crash *between* writes. A kill *during*
a single line's append is NOT covered — `read_jsonl` raises on a malformed row rather than skipping
it, so a torn final line makes the whole file unloadable, despite `append_jsonl`'s docstring
calling itself "crash-safe". Filed as AT-096.

Artifacts inspected on disk: `crawl.json`, `nodes.jsonl`, `edges.jsonl`, `issues.jsonl`,
`frontier.json` — one record per line, plainly readable, human-meaningful fields
(`"name":"Students"`, `"outcome":"navigated"`). C6 holds.

### 10. B5-B9 — no regression

Untouched by this unit (no diff to `browser/session.py` or `browser/secrets.py`). The explorer
composes session primitives only; `tests/test_actuator_chokepoint.py` passes, and no `playwright`
import or `.page.` access exists in `src/autotester/` outside `browser/` (X2). Screenshots go
through `session.screenshot` (masked, B7); the proof runs with an empty `.env` and no credential
of any kind.

### 11. AT-093 — its stated trigger condition has now fired

I re-verified rather than trusting the ledger:

```
'Log out'  -> 'never-click pattern (logout/sign-out)'
'Log-Out'  -> None      'LOG_OUT' -> None
'Log.Out'  -> None      'Sign-Out' -> None
```

Still open, still reproducible. AT-093 was filed at T-142 with the explicit note "should be closed
before T-143 wires a real crawl loop through this guard." T-143 *is* that crawl loop, and it
shipped without closing it — so a gap that was theoretical is now live in the code path X6
governs.

I did not fail the unit for it: the defect lives in T-142's already-checked-and-accepted B4 code,
this unit neither introduced it nor makes any false claim about it, and failing T-143 for a
consciously deferred T-142 defect would re-litigate a closed verdict. I have instead **escalated
AT-093 medium → high** and recorded it as an open gap inside X6 itself. **It must close before
T-145 points the explorer at a real product** — that is the next unit where this becomes
exploitable rather than latent.

## Scoreboard

SCOREBOARD: 12/12 criteria met (X1-X12, with X6 met for the name-forms the baseline covers and
carrying open gap AT-093) · C1, C2, C3, C6 met · B5-B9 no regression · E5 intact
FAILURES: none
ISSUES-WRITTEN: AT-094 (new, low) · AT-095 (new, low) · AT-096 (new, low) · AT-093 (escalated
medium → high, gating T-145)

## Push / commit state

Verified, not assumed. Before this verdict: `git status --short` empty (clean tree) and
`git log origin/master..HEAD` empty — the maker's source commit `bb4c13c` and manifest `600a6dd`
are both genuinely on `origin/master`. My fixture and `crawl_store.py` sabotages were both
restored and hash-verified before writing this. This verdict commits `qa/contracts/explore.md`,
`qa/verdicts/track-b3-crawl-stage.md` and `qa/issues.jsonl`, and pushes per D-007.

## EXPLANATION

This is the strongest unit I have checked in this project, and the adversarial check is why I can
say so rather than merely repeat it. A proof that only ever passes is evidence of nothing; this
one fails loudly and specifically the moment the fixture stops exercising the guard, and it fails
on the *right* assertion (`reached=['deleted.html']`), which means the sentinel pages are real
traps and not decoration. The same held for the persisted-status test, which reproduced the exact
`{'queued'}` defect under sabotage. The maker also found both of its own defects by *running* the
thing rather than reasoning about it, and reported them plainly — the settle_ms one in particular
would have made the crawler unusable against a real ERP and no amount of unit testing would have
surfaced it.

What I added beyond confirming the maker's own claims: the missing twelfth criterion (which D-015
names and the maker's list dropped), a crash proof where the manifest expected only an argument
and an honest boundary on what that proof does *not* cover, and the observation that AT-093's own
stated precondition has now materialised. That last one is the finding I would most want a human
to see: nothing is broken today, but the guard that stops this crawler from logging itself out of
a production ERP does not recognise `Log-Out`, and the next unit is the one that aims it at a real
product.
