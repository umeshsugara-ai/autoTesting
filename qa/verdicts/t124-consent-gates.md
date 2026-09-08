# Verdict — t124-consent-gates

**Date:** 2026-09-08 · **Cycle checked: 1** · **Mode:** A (unit check) · **Bound to:** `d:/autoTesting`
**Unit:** commit `fb261c5`, goal task **T-124**, authorised by **D-018**
**Manifest:** `qa/manifests/t124-consent-gates.md` (Status: ready-for-check, Fix cycle: 1)
**Contract:** `qa/contracts/consent.md` — **authored by this check** from the CN1–CN7 request in
`qa/feedback-inbox.md` (2026-09-08), tightened where measurement demanded it. Also judged against
`core-invariants.md` C1/C2/C3/C6 and `explore.md` X1–X16.

```
VERDICT: FAIL
SCOREBOARD: 8/9 criteria met, 20/20 invariants hold
FAILURES:
- [CN1] sev: high · A refused run is NOT trace-free at either shipped entry point: `autotester
  explore` and `POST /projects/{slug}/explore` both create `projects/<slug>/crawl/<crawl_id>/shots/`
  and launch Chromium before `run_crawl`'s gate refuses, because `BrowserSession.start()`
  (`browser/session.py:103`, `run_dir.mkdir(parents=True, exist_ok=True)`) runs inside the `with`
  that wraps `run_crawl`. The proof invariant calls `run_crawl` directly, so it never covers the
  path an operator uses. · fix: call the consent check before `with BrowserSession(...)` in
  `cli_crawl.explore_cmd` and `ui/routes_crawls.start_crawl` (make `explore._require_consent`
  public and call it there — the seam check stays, CN2 permits a caller-side pre-check *in
  addition*), or make `session.start()`'s `run_dir.mkdir` lazy; hoisting fixes the browser launch
  too. · issue: AT-111
ISSUES-WRITTEN: AT-110, AT-111, AT-112 (+ AT-100 kept open, partially addressed)
EXPLANATION: Every command in the manifest reproduced exactly, and the gate is real, not theatre —
sabotaging `_require_consent` in an isolated copy fails both new explorer tests and drops the proof
to 10/11. Tamper detection, exactness, the refusal's own grant command and the new `done_check` in
BOTH directions all verified on real files. It fails on its own headline criterion: the "leaves no
trace" property the unit sells is proven only on the direct `run_crawl` call, and both shipped
callers create the crawl/shots directory and launch a browser before the refusal. Separately and
NOT charged as a failure: I got past the tamper check — a row widened 12 → 9999 actions with
`production` flipped true and its id recomputed was accepted, and a 500-action crawl ran on a human
grant of 12. No criterion claimed resistance to a forger (CN3 as filed claims id-mismatch
detection, which is exactly true), so it is filed as AT-110 with a HUMAN_GATE for Umesh rather
than a fix cycle — but the operator-facing prose that says an approval "cannot be edited on disk to
widen itself" overclaims and should be corrected in the same cycle as the CN1 fix.
```

---

## What I re-ran myself (nothing below is the maker's pasted output)

All in the running container (`docker compose exec -T autotester`), against the live tree at
`fb261c5`:

| Command | Result | Claimed |
|---|---|---|
| `uv run pytest -q` | `582 passed, 1 skipped, 1 warning in 66.21s` | 582/1 ✅ |
| `uv run ruff check src tests scripts` | `All checks passed!` | ✅ |
| `uv run autotester doctor` | `doctor: clean` | ✅ |
| `uv run python scripts/explore_proof.py` | `11/11 invariants held`, first line `PASS  no approval => nothing runs, nothing written  (refused, no crawl dir created)` | 11/11 ✅ |
| `uv run python scripts/check_crawl_approval.py erp` | `FAIL  no finished crawl on disk for 'erp' (0 crawl dirs)`, **exit 1** | ✅ |
| `uv run python scripts/check_crawl_approval.py` (no args) | usage, **exit 2** | — |

## Adversarial checks

### 1. Is it decorative? **No — proven by sabotage.**
Copied `src`/`tests`/`scripts` to `/tmp/sab` inside the container (never the live tree; the compose
volume mounts the repo at `/app`), confirmed the copy is faithful (`tests/test_explore.py` 19
passed, proof 11/11 with `PYTHONPATH=/tmp/sab/src` shadowing the installed package), then removed
the single line `_require_consent(project, store, bounds)` from `stages/explore.py`:

```
FAILED tests/test_explore.py::test_a_crawl_without_an_approval_refuses_and_writes_nothing
FAILED tests/test_explore.py::test_a_crawl_wider_than_its_approval_refuses
  E  Failed: DID NOT RAISE ApprovalRequired
FAIL  no approval => nothing runs, nothing written  (the crawl ran with no approval on disk)
10/11 invariants held
```

Both new tests and the new first invariant are load-bearing. Sandbox restored from `/app`
immediately after; the live tree was never touched.

### 2. Tamper detection — real for a careless edit, **defeated by a forger**
On a real `approvals.jsonl` in a scratch `AUTOTESTER_ROOT`, editing `max_actions` 12 → 9999 while
keeping the stored id:

```
FAIL  crawl crawl_01M1ZD8DZ8Z5PKCXSSJDR2GFBY ran but no approval covers it:
  - appr_f3616d0cafd7: edited after it was granted (content id no longer matches)
```
…and a real `autotester explore` refused with the same line. Editing `expires_at` on a granted row
is caught identically.

**Then I defeated it.** `core.ids.content_id` is an *unkeyed* sha256, so the id is recomputable by
anyone who can write the file — including the agent the gate exists to bound. Two variants, both
accepted:

- **drop the `id` field** → `model_post_init` mints a matching one (`id` has default `""`).
- **paste a self-computed id** → identical outcome.

End to end, on disk, with the real CLI:

```
forged row id: appr_34d709b1d3ea is_intact: True      # max_actions 9999, wall_clock 99999, production=True
$ AUTOTESTER_ROOT=... uv run autotester explore demo --max-actions 500 --wall-clock 300
crawl_01M1ZD9VR9SKRN9B748KKH721V: completed (frontier empty) — 2 screens, 1 edges, 1 actions...
```

A crawl asking for 500 actions ran on a human grant of 12. **Recorded in CN3 as a stated limitation
and filed as AT-110 (HUMAN_GATE: where does a key live?), not charged as a fix cycle** — no
criterion claimed forgery resistance, and no unkeyed local scheme can provide it. The prose that
does claim it (`schema/approval.py` module docstring first sentence; `approve_cmd`'s docstring, which
is operator-facing `--help` text) is the part that must change.

### 3. Exactness — holds, and the brittleness is correct
Granted `https://host/a`, then requested each variant:

| Target run | Result |
|---|---|
| `https://host/a` | ALLOWED |
| `https://host/a/b` | REFUSED (no approval exists for it) |
| `https://host/a/` | REFUSED |
| `https://HOST/a` | REFUSED |
| `https://host/a?x=1` | REFUSED |

Trailing-slash and case being distinct targets is **correct, not merely brittle**: the alternative
is a URL normaliser, and every normaliser is a place where an approval silently grows. The refusal
always prints the exact string the runner compares, so the cost is one copy-paste. Written into CN5
with that reasoning. Also confirmed: `probes 999 > approved 0` is caught, `production=True`
requested against a non-production grant is refused, and an unparseable `expires_at` is treated as
expired.

### 4. The suggestion works — **verified verbatim**
Took the command out of a real refusal, filled only the `<...>` placeholders, ran it, re-ran the
identical crawl:

```
$ ...explore demo --max-actions 12 --wall-clock 30 --max-screens 3
refusing to start a crawl run against http://127.0.0.1:8765/ — no approval exists for it
Grant one with:
  uv run autotester approve demo --kind crawl --target "http://127.0.0.1:8765/" --scope "<...>"
  --granted-by <name> --expires <YYYY-MM-DD> --max-actions 12 --wall-clock 30.0
$ <that command>
appr_f3616d0cafd7: crawl on http://127.0.0.1:8765/ until 2099-01-01 (actions<=12, probes<=0)
$ <the same explore command again>
crawl_01M1ZD8DZ8Z5PKCXSSJDR2GFBY: completed (frontier empty) — 2 screens, 1 edges, 1 actions
```

The maker's own round-one fix holds. CN6 now pins this as a criterion so it cannot regress silently.

### 5. The `done_check` fails **and** passes — both directions constructed
| State | Output | Exit |
|---|---|---|
| today, `erp` | `FAIL  no finished crawl on disk for 'erp' (0 crawl dirs)` | 1 |
| scratch root: real approved finished crawl | `PASS  crawl crawl_01M1… (completed, …) covered by approval appr_f3616d0cafd7 granted by umesh` | **0** |
| same crawl, approval row deleted | `FAIL  … ran but no approval covers it: no approval exists for it` | 1 |
| same crawl, approval widened on disk (id kept) | `FAIL  … edited after it was granted` | 1 |

CN8 satisfied. Also checked `finished[0]`: `list_crawl_ids` sorts ULIDs `reverse=True`, so "latest"
really is the newest crawl — not a finding.

### 6. My own additions
- **CN1 at the shipped entry points** — the failure above. Proven twice:
  `autotester explore` (exit 2, correct refusal) left `projects/demo/crawl/crawl_01M1ZD6SPNYWVANSFV8EK4BBZN/shots/`
  plus a fully populated Chromium profile under `profiles/demo/` (Cookies, History, Preferences,
  LOG); the UI `POST /projects/demo/explore` returned the intended **403** with the grant command in
  the detail — and left `projects/demo/crawl/crawl_01M1ZDEXS1A5Z3EQW2KPF0YSR1/shots/`. The 403
  itself is right and is credited.
- **`production` is inert for crawls** — nothing computes "is this target production", and the
  explore gate never passes `production=True`, so the live ERP crawl of T-145 is authorised by an
  ordinary crawl approval. CN7 as filed is scoped to adversarial, so this is a boundary, not a
  violation. Recorded in CN7 and filed as **AT-112**.

## The trade the maker asked me to judge — **upheld, and now CRITICAL to reverse**

The gate applying to *every* crawl including local fixtures is right, and I have written it into
the contract as **CN9** so it is not quietly reversed later. The maker's two arguments both survive
contact: a `is this localhost?` predicate fails **open** on exactly the misconfiguration that most
needs a refusal (unresolved host, proxy, tunnelled port, stale `base_url`), and a guard only
production callers pass through is exercised by no test in the suite. The measured cost is small —
one helper (`crawl_fake.grant_crawl_approval`) and four entry points — and the return is that every
crawl test in the suite now also exercises the gate's happy path. Reversing CN9 is a CRITICAL
amendment (weakening a safety invariant): human only.

## Invariants

- **C1** schema-first — `RunApproval` is a Pydantic `Artifact` in `schema/approval.py`,
  `tests/test_schema.py` green in the full run. **Holds.**
- **C2 / C3** — `autotester doctor: clean` (file/function caps, one-concept-one-place, drift
  filenames). **Hold.**
- **C6** artifacts human-editable — `approvals.jsonl` is *deliberately* hostile to hand-editing, but
  it still loads and still deletes cleanly; it refuses an edited row rather than crashing. Recorded
  in the contract as a stated exception. **Holds.**
- **X1–X16** (explore) — untouched: full suite green and `explore_proof.py` 11/11, including X4
  bounds, X5/X6 write-policy and session-ending controls, X7 host re-check, X9 noise, X13 propose-
  never-approve, X16 refusal reporting. The only change to the explore path is the pre-flight gate.
  **All hold.**

## Ledger

- **AT-110** (high, consent) — a widened approval whose id is recomputed is accepted; content-
  addressing without a secret detects carelessness, not a forger. **HUMAN_GATE for Umesh:** does the
  approval get an HMAC keyed from the repo-root `.env` (already the credential boundary), a separate
  signed audit line, or is "accident detection only" the accepted posture? Do not let the maker pick
  this one.
- **AT-111** (high, consent) — CN1 fails at both shipped entry points. **This is the fix for cycle 2.**
- **AT-112** (medium, consent) — `production` inert for `ApprovalKind.CRAWL`.
- **AT-100** — **kept `open`**, not closed. Its first half (T-145's `done_check` was `{"cmd":"true"}`)
  is genuinely fixed and verified here. Its second, explicitly separate half is not: T-145 still
  carries `"criticality": "low"` in `.goal/goal.json` while being the highest outward-facing risk in
  the backlog, and the row itself said to re-examine that "when D-018 lands". D-018 has landed.
  The manifest's `Issues addressed: AT-100` therefore over-claims by half.

## Not raised (so the next cycle does not chase them)

Per-file style (`ruff` green), the absence of revocation / a UI grant form / org approvals (the
unit's own no-fire list, folded into the contract's Out-of-scope), and the `note` field sitting
outside the content payload — that one is a good decision, not a gap.

## Goal task

**T-124 stays `pending`** — a FAIL never closes a task.
