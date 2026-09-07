# Verdict — ui-credential-safety-all-fields

**Date:** 2026-09-07
**Contract:** qa/contracts/ui.md (U1–U7 at submission; U8 added by this check)
**Manifest:** qa/manifests/ui-credential-safety-all-fields.md
**Cycle checked: 1**
**Mode:** A (unit check), bound to `d:/autoTesting`
**Dual check:** no

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met (U1–U7), 0/0 declared invariants (ui.md declares none of its own)
FAILURES: none against ui.md's criteria
ISSUES-WRITTEN: AT-073 (high), AT-074 (medium), AT-075 (medium), AT-076 (medium), AT-077 (low)
ISSUES-CLOSED: AT-070 open→fixed, AT-071 open→fixed
EXPLANATION: Both issues this unit claimed are genuinely closed — I reproduced every bypass
myself with the real PATHLYNKS_USER_PASSWORD read inside the container, and title / target /
expect / value each refuse, as do splits across two rows, three rows, and two different field
types. The four verify commands reproduce. But the guard still stops at the case form: three
routes that write the equally git-tracked project.json accept the same value in cleartext
(AT-073, high, a core-invariants C5 breach), and the substring test is defeated by a
one-step-reversible encoding (AT-074). Neither is a violation of any U-criterion by this unit,
so neither is charged here.
```

## What I re-ran myself (nothing pasted, nothing trusted)

All four manifest commands, re-run in the container:

| Command | Result |
|---|---|
| `docker compose exec -T autotester uv run pytest -q` | exit 0 |
| `… uv run pytest -q tests/test_ui_credential_safety.py` | exit 0, 15 dots (15 passed) |
| `… uv run ruff check src tests scripts` | `All checks passed!` |
| `… uv run autotester doctor` | `doctor: clean` |

Live probes were driven from **inside** the container against `http://localhost:8000`, reading
`PATHLYNKS_USER_PASSWORD` (8 chars) from `/app/.env` in-process so no real value ever entered a
transcript. Probes ran against a scratch project `chkprobe` (and `chkprobe2`), both deleted
afterwards. **The repo-root `.env` was never written to.** `projects/erp/` was left untouched —
its two cases and its `ERP_EMAIL`/`ERP_PASSWORD` declarations are intact.

## 1 — Are AT-070 and AT-071 actually closed?

**Yes, as worded, and further than worded.** Every probe posted the genuine `.env` value:

| Probe | Result |
|---|---|
| 1 — value in `title` | **400**, no value in body |
| 2 — value in `step_target` | **400** |
| 3 — value in `step_value` | **400** |
| 4 — value in `step_expected` | **400** |
| 5 — split across two `step_target` rows (AT-071) | **400** |
| 6 — split across **three** `step_target` rows | **400** |
| 7 — split across `step_target` + `step_expected` (different field types) | **400** |
| 8 — split across `title` + `step_target` | **400** |
| 14 — value via the `rename` door | 404 (unknown case id — the guard is reached only after the case lookup; covered by the maker's own passing test on a real case) |

Verified by reading the code, not only the responses: `create_case`
(`routes_cases.py:162`) builds the guarded list as
`[title, *getlist("step_target"), *getlist("step_value"), *getlist("step_expected")]` and calls
`_refuse_unsafe_submission` **before** `_build_steps` and before any `Case` is constructed, so a
refusal writes nothing. `rename_case` (`:261`) guards the new title on the same helper.

### What I kept hunting, and what is NOT covered

- **`case_class` (probe 12)** — refused 400, and nothing written, *but the 400 body echoes the
  raw submitted string verbatim*: `f"unknown case class '{case_class}'"` at
  `routes_cases.py:158`. The class parse also runs **before** the guard, so the value is echoed
  before any guard sees it. `unknown action '{action}'` (`:112`) has the same shape. This is the
  exact pattern AT-068 removed from `declare_secret`. → **AT-075 (medium)**.
- **The three `project.json` write routes (probes 15/16/17)** — **not covered at all.** Each
  accepted the real credential, persisted it in cleartext, and echoed it back:
  - `POST /onboard` `name=<real value>` → 303, written to `projects/chkprobe2/project.json`
  - `POST /projects/{slug}/edit` `name=<real value>` → 303, written to `project.json`
  - `POST /projects/{slug}/secrets` `description=<real value>` → 303, written to `project.json`

  I confirmed on disk that both `project.json` files contained the value verbatim. Worse than
  `cases.jsonl`: once it is a project **name**, it renders on *every* page — `GET /`,
  `/projects/{slug}`, `/cases`, `/env`, `/edit`, `/report`, `/cases/new` all returned it. And
  `projects/*/project.json` is git-tracked (`git ls-files projects`) in the public repo. The
  `description` box is the sharpest edge: it sits immediately beside the Key box that AT-068
  already identified as the place a user is most likely to paste a value.
  → **AT-073 (high)** — and it breaches core-invariants **C5** ("secret values live only in the
  repo-root `.env`"). Not charged as a FAIL here because it is a pre-existing hole in routes this
  unit neither touched nor claimed, and no ui.md criterion covers it; but it is the next unit.
- **Trivially reversible obfuscation (probes 9/10/11)** — `is_clean` is a plain
  `value in text` substring test, so all three of these were **accepted (303)** and written to
  `cases.jsonl`: the value URL-encoded, the value with a space inserted between halves, and the
  value with a newline inserted. On-disk verification found one row where `unquote(target) == V`
  and two rows where `''.join(target.split()) == V`. Not a byte-for-byte leak, but a
  one-transformation-away leak in a public repo. → **AT-074 (medium)**.
- **HTML-entity encoding** — not separately probed; it is the same class as AT-074 and is filed
  under it rather than as a fabricated separate finding.

## 2 — The concatenation check's false-positive cost

**Structure.** `_refuse_unsafe_submission` joins **16** fields (`title` + 5 × target/value/expect)
with **no separator**, creating **15 artificial boundaries** that exist in no real string. A
false positive fires when a `.env` value straddles one of them.

**How likely.** For a high-entropy 20+ char secret the straddle probability is negligible. It is
*not* negligible here, because the redactor masks **every** value in the shared repo-root `.env`,
declared or not (`SecretStore._all_values` merges `_shadow`). This repo's `.env` currently holds
8 non-empty values including two 8-char passwords, two emails and two login URLs — every one of
which is a string a tester might legitimately type or straddle.

**Reproduced (FP-B):** `title="Open " + V[:4]`, `step_target = V[4:] + "/x"` → **400**, with
*neither field individually refused*.

**Cost when it misfires.** The message is: *"a real credential appears to be split across these
fields. Declare it in Project settings and reference it as `{{SECRET:KEY}}` instead."* It names
no field, and the advice is unactionable — no single field contains a credential, so there is
nothing to replace. The user has no way to work out what to change. → **AT-077 (low)**.

**The worse false positive is not the concatenation at all (FP-A).** A single field holding a
value that is in `.env` is refused outright — so posting the **real `PATHLYNKS_USER_LOGIN_URL`
as a navigate target** returns 400 "that looks like a real credential". That is the most natural
first case anyone writes. And here the suggested remedy genuinely **does not work**:
`session.goto` (`browser/session.py:153`) never calls `secrets.resolve`; only `fill` (`:163`)
does. A `{{SECRET:…}}` in a target would be handed to Playwright literally. The only escapes are
removing the URL from `.env` or hand-editing `cases.jsonl`. Distinct from AT-072 (short /
word-like values) because this is a long, legitimate, deliberately-typed value. → **AT-076
(medium)**. Directly relevant to the imminent ERP work: `ERP_EMAIL`'s value, once in `.env`,
becomes untypeable as expect-text or as a target anywhere in any project.

## 3 — The BLOCKED-verdict change in `grade.py`

All four sub-questions check out.

- **It yields a real `Verdict` with `Result.BLOCKED`.** The handler calls the same `_verdict`
  factory every other path uses, so the object is a fully-formed `Verdict` (correct `run_id`,
  `case_id`, `criteria_total`, `rubric_hash`), not a stub. The maker's unit test at
  `tests/test_ui_credential_safety.py:271` exercises it and passes.
- **The note names no value.** `f"a credential value reached the grading prompt … "
  f"({type(exc).__name__}) …"` — `type(exc).__name__` renders `ValueError`. The only other
  interpolation is the literal `{{SECRET:KEY}}`. The exception's own message is never rendered,
  and `assert_no_raw_secrets`'s message ("refusing to proceed: raw secret value present in
  payload") carries no value either.
- **No other `ValueError` is swallowed.** The `try` wraps **exactly one statement** —
  `secrets.guard_prompt(prompt)`. `build_grade_prompt` (which does file I/O and could raise) is
  *above* it; `judge.judge`, `_inconsistency` and the final `_verdict` are all *below* it.
  `guard_prompt` → `assert_no_raw_secrets` is a substring loop whose only `raise` is the intended
  one. Nothing else that should propagate can be caught here.
- **The three script callers are unaffected.** `scripts/bench_trial.py:101`,
  `scripts/regression_proof.py:111` and `scripts/run_pathlynks_first_cases.py:139` all call
  `grade(...)` with no `secrets` argument → `secrets is None` → the whole `if secrets is not
  None:` block is skipped. Only `stages/run_case_pipeline.py:101` passes
  `secrets=session.secrets`. Grepped exhaustively across `src/`, `scripts/` and `tests/`.

## 4 — `_build_steps`'s reverted signature

**No path lost its guard.** `_build_steps` has exactly **one** caller in the whole repo
(`routes_cases.py:165`, inside `create_case`), and the guard call sits at `:162`, three lines
above it — so reverting the signature moved the guard *earlier*, not away. The two UI doors that
write a case title are `create_case` and `rename_case`; both call
`_refuse_unsafe_submission`. `store.add_case` / `store.update_case` are otherwise reached only
from tests and from `scripts/` (three CLI scripts) and from `stages/expand.py`'s FlowSpec path —
none of which is a UI route, none of which this contract covers, and none of which is a path a
user types into. The consolidation is a genuine improvement: one guard, one place.

## 5 — Regression

- **Ordinary cases still create.** Control probe 13 (`"Chkprobe smoke"`, a plain
  `https://www.vidysea.com/erp` navigate target) → 303/200 and the case landed on disk.
- **All five U6 refusals still fire, unchanged:** blank title → 400 `"a case needs a title"`;
  zero surviving steps → 400 `"a case needs at least one step"`; unknown `case_class` → 400;
  unknown `action` → 400; unknown project → **404**.
- **The duplicate 400 is genuinely the duplicate check, not the guard misfiring.** I posted
  `"Dup A"` (303), then an identical-steps `"Dup B"`: the 400 body reads *"this project already
  has a case with exactly these steps: **'Dup A'**…"* — it names the clashing case, and contains
  no credential wording. Confirmed programmatically (`"'Dup A'" in body` → True,
  `"credential" in body` → False).
- **U1–U5, U7 spot-checked live:** `/`, `/projects/{slug}`, `/cases`, `/env`, `/edit`,
  `/report`, `/cases/new` all 200; unknown slug 404; `_require_reachable_base_url` is
  byte-unchanged in this diff; the edit route still round-trips and preserves `secrets`.

## 6 — Source commit (AT-055 lesson)

**Yes, I had to commit the maker's source myself.** At the time of this check the working tree
carried `src/autotester/ui/helpers.py`, `src/autotester/ui/routes_cases.py`,
`src/autotester/stages/grade.py` and `tests/test_ui_credential_safety.py` as **modified but
uncommitted**, and the manifest as **untracked** — exactly the AT-055 failure. I committed those
five paths with a narrow pathspec. `projects/`, `.work/` and `.env` were **not** committed;
`projects/erp/` remains untracked and untouched.

## Cleanup performed

- Scratch projects `projects/chkprobe/` and `projects/chkprobe2/` deleted (both had a real value
  in `project.json` from probes 15–17).
- Probe scripts removed from the container's `/tmp`.
- **The repo-root `.env` was never written to** — probes only read it in-process.
- `projects/erp/` untouched: `ERP_EMAIL` + `ERP_PASSWORD` still declared, both legitimate cases
  still present.

## What Umesh should know before typing real ERP credentials

The **case form is now safe** against typing the value in verbatim — that was the thing standing
in the way, and it is fixed. Two live cautions remain:

1. **Do not type a real credential into the Project-settings "What it is" (description) box, the
   project Name box, or the onboarding Name box.** Those three still write it in cleartext to
   git-tracked `project.json` and then render it on the home page (AT-073). Only the **Key** box
   (`ERP_PASSWORD`) and the **Credentials page value** box are safe.
2. Once `ERP_EMAIL`/`ERP_PASSWORD` hold real values, those exact strings become untypeable
   anywhere in any project's case form, including as expect-text (AT-076).
