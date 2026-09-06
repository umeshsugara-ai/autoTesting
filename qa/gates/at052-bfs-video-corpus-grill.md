# Gate — AT-052: whole-platform BFS crawl + video-corpus eval methodology

**Question:** should AutoTester's scope grow to (a) an autonomous whole-platform BFS crawl that
clicks every icon/button on a live logged-in product and builds the full screen graph itself, and
(b) a video-learning pipeline that mines `C:\Users\Lenovo\Videos\Screen Recordings` (and future
screen-recording uploads) as ground truth for how the team currently tests — and if so, how do
these relate to the already-shipped DFS-trace + BFS-merged-tree report visualizations (F-027/
F-028/F-029) and the existing reviewed-FlowSpec-driven ingest/expand pipeline?

**Options:** (1) scope both as new, explicitly-bounded capabilities with their own contracts —
building on the plan already drafted this session (video pipeline ported into this repo, 2-model
Gemini ensemble, BFS explorer generic/not URL-bound); (2) scope only one of the two now, defer
the other; (3) decide neither belongs in this repo's north star as currently written and this is
a separate project; (4) something else that emerges from the grill.

**Command:** `/grill "whole-platform BFS crawl + video-corpus eval methodology"`
**Capture path:** `D:/autoTesting/brainstorms/<tick-date>-bfs-video-corpus-grill.md` (this project
sits outside `D:/ai_os`, so `/grill`'s own path table routes it here, not to
`D:/ai_os/umesh/brainstorms/`).

**Blocks:** AT-052 (`qa/issues.jsonl`); the GRILL row in `qa/QUEUE.md`; any future unit that would
build Capability A (video learning) or Capability B (BFS explorer) from the earlier planning
discussion this session — none of that work should start before this gate is answered.

**Opened:** 2026-09-06T14:13:52+05:30 (first named by the checker sweep this session)

**Answered:** (pending)
