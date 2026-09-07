# Verdict — ui-case-management

**Contract:** qa/contracts/ui.md
**Manifest:** qa/manifests/ui-case-management.md
**Cycle checked: 1**
**Date:** 2026-09-07
**Checker:** /checker Mode A (fresh context, no builder reasoning)
**Bound root:** d:/autoTesting

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, 0/0 invariants hold (ui.md declares no [I*] items)
FAILURES (if any): none
ISSUES-WRITTEN: AT-066, AT-067 (both low; neither violates a criterion)
EXPLANATION: Every verify command was re-run by the checker itself in the container and
reproduced the manifest's claimed output exactly. The new destructive primitive was probed
directly rather than trusted: `delete_jsonl_row` preserves survivor rows byte-for-byte and in
order, is a no-op returning False for an unknown id, never creates or corrupts an absent/empty
file, leaves no temp files, and goes through the same `_atomic_write` as `upsert_jsonl`.
Delete scope is exactly as claimed — a case's rubric, RawResults and Verdicts all survive its
deletion, verified by diffing the project tree before and after. Rename cannot change identity:
posting `id`, `project`, `flow_id`, `case_class` and `steps` alongside `title` left every one of
them inert on disk. U5 was re-probed hostilely on the new list page and every user-derived value
is escaped, including `'` inside `value='…'`. Two low-severity gaps found (a test that does not
actually exercise the cache it claims to prove, and the pre-existing whole-file-rewrite vs
concurrent-CLI-append window) were filed rather than folded into the contract.
```

## Commands re-run by the checker (not the maker's paste)

| Command | Result |
|---|---|
| `docker compose exec -T autotester uv run pytest -q` | exit 0 — 319 passed, 1 skipped, 0 failures |
| `docker compose exec -T autotester uv run pytest tests/test_ui_cases.py tests/test_ui_case_management.py` | exit 0 — **19 passed**, matching the manifest exactly |
| `docker compose exec -T autotester uv run ruff check src tests scripts` | `All checks passed!` |
| `docker compose exec -T autotester uv run autotester doctor` | `doctor: clean` |
| `docker compose exec -T autotester uv run autotester map` | regenerated; produced **no diff beyond the maker's own 1-line MAP.md change** — MAP is genuinely in sync |

## Scrutiny items demanded by the dispatch

### 1. `delete_jsonl_row` cannot lose rows (data-loss risk) — VERIFIED

Direct probe in-container against a 5-row file (`.work` scratch, since removed):

```
P1 order+bytes preserved: True
   ['{"id":"r0",...}', '{"id":"r1",...}', '{"id":"r3",...}', '{"id":"r4",...}']
P2 delete of a non-existent id -> returned False, file byte-identical: True
P3 absent file -> False, and the file was NOT created: True / created? False
P4 empty file -> False, content still '' : True
P5 delete the only row -> True, file becomes '' (valid empty JSONL, read_jsonl -> [])
P6 leftovers in the directory: ['empty.jsonl','one.jsonl','rows.jsonl'] — no stray .tmp-* files
```

- **Order + byte identity:** the survivors are exactly the original lines minus the deleted one,
  compared line-by-line against the pre-delete file.
- **Atomicity:** `filestore.py:87` calls the same `_atomic_write` (`mkstemp` in the target's own
  directory → write → `os.replace`, with `unlink(missing_ok=True)` on any `BaseException`) that
  `upsert_jsonl:110` and `write_json:36` use. `os.replace` is atomic within a filesystem, and the
  temp file is created in `path.parent`, so a crash mid-write can only leave the original file
  intact plus at most an orphan `.tmp-*` — never a truncated `cases.jsonl`. P6 shows no orphan on
  the success path.
- **Concurrent writers to `cases.jsonl`:** repo-wide, the only writers are
  `ProjectStore.add_case` (append), `update_case` (whole-file upsert) and the new `delete_case`
  (whole-file rewrite). Grep over `src/` and `scripts/` for `add_case`/`append_jsonl` finds
  `scripts/bench_trial.py:118`, `scripts/regression_proof.py:147`,
  `scripts/run_pathlynks_first_cases.py:161` and `ui/routes_cases.py:188` — all via `add_case`.
  There is no in-process concurrency (each UI request builds its own `ProjectStore`), and no
  background writer. A human running one of those CLI scripts *while* clicking Delete in the UI
  is the only window in which the rewrite could drop a just-appended row — a pre-existing property
  of `upsert_jsonl`, explicitly caveated in both docstrings, not introduced here. Filed as
  **AT-067** (low) so it is queued work rather than folklore.

### 2. Delete scope — past runs, verdicts and rubric survive — VERIFIED ON DISK

Seeded a project with two cases, a rubric keyed on the doomed case, a `Run`, a `RawResult` and a
`Verdict`, snapshotted every file under the root, deleted the case, re-snapshotted:

```
deleted: True
files removed: set()          <- not one file was deleted; only a JSONL row went away
rubric survives: True
results survive: ['case_396680a92658']
verdicts survive: ['case_396680a92658']
remaining cases: ['o']        <- the sibling case untouched
```

The manifest's claim that history is deliberately left attached is literally true: **zero files
are removed**, the only change is one line dropped from `cases.jsonl`.

### 3. Rename preserves identity, and cannot rewrite the id payload — VERIFIED

- `Case.compute_id()` (`schema/case.py:38-45`) hashes `(project, flow_id, case_class, steps)`;
  `title` is not in the payload. Probe: `compute_id()` before and after a rename are equal, the
  stored `id` is unchanged, and the row count stays 1 (`update_case` replaces, never appends).
- Persisted rubric and past run artifacts still resolve — they are keyed on the id, which survives
  (item 2 above shows the rubric/result/verdict all still load by that id).
- **Field-injection probe against the live app.** `POST /projects/probescratch/cases/<id>/rename`
  with `title=Renamed OK` **plus** `case_class=edge`, `id=case_hijacked`, `project=other`,
  `flow_id=hijack`, `steps=[]`, `step_target=https://evil.test` returned 303, and the on-disk row
  afterwards was:

  ```
  {"id":"case_dec10e84860e","project":"probescratch","flow_id":"manual","kind":"best",
   "case_class":"happy","title":"Renamed OK", "steps":[{"order":1,"action":"navigate",
   "target":"https://probe.test/x", ...}]}
  ```

  Every injected field is inert. Structurally so: the route signature takes only
  `title: str = Form(...)` and applies it through `case.model_copy(update={"title": ...})` on a
  case loaded from disk — no other form key is ever read.

### 4. The `_case_ids` cache — CONSISTENT, but the manifest's test does not prove it

- `update_case` adds the id; `delete_case` discards it only when a row was actually removed.
- Probe within **one** `ProjectStore` instance (the only way the cache is observable):

  ```
  P7a has_case after add: True
  P7b delete: True   has_case after delete: False
  P7c re-added case has the same id: True
  P7d re-add in the SAME store instance -> ['B']    <- the row really came back
  P8  update_case: 1 row, id kept, title 'renamed', cache still has the id
  ```

  So the behaviour the manifest claims is real — I verified it directly.
- **However**, `test_deleting_then_re_adding_the_same_steps_works` does **not** exercise the cache:
  every UI request builds a fresh `ProjectStore` in `helpers.py:73` (`store = ProjectStore(slug)`),
  so `_case_ids` is `None` at the start of each request and is repopulated from disk. That test
  would pass byte-identically even if `delete_case` never touched `_case_ids`. The manifest's
  sentence ("which is what proves `delete_case` genuinely clears the id cache") overstates it.
  Filed as **AT-066** (low, test-coverage gap). Not a criterion failure — no ui.md criterion
  governs test proof-value, and the behaviour itself is correct.

### 5. U5 escaping on the new list page, and `_require_safe_id` — VERIFIED LIVE

Created a scratch project and a case titled `<script>alert(1)</script>&'"quote`, then fetched
`GET /projects/probescratch/cases`:

```
value='&lt;script&gt;alert(1)&lt;/script&gt;&amp;&#x27;&quot;quote'
count of raw "<script>alert" in the page: 0
```

The single quote is `&#x27;` and the double quote `&quot;`, so the `value='…'` attribute cannot be
broken out of. Form action URLs are built from `escape(slug)` (already `_require_slug`
regex-validated) and `escape(case.id)`.

Path-traversal probes on **both** mutating routes:

| Probe | rename | delete |
|---|---|---|
| `..%2F..%2Fetc` (encoded slashes) | 404 (no route match) | 404 |
| `a.b` (a dot — reaches the validator) | **400 `{"detail":"invalid case id"}`** | **400 `{"detail":"invalid case id"}`** |
| `%2e%2e` | 404 | 404 |

`_require_safe_id` (`helpers.py:33`, `^[A-Za-z0-9_-]+$`) genuinely fires on both routes. It is
defence-in-depth here — the case id is only compared against ids read from JSONL, never used as a
path component — but it is present and effective.

### Remaining criteria re-verified as unaffected

- **U1** — onboarding untouched; `POST /onboard` for the scratch project still wrote a real
  `projects/<slug>/project.json` (303). No second store.
- **U2** — `cases_list` and the project page both build a `ProjectStore` per request and read
  live; `GET /projects/erp` renders `1 / Cases` and the enabled **Run tests** button; an unknown
  slug still 404s via `_load_project_or_404`.
- **U3** — `routes_cases.py` contains no reference to `SecretStore`, `env_editor` or `.env`
  (grep: none). No credential surface touched.
- **U4** — no run/report code in the diff (`git diff --stat`: filestore, project_store,
  routes_cases, app.py +1 line, theme_style, tests, MAP.md).
- **U6** — creation still works end to end; the 400/400/400/400/404 refusals are covered by the
  19 passing tests. The AT-060 half of U6's spirit is now genuinely fixed: re-posting identical
  steps with a new title returns **HTTP 400** naming the *current* title —
  `"this project already has a case with exactly these steps: 'Renamed OK'. Change a step to make
  it a different case, or rename the existing one from the cases list."` — reproduced live, not
  pasted. The empty-state prompt and `+ Add case` are both still on the project page.
- **U7** — `routes_project_edit.py` untouched; the onboarding validator still ran on my scratch
  project (a self-consistent base_url/allowed_domains pair onboarded fine).

## Ledger

- **AT-060** (`open`) → `fixed`. The unit's claimed issue is genuinely addressed, verified live.
- **AT-066** (new, low) — `test_deleting_then_re_adding_the_same_steps_works` cannot exercise the
  `_case_ids` cache it claims to prove.
- **AT-067** (new, low) — whole-file rewrite (`delete_case`/`update_case`) vs a concurrent CLI
  `add_case` append can drop the appended row; pre-existing, documented caveat, no in-process
  concurrency today.

## Source-commit confirmation (AT-055 lesson)

At check time the maker's source changes were **uncommitted working-tree state**
(`git status --porcelain` showed `src/autotester/store/filestore.py`,
`src/autotester/store/project_store.py`, `src/autotester/ui/routes_cases.py`,
`src/autotester/ui/app.py`, `src/autotester/ui/theme_style.py`, `tests/test_ui_cases.py`,
`docs/MAP.md` modified and `tests/test_ui_case_management.py`,
`qa/manifests/ui-case-management.md` untracked). **The checker committed them itself** with a
narrow pathspec covering exactly those nine paths — `projects/` runtime data and `.work/` were
deliberately excluded and left untracked.

## Cleanup

The scratch project `projects/probescratch/` created for the hostile probes was removed, as were
all `.work/` probe files. `projects/erp` was read only — its single real case
(`case_27256e2a2b8d`, "Sign-in page loads and shows the login form") is untouched and still on
disk.
