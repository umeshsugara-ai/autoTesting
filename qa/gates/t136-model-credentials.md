# HUMAN_GATE — a model API key, for Track A's first real recall number

**Opened:** 2026-09-09 · **Blocks:** T-136's acceptance number (not the scorer itself)

## The question, in one line

Which vision-model credential should AutoTester use to actually watch `erp1/2/3.mp4`, and where
does its key go?

## Why this is a gate and not a build task

`uv run autotester providers` reports **`available providers: mock`**. There is no Gemini
credential on this machine, so:

- `projects/erp/` has **no `sources.jsonl`, no `media.json`, no `analysis.json`, no `issues.jsonl`**.
- **No model has ever watched a recording.** Every Track A unit so far (T-130 schema, T-131
  provider, T-132 media prep, T-133 ensemble + issues) is built and checker-PASSed against
  fixtures and mocks. That is real work and the tests are real, but it means the pipeline's
  output has never been compared to a human's.
- The scorer being built in this unit can therefore be *correct* and still produce **recall 0/7**,
  because there is nothing to score.

## Options

| | What it means |
|---|---|
| **A. Gemini API key** (the plan's choice) | `GEMINI_API_KEY` entered at `/projects/erp/env` in the UI, never in chat. The plan's ensemble is `gemini-3.1-pro-preview` + `gemini-3.8-flash`. Cost: 3 short clips x 2 models x 2 prompts — small. |
| **B. A different provider** | Any provider behind `providers.base.Provider`. Needs a new adapter unit first. |
| **C. Defer** | The scorer ships tested and unused; Track A's acceptance stays open. Track A is the only track with a human ground-truth sheet waiting, so this is the option that keeps the north star unmeasured. |

## How to answer

Enter the key in the platform UI at `/projects/erp/env` — **never paste a key into chat**. Then
say "key is in" and the next tick runs `ingest register` -> `ingest prep` -> `ingest analyze` ->
`issues derive` -> the scorer, and the manifest carries real recall and false-positive numbers
against `ERP_Issues_Trainers.xlsx` (7 rows).

## What is NOT blocked by this

The scorer itself: matching rules, both sheet shapes, MM:SS parsing, the greedy one-row-one-match
bound, and its refusal to report a score when there is nothing to score. All of that is built and
tested in this unit against fixtures and against the real workbooks on disk.

**Answered:** _(pending)_

---

**Answered: 2026-09-09 — THE GATE WAS WRONG. Umesh had already provided the credentials.**

He said so directly: *"maine pathlynks and all ki credentials for the development and testing part
.env mai tho di hui hai, use them for development purpose."* Measured immediately after: the
repo-root `.env` (gitignored, untracked) holds **`GEMINI_API_KEY` SET**, plus all four Pathlynks
keys. `google-genai 2.22.0` is installed, and `GeminiProvider().available()` returns **True** the
moment `load_dotenv('.env')` runs.

**Why I reported a blocker that was not there:** `src/autotester/ui/app.py:55` loads the repo-root
`.env`; **no CLI entry point does**. So `autotester providers` answered `mock`, and I took that as
ground truth about the machine instead of about the command. Filed as **AT-228 (high)**.

This gate cost the user time waiting for something he had already given me, which is the opposite
of what a gate is for. Recording it as answered-and-wrong rather than deleting it: a gate that was
never real is worth more on disk than a clean gates directory.

**What it does NOT retract:** no model *has* yet watched a recording, and T-136 still has no recall
number. That part of the T-136 manifest stands. What changes is the reason — it is a one-line
`load_dotenv` away, not a human decision.
