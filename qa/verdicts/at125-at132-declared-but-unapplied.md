# Verdict — at125-at132-declared-but-unapplied

**Date:** 2026-09-08
**Unit:** AT-125 + AT-128 + AT-129 + AT-132, and (cycle 2) AT-133 + AT-134 + AT-135
**Manifest:** `qa/manifests/at125-at132-declared-but-unapplied.md`
**Commit checked:** `d9396d4` (HEAD `521b79a` = manifest-only stamp; `src`/`tests`/`scripts` identical)
**Contract:** `qa/contracts/ingest.md` (I7–I10)
**Cycle checked: 2**

> The cycle-1 FAIL verdict is preserved in git history (commit before this one). This file is the
> cycle-2 verdict.

---

## VERDICT: PASS

**SCOREBOARD: 4/4 in-scope invariants hold (I7, I8, I9, I10). 7/7 named issues closed.**

The cycle-1 FAIL was AT-133 alone; the direction given was "fix AT-133 only — the cheapest correct
fix also closes AT-134." The maker fixed AT-133, AT-134 and AT-135. I re-ran all of it myself.

---

## Verify commands (re-run by me, host, Docker down, `uv` native)

| Command | Manifest claim | My result |
|---|---|---|
| `uv run pytest` (bare — `-q` + `addopts=-q` is `-qq`) | 623 passed, 2 skipped | **623 passed, 2 skipped, 1 warning in 70.30s** ✔ |
| `uv run ruff check src tests scripts` | All checks passed | **All checks passed!** ✔ |
| `uv run autotester doctor` | doctor: clean | **doctor: clean** ✔ |

The maker adopted the `-qq` correction and its counts are now reproducible from the command it
documents. 2 skips on host (1 in the container) — unchanged, environmental.

---

## 1. AT-133 — closed. My own cycle-1 repros, re-run through the real CLI at `d9396d4`

Not the maker's tests: my own `CliRunner` probe on the real `app`, `AUTOTESTER_ROOT` in a temp dir,
`providers.get` monkeypatched to a spy `MockProvider`, `ingest register` then `ingest run`.

| sidecar content | cycle 1 | cycle 2 |
|---|---|---|
| `[1,2,3]` | exit **1**, `AttributeError` | **exit 0**, prompt says "could not be read" |
| `{"segments":["hi"]}` | exit **1**, `TypeError` | **exit 0**, "could not be read" |
| non-JSON (`not json at all {{{`) | exit 0 (`ValueError` caught) | **exit 0**, "could not be read" |
| `{"segments":[{start,end,text,confidence}]}` (`extra="forbid"`) | exit 0, prompt asserted **"no speech detected"** | **exit 0**, "could not be read" |

All four exit 0 through the shipped CLI. I8's best-effort promise is now applied by the path that
ships, which is the whole point of this unit.

## 2. AT-134 — closed, and the fix does not swap one wrong answer for another

Same probe, the discriminating pair:

```
sidecar with real speech + a `confidence` key ->  "no speech detected": False
                                                  "could not be read":  True
absent sidecar                                ->  "no speech detected": True
                                                  "could not be read":  False
```

So the unreadable case no longer asserts silence, **and the genuinely-silent case still asserts
silence** — I checked the second half explicitly, because a fix that made everything "unreadable"
would satisfy the failing test and destroy I8's "when no speech exists, the prompt says so".

## 3. AT-135 — closed. Both paths, plus the suggested command

| Probe | Result |
|---|---|
| registered path is now a **directory**, through `ingest run` | **exit 2**, `SourceChanged` text, no traceback (cycle 1: raw `PermissionError`) |
| `verify_source_bytes` on that source, called directly | `SourceChanged` — guards every caller, not just the CLI |
| `upload_and_wait(client, missing.mp4)` | `ProviderError: nothing to upload: … is not a readable file` (cycle 1: bare `FileNotFoundError`) |
| `upload_and_wait(client, <a directory>)` | `ProviderError`, same shape |
| the changed-bytes refusal's suggested command, run **verbatim** (extracted from the message by regex, `shlex.split`, fed straight to the CLI) | **exit 0**, new source minted — quoting and argument order are still right |

## 4. Sabotages H, I, J — reproduced, separation verified literally

`git archive HEAD | tar -x` into the scratchpad, `PYTHONPATH` pinned to the scratch `src` (import
path confirmed resolving there); the live tree was never touched (AT-101/AT-131). Baseline in the
copy: **16 passed**.

| Sabotage | Maker's claim | What I got |
|---|---|---|
| **H** — narrow catch + `return None` | 4 failures | **4 failed, 12 passed** — both `..._never_stops_an_ingest` params and both `..._never_reported_as_silence` params ✔ |
| **I** — broad catch, but drop only the UNREADABLE branch (`return None`) | exactly the 2 silence cases | **2 failed, 14 passed** — exactly `..._never_reported_as_silence[[1, 2, 3]]` and `[…confidence…]` ✔ |
| **J** — `exists()` instead of `is_file()` | 1 failure | **1 failed, 15 passed** — `test_a_source_pointing_at_a_directory_gets_a_typed_refusal` ✔ |
| RESTORE | 16 passed | **16 passed** ✔ |

The claimed separation is literally true. It is worth stating what it proves, because the maker
over-claims it slightly: it proves the crash half and the silence half are defended by different
tests, so a fix to either alone leaves a red test. It does not prove the tests are independent of
the *implementation shape* — H is a superset of I by construction. The evidence supports the claim
it is offered for.

## 5. Cycle-1 fixes — no regression

Re-measured live at `d9396d4`, not inferred from the green suite:

```
AT-125  ingest run exit 0 · vision_options[0].media_resolution = 'high' · canary phrase in prompt: True
AT-128  same-size re-export produces a DIFFERENT cache key: True
AT-129  changed bytes -> SourceChanged naming both digests; deleted/dir path -> SourceChanged
AT-132  RepoDocs().prompts_dir = D:\autoTesting\src\autotester\prompts under AUTOTESTER_ROOT=<temp>
```

`git diff --stat c4c878a HEAD -- src tests scripts` is three files: `gemini_files.py` (+3),
`ingest.py`, `test_ingest_real_cli.py`. Nothing cycle 1 fixed was touched.

## 6. The AT-108/AT-114 reconciliation — sound, not a reframe

I checked the code and the contract rather than the maker's characterisation of them.

- `stages/explore_node.py::capture` still **swallows** every exception and still returns `None` —
  it was never changed to re-raise. What AT-114's fix added was `add_issue(… IssueKind.EVIDENCE,
  f"could not screenshot this screen — {type(exc).__name__}: {exc}")`.
- `qa/contracts/explore.md` amendment log, verbatim: *"`capture()` staying non-fatal was also
  upheld: AT-114's defect is the SILENCE, not the survival."*
- `_why()`/`_recover()` (AT-108) likewise keep going and record the cause.

So the rule that sweep actually established is *never let a failure become a confident-looking
silence* — not *always re-raise*. AT-134's fix is that rule at one layer up. **The reconciliation
is sound.**

One place it is *not* fully applied, and this is a new finding rather than a re-litigation: AT-108's
other half is that the **cause is recorded** ("cause not recorded" is explicitly called the honest
worst case, not the target). `load_sidecar`'s `except Exception` discards the exception entirely —
no type, no message, nothing on stderr — so an operator running `autotester ingest run` gets no
signal that a sidecar was present and unparseable, and the parse error that would tell them which
key broke is gone. The model is told; the human is not. Cycle 1 asked for "one line on stderr naming
the sidecar and the parse error". That half is unimplemented. It does not fail the unit — the
defect as it mattered (a false assertion inside the ground-truth block) is closed, and this is a
lower-severity, different consequence — but it is filed: **AT-138 (low)**.

## 7. Adversarial probing of the new code

| Case | Behaviour | Judgement |
|---|---|---|
| `Transcript(engine="unreadable")` **with** segments | `narration_block` returns the segments | Correct precedence — real narration beats a stale engine tag; unreachable from `load_sidecar`, which never mints that combination |
| sidecar `{}` (empty object) | parses, `segments=[]`, engine `sidecar` → prompt asserts **"no speech detected"** | A confident silence claim from a file that says nothing either way — same class as AT-134, contrived trigger. **AT-139 (low)**, not a blocker |
| sidecar `{"segments": [], "speech_seconds": 0}` | asserts "no speech detected" | **Correct** — this is exactly what a transcriber writes for a silent recording; the real corpus shape |
| sidecar valid but for a DIFFERENT video | loads, narration injected, undetectable | Unchanged from cycle 1's ruling: `from_sidecar` stamps `source_id` from the `Source` and ignores any in-file id, so adjacency is the only binding and cannot disagree with itself. Design, not defect |
| `except Exception` and `MemoryError` | `MemoryError` **is** an `Exception` and would be swallowed → the sidecar reads as unreadable and the ingest continues | Acceptable here: the fallback is honest, not an assertion, and the very next step uploads a video far larger than the sidecar, so a genuine OOM cannot stay hidden. `KeyboardInterrupt`/`SystemExit` are `BaseException` and correctly pass through — verified in the CLI probe, where `typer.Exit`'s `SystemExit` propagates normally |

## 8. AT-136 / AT-137 — genuinely untouched, still open

Confirmed by reading, not by the manifest's word: `Source.duration_s` and `Source.notes` are still
written by nothing (`grep "duration_s=|notes="` in `src/` hits only `bench.py` and `execute.py`,
different models); `FlowSpec.app_overview` is still written at `stages/ingest.py:237` and read by
nothing; `core/paths.py:196,246` still carries `_root_given`. Neither file is in this commit's diff.

---

## ISSUES

**Moved `open → fixed`:** AT-133, AT-134, AT-135.
**Moved `fixed → verified`:** AT-125, AT-128, AT-129, AT-132 (this is the later re-check cycle 1
said they needed; I re-measured each one live above).
**Still open, untouched, correctly deferred:** AT-136, AT-137. Also unchanged from cycle 1's
no-claims list: AT-126, AT-127, AT-130 (A3), AT-131, AT-123, AT-124.

**ISSUES-WRITTEN (new):**

- **AT-138 (low, ingest)** — `load_sidecar` discards the parse exception entirely; nothing on
  stderr and no cause recorded anywhere, so a present-but-unreadable sidecar is invisible to the
  operator. AT-108's rule ("cause not recorded" is the honest worst case, not the target) applies.
- **AT-139 (low, ingest)** — a sidecar with no `segments` key (`{}`) is parsed as a valid empty
  transcript via `raw.get("segments", [])` and the prompt then asserts "no speech detected" about a
  recording nothing has established is silent — AT-134's class, from a malformed-file trigger.

---

```
VERDICT: PASS
SCOREBOARD: 4/4 in-scope invariants hold (I7, I8, I9, I10); 7/7 named issues closed
FAILURES: none
ISSUES-WRITTEN: AT-138, AT-139 (both low, both follow-ups, neither blocking)
EXPLANATION: I re-ran my own cycle-1 AT-133 repros through the shipped CLI at d9396d4 — all four
malformed sidecars now exit 0 and the prompt says the sidecar could not be read, while a genuinely
absent sidecar still asserts silence, so the fix did not replace one wrong answer with another.
AT-135's typed refusals hold in both paths and the SourceChanged message's suggested command still
runs verbatim. Sabotages H/I/J reproduce with exactly the claimed 4/2/1 separation in a git-archive
scratch copy, and the cycle-1 fixes (AT-125/128/129/132) all re-measure live with no regression.
The AT-108/AT-114 reconciliation is sound on the evidence — capture() still swallows and the explore
contract itself records that the defect was the silence, not the survival — with the one unapplied
half (record the cause) filed as AT-138 rather than held against the unit.
```
