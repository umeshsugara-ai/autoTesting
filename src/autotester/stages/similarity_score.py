"""How two bug reports are compared for `stages/score.py`'s T-136 scorer.

Split out of `score.py` when it crossed the 300-line cap adding this fix —
one job (text similarity), not a second decision about matching (that stays
`score()`'s own, unchanged).

Contract: qa/contracts/video-learning.md (T-136 acceptance).
"""

from __future__ import annotations

import re

STOPWORDS = frozenset((
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "on", "in", "at",
    "to", "of", "for", "with", "and", "or", "not", "no", "but", "so", "than",
    "this", "that", "these", "those", "it", "its", "it's", "field", "fields", "error",
    "errors", "validation", "prevents", "allows", "form", "forms", "submission", "screen",
    "screens", "edit", "edits", "page", "pages", "should", "does", "do", "can", "cannot",
    "instead", "offers", "offer", "only", "actual", "real", "shows", "show", "appears",
    "reads", "presents",
))
"""AT-232: a curated, in-file list — dumb and auditable, not exhaustive. Its
job is only to strip the boilerplate a bug-report vocabulary repeats across
UNRELATED faults ("field", "validation", "error", "prevents", "form",
"screen", "edit") so containment measures distinctive content, not shared
phrasing. Known limitation, stated rather than hidden: a real fault whose
distinctive words happen to be common English will score lower than it
should. Extend this list only on a measured false positive, never by guess."""


def similarity(left: str, right: str) -> float:
    """AT-232: containment over stopword-filtered word sets, not a
    character-sequence ratio.

    `SequenceMatcher.ratio()` is length-symmetric: it penalises the SHORTER
    text for being terser, regardless of content. Measured on the real
    corpus (`.work/at232-probe.py`, since removed): a human's ~200-word
    explanation and the model's ~20-word report of the SAME fault, 2 seconds
    apart in the SAME recording, scored 0.023 under the old ratio — a
    genuine finding reported as a miss, because length asymmetry crushed the
    ratio before content ever mattered.

    Containment — what fraction of the SHORTER text's distinct (stopword-
    filtered) words also appear in the longer one — does not penalise
    brevity: a terse, accurate report scores as well as a verbose one, as
    long as its words are a real subset of what the human said. The SAME
    real pair scores 0.5 under this measure; a genuinely unrelated pair
    sharing only bug-report boilerplate ("field validation error prevents
    form submission on the ... screen") scores 0.0, because the shared words
    are exactly what STOPWORDS strips."""
    left_words = set(re.findall(r"\w+", left.casefold())) - STOPWORDS
    right_words = set(re.findall(r"\w+", right.casefold())) - STOPWORDS
    if not left_words or not right_words:
        return 0.0
    shorter, longer = (
        (left_words, right_words) if len(left_words) <= len(right_words)
        else (right_words, left_words)
    )
    return len(shorter & longer) / len(shorter)
