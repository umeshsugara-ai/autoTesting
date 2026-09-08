# Verdict — at125-at132-declared-but-unapplied

**Date:** 2026-09-08
**Unit:** AT-125 + AT-128 + AT-129 + AT-132
**Manifest:** `qa/manifests/at125-at132-declared-but-unapplied.md`
**Commit checked:** `c4c878a` (verified identical to `HEAD` 13c5cd0 for `src`/`tests`/`scripts`)
**Contract:** `qa/contracts/ingest.md` (I7–I10)
**Cycle checked: 1**

> Re-dispatch note: a previous checker on this unit died on an API auth error after one tool
> call and wrote nothing. A crashed checker is not a verdict; this is cycle 1, not cycle 2.

---

## VERDICT: FAIL

**SCOREBOARD: 3/4 in-scope invariants hold (I7, I9, I10) — I8 fails.**

Three of the four named bugs (AT-125, AT-128, AT-129) and AT-132 are genuinely closed, verified
by my own execution against the shipped CLI, not by the manifest's transcripts. The unit fails on
a **new instance of the exact defect it exists to close**: `load_sidecar` declares a guarantee in
its own docstring — "a malformed sidecar must not stop an ingest" — and does not apply it. Two
plausible malformed shapes escape its `except (OSError, ValueError)` and crash
`autotester ingest run` with an unhandled traceback.

---

## What I re-ran myself

| Command | Manifest claim | My result |
|---|---|---|
| `uv run pytest` (host, native) | 614 passed, 2 skipped | **614 passed, 2 skipped, 1 warning in 86.67s** ✔ |
| `uv run ruff check src tests scripts` | All checks passed | **All checks passed!** ✔ |
| `uv run autotester doctor` | doctor: clean | **doctor: clean** ✔ |

Note for future manifests: `addopts = "-q"` in `pyproject.toml` plus a command-line `-q` is `-qq`
under pytest 9 and **suppresses the count line entirely**. `uv run pytest -q` prints no
`N passed`. The documented command therefore cannot produce the number the manifest quotes; I got
it with a bare `uv run pytest`. Not a defect in this unit — recorded so the next manifest's
evidence block is reproducible.

---

## AT-125 — closed (verified through the shipped CLI)

My own probe, not the maker's test: `AUTOTESTER_ROOT` set to a temp dir, `providers.get`
monkeypatched to a spy `MockProvider`, `autotester ingest register` then `autotester ingest run`
invoked through `CliRunner` on the real `app`:

```
register exit 0  src_2a9dbdd46186  (no label)  sha256=5d50d66fa9e7
run      exit 0  demo: 1 screens, 0 flows from src_2a9dbdd46186 (review status draft)
vision_options = [VisionOptions(fps=2.0, seed=7, max_output_tokens=65536,
                                media_resolution='high', thinking_level='high', ...)]
canary phrase in prompt: True
"no speech detected" in prompt: False
```

`vision_options` is no longer `[None]`; `media_resolution='high'` now genuinely reaches the
provider from the only shipped entry point. The sidecar canary phrase reaches the prompt.
Both halves of AT-125 (options **and** the unfiled narration twin) are closed. Ledger row
AT-125 → `fixed`.

## AT-128 — closed

`_cache_key` keys on `file_sha256`. Reproduced sabotage E in a scratch copy (below): reverting to
`resolve()::st_size` makes a same-size re-export a cache HIT again (`assert 1 == 2`). The cache
still does its job — the same bytes upload once. Ledger row AT-128 → `fixed`.

## AT-129 — closed, with one probe finding

`verify_source_bytes` is called from `ingest_video`, so it guards every caller, not just the CLI.
Probed directly:

| Input | Behaviour | Judgement |
|---|---|---|
| `sha256=None` | returns, no refusal | correct — only text/url sources lack one |
| bytes match | returns | correct |
| bytes changed | `SourceChanged`, message names both digests | correct |
| path deleted | `SourceChanged`, "which no longer exists" | correct |
| path now a **directory** | **raw `PermissionError`**, uncaught | AT-135 |
| Windows upper-cased path | returns (no false refusal) | correct — content-keyed, casing is irrelevant |

**The suggested command works verbatim.** I ran `autotester ingest register demo "<path>"` in
exactly the form the refusal prints: exit 0, a new source minted. Argument order and quoting are
right.

**Re-hash cost is not a regression.** Measured on this host: `file_sha256` of a 210 MB file =
**0.25 s** (~840 MB/s). A 200 MB recording in an ensemble loop pays ~0.25 s per `upload_and_wait`
and ~0.25 s per ingest, against a multi-second-to-minutes upload of the same bytes. The content
key buys correctness for a cost that is invisible next to the network call it protects. No issue
filed; do not "optimise" this back to `st_size`.

## AT-132 — closed, and the design ruling the dispatch asked for

Verified live: with `AUTOTESTER_ROOT` pointed at a temp dir, `RepoDocs().prompts_dir` resolves to
`D:\autoTesting\src\autotester\prompts` — the package, not the data root. Sabotage G reproduces.

**Ruling: the `_root_given` distinction is CORRECT in effect, and the mechanism is a smell — not
a split-brain, and not a FAIL.** I checked the thing that would make it one: whether two different
prompt directories can be in play in production. They cannot. Every `prompts_dir` consumer
(`stages/ingest.py:46`, `expand.py:69`, `grade.py:44`, `agent_loop.py:56`,
`ledger/relitigation.py:42`) receives `RepoDocs()` with no root from `cli.py` and `cli_video.py`.
The only production caller that passes a root is `doctor.py`, and `doctor` never touches
`prompts_dir` (grepped). So the second branch is reachable only from tests.

I also examined the alternative the dispatch names — prompts *never* under `root`, fix the ledger
fixture. `tests/test_ledger.py::make_docs` is not an incidental fixture: it builds a whole fake
repo (docs/, `src/autotester/thing.py`, `src/autotester/schema/m.py`, and a stub
`relitigation_v1.md`) under `tmp_path`. That is a deliberate stub prompt tree, and the maker is
right that substituting one is a legitimate test move. Rewriting it to satisfy a purer rule would
be churn, not correctness.

What is genuinely wrong is the *shape* of the seam: one parameter (`root`) now carries two
meanings, selected by a hidden boolean, so `RepoDocs()` and `RepoDocs(repo_root())` are no longer
equivalent constructions. That is a trap for the next reader even though it cannot misfire today.
Filed as **AT-137 (medium)**: name the seam — `RepoDocs(root, prompts_dir=...)` — rather than
inferring it from whether `root` was passed. Follow-up, not a blocker.

---

## Sabotage reproduction (all four, in a `git archive HEAD` scratch copy)

Per AT-101 / AT-131 the live tree was never touched: `git archive HEAD | tar -x` into the
scratchpad, `PYTHONPATH` pinned to the scratch `src` (import path confirmed to resolve there),
each sabotage applied and reverted in the copy only. Baseline in the copy: **7 passed**.

| Sabotage | Manifest claim | What I got |
|---|---|---|
| **D** — CLI stops passing options + transcript | 2 FAILED: `..._passes_vision_options`, `..._injects_the_sidecar_narration` | **exactly those 2** ✔ |
| **E** — cache key back to `path::size` | 1 FAILED with `assert 1 == 2` | **`assert 1 == 2`, that one test** ✔ |
| **F** — no byte re-validation | 2 FAILED: `..._that_changed_is_refused`, `..._writes_no_flowspec` | **exactly those 2** ✔ |
| **G** — prompts under the data root | 3 FAILED (incl. `..._no_sidecar_still_ingests`) | **exactly those 3** ✔ |

All four transcripts match reality. After AT-117 (a fabricated transcript) this was the thing most
worth checking, and it holds.

One honest wrinkle, reported because it is the kind of thing that decays into AT-117: sabotage D's
parenthetical calls itself "the shipped state at 1c8c8e4". Restoring the *whole* parent
`cli_video.py` produces **3** failures, not 2 — the parent also lacks the `except SourceChanged`
handler, so `..._that_changed_is_refused` exits 1 instead of 2. The sabotage as *described* (drop
the options and transcript arguments) reproduces the quoted 2 exactly, which I confirmed
separately. The transcript is accurate; the parenthetical overstates what was reverted.

---

## FAILURES

- **[I8] sev: high** · `load_sidecar`'s `except (OSError, ValueError)` does not cover the malformed
  shapes it promises to survive, so a bad sidecar **crashes the shipped CLI** ·
  catch the parse broadly (or validate the top-level shape) so a bad sidecar degrades to
  no-narration as the docstring says · issue: **AT-133**

Reproduced end-to-end through `CliRunner` on the real `app`, not against the function:

```
sidecar = "[1,2,3]"                      -> ingest run exit=1  AttributeError
sidecar = {"segments": ["hi"]}           -> ingest run exit=1  TypeError
```

`Transcript.from_sidecar` calls `raw.get(...)` on whatever JSON decodes (an `AttributeError` if
that is a list or a scalar) and `TranscriptSegment(**seg)` on whatever is in `segments` (a
`TypeError` if those are not mappings). Neither is an `OSError` or a `ValueError`. The docstring
three lines above says *"a malformed sidecar must not stop an ingest, because a reading with no
narration is still worth having."* It stops the ingest. **This is the unit's own thesis — a
guarantee declared, plumbed, and not applied by the path that ships — reappearing in the fix for
it.** That is why it is a FAIL rather than a filed follow-up: the unit's claim is precisely that
this shape was closed.

Neither shape occurs in the real corpus (I checked all 10 `*.transcript.json` files under
`C:/Users/Lenovo/Videos/Screen Recordings/`; every one is `{segments:[{start,end,text}],
speech_seconds}`, one additionally carrying a benign top-level `source` key). So this is latent,
not live — which is exactly what AT-125 was too.

---

## The `load_sidecar` scope question — ruled

**Correct scope, not creep.** It is the same defect as AT-125 in the same function's argument
list: `build_ingest_prompt` took a `transcript` since T-131 and no caller passed one, so
`{{NARRATION}}` rendered "no speech detected" on every real ingest. Fixing the options while
leaving its twin dead would have been the narrower error. Filing an id first would have been
tidier bookkeeping; it would not have been better work.

**On the tension the dispatch names — the maker's own AT-108/AT-114 sweep held that swallowing a
cause IS a defect, and `load_sidecar` swallows one.** That ruling applies to this code, and I am
upholding it, at medium rather than high:

```
sidecar = {"segments":[{"start":0,"end":2,"text":"real speech","confidence":0.9}]}
  -> ingest run exit=0, and the prompt asserts "no speech detected": True
```

`TranscriptSegment` is `extra="forbid"`, so one unexpected key from a future transcriber makes the
whole transcript vanish, and the prompt then states a **positive falsehood** about the recording —
that nobody spoke — while nothing anywhere records that a sidecar was present and unreadable. I8
says the prompt must say "no speech" *when no speech exists*; this says it when speech exists. A
best-effort load is right; a *silent* one that substitutes a confident negative claim is not. The
degradation must remain, but it must announce itself (one line on stderr naming the sidecar and
the parse error is enough). Filed **AT-134 (medium)**.

The distinction I am drawing, so it is reusable: swallowing is acceptable when the fallback is
**neutral** (a re-upload, an empty optional), and a defect when the fallback is an **assertion**
the reader will believe.

Other `load_sidecar` failure modes probed and found **correct**: malformed JSON → `None`; a
segment missing a field → `None`; a `speech_seconds` of the wrong type → `None`; the sidecar path
being a directory → `None` (the `read_text` `PermissionError` is an `OSError`). A sidecar
"belonging to a different video" is not expressible: `from_sidecar` stamps `source_id` from the
`Source`, and a `source_id` key inside the file is ignored, so adjacency is the only binding and
it cannot disagree with itself. That is a defensible design; it does mean a sidecar copied next to
the wrong recording is undetectable, which is worth knowing but is not a defect to file.

---

## Adversarial test of the unit's headline claim

The manifest claims this unit closes the "declared but never applied" shape. It bounds that claim
to four bugs, and within those bounds it is honest. Beyond them the shape survives — I swept the
fields the dispatch named:

| Thing | Verdict |
|---|---|
| `--model` | **applied** — `providers.get(provider, **{"model": model})` |
| `--replace` | **applied** — reaches `persist_ingest(replace=...)`, guards I6 |
| `label`, `recorded_on` | **applied** — passed to `register_source`; the I10 "second registration's label is not applied" case is a recorded decision, not a bug |
| `Source.duration_s` | **declared, written by nothing, read by nothing** (`MediaPrep.duration_s` is the live one) |
| `Source.notes` | **declared, written by nothing, read by nothing** |
| `FlowSpec.app_overview` | **written** from `observation.summary`, **read by nothing** |

Filed as **AT-136 (low)** — three more instances, all inert today, none a regression from this
unit and none claimed by it. Recorded so the shape stays visible rather than being declared solved.

---

## ISSUES-WRITTEN

- **AT-133** (high, ingest) — `load_sidecar` crashes the CLI on a sidecar shape its own docstring
  promises to survive. **This is the FAIL.**
- **AT-134** (medium, ingest) — a rejected sidecar degrades silently to the prompt asserting "no
  speech detected" on a recording that has speech; nothing is logged.
- **AT-135** (medium, ingest) — untyped refusals: `verify_source_bytes` raises a raw
  `PermissionError` when the registered path is now a directory, and `_cache_key` now raises a bare
  `FileNotFoundError` from `upload_and_wait` for a missing local file where the old size-key fell
  through to the SDK-wrapping `try` that produces a `ProviderError`.
- **AT-136** (low, ingest) — `Source.duration_s`, `Source.notes`, `FlowSpec.app_overview` remain
  declared-and-unapplied.
- **AT-137** (medium, ingest) — `RepoDocs.prompts_dir` behaviour depends on a hidden `_root_given`
  flag; name the seam instead.

Status moved to `fixed`: **AT-125, AT-128, AT-129**. **AT-132** added as a row (found by the
maker, fix verified here) at `fixed`. None move to `verified` — that takes a later re-check.

---

## What a PASS needs next cycle

Fix AT-133 only. Everything else here is a filed follow-up, and the four named bugs are closed.
The cheapest correct fix also closes AT-134: catch the parse broadly, and say one line on stderr
when a sidecar exists and could not be read.

```
VERDICT: FAIL
SCOREBOARD: 3/4 in-scope invariants hold (I7, I9, I10 hold; I8 fails)
FAILURES:
- [I8] sev: high · a malformed sidecar escapes `except (OSError, ValueError)` and crashes
  `autotester ingest run` (exit 1, AttributeError/TypeError), contradicting `load_sidecar`'s own
  docstring guarantee · catch the parse broadly and warn on stderr instead of degrading silently ·
  issue: AT-133
ISSUES-WRITTEN: AT-133, AT-134, AT-135, AT-136, AT-137
EXPLANATION: AT-125, AT-128, AT-129 and AT-132 are all genuinely closed — I drove the real CLI
myself and measured VisionOptions(media_resolution='high') and the sidecar canary reaching the
provider, and all four sabotage transcripts reproduce exactly. The unit fails on a new instance of
its own thesis: load_sidecar declares in its docstring that a malformed sidecar must not stop an
ingest, and two plausible malformed shapes crash the shipped CLI outright. The AT-132 design is
ruled correct in effect (no production caller reaches the second branch) with the hidden
_root_given flag filed as a follow-up rather than a blocker.
```
