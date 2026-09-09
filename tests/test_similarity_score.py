"""`similarity_score.py`'s STOPWORDS-filtered containment measure, directly.

Split out of `test_score.py` (already at the 300-line cap) — one job (the
similarity function itself), separate from `score()`'s matching logic.

Contract: qa/contracts/video-learning.md (T-136 acceptance).
"""

from __future__ import annotations

import pytest

from autotester.schema.enums import IssueCategory, Severity
from autotester.schema.issue import Issue
from autotester.stages.score import TruthRow, score
from autotester.stages.similarity_score import STOPWORDS, similarity

# -- AT-276: a second measured false-positive tranche -----------------------
# Six pairs of genuinely DIFFERENT faults sharing only generic bug-report
# vocabulary, the same shape AT-232's own stress test found and closed for
# ONE word set. Five reproduce the checker's own reported pairs verbatim or
# from its named word groups; each must score BELOW the 0.30 threshold
# score() uses, now that STOPWORDS covers this vocabulary too.

FALSE_POSITIVE_PAIRS = [
    pytest.param(
        "Login button does not respond when clicked twice quickly on mobile",
        "Logout button does not respond when clicked twice quickly on desktop",
        id="login-vs-logout-button",
    ),
    pytest.param(
        "Notification badge count is wrong after marking messages as read",
        "Notification badge count is wrong after deleting messages",
        id="badge-count-marking-vs-deleting",
    ),
    pytest.param(
        "File upload fails silently when the file size exceeds the limit",
        "Video upload fails silently when the duration exceeds ten minutes",
        id="upload-fails-file-vs-video",
    ),
    pytest.param(
        "Search results do not update when the filter is changed on Trainers",
        "Search results do not update when the filter is changed on Applicants",
        id="search-filter-trainers-vs-applicants",
    ),
    pytest.param(
        "Export downloads a corrupted file when the report is large",
        "Import downloads a corrupted file when the dataset is large",
        id="export-vs-import-corrupted-file",
    ),
]


@pytest.mark.parametrize("left,right", FALSE_POSITIVE_PAIRS)
def test_generic_ui_action_vocabulary_does_not_falsely_match(left: str, right: str) -> None:
    assert similarity(left, right) < 0.30


# -- the real matches AT-232 fixed must still clear the threshold -----------
# Reproduced from the real ERP_Issues_Trainers.xlsx corpus (see AT-232's own
# manifest for the full derivation) -- a regression here would mean the
# STOPWORDS extension traded a false-positive fix for a false-negative one.

def test_the_real_asymmetric_length_match_still_clears_threshold() -> None:
    human = (
        "Home location offers centres only, so a trainer's actual home town cannot "
        "be recorded. The Home location dropdown on the trainer edit drawer is "
        "populated exclusively with training centres, drawn from the same list the "
        "assignment screen uses. A trainer's real home town, which is a free-text "
        "field on the application form and appears correctly on the applicant "
        "summary, is nowhere selectable here."
    )
    model = "Home Location field presents training centers instead of personal location"

    assert similarity(human, model) >= 0.30


def test_the_document_type_match_still_clears_threshold() -> None:
    human = "Document type is labelled 'CIPSA Certificate'; it should read 'CITS Certificate'"
    model = "Incorrect document type option"

    assert similarity(human, model) >= 0.30


# -- the extension is additive, not a replacement ----------------------------

def test_the_original_AT_232_boilerplate_case_still_rejects() -> None:
    """The stress pair AT-232's own manifest introduced must still reject --
    this extension adds vocabulary, it does not touch the mechanism."""
    left = ("Home location field validation error prevents form submission on "
           "the trainer edit screen")
    right = ("Date of birth field validation error prevents form submission on "
            "the applicant edit screen")

    assert similarity(left, right) < 0.30


def test_the_new_words_are_a_strict_superset_of_the_original_list() -> None:
    """A sanity check on the edit itself: AT-276 must not have accidentally
    REMOVED any of AT-232's original stopwords while adding new ones."""
    original = frozenset((
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "on", "in",
        "at", "to", "of", "for", "with", "and", "or", "not", "no", "but", "so", "than",
        "this", "that", "these", "those", "it", "its", "it's", "field", "fields", "error",
        "errors", "validation", "prevents", "allows", "form", "forms", "submission",
        "screen", "screens", "edit", "edits", "page", "pages", "should", "does", "do",
        "can", "cannot", "instead", "offers", "offer", "only", "actual", "real", "shows",
        "show", "appears", "reads", "presents",
    ))
    assert original <= STOPWORDS


# -- AT-278: a STOPWORDS-eroded short report is not evidence -----------------
# Growing STOPWORDS has a structural cost this floor closes: a content-bearing
# word added to the list (AT-276's own extension did this) can strip a short
# report down to one remaining word, and a 1-word containment is 0.0 or 1.0
# by construction -- never real evidence either way. Both pairs below are
# genuinely UNRELATED faults that AT-276's own extension alone drove to 1.0.

AT_278_PAIRS = [
    pytest.param(
        "Certificate export downloads corrupted when large",
        "Certificate generation crashes when the network is slow",
        id="export-corruption-vs-network-crash",
    ),
    pytest.param(
        "Trainer count updates wrong after filter change",
        "Trainer profile photo fails to render after refresh",
        id="count-update-vs-photo-render",
    ),
]


@pytest.mark.parametrize("left,right", AT_278_PAIRS)
def test_a_report_eroded_to_almost_nothing_does_not_falsely_match(
    left: str, right: str,
) -> None:
    assert similarity(left, right) < 0.30


def test_a_single_shared_word_is_never_evidence_of_a_match() -> None:
    """The floor's own reasoning, made direct: two texts sharing exactly one
    distinctive word must score 0.0, whatever that word is -- a 1-word
    containment can only ever be 0.0 or 1.0, and 1.0 is never trustworthy."""
    assert similarity("Certificate upload fails", "Certificate renders correctly") == 0.0


def test_the_floor_does_not_cost_a_genuinely_short_real_match() -> None:
    """Two distinctive words shared between a terse report and a fuller one
    still admit a real, floor-clearing match -- the floor refuses UNDER 2
    words, not every short pair."""
    assert similarity(
        "Trainer certificate upload rejected",
        "Trainer certificate upload was rejected by the server",
    ) >= 0.30


# -- AT-279: exact short content survives; one shared word never suffices ----

def _score_short_pair(truth_text: str, issue_text: str):
    row = TruthRow(
        id="E-short", title=truth_text, what_is_wrong="",
        recording="clip.mp4", at_s=10.0, row_number=2,
    )
    issue = Issue(
        project="demo", source_id="src_short", recording_label="clip.mp4", at_s=10.0,
        screen="Demo", title=issue_text, what_is_wrong="", severity=Severity.S2,
        category=IssueCategory.FEATURE_GAP,
    )
    return score([row], [issue])


def test_exact_one_token_content_is_a_full_match_through_the_real_scorer() -> None:
    card = _score_short_pair("Timeout", "timeout!")

    assert card.recall == 1.0
    assert card.false_positives == []


@pytest.mark.parametrize(("truth_text", "issue_text"), [
    ("Invoice rejected", "Invoice approved"),
    ("Password reset", "Password leaked"),
])
def test_one_shared_token_cannot_match_contradictory_short_reports(
    truth_text: str, issue_text: str,
) -> None:
    card = _score_short_pair(truth_text, issue_text)

    assert card.recall == 0.0
    assert card.false_positives == [issue_text]
