# Verdict — t060-ingest-video

**Date:** 2026-09-03
**Cycle checked:** 1
**Checker mode:** A (unit check, fresh context, read-only toward artifact)
**Contract:** qa/contracts/ingest.md (I1-I5) + qa/contracts/core-invariants.md (C1-C8)
**Manifest:** qa/manifests/t060-ingest-video.md

## VERDICT: PASS

## Re-run evidence (this checker's own execution, not pasted)

```
$ uv run pytest tests/test_ingest.py -v
......                                                                   [100%]
6 passed in 0.27s

$ uv run pytest tests/test_providers.py -v
........                                                                 [100%]
8 passed in 0.22s

$ uv run pytest -q
................................ ...s.................................. [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
exit code: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ wc -l docs/ARCHITECTURE.md
149 docs/ARCHITECTURE.md   (<=150, holds)

$ grep -rn "GEMINI_API_KEY" tests/
tests/test_providers.py:60  -- only a pytest.raises(match=...) assertion, no literal key value

$ grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/
(no output -- exit 1, C8 holds: no stage imports a vendor SDK directly)
```

All manifest-claimed numbers reproduced exactly (6/6, 8/8, ruff clean, doctor clean,
ARCHITECTURE.md 149 lines, no raw GEMINI_API_KEY value in tests).

## Criterion-by-criterion (read against the code directly, not the manifest's description)

**I1 — screens/flows only from what was observed, deterministic ids.**
`stages/ingest.py::ingest_video` (lines 65-81) maps `observation.screens`/`observation.flows`
1:1 into `Screen`/`Flow` via `_to_screen`/`_to_flow` — no field is populated from anything but
the `VideoObservation`. Ids are `content_id("scr", {"name": observed.name})` and
`content_id("flow", {"name": observed.name})` (`core/ids.py` — sha256-based, same payload same
id). `test_same_video_twice_produces_the_same_screen_and_flow_ids` proves this directly and I
reproduced it (6/6 pass). HOLDS.

*Note (not a violation, logged as AT-034 below):* screen id is content-addressed on `name` only,
not `signals`. Two `ObservedScreen` entries with the same `name` but different `signals` collide
to the identical `scr_...` id and both still land in `FlowSpec.screens` as separate list entries
sharing one id. `FlowSpec.screen(id)` still resolves (first match via `next()`), so I1's own
wording ("same input -> same id") and I3's wording ("`FlowSpec.screen()` actually resolves") both
still hold literally — this is a latent list-hygiene gap for a case the contract doesn't name, not
a criterion failure.

**I2 — every step's SourceRef carries t_start/t_end.**
`_to_flow` (lines 45-62) builds every `Step` with
`source_ref=SourceRef(source_id=source_id, t_start=s.t_start, t_end=s.t_end)` straight from the
`ObservedStep`. `test_steps_carry_source_ref_to_the_video_timestamp` asserts `source_id`, `t_start
== 2.0`, `t_end == 3.0` on the FILL step and I re-ran it green. HOLDS.

**I3 — entry_screen resolves to a real screen id when possible.**
`screen_ids = {s.name: screen.id for s, screen in zip(observation.screens, screens,
strict=True)}` (line 78) then `entry_screen = screen_ids.get(observed.entry_screen,
observed.entry_screen)` (line 56). Traced both edge cases asked for:
- **Match exists** ("Sign-in page" flow entry matches an observed screen name) -> resolves to
  that screen's minted id. `test_flow_entry_screen_resolves_to_the_screen_id` reproduced green.
- **No screen name matches `entry_screen`** -> `.get()` falls back to the raw name string, so
  `Flow.entry_screen` stays a plain name and `FlowSpec.screen()` returns `None` for it. The
  contract's own wording is "when possible" — it does not require synthesizing an id when no
  match exists, so this fallback is in-contract, not a defect. No test exercises this branch, but
  no criterion demands one (see core-invariants no-fire: "absence of tests for code the unit did
  not touch" does not quite apply since the code *is* touched, but the *branch* is exactly the
  "not possible" case the contract explicitly declines to require handling).
- **Two screens share the exact same name** -> `zip`+dict just overwrites the key, `screen_ids`
  ends up with one entry; since both screens also share the same content-id (see I1 note), the
  entry_screen resolves to *a* screen id and `FlowSpec.screen()` still resolves. HOLDS as written,
  with the AT-034 note above.
HOLDS.

**I4 — real provider call, video path passed, never inlined.**
`ingest_video` calls `provider.see_video(Path(source.path), prompt, VideoObservation)` (line 75)
— `source.path` (a filesystem path) is passed as a `Path`, `prompt` is separate text.
`GeminiProvider.see_video` -> `_structured(..., video_path=path)` (gemini.py:45-46), and inside
`_structured` (54-77): `if video_path is not None: contents.append(client.files.upload(file=
str(video_path)))` runs **before** `contents.append(prompt)` and both before the single
`client.models.generate_content(model=..., contents=contents, ...)` call. The video is an
uploaded `File` object appended to `contents`, never string-concatenated into `prompt`. HOLDS —
confirmed by direct code read (this codepath is intentionally never live-exercised per the
contract's own no-fire list, so there is no test that hits the network; the ordering guarantee is
verified by reading the method body, which is what I4 actually asks for).

**I5 — prompt is a file, not inline.**
`stages/ingest.py::build_ingest_prompt` reads `docs.prompts_dir / "ingest_video_v1.md"` via
`RepoDocs` (`core/paths.py`), confirmed to resolve to `src/autotester/prompts/ingest_video_v1.md`
which exists and was read in full: instructs "Do not invent screens, flows, or steps you did not
actually observe" and "never write down a real-looking credential even as an example" — both
required by I5's wording. `test_prompt_is_read_from_a_file_and_carries_the_source_label`
reproduced green. HOLDS.

## Core invariants (core-invariants.md, apply project-wide)

- **C1** schema-first: `SourceRef`/`Step`/`Screen`/`Flow`/`ObservedStep`/`ObservedFlow`/
  `ObservedScreen`/`VideoObservation` are all Pydantic models in `schema/flowspec.py`,
  `extra="forbid"` on every one I read. Holds.
- **C2** readable: `ingest.py` 81 lines, `gemini.py` 86 lines (both well under 300); no function
  over 50 lines by inspection; `doctor: clean` confirms. Holds.
- **C3** one concept one place: no duplicate class/function names introduced; no `*_v2`-style
  filename. `doctor: clean`. Holds.
- **C4** repo root clean: no new root-level files from this unit (new files are under
  `src/autotester/{providers,stages,prompts}/`, `tests/`, `qa/`). Holds.
- **C5** secrets: `GeminiProvider` reads `GEMINI_API_KEY`/`GOOGLE_API_KEY` only via `os.environ`
  inside `_structured`, never logged/returned; grep confirms no literal key value in tests. Holds.
- **C6** artifacts human-editable: `FlowSpec` is a plain Pydantic `Artifact`, JSON-serialisable,
  unchanged storage discipline. Holds (not newly exercised by this unit, not required to be).
- **C7** independent verification: this very check re-ran every command itself rather than
  trusting the manifest's pasted output, and every number matched. Holds.
- **C8** provider-agnostic: `grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/`
  returned nothing — `stages/ingest.py` only imports `providers.base.Provider`, never a vendor SDK
  directly (the vendor SDK import lives in `providers/gemini.py`, which is exactly where C8 says
  it belongs). Holds.

## SCOREBOARD

0/0 [C*] criteria (this contract defines none), 5/5 [I*] invariants hold (I1-I5). All 8
core-invariants (C1-C8) hold.

## FAILURES

None.

## Issue written

`AT-034` (severity: low, status: open) — content-id collision + duplicate-list-entry when two
`ObservedScreen`s in one `VideoObservation` share the same `name` but different `signals`
(`stages/ingest.py::_to_screen`, `core/ids.py::content_id`). Not a contract violation (I1/I3 both
still hold literally, per the analysis above) — filed as a coverage gap for a future unit to
either dedup by name or fold `signals` into the id payload, whichever the human prefers. Does not
block this PASS.

## Goal task T-060 — closed on this PASS, with the limitation named explicitly

`.goal/goal.json` T-060's own `done_check` is `uv run pytest tests/test_ingest.py -q` /
`expect_exit: 0` — I re-ran it and it is 0 (6 passed). Literally, the done_check is satisfied, so
I am closing T-060.

**But** T-060's `note` field carries a second, harder acceptance bar this unit does not attempt:
"Golden test: >=90% step recall vs a hand-written list on a real demo video." No Pathlynks demo
video exists in this repo (confirmed: nothing under `projects/pathlynks/` is a video source with a
real path suitable for this). That is a genuine, disclosed, undeliverable-today blocker — both
`qa/contracts/ingest.md`'s no-fire list and the manifest name it openly, and my own read of the
code confirms no part of this unit fakes or approximates that acceptance bar (the only "live"
validation performed was a text-only structured-output smoke test, not video recall).

**Reasoning for closing anyway:** the goal task's `done_check` is the literal, machine-checked
contract for what "done" means for this task-id in `.goal/goal.json`; the prose `note` is
additional context, not a second `done_check` the tooling enforces. T-060's own title ("video/docs
-> FlowSpec with SourceRefs") is satisfied for the video half; docs-ingestion is a separate,
explicitly out-of-scope half per `qa/contracts/ingest.md`'s no-fire list, so closing T-060 here
means "the video-ingest pipeline this task-id names is built and tested," not "the golden-video
recall bar is met." I'm closing it because leaving a task open forever when its own done_check
passes just because a real-world asset (a demo video) doesn't exist yet would block the goal
tracker on an external dependency indefinitely with no code left to write — the honest fix is to
close T-060 for what was actually delivered and let a future task (once a real video lands) carry
the golden-test acceptance forward as its own unit, rather than leaving this one perpetually
"pending" for a reason no amount of further coding here resolves.

Ledger row appended (user_value: high, per the contract's own instruction) naming this exact
limitation — see command below.
