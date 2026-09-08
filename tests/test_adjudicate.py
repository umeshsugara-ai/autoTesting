"""ADJUDICATE is pure and deterministic — VL3/VL4.

The on-disk observation cache is only worth having if re-running the analysis
over it changes nothing. That makes determinism the load-bearing property here,
not a nicety: every test below is about the merge being a function of its
inputs and nothing else.

Contract: qa/contracts/video-learning.md VL3/VL4.
"""

from __future__ import annotations

import pytest
from video_fakes import FLASH, PRO, issue, obs, screen

from autotester.schema.enums import Confidence, IssueCategory, Severity
from autotester.stages.adjudicate import (
    adjudicate,
    join_issues,
    join_screens,
    screen_key,
    shift,
    worst,
)

# -- severity: the comparison I got backwards ------------------------------

def test_the_worst_severity_is_S1_not_S3() -> None:
    """`Severity` is declared S1, S2, S3 in DESCENDING severity — S1 blocks a
    core flow, S3 is cosmetic — so `max()` on it is backwards and reads as if
    it were right. That is how I first wrote it.

    An inverted comparison here would quietly DOWNGRADE every issue the two
    models disagreed about, and disagreement is exactly when severity matters
    most."""
    assert worst(Severity.S3, Severity.S1) is Severity.S1
    assert worst(Severity.S2, Severity.S3) is Severity.S2
    assert worst(Severity.S2, Severity.S1) is Severity.S1
    assert worst(Severity.S3, Severity.S3) is Severity.S3


def test_two_models_disagreeing_on_severity_keep_the_worse_one(
) -> None:
    merged = join_issues([
        (PRO, issue("Trainers", 10.0, severity=Severity.S3)),
        (FLASH, issue("Trainers", 12.0, severity=Severity.S1)),
    ])

    assert len(merged) == 1
    assert merged[0].severity is Severity.S1


# -- shift: timestamps move in code, never by the model --------------------

def test_a_chunks_timestamps_move_into_whole_video_time() -> None:
    """A model asked to add its own offset gets it wrong occasionally and
    silently, and every reported second depends on this being exact."""
    shifted = shift(obs(PRO, chunk=2, offset=330.0,
                        screens=[screen("Home", 5.0, 9.0)],
                        issues=[issue("Home", 7.0)]))

    assert shifted.observation.screens[0].t_start == 335.0
    assert shifted.observation.screens[0].t_end == 339.0
    assert shifted.observation.issues[0].t_start == 337.0


def test_shifting_does_not_mutate_the_cached_observation() -> None:
    """The cache is read many times. A shift that edited in place would make
    the second read wrong by one offset, and the third wrong by two."""
    original = obs(PRO, offset=100.0, screens=[screen("Home", 5.0)])

    shift(original)

    assert original.observation.screens[0].t_start == 5.0


def test_a_zero_offset_chunk_is_returned_unchanged() -> None:
    original = obs(PRO, offset=0.0, screens=[screen("Home", 5.0)])

    assert shift(original) is original


# -- screens: same name AND overlapping interval ---------------------------

def test_the_same_screen_seen_by_two_models_is_one_screen() -> None:
    merged = join_screens([
        (PRO, screen("Edit Trainer drawer", 3.0, 14.0)),
        (FLASH, screen("edit trainer  Drawer", 2.0, 15.0)),   # case + spacing differ
    ])

    assert len(merged) == 1
    assert merged[0].models_agreeing == 2
    assert sorted(merged[0].model_labels) == sorted([PRO, FLASH])
    assert (merged[0].t_start, merged[0].t_end) == (2.0, 15.0)


def test_the_same_screen_visited_twice_stays_two_visits() -> None:
    """A product often shows one screen twice in a recording. Merging those
    would erase the second visit from the journey, and the journey is what a
    human reads to understand the flow."""
    merged = join_screens([
        (PRO, screen("Trainers list", 5.0, 12.0)),
        (PRO, screen("Trainers list", 200.0, 210.0)),
    ])

    assert len(merged) == 2


def test_every_descriptive_list_only_one_model_noticed_survives_the_merge() -> None:
    """A union, not a choice: if one model saw something the other missed, it
    exists — the disagreement is about attention, not fact.

    It used to be named for `fields` and assert only on `signals`, which is
    exactly how AT-202 hid: `_merge_lists` dropped `fields`, and the one test
    whose NAME covered it never touched it. Now it asserts on each list."""
    merged = join_screens([
        (PRO, screen("Home", 1.0, 9.0, signals=["Dashboard"], fields=["Email"],
                     ui_elements=["Sign in"], url="")),
        (FLASH, screen("Home", 2.0, 9.0, signals=["Welcome"],
                       fields=["Email", "Password"], ui_elements=["Sign in", "Help"],
                       url="https://demo.test/home")),
    ])

    assert merged[0].signals == ["Dashboard", "Welcome"]
    assert merged[0].fields == ["Email", "Password"]
    assert merged[0].ui_elements == ["Sign in", "Help"]
    assert merged[0].url == "https://demo.test/home"


# -- issues: agreement raises confidence, never severity -------------------

def test_two_models_reporting_one_fault_merge_and_gain_confidence() -> None:
    merged = join_issues([
        (PRO, issue("Trainers", 8.0)),
        (FLASH, issue("Trainers", 15.0)),   # 7s apart: inside the window
    ])

    assert len(merged) == 1
    assert merged[0].models_agreeing == 2
    assert merged[0].confidence is Confidence.HIGH


def test_the_same_fault_reported_far_apart_stays_two_issues() -> None:
    """8s and 30s are 22s apart — beyond the window, so this is the product
    doing the same wrong thing twice, which is two findings."""
    merged = join_issues([
        (PRO, issue("Trainers", 8.0)),
        (PRO, issue("Trainers", 30.0)),
    ])

    assert len(merged) == 2


def test_different_categories_on_one_screen_stay_separate() -> None:
    merged = join_issues([
        (PRO, issue("Trainers", 8.0, category=IssueCategory.FEATURE_GAP)),
        (FLASH, issue("Trainers", 9.0, category=IssueCategory.DATA_ERROR)),
    ])

    assert len(merged) == 2


def test_one_model_alone_does_not_gain_confidence() -> None:
    """Agreement is the signal. A single model repeating itself is not
    agreement, and treating it as such would inflate every finding."""
    merged = join_issues([(PRO, issue("Trainers", 8.0))])

    assert merged[0].models_agreeing == 1
    assert merged[0].confidence is not Confidence.HIGH


def test_the_journey_follows_the_recording_in_time() -> None:
    analysis = adjudicate([
        obs(PRO, chunk=1, offset=165.0, screens=[screen("Second", 5.0, 9.0)]),
        obs(PRO, chunk=0, offset=0.0, screens=[screen("First", 1.0, 4.0)]),
    ], "src_1")

    assert [stop.name for stop in analysis.journey] == ["First", "Second"]


def test_an_empty_ensemble_produces_an_empty_analysis() -> None:
    analysis = adjudicate([], "src_1")

    assert analysis.screens == [] and analysis.issues == []
    assert analysis.source_id == "src_1"


@pytest.mark.parametrize("name,expected", [
    ("Edit Trainer", "edit trainer"),
    ("  edit   TRAINER  ", "edit trainer"),
    ("Edit\tTrainer", "edit trainer"),
])
def test_screen_keys_ignore_case_and_spacing(name: str, expected: str) -> None:
    assert screen_key(screen(name, 0.0)) == expected
