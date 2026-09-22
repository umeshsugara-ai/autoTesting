# Pilot sample — FROZEN 2026-09-22 (before any run)

Goal: measure Anthropic tokens per PASSed unit for delegation (Ollama build + Claude checker)
vs a Claude-only build, across unit sizes. Kill rule: delegation total >= 70% of Claude-only
baseline = FAIL. Method: replay each unit at <build_commit>^ in two worktrees, one shared brief,
both verified by the unit's verify commands. A unit that breaks is reported, never swapped.

| # | size | unit | build_commit | replay base (^) | verify |
|---|------|------|--------------|-----------------|--------|
| 1 | small  | AT-154 | 90e4219 | ab5ffad | uv run pytest + ruff |
| 2 | small  | AT-121 | 6c653fd | 6caa5e1 | uv run pytest + ruff |
| 3 | medium | AT-113 | ea7e25d | c1bb404 | uv run pytest + ruff |
| 4 | medium | AT-143 | f19471e | 1e08fd6 | uv run pytest + ruff |
| 5 | large  | AT-125 | c4c878a | f71e602 | uv run pytest + ruff |
| 6 | large  | AT-176 | e2f119f | 25331d2 | uv run pytest + ruff |

Prior A/B anchor (not in this sample): AT-543 build step = Ollama ~1,100 tok / $0 vs Claude 79,548 tok.
Baseline for the 70% rule = the Claude-only arm run on the SAME 6 units here (build + shared checker).
