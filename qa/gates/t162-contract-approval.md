# HUMAN_GATE — T-162 needs a contract, and a new contract for a heavy module needs approval

**Raised:** 2026-09-11T05:20+00:00 · maker
**Blocks:** T-162 (multi-source adapters), and therefore T-163 (resumable orchestrator) which
depends on it.

## Why this is a gate and not a build task

Umesh already answered `qa/gates/next-unit-scope.md`: **Option C (AT-227) then B (T-163)**. AT-227
is now closed (`checked-PASS`, verdict `1ad5496`). But `T-163`'s own declared dependency is
`T-162`, which is `pending` — so B cannot start yet; its prerequisite has to exist first.

`T-162` ("Multi-source adapters: Google Drive, video, audio, document, email and text into one
evidence model") has **no contract** in `qa/contracts/` — the closest is `ingest.md`, which is
scoped narrowly to video-via-vision-provider and says so in its own header. The maker cycle's own
rule for this exact situation: *"If no contract exists for this feature → run init-contract before
building anything... for heavy modules route through /cto-advisor HLD or /product-manager PRD...
User approves the initial contract."* This is not the maker deciding routine implementation
detail — it is real design surface: new `SourceKind` values (`DRIVE`, `AUDIO`, `EMAIL` don't exist
yet), a Google Drive credential/OAuth story on top of this project's existing `.env`-scoped-secret
model (`BR-6`, C5 — credentials never reach a model/log/screenshot), and a decision about whether
every source kind converges on today's `Source` model or needs its own shape.

## What IS blocked by this — CORRECTED 2026-09-16T15:30+05:30 (AT-420, high)

**This section said the opposite, and it was never true.** It read:

> Nothing else in the backlog depends on T-162/T-163. The maker will keep working smaller open
> issues (bounded, non-gated) while this is open, rather than idle.

The second sentence is exactly what has happened for five days. The first sentence is false, and
**not because it went stale** — every row below carries `created: 2026-09-10T05:58:09`, committed
in `4add220` on 2026-09-10, a full day *before* this gate was raised on 2026-09-11. It was wrong
when it was written.

`T-163` is depended on, directly or transitively, by **six further pending tasks** — re-derived
from `.goal/goal.json`, field `deps`:

| Task | Criticality | `deps` | Title |
|---|---|---|---|
| T-164 | high | `['T-163']` | Durable Portal Persona JSON + knowledge page |
| T-165 | **critical** | `['T-163','T-144']` | BFS frontier completeness, forward/back recovery |
| T-166 | high | `['T-125','T-164','T-165']` | Traceable eval compiler from user rules |
| T-167 | **critical** | `['T-166','T-110']` | Commit-triggered visible-browser regression |
| T-168 | high | `['T-155','T-164','T-165','T-167']` | Unified damage-control report |
| T-169 | **critical** | `['T-136','T-145','T-168']` | Generic two-mode acceptance |

So the true blast radius is **8 pending tasks — T-162, T-163 and these six — of which five are
`critical`** (T-162, T-163, T-165, T-167, T-169), not the two this gate advertised.

**Why this mattered more than a wrong sentence.** The claim is what set this gate's urgency: it
licensed "the maker will keep working smaller open issues rather than idle" as an acceptable
holding pattern. That reading was reasonable if two tasks were waiting. With eight waiting and five
of them critical, the cost of leaving this unanswered is roughly four times what the gate stated,
and the entire back half of the goal backlog is behind it.

**A distinction worth keeping.** `at365`'s premise was true and went stale — a periodic re-derive
would have caught it. This one was **false on arrival**, and nothing on a timer would ever have
caught it. The two need different remedies; AT-415 covers the first, and this is the argument that
it does not cover the second.

Nothing about the decision changes: the four options below stand exactly as written, and Option A's
four design questions are still the right ones.

## Options

| | What it means |
|---|---|
| **A. Interview now, in chat** | Umesh answers a short set of design questions directly (source-kind list, Drive auth approach, whether audio reuses the existing `transcribe.py`/Whisper path, email format scope) and the maker drafts `qa/contracts/source-adapters.md` from those answers this session. |
| **B. Dispatch a CTO-brief HLD pass first** | The maker dispatches a read-only design-brief agent (current state, options, recommended direction, risks) over T-162's scope, Umesh reviews that brief and approves/edits it, then the maker turns it into a contract. Slower, more rigorous, appropriate given `criticality: critical` sits one hop downstream (T-163). |
| **C. Skip T-162, re-answer next-unit-scope** | Umesh picks a different next unit instead of B, since B's own prerequisite isn't ready — e.g. stay on smaller open-issue cleanup, or reconsider option A (T-162 itself, which is exactly this) as the *directly* next unit rather than routing through T-163 first. |
| **D. Pause** | `/maker pause "<why>"` if none of the above is wanted right now. |

## How to answer

Say which option (or name your own). If A, answer the four design questions above inline and the
next unit becomes drafting the contract from them. If B, just say "B" and the brief gets
dispatched this tick.

**Answered:** _(unanswered — append `Answered: <ISO date> — <choice> — <where>` below before acting)_
