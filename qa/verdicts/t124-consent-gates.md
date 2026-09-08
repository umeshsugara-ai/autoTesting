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

---

# Verdict — t124-consent-gates (cycle 2)

**Date:** 2026-09-08 · **Cycle checked: 2** · **Mode:** A (unit check) · **Bound to:** `d:/autoTesting`
**Unit:** commit `1d2e647` (tree clean at `9a74852`), goal task **T-124**, authorised by **D-018**
**Manifest:** `qa/manifests/t124-consent-gates.md` (Status: ready-for-check, Fix cycle: 2)
**Contract:** `qa/contracts/consent.md` CN1–CN9 (authored at cycle 1), plus `core-invariants.md`
C1/C2/C3/C6 and `explore.md` X1–X16.
**Note:** this is a **retry** of cycle 2 — a previous cycle-2 checker died on a network error and
wrote nothing. I started clean from the cycle-1 FAIL above; nothing that run may have said is
evidence here. No contract amendment was needed this cycle.

```
VERDICT: PASS
SCOREBOARD: 9/9 criteria met, 20/20 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-116 (new, high) · AT-111 open → verified · AT-110 and AT-100 notes updated, both stay open
EXPLANATION: The cycle-1 failure is closed and I proved it on the disk, not in the proof script: a
refused `autotester explore` and a refused `POST /projects/{slug}/explore` each exit 2 / 403 and
leave the scratch root byte-identical to before — no `projects/<slug>/crawl/`, no `profiles/`. The
new evidence is not vacuous: sabotaging `_preflight_consent` out of `cli_crawl.py` in a git-archive
sandbox drops `explore_proof.py` to 10/11 with exactly the predicted line `refused BUT left: crawl
dir, browser profile`, and the UI pre-flight and the seam each fail their own tests when sabotaged
independently — the check was ADDED, not MOVED. Every other criterion re-derived on real files.
AT-100 does NOT close and the manifest over-claims it for the second cycle running: the maker set
`base_criticality: "CRITICAL"` on T-145, but `criticality.py` only knows lowercase, so the floor
degrades to "low" and `classify(T-145)` returns 'low' — T-145 will get a single checker, not the
dual check the escalation was meant to buy. That is a project-wide vocabulary defect this unit did
not cause, so it is AT-116 rather than a FAILURE line; the contract's nine criteria all hold.
```

---

## What I re-ran myself (nothing below is the maker's pasted output)

All in the running container (`docker compose exec -T autotester`), against the live tree.

| Command | My result | Claimed |
|---|---|---|
| `uv run pytest -q --junitxml=…` | `tests="584" failures="0" errors="0" skipped="1"` → **583 passed, 1 skipped** | 583/1 ✅ |
| `uv run ruff check src tests scripts` | `All checks passed!` (exit 0) | ✅ |
| `uv run autotester doctor` | `doctor: clean` (exit 0) | ✅ |
| `uv run python scripts/explore_proof.py` | `11/11 invariants held` (exit 0), first line `PASS  no approval => nothing runs, nothing written  (CLI exit 2, no crawl dir, no browser profile)` | 11/11 ✅ |
| `uv run python scripts/check_crawl_approval.py erp` | `FAIL  no finished crawl on disk for 'erp' (0 crawl dirs)`, **exit 1** | ✅ |

`-q` really does suppress the summary line here, so the counts above come from a JUnit XML run, not
from reading dots. **One caveat that is mine, not the maker's:** my first attempt passed
`--junitxml=/tmp/j.xml` through Git-Bash, which rewrote the path and made the container create
`C:/Users/…` **under the repo root**; `autotester doctor` caught it immediately
(`root-clutter: C: — scratch and evidence belong in .work/`). I removed the directory and doctor
returned `clean`. Recorded because it is an unplanned live proof that C4's root-clutter rule works.

## 1. CN1 — the cycle-1 failure, reproduced on the disk

Not read from the proof script. Scratch `AUTOTESTER_ROOT=/tmp/scratchroot` containing exactly
`.env` + `projects/demo/project.json` (`paths.ensure()` deliberately never called), a real fixture
site served on `127.0.0.1:8765` so a non-refusing run would actually have crawled.

**CLI**
```
$ AUTOTESTER_ROOT=/tmp/scratchroot uv run autotester explore demo --max-actions 5
refusing to start a crawl run against http://127.0.0.1:8765/ — no approval exists for it
Grant one with:
  uv run autotester approve demo --kind crawl --target "http://127.0.0.1:8765/" --scope "<what this
  run may touch>" --granted-by <name> --expires <YYYY-MM-DD> --max-actions 5 --wall-clock 600.0
EXIT=2
--- FILESYSTEM AFTER ---
/tmp/scratchroot/.env
/tmp/scratchroot/projects/demo/project.json
ls: cannot access '/tmp/scratchroot/projects/demo/crawl': No such file or directory
ls: cannot access '/tmp/scratchroot/profiles': No such file or directory
```

**UI** (`TestClient`, `POST /projects/demo/explore`, own copy of the root)
```
STATUS 403
BODY {"detail":"refusing to start a crawl run against http://127.0.0.1:8765/ — no approval exists
for it\nGrant one with:\n  uv run autotester approve demo --kind crawl …"}
--- FILESYSTEM AFTER ---
/tmp/scratchroot2/.env
/tmp/scratchroot2/projects/demo/project.json
```

Compare cycle 1, where the same two commands left `crawl/<id>/shots/` and a populated Chromium
profile. **CN1 met at all three entry points.** AT-111 → `verified`.

## 2. Is the new evidence real? — yes, and I proved it by sabotage

`git archive HEAD | tar -x -C /tmp/sab` (never `git stash`/`checkout`/`restore`; the live tree was
never touched — AT-101). The sandbox is faithful: `explore_proof.py` there gives 11/11 unmodified.

One subtlety that matters: the proof's first invariant now runs the CLI in a **subprocess**, which
does not inherit the script's `sys.path.insert`, so a sandbox edit only reaches it with
`PYTHONPATH=/tmp/sab/src`. Pinned that first and re-confirmed 11/11 before touching anything.

```
$ python3 -c "…replace '    _preflight_consent(proj, store_, bounds)' with 'pass  # SABOTAGED'…"
$ PYTHONPATH=/tmp/sab/src uv run --project /app python /tmp/sab/scripts/explore_proof.py
FAIL  no approval => nothing runs, nothing written  (refused BUT left: crawl dir, browser profile)
…
10/11 invariants held        (exit 1)
```

Character-for-character the string the manifest predicts. The invariant is load-bearing; the
evidence is not vacuous.

Each layer has its own sabotage, in three independent sandboxes:

| Sabotage | What breaks |
|---|---|
| `cli_crawl.py` pre-flight removed | `explore_proof.py` → 10/11, `refused BUT left: crawl dir, browser profile` |
| `ui/routes_crawls.py` pre-flight removed | `test_ui_crawls.py::test_explore_without_an_approval_is_refused_and_leaves_no_trace` FAILS (1 failed, 12 passed) |
| `stages/explore.py` seam gate removed | `test_explore.py::test_a_crawl_without_an_approval_refuses_and_writes_nothing` and `::test_a_crawl_wider_than_its_approval_refuses` FAIL — `DID NOT RAISE ApprovalRequired` (2 failed, 47 passed) |

## 3. Did the seam survive? — yes, the check was ADDED, not MOVED (CN2)

`stages/explore.py:199` still calls `require_consent(project, store, bounds)` as the **first**
statement of `run_crawl`. Probed directly rather than by reading:

```
run_crawl(project, None, store, observer=None)   # no approval on disk, session deliberately None
RAISED ApprovalRequired: refusing to start a crawl run against http://127.0.0.1:8765/ — no approval
files after: ['.env', 'projects', 'projects/demo', 'projects/demo/project.json']
```

It refuses before it touches the session it was handed, and writes nothing. A new caller that
forgets the pre-flight is still refused. Note that the UI test above still passes with the seam
sabotaged and the two `test_explore.py` tests still pass with the pre-flight sabotaged — that is the
correct signature of two independent layers, and it is why all three sabotages were needed.

## 4. AT-110 — the prose, and behaviour unchanged

`schema/approval.py`'s module docstring now ends "**Do not read the check below as tamper
*proofing*; it is tamper *evidence*.**" and names the measured forgery. `uv run autotester approve
--help` renders, to an operator:

```
Nothing outward-facing starts without one. The approval is content-addressed, so an accidental
edit to the row invalidates it rather than silently taking effect — but the hash is unkeyed, so
this is tamper EVIDENCE, not tamper proofing: anyone who can write approvals.jsonl can recompute
a valid id (AT-110).
```

`grep -rn "cannot be edited\|tamper-proof\|tamper proof" src/ scripts/` → nothing. **The claim is
now honest.** Judged as prose: it states the limitation, names who can exploit it (the agent the
gate exists to bound), and points at the open decision — it does not bury it in a module docstring
only a maintainer reads, which is why the `--help` half is the one that counts.

Behaviour re-run and **unchanged**, which is the requirement — only the claim was supposed to move.
Fresh human grant `appr_77d1ba6115a2`, `max_actions=12`:

| Edit to `approvals.jsonl` | Result |
|---|---|
| `max_actions` 12 → 9999, stored `id` kept | **REFUSED** — `appr_77d1ba6115a2: edited after it was granted (content id no longer matches)`, exit 2 |
| `max_actions` 9999, `wall_clock_s` 99999, `production` true, `id` key **removed** | **ACCEPTED** — `crawl_01M1ZN1Q68PE8WKVJNQ7YMNMMB: completed` on `--max-actions 500 --wall-clock 300` |

AT-110 stays open on its design half only (`qa/gates/at110-approval-forgery.md`, HUMAN_GATE for
Umesh). Still not charged as a failure: CN3 claims exactly what it delivers.

## 5. AT-100 — does NOT close, and the manifest over-claims it again

The maker added `"base_criticality": "CRITICAL"` to T-145. **The escalation is inert.**

`D:/ai_os/.claude/skills/goal/scripts/criticality.py:11` defines
`_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}` — lowercase — and `base_criticality()`
at :40 is `return b if b in _ORDER else "low"`. Executed against the real file:

```
base_criticality(T-145) -> low
classify(T-145, tasks, now) -> low
is_side_effect(T-145) -> False
```

and T-145's derived field on disk still reads `"criticality": "low"`. `maker/SKILL.md` step 7b
dispatches the dual check on `criticality: critical`, falling back to `base_criticality` — both read
low. So when T-145 runs, the highest outward-facing risk in the backlog gets a **single** checker:
the AT-100 shape (a control that cannot fire) one level up from where AT-100 found it.

The cause is **project-wide and predates this unit** — all 44 rows use an uppercase vocabulary
(`HIGH` ×20, `NORMAL` ×12, `MEDIUM` ×7, `LOW` ×3, `CRITICAL` ×3) that `criticality.py` cannot read,
and the derived column is `{low: 41, critical: 3, None: 1}` where those three earned it from
`SIDE_EFFECT_KEYWORDS`, not from their floor. So it is **AT-116** (high), not a FAILURE line against
CN1–CN9. But **AT-100 stays open**, and the manifest's `Issues addressed: AT-100 both halves` is
wrong for the second cycle in a row — the first cycle claimed a half it had not done, this one
claims a half it attempted and did not achieve. The fix is small and inside this project: normalise
`.goal/goal.json` to the lowercase set (deciding `NORMAL` → `medium` or `low` per row), then
re-run `classify(T-145)` and get `critical`.

## 6. Every other criterion, re-derived

**CN3 — careless edit caught.** Table in §4, row 1. Holds as stated (accident detection only).

**CN4 — consent is never open-ended.** On real rows:
```
expired grant (expires_at 2020-01-02)  -> REFUSED :: appr_04f83570a7f0: expired 2020-01-02
unparseable expiry on an INTACT row    -> REFUSED :: appr_1303c343888b: expired not-a-date
```
The second was constructed through the model so the id matches — otherwise tamper detection fires
first and the expiry path is never reached. Unparseable is treated as expired, never as eternal.

**CN5 — approval does not transfer.** Granted `https://host/a`:

| Requested target | Result |
|---|---|
| `https://host/a` | ALLOWED |
| `https://host/a/b` | REFUSED |
| `https://host/a/` | REFUSED |
| `https://HOST/a` | REFUSED |
| `https://host/a?x=1` | REFUSED |

**CN6 — bounds, all reasons, and a suggestion that works.**
```
actions 150 vs 20   -> appr_24be95f0482f: narrower than this run — actions 150 > approved 20
wall clock 9999 vs 60 -> appr_24be95f0482f: narrower than this run — wall clock 9999.0s > approved 60.0s
two narrow rows     -> appr_24be95f0482f: … > approved 20
                       appr_fbf0e484c6d6: … > approved 5      (both reported, not just the first)
```
End to end, the refusal's own command, placeholders filled and nothing else changed:
```
$ AUTOTESTER_ROOT=/tmp/sugg uv run autotester approve demo --kind crawl \
    --target "http://127.0.0.1:8765/" --scope "checker CN6 verbatim paste" \
    --granted-by umesh --expires 2099-01-01 --max-actions 5 --wall-clock 600.0
appr_c88d700c73a4: crawl on http://127.0.0.1:8765/ until 2099-01-01 (actions<=5, probes<=0)
$ AUTOTESTER_ROOT=/tmp/sugg uv run autotester explore demo --max-actions 5
crawl_01M1ZN7V459CX98W3CWA7KWA3C: completed (frontier empty) — 2 screens, 1 edges, 1 actions
```

**CN7 — adversarial/production.** Unchanged and still a recorded boundary: no crawl caller passes
`production=`, so the field is inert for `ApprovalKind.CRAWL` (AT-112, open, out of scope per the
contract — not re-raised as new).

**CN8 — the done_check fails *and* passes.** Constructed both directions myself:

| State | Output | Exit |
|---|---|---|
| `/tmp/sugg`, real approved finished crawl | `PASS  crawl crawl_01M1ZN7V… covered by approval appr_c88d700c73a4 granted by umesh` | **0** |
| same crawl, `approvals.jsonl` emptied | `FAIL  … ran but no approval covers it: no approval exists for it` | 1 |
| same crawl, approval widened on disk (id kept) | `FAIL  … edited after it was granted` | 1 |
| live repo, `erp` | `FAIL  no finished crawl on disk for 'erp' (0 crawl dirs)` | 1 |
| no argument | `usage: check_crawl_approval.py <project-slug>` | 2 |

**CN9 — the gate applies to every crawl.** `grep -rn "localhost\|127\.0\.0\.1\|is_remote\|is_local"`
over `core/consent.py`, `stages/explore.py`, `cli_crawl.py`, `ui/routes_crawls.py` returns
**nothing** — there is no "is this remote?" predicate to fail open. Confirmed dynamically too: the
seam sabotage broke only the two *no-approval* tests and left 47 crawl tests passing, which is only
possible because those tests grant a real `RunApproval` rather than bypassing the gate. Upheld as
written; reversal remains a CRITICAL amendment.

## Invariants

- **C1** schema-first — `issubclass(RunApproval, Artifact)` → True, `model_config["extra"]` →
  `forbid`, and an unknown key raises `ValidationError` (executed). **Holds.**
- **C2 / C3** — `autotester doctor: clean`, `ruff` clean. No new module beyond the two the manifest
  declares (`schema/approval.py`, `core/consent.py`, `scripts/check_crawl_approval.py`); the AT-111
  fix edited `cli_crawl.py` and `routes_crawls.py` **in place**. **Hold.**
- **C6** artifacts human-editable — re-confirmed by the CN8 table: emptying `approvals.jsonl` by
  hand loads fine and produces a clean refusal, not a crash. The contract's stated exception stands.
  **Holds.**
- **X1–X16** (explore) — untouched: full suite green (583 passed) and `explore_proof.py` 11/11,
  covering X4 bounds, X5/X6 write-policy and session-ending controls, X7 host re-check, X9 noise,
  X13 propose-never-approve, X16 refusal reporting. The only change on the explore path is the
  hoisted pre-flight and the `require_consent` rename. **All hold.**

## Ledger

- **AT-111** (high) → **`verified`**. Reproduction from its own evidence field re-run at both
  shipped entry points; it no longer reproduces, and the fix is sabotage-proven.
- **AT-116** (high, new) — every `base_criticality` floor in `.goal/goal.json` is inert
  (uppercase vocabulary `criticality.py` cannot read). This is what blocks AT-100.
- **AT-100** — stays **open**. First half closed and re-verified; second half attempted and
  ineffective. Manifest over-claims it again.
- **AT-110** — stays **open** on the design half only; prose half closed and re-verified, behaviour
  confirmed unchanged. HUMAN_GATE, Umesh decides.
- **AT-112** — stays **open**, out of scope per the contract; not re-raised as a new finding.

## Not raised (so the next cycle does not chase them)

Style (`ruff` green); revocation / UI grant form / org approvals (the contract's Out-of-scope);
`production` inertness for crawls (AT-112); the `note` field outside the content payload — still a
good decision. The `C:/…` directory in the repo root during this check was **mine**, from a
mangled `--junitxml` path, and was removed; `git status --porcelain src tests scripts` is clean.

## Goal task

**T-124 → `done`.** A PASS closes the matching task; the checker performs the close.
