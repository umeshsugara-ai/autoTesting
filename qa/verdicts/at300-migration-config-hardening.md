# VERDICT — at300-migration-config-hardening

**Date:** 2026-09-11
**Manifest:** `qa/manifests/at300-migration-config-hardening.md`
**Contract:** `qa/contracts/coverage.md` (V1) · `qa/contracts/core-invariants.md`
**Commit checked:** `8d30823`
**Cycle checked: 1**
**Checker:** fresh subagent, bound to `d:/autoTesting`, read-only toward the artifact.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met, 5/5 applicable invariants hold
FAILURES (if any): none
LIVE-BROWSER: not-applicable (changed paths: qa/, scripts/migrate_url_patterns.py,
              tests/test_migrate_url_patterns.py - no ui/, no src/; `grep -rn
              migrate_url_patterns src/ ui/` returns nothing; the script has no production
              caller and no request path reaches it). Mode D is NOT required for this unit.
ISSUES-WRITTEN: AT-307, AT-308, AT-309, AT-310 (all low) · AT-300..AT-304 closed to `fixed`
EXPLANATION: Every pasted output reproduced exactly, and the maker's central claim - that it
mutation-tested its own tests before submitting - is independently confirmed: I re-ran its
harness (4/4 KILLED) and then ran twelve mutations of my own that it did not write. No test in
this unit is vacuous for the property it names. The nine survivors of my own set are undefended
DEFENSIVE branches, not vacuous tests; each is behaviourally correct today (I probed all of them
directly) and each is filed rather than charged. The three judgements are ruled below; #2 is
upheld as accurate and now MEASURED rather than presumed, but declaring it is not sufficient on
its own - it is filed as AT-310 so it outlives the manifest.
```

---

## 1. THE CRUX — test non-vacuity, verified independently

### 1a. The maker's harness re-run by me (not read)

`uv run python qa/evidence/at300-migration-config-hardening/mutation_harness.py` — exit 0,
reproduced verbatim including the per-mutation FAILED test names:

```
BASELINE: exit=0  21 passed in 0.19s
M1 allowed_domains list-guard removed      KILLED  1 failed  - test_allowed_domains_given_as_a_string_contributes_no_hosts
M2 hostname/port reverted to netloc.split  KILLED  2 failed  - test_base_url_userinfo_is_not_treated_as_a_host
                                                             - test_an_ipv6_base_url_does_not_declare_a_bracket_as_a_host
M3 port fallback in repair removed         KILLED  1 failed  - test_a_pattern_carrying_a_port_matches_a_host_declared_without_one
M4 _project_dir_of reverted to depth-1     KILLED  1 failed  - test_a_nested_artifact_under_a_flat_root_is_still_judged_by_its_project
target restored byte-identically; live repo never touched
```

**Is the harness itself rigged?** Audited against C7's clauses:

| Property | Present? |
|---|---|
| Anchor asserted to match **exactly once** | YES - `assert ORIGINAL.count(old) == 1` before every patch |
| File asserted to have **actually changed** | YES - `assert TARGET.read_text() != ORIGINAL` |
| Restores, and **asserts** the restore | YES - per-mutation restore + final `assert ... == ORIGINAL` |
| Operates **outside** the repo | YES - `tempfile.mkdtemp` + `shutil.copytree`; `projects/erp/screenmap.json` hash identical before and after (section 4) |
| Named defending test actually the one that fails | YES - prints `FAILED` names; all four match their `defends` string |
| **Baseline asserted green** | NO - **the one hole.** `KILLED` is defined as `code != 0`, and the baseline is printed but never asserted. A red baseline (this repo has a documented flake, AT-196) would report *every* mutation KILLED. Not a false claim here - the baseline is genuinely green, and my own harness asserts it - but it is the same species of hole C7 already closed twice. Filed **AT-307**; C7 amended (section 6). |

The M4 self-catch is corroborated, not taken on trust: the rewritten test's own docstring names
the shape (`--root projects/erp` with the artifact in a subdirectory, `parts[0] == "crawl"`), and
M4 kills exactly that test. AT-303's own ledger row predicted this remedy; the shipped test
matches it.

### 1b. My own mutations — twelve, beyond the maker's four

Independent harness (baseline **asserted** green before believing anything; anchor-count,
changed-file and byte-identical-restore assertions as above), run against `8d30823`:

```
BASELINE asserted green: 21 passed
N7  list-guard widened to accept a STRING (AT-300 re-introduced)  KILLED  - test_allowed_domains_given_as_a_string_contributes_no_hosts
N8  _screens list-guard REMOVED                                   KILLED  - test_it_walks_past_json_that_uses_screens_for_something_else
N12 non-dict config guard REMOVED                                 KILLED  - test_a_non_dict_project_json_contributes_nothing
N1  ValueError guard on a bad authority REMOVED                   SURVIVED
N2  root-containment `break` REMOVED (walks above --root)         SURVIVED
N3  final `{h for h in hosts if h}` filter REMOVED                SURVIVED
N4  .strip()/.lower() on allowed_domains REMOVED                  SURVIVED
N5  pattern.startswith("/") guard REMOVED                         SURVIVED
N6  isinstance(base, str) guard REMOVED                           SURVIVED
N9  _project_dir_of fallback root -> path.parent                  SURVIVED
N10 project.json .is_file() -> .exists() (a DIRECTORY counts)     SURVIVED
N11 known_hosts json/OSError except REMOVED                       SURVIVED
```

**Ruling: no test in this unit is vacuous for its stated property.** Every property a test in this
unit is *named for* dies under the mutation that removes it — M1-M4 and N7/N8/N12 between them
cover `allowed_domains` type-guarding, `.hostname`/`.port` parsing, the port fallback in `repair`,
the upward walk in `_project_dir_of`, the `screens`-is-a-count guard and the non-dict config guard.

The nine survivors are a **different finding**: they are defensive branches for which *no test was
ever written or claimed*, so the honest label is "undefended", not "vacuous". Three deserve their
own rows because the manifest leans on them:

- **N1** — the manifest names the `ValueError` guard as part of the AT-301/AT-302 fix, and nothing
  tests it. It is real and load-bearing: without it a bad authority raises **out of** `known_hosts`
  and aborts the whole `scan` walk mid-migration. Behaviourally verified by me (section 2).
- **N2** — the `if parent == root: break` containment bound, undefended, in a repo whose
  AT-149/AT-150 history is precisely path containment. See section 2 for a real (if unreachable)
  hole in it.
- **N10/N11/N6** — `project.json` as a directory, as unreadable, and `base_url` as a non-string are
  all correct today and all deletable with the suite green.

Filed as **AT-308** (`known_hosts` guards) and **AT-309** (`_project_dir_of` containment). Precedent
for filing this shape as a residual rather than a FAIL: AT-261, and AT-303's own row.

---

## 2. Are the fixes correct? — direct hostile probing, not inference

`known_hosts` against 19 hostile/malformed configs (run directly against `8d30823`):

```
allowed_domains as DICT             -> []          allowed_domains list of INTS  -> []
allowed_domains list with NULL      -> ['ok.test'] allowed_domains NESTED list   -> []
base_url as NUMBER                  -> []          base_url as NULL              -> []
base_url port OUT OF RANGE (99999)  -> []          base_url port NEGATIVE (-1)   -> []
base_url port NON-NUMERIC (:abc)    -> []          base_url unclosed IPv6 ([::1  -> []
base_url schemeless                 -> []          base_url empty string         -> ['a.test']
IDN host (b<u-umlaut>cher.example)  -> ['b<u-umlaut>cher.example']
punycode host                       -> ['xn--bcher-kva.example']
trailing-dot host                   -> ['vidysea.com.']
UPPERCASE base_url                  -> ['www.vidysea.com']
UPPERCASE allowed_domains           -> ['www.vidysea.com']
allowed_domains with whitespace     -> ['pad.test']
```

Every malformed shape contributes **nothing** — the fail-safe direction the manifest claims, and
this time it holds (AT-300's whole complaint was that the previous claim did not).

- **Does the `ValueError` guard actually fire, and is `.port` what raises?** Yes to both, and it is
  broader than the manifest says. `.hostname` never raises; `.port` raises `ValueError` for an
  out-of-range, negative or non-numeric port, and `urlsplit` *itself* raises for an unclosed IPv6
  bracket — the `try` wraps both, so both are caught. The guard's effect is that a host with a bad
  port contributes **nothing at all** (not "the host without the port"): conservative, i.e. it
  under-repairs rather than eating a path. Correct, and untested (AT-308).
- **IDN / punycode / trailing dot / uppercase** — all handled in the safe direction. IDN and
  punycode are stored as written and never cross-match, so an IDN project would under-repair; a
  trailing-dot host likewise. No corruption path.

`_project_dir_of` and containment:

- **`project.json` above the root** — contained. With `root=<outer>/inner` and the config in
  `<outer>`, `_project_dir_of` returns `root`, `known_hosts` returns `set()`, and `scan` reports
  `{}`. The foreign project's hosts are **not** adopted.
- **`project.json` as a DIRECTORY** — `is_file()` refuses it, and `known_hosts` on that directory
  returns `set()` (the `OSError` arm). Both fail safe.
- **Symlinks / lexical escape** — `path.parent.parents` is lexical, so a followed symlink still
  yields a path textually under the root. **One real hole:** the `parent == root` bound is a
  *lexical* comparison, so a **relative** `root` combined with **absolute** paths never matches and
  the walk climbs to the filesystem root, adopting a foreign `project.json`'s hosts
  (`_project_dir_of(<abs>/outer/inner/screenmap.json, Path("inner")) -> <abs>/outer`). **Not
  reachable through `main()`**: `root.rglob` yields paths in the same form as `root`, so the CLI is
  always lexically consistent — I confirmed `scan(Path("inner"))` returns `{}` for that same tree.
  Filed **AT-309** (low) with the reachability stated honestly rather than dressed up.
- **`repair` edges** — `repair("vidysea.com/x")`, `repair("")`, `repair("//vidysea.com/x")` all
  return `None`; `repair("/VIDYSEA.COM/x", {"vidysea.com"}) == "/x"` (intended, candidate lowered).

---

## 3. Ruling on the three judgements offered

**#1 — AT-305 deliberately not fixed. UPHELD.** Leaving it is right, and the reasoning is the
correct one: fixing it means suffix matching, which is a *guess*, and this saga has now paid three
times for guessing host-ness. The residual is under-repair (a stale display), never corruption.
AT-305 stays `open` as a documentation correction with no code change.

**#2 — AT-302 is a knowingly PARTIAL fix. UPHELD AS ACCURATE, AND FILED. Declaring it is
necessary but not sufficient.** The maker wrote "presumably"; I measured it instead, and the
presumption is exactly right:

```
url_template('[::1]:8080/app', keep_host=False)  ->  '/[::1]:8080/app'   <- what the AT-287/294
                                                                            mangler would store
repair('/[::1]:8080/app', {'::1', '::1:8080'})   ->  None                <- NOT repaired
repair('/::1:8080/app',   {'::1', '::1:8080'})   ->  '/app'              <- only the bracketless
                                                                            form is repaired
```

So the false-positive half of AT-302 is genuinely fixed (`[` is no longer a declared host, and the
real host now is), while the true-positive half — repairing a *genuinely* mangled IPv6 pattern —
is not implemented, because `known_hosts` stores hosts bracketless and the mangled pattern is
bracketed.

Ruling: **do not fix it now, and do not fix it untested** — the maker's judgement on that is
correct, no project uses IPv6, and inventing bracket handling with no real specimen is how AT-298
happened. But **declaring it in a manifest is not where a known limitation gets to live.** A
manifest is a submission; it is read once. Filed as **AT-310** (low) so the next person who points
this script at an IPv6-bearing tree meets the limitation in the ledger instead of rediscovering it.
The remedy, when someone has a real specimen: strip `[`/`]` from `candidate` before the host
lookup, or add the bracketed form alongside the bare one in `known_hosts`.

**#3 — harness under `qa/evidence/`, not `scripts/`. UPHELD.** It is evidence for this unit, not a
supported tool, and `qa/evidence/` is the right home. The maker was also right not to pre-empt the
standing proposal by wiring it into `qa/adapter.json`: that fold-in is the sweep's (check 2) and
mine, not the maker's. My position for the record, so the sweep is not starting cold — **the
proposal is sound and I intend to fold it**, with the addition this check surfaced: a mutation step
in slot-1 must assert its baseline green (AT-307), or it will report `KILLED` for everything on a
red suite. C7 has been tightened accordingly (section 6).

---

## 4. Reproduction of the pasted outputs — all four, re-run by me

`projects/erp/screenmap.json` SHA-256, taken **before** anything ran and **after** everything
(the maker's harness, my twelve mutations, two full suites, the dry run):

```
before: 46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf
after : 46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf   IDENTICAL
```

| Manifest claim | My run | Verdict |
|---|---|---|
| `uv run pytest -q` -> 1054 passed, 2 skipped, exit 0 | `1054 passed, 2 skipped, 1 warning in 86.55s`, exit 0 | exact |
| `uv run ruff check src tests scripts` -> exit 0 | `All checks passed!`, exit 0 | exact |
| `uv run autotester doctor` -> exit 1, **exactly one** violation (AGENTS.md) | `root-clutter: AGENTS.md ...` / `1 violation(s)`, exit 1 | exactly one, and it is the pre-existing untracked-root-file AT-283, not this unit's |
| dry run -> 3 rows, 1 file, writes nothing | `projects\erp\screenmap.json` x3 -> `/erp/trainers`; `would repair 3 url_pattern(s) across 1 file(s)`; `dry run - re-run with --write`, exit 0 | exact, and the hash proves "writes nothing" |
| mutation harness -> baseline 21, four KILLED | reproduced verbatim (section 1a) | exact |

Note: `pyproject.toml` sets `addopts = "-q"`, so `uv run pytest -q` is `-q -q` and suppresses the
summary line entirely; the count above was obtained with `-o addopts= -q`. Worth knowing before the
next reader concludes the suite printed nothing.

Also checked against `core-invariants` C2: `tests/test_migrate_url_patterns.py` 277 lines,
`scripts/migrate_url_patterns.py` 207 lines, longest function 39 lines (`main`) — all within limits.
C3: edited in place, no new module in `src/`. C7: satisfied (section 1a), with AT-307 noted.

---

## 5. Migration not run; the human gate

- **Not run on real data.** `projects/erp/screenmap.json` is byte-identical (hash above) and the
  dry run still reports the same 3 mangled rows — if it had been applied there would be nothing to
  find. It remains **untracked**, exactly as the gate's Option A warns.
- **`qa/gates/t135-url-pattern-data-migration.md` remains UNANSWERED** — its `## Answer` section
  still reads `_(unanswered ...)_`, and no `Answered:` line exists anywhere on disk, in this unit's
  manifest, or in `8d30823`'s commit message.
- **"Now accurate" — mostly, with one recurrence.** Its substantive claims all hold: the producer
  is fixed, the dry run really is 3 rows / 1 file, the AT-298 RESOLVED block's description of the
  declared-hosts guard is correct, and Option A's "untracked, no commit to revert" is true. But it
  states **"14 tests in `tests/test_migrate_url_patterns.py`"** at lines 26 and 39, and the file now
  collects **21**. AT-306 (the 9-vs-14 self-contradiction) was fixed by making both numbers 14, and
  this unit then moved the number again without updating the gate. Not this unit's changed file and
  not blocking — recorded on **AT-306**, which stays `open` until the gate says 21.

---

## 6. Contract action (checker is the single writer)

`qa/contracts/core-invariants.md` **C7**, routine tightening — a mutation/sabotage harness must
assert its **baseline is green** before believing any result, because `KILLED`/`failed` is read from
a non-zero exit and a red baseline makes every mutation look killed. Tightening only, weakens
nothing, so it applies under the routine gate. Evidenced by this unit and by the standing
`qa/feedback-inbox.md` proposal to promote mutation into slot-1 verify, where the hole would become
load-bearing. Third C7 clause of the same family (2026-09-08 anchor assertion, 2026-09-08
zero-failure, this one).

---

## 7. Ledger

- `AT-300` `AT-301` `AT-302` `AT-303` `AT-304` -> **`fixed`** (`fixed_date` 2026-09-11), each with
  the mutation that now defends it. `verified_date` stays null — only a later re-check moves
  `fixed -> verified`.
- `AT-305` stays **open** — ruled: correct as designed, documentation-only remedy.
- `AT-306` stays **open**, evidence extended: the gate's count is stale again (14 vs 21).
- New: `AT-307` (harness baseline unasserted), `AT-308` (`known_hosts` fail-safe guards undefended),
  `AT-309` (`_project_dir_of` containment bound undefended + lexical), `AT-310` (AT-302 partial fix:
  a genuinely mangled IPv6 pattern is not repaired). All **low**, all filed rather than charged.
