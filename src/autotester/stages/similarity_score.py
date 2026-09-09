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
    # AT-276: a second measured false-positive tranche, the SAME boilerplate
    # shape as AT-232's original example recurring in a different vocabulary
    # (generic UI-action words, not this one product's field-validation
    # phrasing). Six pairs of genuinely DIFFERENT faults, constructed from the
    # checker's own reported word groups, scored 0.50-0.86 before this
    # addition; all five reproducible pairs score 0.0 after (see
    # test_similarity_score.py). Real matches (the E-01/E-02/E-03 pairs
    # AT-232 fixed) re-verified to still clear the 0.30 threshold.
    "button", "respond", "responds", "clicked", "click", "twice", "quickly",
    "upload", "uploads", "uploading", "fails", "fail", "silently", "exceeds", "exceed",
    "notification", "notifications", "badge", "count", "wrong", "messages", "message",
    "search", "results", "result", "update", "updates", "filter", "filters",
    "export", "exports", "import", "imports", "downloads", "download", "corrupted",
    "file", "files", "large", "when", "after", "marking", "mark", "deleting", "delete",
    "changed", "change",
))
"""AT-232/AT-276: a curated, in-file list — dumb and auditable, not
exhaustive. Its job is only to strip the boilerplate a bug-report vocabulary
repeats across UNRELATED faults ("field", "validation", "button", "clicked",
"upload", "notification"...) so containment measures distinctive content,
not shared phrasing or genre. Known limitation, stated rather than hidden: a
real fault whose distinctive words happen to be common English or common
bug-report vocabulary will score lower than it should, and a false positive
in a NEW vocabulary not yet seen will recur — this list grows by measurement,
not by anticipation. Extend it only on a measured false positive, never by
guess."""


MIN_SHARED_DISTINCTIVE_WORDS = 2
"""AT-278/AT-279: non-identical reports need at least two shared distinctive
words. One shared word is too coarse at both a one-word and two-word
denominator; exact normalized content has its own unambiguous path."""


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
    are exactly what STOPWORDS strips.

    AT-278/AT-279: STOPWORDS growth can erode the shorter denominator until
    one incidental shared word scores 0.5 or 1.0. Exact normalized content
    remains a full match; every non-identical pair needs at least two shared
    distinctive words before containment is meaningful."""
    left_tokens = tuple(re.findall(r"\w+", left.casefold()))
    right_tokens = tuple(re.findall(r"\w+", right.casefold()))
    if left_tokens and left_tokens == right_tokens:
        return 1.0
    left_words = set(left_tokens) - STOPWORDS
    right_words = set(right_tokens) - STOPWORDS
    if not left_words or not right_words:
        return 0.0
    shorter, longer = (
        (left_words, right_words) if len(left_words) <= len(right_words)
        else (right_words, left_words)
    )
    if len(shorter & longer) < MIN_SHARED_DISTINCTIVE_WORDS:
        return 0.0
    return len(shorter & longer) / len(shorter)
