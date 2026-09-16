# GATE — at416-clip-vs-reach-direction

**Opened:** 2026-09-16
**Blocks:** AT-379, AT-416 · and transitively the unit that wires `visual_text` into the crawl
**Unit that stalled on it:** `at379-scrollable-pane-reachability` (3 of 3 fix cycles spent)
**Evidence:** `qa/verdicts/at379-scrollable-pane-reachability.md` (cycles 1–3) ·
`qa/evidence/browser-at379-scrollable-pane-reachability-2026-09-16-checker-c3/report.json`

## The question in one line

When a scrollable pane sits inside a clipping box, should `visual_order.js` risk reporting text a
reader cannot see, or risk missing text a reader can?

## Why it needs you rather than another fix cycle

The same line has been wrong five times, always in the same direction, and each fix was written by
the same reasoning that produced the previous one:

| | the rule | what vanished |
|---|---|---|
| AT-373 | viewport-relative test | everything above the window's fold |
| AT-379 | a scrollable pane read as a hard clip | everything below the pane's fold |
| AT-392 | window offset only | everything before a scrolled pane's offset |
| AT-408 | walk stopped at the first one-axis scroller | nested panes' outer offset |
| AT-416 | outer clips intersected against the glyph's current rect | a pane inside any `overflow:hidden` card |

A sixth attempt by the same maker on the same line is not evidence of anything. The choice below is
between two costs the product's north star names explicitly, so it is a product call.

## The options

**A — Revert to the unbounded scrollable axis; re-accept AT-393.**
A scrollable ancestor stops the clip walk, as in cycle 2. AT-379 and AT-416 close; AT-393's nested
-clip **false positive** returns (text inside an outer clip is reported although a reader cannot see
it). Cost: the north star's false-positive-rate term. Smallest change, known-good behaviour.

**B — Intersect outer clips against the innermost SCROLLER'S BOX, not the glyph's rect.**
The checker's suggested fix: a glyph is reachable if the *container that can move it* intersects the
outer clip, wherever the glyph currently sits. Closes AT-379, AT-416 and AT-393 together. Cost: new
logic on the path every glyph takes, unproven, and this line's record is five for five against
confident reasoning. Would need its own unit and its own cycles.

**C — Ship neither; disclose the whole class.**
Add "a scrollable pane inside a clipping ancestor" to the module's `WHAT THIS DOES NOT SEE` block
and leave both defects open. Honest, costs nothing, and leaves a known false negative in an
instrument whose entire purpose is catching the false-negative class.

## Recommendation

**A**, unless you want B built as its own unit. A false positive costs a metric; a false negative
costs a missed credential, which is the failure this module exists to prevent — and the module's own
stated direction already prefers the former. C is worse than A here: the same exposure, minus the
fix, and disclosure does not make an instrument see.

## How to answer

Reply with `A`, `B` or `C` (or your own direction). I will append
`Answered: <ISO date> — <choice> — <where>` to this file before acting on it.

Answered: (pending)
