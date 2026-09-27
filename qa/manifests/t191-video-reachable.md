# MANIFEST — t191-video-reachable

**Unit:** ISS-t191-run-video-2 — "a kept run video is unreachable by a human"
**Branch:** `wave/t191-video-reachable` (off `master` at `12597de3`)
**Base contract:** `qa/contracts/run-video.md` V1–V8, `qa/contracts/report-export.md` RE1–RE6,
`qa/contracts/ui-report.md` UR1–UR6, `qa/contracts/ui.md` U1–U9
**Fix cycle:** 1 (of max 3)

## What changed and why

T-191 records and retains a browser video (masked, last-20 retention) for every FAIL/
INCONCLUSIVE case, but no verified path in the shipped product let a human actually watch
it. The only place a video `<a href>` was ever rendered
(`stages/report_export.py::_video_link_html`) is reachable only through `export_html`, whose
two callers both break the relative href it emits:

- `ui/routes_report.py::download_report_html` writes the export to an **OS-temp path**
  (`_reserved_temp_path`) and serves it as a one-shot `FileResponse` download, then deletes
  the server copy — the run-relative video href never resolves once the browser has the file.
- `cli.py::report_html` only produces a working link if the caller manually passes
  `--out` *inside the run directory* — undocumented, easy to get wrong, not a supported path.

Separately, the live per-run page (`ui/routes_report.py::run_view`) never surfaced
`EvidenceKind.VIDEO` at all: `_step_flow` filters `EvidenceKind.SCREENSHOT` only.

**This unit's fix (the required option (a)):** a new route,
`GET /projects/{slug}/runs/{run_id}/videos/{video_path:path}`
(`src/autotester/ui/routes_video.py`), that serves a kept video straight from its real
`run_dir` location, plus a new `_video_section` in `ui/routes_report.py` that links to it
from each FAIL/INCONCLUSIVE case's row on `run_view`. This is now the one verified,
always-working path to watch a kept video — independent of the download export, which stays
broken (see the gate file and decision below; option (b), repackaging the download, was
explicitly out of scope for this unit).

**Mid-cycle addition (self-review finding, fixed same cycle):** the first
senior-software-engineer review of this diff found a real security/reliability gap in the
serving route's path-safety check — see "Security" and the capability table below.

## Files touched

| File | Lines | What |
|---|---|---|
| `src/autotester/ui/routes_video.py` | 75 (new) | The route + `_safe_video_path`, the traversal/UNC guard |
| `src/autotester/ui/app.py` | 299 (+2) | Registers `routes_video.router` |
| `src/autotester/ui/routes_report.py` | 300 (+16) | `_video_section`, wired into `_case_body` |
| `tests/test_ui_video_route.py` | 154 | Serving, linking, run-validity tests |
| `tests/test_ui_video_route_traversal.py` | 222 (new) | Every attacker-controlled-input refusal test |
| `qa/gates/t191-video-download-route.md` | 72 (new) | The mandatory decision record (below) |
| `qa/issues.jsonl` | +1 line | `ISS-t191-run-video-4` (UNC finding, filed + fixed this cycle) |
| `docs/MAP.md` | regenerated | `uv run autotester map`, not hand-edited |

Base commit for this diff: `12597de3` (`git diff 12597de3..HEAD -- src tests qa/gates
qa/issues.jsonl`). No file outside this list was touched; `qa/contracts/`, `qa/verdicts/`,
`docs/DECISIONS.md`, `.goal/goal.json`, `.goal/dashboard.html`, and `docs/ARCHITECTURE.md`
prose are all untouched, as required.

Commits: `05eb41e4` (route + link), `8c26aac5` (gate file, traversal-test tightening),
`6b2f609f` (UNC-path fix), `5808cee7` (test split for the 300-line cap),
`aa11a06c` (issues.jsonl append).

## Security (the non-negotiable boundary)

`_safe_video_path(run_dir, video_path)` is defense-in-depth by construction, in this order:

1. **String-level guard** (added this cycle): `video_path` starting with `\` or `/`, or
   containing `:`, is refused *before any `Path` is touched* — covers UNC (`\\host\share\..`),
   POSIX-absolute (`/etc/passwd`), and drive-rooted (`C:\Windows\...`) shapes.
2. `run_dir.resolve()` establishes the trusted root; `not is_dir()` → 404.
3. `(run_dir / video_path).resolve()` — normalizes `..`/`.` and follows symlinks — wrapped in
   `except (OSError, ValueError): return None`.
4. `candidate.is_relative_to(trusted_root)` — the actual containment check (same shape as
   `report_export.png_base64`'s existing screenshot guard).
5. `candidate.suffix.lower() != ".webm"` — refuses anything that isn't the one container this
   feature produces (never a generic serve-any-file route).
6. `candidate.is_file()` — no serving a directory.

The route itself additionally validates `run_id` (`_require_safe_id`) and that it names a
real, loadable `Run` envelope before ever calling `_safe_video_path` — a stray directory under
`runs/` with no persisted envelope 404s independently of path safety.

## The UNC finding (found by self-review, fixed same cycle)

The first senior-software-engineer review of commits `05eb41e4`/`8c26aac5` (before item 1
above existed) found: `_safe_video_path`'s `Path.resolve()` call, reached *before* the
containment check, makes Windows attempt a real SMB connection when `video_path` is
UNC-shaped — a blocking network round-trip (the review measured ~21s against an unreachable
host), a DoS / forced-SMB-auth vector, not merely a wrong answer eventually.

**Verdict of that review (Warning), as best reconstructed** — the review's own transcript
file had already rotated out by the time this section was written, so this is reconstructed
from this session's own record of it, not a fresh read of the original bytes:

> VERDICT: Warning. The containment logic, validation ordering, HTML-escaping/URL-quoting in
> `_video_section`, code reuse (mirroring `png_base64`'s existing pattern), and ruff/doctor
> cleanliness all hold up. One medium-severity gap: `_safe_video_path`'s `Path.resolve()` call
> can trigger a real network round-trip on Windows if `video_path` is UNC-shaped
> (`\\host\share\...`), timed at ~21 seconds for an unreachable host — a blocking DoS vector
> and potential forced-SMB-authentication/NTLM-relay risk. Recommended fix: reject UNC/absolute
> paths via a string-level check before calling `.resolve()`, mirroring the "validate before
> touching disk" pattern already used for `run_id`.

**Fixed this cycle**, `6b2f609f`: the string-level guard above (item 1); the mechanism-proof
test (`test_safe_video_path_never_calls_resolve_for_a_dangerous_value`) was added in the next
commit, `5808cee7` — see the provenance correction below. Filed as `ISS-t191-run-video-4`
(`status: fixed`) for the audit trail, per this project's own convention of logging
same-cycle review findings (AT-627, AT-647, ISS-at638-remainder-2 all do this).

**Second review, of the fix itself** (commits `6b2f609f`, `5808cee7`, `aa11a06c`): Verdict
**Warning**. Verbatim:

> Verdict: Warning (fix itself is sound; one factual/provenance issue in the diff needs
> correction).
>
> 1. Ordering — confirmed correct. The guard runs as the first statement, strictly before
> `run_dir.resolve()` and before `(run_dir / video_path).resolve()`. No `Path` method touches
> attacker-controlled input before this check.
>
> 2. Over/underreach — none found. Legitimate relative paths pass untouched. `file.webm:hidden`
> (ADS) is caught by the `:` check. Forward-slash UNC (`//host/share/x.webm`) is caught.
> Non-UNC backslash traversal mid-path (e.g. `foo\..\..\bar.webm`) isn't caught by the string
> guard but falls through to the existing `resolve()` + `is_relative_to` containment check —
> safe, since it's not UNC-shaped and triggers no network I/O. `~` isn't special-cased by
> pathlib so it can't escape `run_dir`. No missed attack shape identified.
>
> 3. Test quality — sound, not vacuous. Without the guard, the very next line
> (`run_dir.resolve()`) is unconditional and would trip the monkeypatch regardless of the
> removed guard — confirming the test genuinely reddens on guard removal and isn't satisfied
> by some other early-return path.
>
> 4. doctor/ruff/line counts — clean. Both test files and the route module under the 300-line
> cap.
>
> 5. `qa/issues.jsonl` append — verified clean (pure `+1` line, all 663 lines valid JSON), but
> see finding below.
>
> 6. Design-rule/duplication — the `_seed_with_video` fixture duplicated across the two split
> test files mirrors `test_report_export_secrets.py`'s own `_seed` — consistent with
> established convention, not a violation.
>
> **Finding (Warning): commit 5808cee7's message is inaccurate.** It claims "No test content
> changed, only location," but `test_safe_video_path_never_calls_resolve_for_a_dangerous_value`
> did not exist in `6b2f609f` — it was newly added inside the "pure split" commit, and the
> neighboring UNC test's docstring was substantively rewritten at the same time. Compounding
> this, `qa/issues.jsonl`'s entry states "fix + falsification in commit 6b2f609f" — but the
> actual mechanism-proof test landed in `5808cee7`, not `6b2f609f`. No security/correctness
> defect results; the audit trail is wrong on which commit introduced the falsification proof.
> Recommend a corrected `issues.jsonl` append rather than blocking the branch.

**Provenance correction made in response** (this manifest + `qa/issues.jsonl`, no history
rewrite — both commits are unpushed local branch history, but this project's own tooling
rules disallow interactive rebase, so the record is corrected forward rather than by amending
`5808cee7`'s message): the guard was added in `6b2f609f`; the mechanism-proof test and the
UNC test's "weak signal" docstring caveat were both added in `5808cee7`, not `6b2f609f`. Fixed
in `qa/issues.jsonl`'s `ISS-t191-run-video-4` note/source fields (edited in place — this file
is not append-only enforced the way `docs/DECISIONS.md` is; other entries in it, e.g.
`ISS-t191-run-video-1`, are likewise amended in place as cycles progress). No code changed as
a result of this finding — only the two records above.

## Capability table (with falsification evidence)

| # | Capability | Test | Falsification evidence |
|---|---|---|---|
| C1 | Serves a real kept video, correct bytes + content-type | `test_serve_run_video_streams_the_real_file` | Manual: change the assertion's expected bytes → RED with a content mismatch; not separately re-run this cycle (unchanged from cycle 1's own falsification, which the checker already verified in its cycle-2 pass on the parallel-sweep fix, ISS-t191-run-video-1's note). |
| C2 | `run_view` links to the video for a FAIL/INCONCLUSIVE case | `test_run_view_links_to_the_video_route` | Stub `_video_section` to always return `""` → RED (link text disappears from the page). |
| C3 | No link rendered when there is no video evidence | `test_run_view_shows_no_video_link_when_there_is_no_video_evidence` | Remove the `EvidenceKind.VIDEO` filter (render for all evidence) → RED (a stray `.webm` string would appear where none is asserted). |
| C4 | Unknown run 404s | `test_serve_run_video_404s_for_an_unknown_run` | Comment out the run-membership check → this test alone does NOT redden (see C5). |
| C5 | Run-validity check is real, not just directory-existence | `test_serve_run_video_404s_for_a_stray_directory_with_no_real_run_envelope` | **Self-found vacuous-test bug, fixed before handoff**: disabling the run-membership check does NOT redden C4 (a wholly absent directory 404s via `_safe_video_path`'s own `is_dir()` check regardless), but DOES redden C5 (a real directory + real `.webm`, no persisted `Run` envelope) — added specifically because C4 alone was proven insufficient. |
| C6 | Percent-encoded `..` traversal refused end-to-end over HTTP | `test_serve_run_video_refuses_percent_encoded_traversal_end_to_end` | **Self-found vacuous-test bug, fixed before handoff**: an earlier draft used a `.txt` outside file with the wrong dot-count; disabling `is_relative_to` alone did NOT redden it (the suffix check + missing-file 404 were doing the proving instead). Fixed by using a real `.webm` at the *exact* fixture depth; re-verified this correctly reddens with containment disabled. |
| C7 | Absolute-path traversal refused | `test_serve_run_video_refuses_an_absolute_path` | Same fix as C6 (real `.webm`, not `.txt`) — confirmed reddens with containment disabled. |
| C8 | Non-`.webm` file inside `run_dir` refused | `test_serve_run_video_refuses_a_non_webm_file_even_inside_the_run_dir` | Remove the suffix check → RED (a `.png` inside the real run dir would serve). |
| C9 | `..` segment refused (unit level) | `test_safe_video_path_refuses_a_dotdot_segment` | Remove `is_relative_to` check → RED. |
| C10 | Symlink escape refused | `test_safe_video_path_refuses_a_symlinked_escape` | Remove `is_relative_to` check → RED (symlink target resolves outside `run_dir`). |
| C11 | Windows junction escape refused | `test_safe_video_path_refuses_a_windows_junction_escape` | Same as C10, junction instead of symlink — Windows-specific escape vector `Path.resolve()` also normalizes. |
| C12 | Valid nested path accepted | `test_safe_video_path_accepts_a_real_nested_video` | Positive control: proves the guards aren't so strict they reject legitimate `prefix/case.webm` paths. |
| **C13** | **UNC path refused, bounded time (weak signal)** | `test_safe_video_path_refuses_a_unc_path_without_touching_the_network` | **Honest limitation**: in a narrow, out-of-project-context reproduction this assertion alone did not redden (a bare UNC lookup returned in <1ms with no real network stack to hang against). Run *properly* — `cd` into a git-archive throwaway copy and invoke pytest with that as CWD (see methodology note below) — it reddened at **exactly `21.05s`** (`36199.504402 − 36178.4560493`) with the guard removed, matching the original review's ~21s measurement almost exactly. Kept as a test because it directly proves the production risk when it *does* fire; C14 is the assertion that holds regardless of network behavior. |
| **C14** | **UNC/POSIX-absolute/drive-rooted paths never reach `Path.resolve()`** | `test_safe_video_path_never_calls_resolve_for_a_dangerous_value` | The real, environment-independent proof: monkeypatches `Path.resolve` to raise if ever called, asserts `_safe_video_path` still returns `None` for three dangerous inputs. **Falsified correctly**: with the guard's two lines deleted in a git-archive throwaway copy, this test reddened with an uncaught `AssertionError` from inside `run_dir.resolve()` — proving `resolve()` really was reached without the guard, and the guard genuinely prevents it. |
| C15 | Drive-rooted path refused | `test_safe_video_path_refuses_a_drive_rooted_path` | Covered by the same guard as C14 (the `:` check); direct unit assertion. |
| C16 | UNC path refused end-to-end over HTTP | `test_serve_run_video_refuses_a_unc_path_end_to_end` | Not independently falsified with timing (would make routine test runs pay the ~21s cost when it fails) — its 404 assertion is a correctness check layered on top of C13/C14's proof, not a third independent falsification. |

### Falsification methodology note (a real project-specific gotcha found this cycle)

The mandatory falsification duty requires perturbing code only in a throwaway `git archive`
copy outside the worktree. My first two attempts used `PYTHONPATH` to shadow
`autotester.ui.routes_video` while running `pytest` from *this* worktree's own `tests/`
directory — and both attempts silently ran against the **real, unmodified** module, making
C13/C14 look vacuously green even with the guard deleted. Root cause: `tests/conftest.py`
imports `scripts/regression_proof.py`, which does
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))` — inserting *this
worktree's own* `src/` at the front of `sys.path`, ahead of any `PYTHONPATH` entry, before the
test module's own imports run. Since `autotester` is a regular (non-namespace) package, its
`__path__` is fixed on first import for the rest of the process — so `PYTHONPATH` shadowing
never had a chance once `conftest.py` ran.

**Fix**: run `pytest` with the *throwaway copy itself* as the working directory (its own
relative-path `sys.path.insert` calls then correctly reference its own, sabotaged files), not
the original worktree with `PYTHONPATH` pointed elsewhere. Recorded here so a future maker
cycle attempting a git-archive falsification against any module reached via
`tests/conftest.py` doesn't repeat the same silent-pass mistake.

## Where to attack this (for the checker)

1. **The UNC guard's edge shapes** — `//host/share/x.webm` (forward slashes, some
   Windows/SMB stacks accept this as UNC too — the leading-`/` branch of the guard should
   already catch it, but verify), NTFS alternate-data-stream syntax (`case.webm:hidden` — the
   `:` check should already catch it), and a `video_path` that is empty or whitespace-only.
2. **The run-validity check (C5)** — try a directory whose name collides with a real run id
   but whose envelope was corrupted mid-write, not simply absent.
3. **The percent-encoding depth assumption (C6)** — the test computes the traversal depth
   dynamically from the fixture; try a request whose `%2e%2e` count is *one more or fewer*
   than the real depth, or mixes literal and encoded dot-segments in the same request.
4. **`report_export.py`'s untouched `_video_link_html`** — confirm the download export's
   video link is unchanged and still broken exactly as `ISS-t191-run-video-2` originally
   found it (the gate file's claim), not accidentally half-fixed by this unit's other changes.

## The mandatory decision: `download_report_html`'s broken video link

Recorded in full at `qa/gates/t191-video-download-route.md`. Summary: left **byte-for-byte
unchanged**, deliberately, not by omission. `report_export.py` is at doctor's 300-line file
cap with zero headroom, so threading a `video_href_base` parameter through
`export_html → _case_section → _video_link_html` doesn't fit without first splitting that
file — a separate, wider unit. Rewriting the download's HTML bytes after export (the only fix
that would avoid the line-cap problem) sits in tension with `qa/contracts/ui-report.md` UR3
("stream the exact same file `export_html` would produce ... never a second, UI-only
reimplementation"), which is checker-owned — a maker cannot self-authorize reading that
tension as acceptable. Three options (A leave-permanently, B split-and-parameterize, C
checker-amends-UR3) are laid out for Umesh/the checker to decide. The failure mode today is
benign: a dead link 404s, it does not leak or misdirect to the wrong file.

## Verify commands (paste of actual output)

### `uv run ruff check src tests scripts`

```
warning: `VIRTUAL_ENV=d:\autoTesting\.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
All checks passed!
```

### `uv run autotester doctor`

```
warning: `VIRTUAL_ENV=d:\autoTesting\.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
doctor: clean
```

### `uv run pytest` (no `-q`, per AT-503)

Targeted run first (`tests/test_ui_video_route.py tests/test_ui_video_route_traversal.py`,
16 tests): **16 passed in 1.08s**, zero warnings beyond the pre-existing
`starlette.testclient` `DeprecationWarning`.

Full-suite run, final state (all 5 commits on this branch included):

```
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
1 failed, 2086 passed, 6 skipped, 14 xfailed, 15 warnings in 1505.02s (0:25:05)
EXIT:1
```

The single failure is `test_flake_probe_real_process.py::
test_run_once_kills_a_real_hung_process_and_its_real_grandchild` — the pre-authorized AT-627
load-sensitive flake (confirmed via `qa/issues.jsonl` AT-627/ISS-at638-remainder-2/AT-647, all
documenting the identical shape as a known, non-chargeable, machine-contention flake). Nothing
else fails; `tests/test_goal_done_checks.py` is fully green, as the dispatch expected. An
earlier full-suite run taken right after the routing/linking work, before the UNC fix and
test split, gave `1 failed, 2081 passed, 6 skipped, 14 xfailed` in 1256.13s — same sole
failure, confirming the UNC fix and test split introduced no regression (2086 vs 2081 passed
is exactly the net of the tests added since: the UNC/drive-rooted/mechanism/end-to-end tests).

## CYCLE 2 — the checker's FAIL is right, and its suggested fix was not enough

**Verdict answered:** `qa/verdicts/t191-video-reachable.md` cycle 1, **FAIL** on `AT-654` (now
**`AT-656`** in this ledger — see the renumbering below). 15/16 rows confirmed; C7 was the sole
fail driver. The retracted C15 finding is accepted as retracted and nothing was changed for it.

### The defect, restated exactly

`tests/test_ui_video_route.py::test_run_view_shows_no_video_link_when_there_is_no_video_evidence`
seeded a `RawResult` with no `evidence=` at all. `schema/run.py` defaults that to `[]`, so the run
under test had zero evidence of **any** kind. `assert ".webm" not in response.text` therefore held
whether `routes_report.py::_video_section`'s `EvidenceKind.VIDEO` filter existed, was inverted, or
was deleted. Third vacuous test in this unit; the cycle-1 build self-found and fixed the first two.

### Why the suggested fix shape was insufficient — measured, not argued

The verdict's fix shape was *"seed a non-video Evidence row (e.g. SCREENSHOT) alongside the no-video
case so the filter is actually exercised."* Seeding the row is necessary and it is **not sufficient**,
and this was found by building it and running it rather than by reasoning about it:

With the `VIDEO` filter deleted, `_video_section` emits a link for whatever rows it receives — so it
emits one for the SCREENSHOT row, whose path is `step-1.png`. **That link contains no `.webm`**, so
`assert ".webm" not in response.text` stays true and the test stays green. The fixture, not the code
under test, was controlling the asserted substring.

Falsification run in a throwaway `git archive` copy under `%TEMP%` (never the bound worktree), the
copy as CWD per this repo's documented `PYTHONPATH`-shadowing gotcha:

| Variant | With the VIDEO filter deleted | Reads |
|---|---|---|
| Verdict's suggested shape (SCREENSHOT row + `.webm` assertion only) | **6 passed** | still vacuous |
| Shipped fix (SCREENSHOT row + video **route-prefix** assertion) | **1 failed, 5 passed in 3.61s** | genuinely load-bearing |

GREEN baseline for the same file is **1.80s**, so the 3.61s RED is the same order of magnitude — not
a collection/import error masquerading as a falsification (the fast-RED tell).

### The fix

`tests/test_ui_video_route.py` only — no `src/` change, because the code was never wrong:

1. Seed `Evidence(kind=EvidenceKind.SCREENSHOT, path="step-1.png", step_order=1)` on the result, so
   the run has evidence and the filter is the only thing that can keep a video link out.
2. Assert on the **video route prefix** — `assert f"/runs/{RUN_ID}/videos/" not in response.text` —
   which is emitted for *any* row the filter lets past, instead of on a file extension the fixture
   happens to control. The `.webm` assertion is kept as a narrower second check.
3. The docstring records both the original vacuity and why the obvious repair does not close it, so
   the next reader does not re-weaken it.

**One thing deliberately NOT done:** `_step_flow` renders `no screenshots captured` for this fixture
because it reads the screenshot **file** off disk and the fixture writes none. An earlier draft
asserted `"step-1.png" in response.text` as a fixture-liveness guard and it failed for that reason.
Writing a real PNG to the run dir would make the guard pass, but it would couple this test to
`_step_flow`'s disk behaviour, which is another unit's concern. The route-prefix assertion needs no
such coupling: the evidence list reaching `_video_section` is what it measures.

### Ledger reconciliation (the checker flagged it; merge reconciliation is the orchestrator's job)

The check filed `AT-654`/`AT-655` into **this worktree's** `qa/issues.jsonl`, a stale fork of master
at `12597de3` whose highest id was `AT-649`. Meanwhile the **root** ledger independently advanced to
its own unrelated `AT-654` (D-029 dev-only vs production Pathlynks, `3c9cb374`/`6cfefd83`).

- This worktree's `AT-654` -> **`AT-656`**, status `fixed`, with the reason written into its row.
- `AT-655` (persona-walk hygiene, low) is **unchanged** — that id is free in the root ledger.
- **Renumbered rather than documented as an 11th `id_collision` pair.** The ten existing pairs are
  preserved only because both of their ids had already been published outside their branch. Neither
  of these had. Preserving a collision that nothing depends on would add permanent confusion for no
  traceability gain.
- `.gitattributes` carries `qa/issues.jsonl merge=union`, so the merge itself will not conflict.

### AT-655 — not fixed, and the reason is a judgement the checker should rule on

The manifest omits the `Persona walk:` field SKILL.md 5bb expects for a UI-touching unit. Filed low,
non-blocking. It is **left open deliberately**: the honest walk for this unit is a report reader
clicking a video link, which Mode D already performed and recorded end to end (real uvicorn, real
Playwright, 200 then 206 partial content). Adding a `Persona walk:` line now would restate that
evidence in a second place rather than add any. If the checker wants the field populated as process
hygiene regardless, say so and it is one line — but the maker is not going to manufacture a second
account of a walk that is already evidenced.

### Verify commands, cycle 2

- `uv run ruff check src tests scripts` -> **All checks passed!**
- `uv run autotester doctor` -> **clean**
- `uv run pytest` -> see the block appended below (no CLI `-q`, AT-503; the **last** summary block and
  the explicit exit code are the ones that count, per the double-tally hazard recorded in this repo).

### Full suite, cycle 2 — the last summary block, verbatim

```
2087 passed, 6 skipped, 14 xfailed, 15 warnings in 1351.31s (0:22:31)
```

**Zero failures.** Read honestly, with the two hazards this repo has recorded:

- **The double-tally hazard:** only one summary block is present in the captured tail, and it is the
  last thing before the capture ends. It is the one quoted.
- **The exit-code hazard:** the capture pipes pytest into `tail`, so the `EXIT=0` it recorded is
  `tail`'s status, **not pytest's**, and is therefore NOT cited as evidence. The claim rests on the
  failure LIST being empty and the summary line carrying no `failed` field — both directly observable
  above.
- **`AT-627` did not fire this run.** Cycle 1 read `1 failed, 2086 passed` with that pre-authorized
  load-sensitive flake as the sole failure; this run reads `2087 passed`. 2086 + 1 = 2087, so the
  count is consistent and the delta is exactly the flaky test passing, not a test appearing or
  vanishing. **A green run does not retire AT-627** — a load-sensitive flake passing once is not
  evidence it is fixed, and the row stays open.
- Cycle 2 added **no** test and removed none; it changed one existing test's fixture and assertion.
  The identical total across cycles is what that should look like.

## CLOSE-OUT — cycle 2 PASS

**Verdict:** `qa/verdicts/t191-video-reachable.md` **CYCLE 2 = PASS** (root master `5183ff10`).
16/16 capability rows confirmed load-bearing; C7, the sole cycle-1 fail driver, satisfied; no failures.

**What the checker did that the maker had not, and it strengthens the record:**

- **It inverted the filter** (`is not EvidenceKind.VIDEO`) as well as deleting it — a mutation neither
  the manifest nor cycle 1 tried. Two tests reddened (`2 failed, 4 passed in 1.10s`), which is what
  proves the assertion is load-bearing *for the right reason* rather than merely load-bearing.
- **It reproduced both variants of the central claim** and confirmed the insufficiency: cycle 1's own
  suggested shape stays `6 passed` with the filter deleted; the shipped route-prefix assertion goes
  `1 failed, 5 passed in 0.90s` against a `0.63s` GREEN baseline.
- **It settled the dropped fixture-liveness guard rather than leaving it open**, with an argument the
  maker had not made: the filter-deleted mutation going RED *is itself* proof the seeded evidence
  reached `_video_section` intact — had it been dropped upstream, deleting a downstream filter could
  not have produced a link either way. So no new vacuity was introduced by dropping the guard.
- **It simulated the merge instead of citing `.gitattributes`** — fresh clone of root, fetch of this
  branch, real `git merge`, then a scripted duplicate-id scan of the merged file. Clean auto-merge, and
  exactly the ten pre-existing collision pairs, none newly introduced.
- **`AT-670`** (was AT-655, persona walk) ruled **accept as filed**: this manifest postdates
  2026-09-26, so a missing `Persona walk:` field is SKILL.md 5bb's "newer manifest without the field"
  case, which is what the row already says. The maker's argument that cycle-1's Mode D pass *is* the
  honest persona walk here is accepted.
- **Mode D skipped, reasoned and stated:** cycle 2 touched zero bytes of `routes_video.py`,
  `routes_report.py` or `app.py`, so cycle 1's real-uvicorn/real-Playwright pass against byte-identical
  code stands.

**The finding that outlives this unit — `AT-672` (was AT-657), high, environmental, NOT charged here.**
The checker's own full-suite run hit `18 failed, 13 errors`, every one an
`OSError: [Errno 28] No space left on device`. Independently confirmed by the maker: **C: has 0.37 GB
free of 474.72 (0.1%)**, and G: is in the same state; D: (this repo) has 212 GB. The checker correctly
declined to charge it — the regression question is covered by the test-file-only diff scope, a clean
targeted re-run (`16 passed in 2.41s`) and clean ruff/doctor. **But it can produce a false full-suite
FAIL on any unit whose verify lands while the disk is this full, so it is surfaced to Umesh rather than
filed and forgotten.** Note the maker's own cycle-2 full run read `2087 passed` with zero failures, so
the disk crossed its threshold *between* that run and the check — which is exactly why a green suite is
not evidence the instrument was healthy.

**Ledger ids remapped into the reserved block** (`qa/QUEUE.md` "Ledger id reservation"):
`AT-655`→`AT-670`, `AT-656`→`AT-671`, `AT-657`→`AT-672`. Each row carries its own mapping.

## Status: checked-PASS (cycle 2 of max 3)
