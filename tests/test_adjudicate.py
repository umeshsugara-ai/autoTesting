"""ADJUDICATE is pure and deterministic — VL3/VL4.

The on-disk observation cache is only worth having if re-running the analysis
over it changes nothing. That makes determinism the load-bearing property here,
not a nicety: every test below is about the merge being a function of its
inputs and nothing else.

Contract: qa/contracts/video-learning.md VL3/VL4.
"""

from __future__ import annotations

import random

import pytest

from autotester.schema.enums import Confidence, IssueCategory, Severity
from autotester.schema.observation import (
    ModelObservation,
    ObservedIssue,
    ObservedScreen,
    VideoObservation,
)
from autotester.stages.adjudicate import (
    adjudicate,
    join_issues,
    join_screens,
    screen_key,
    shift,
    worst,
)

PRO = "gemini:gemini-3.1-pro-preview"
FLASH = "gemini:gemini-3.8-flash"


def obs(label: str, *, chunk: int = 0, offset: float = 0.0,
        screens: list[ObservedScreen] | None = None,
        issues: list[ObservedIssue] | None = None,
        summary: str = "") -> ModelObservation:
    return ModelObservation(
        source_id="src_1", provider_label=label, prompt_name="video_issues_v1",
        chunk_index=chunk, offset_s=offset, length_s=180.0,
        observation=VideoObservation(screens=screens or [], issues=issues or [],
                                     summary=summary),
    )


def screen(name: str, t_start: float, t_end: float | None = None, **kw) -> ObservedScreen:
    return ObservedScreen(name=name, t_start=t_start, t_end=t_end, **kw)


def issue(screen_name: str, t_start: float, *, category: IssueCategory = IssueCategory.OTHER,
          severity: Severity = Severity.S2, **kw) -> ObservedIssue:
    return ObservedIssue(screen=screen_name, t_start=t_start, category=category,
                         severity=severity, title=kw.pop("title", "t"),
                         what_is_wrong=kw.pop("what_is_wrong", "w"), **kw)


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


def test_a_field_only_one_model_noticed_survives_the_merge() -> None:
    """A union, not a choice: if one model saw a field the other missed, the
    field exists — the disagreement is about attention, not fact."""
    merged = join_screens([
        (PRO, screen("Home", 1.0, 9.0, signals=["Dashboard"], url="")),
        (FLASH, screen("Home", 2.0, 9.0, signals=["Welcome"],
                       url="https://demo.test/home")),
    ])

    assert merged[0].signals == ["Dashboard", "Welcome"]
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


# -- the property the cache rests on ---------------------------------------

def content(analysis) -> str:
    """The analysis WITHOUT its provenance envelope.

    `Artifact.created_at` is a wall-clock stamp, so two calls a microsecond
    apart differ there and nowhere else. Comparing whole JSON conflated
    "adjudication is deterministic" with "the clock did not tick" — my first
    version of the determinism test failed on exactly that, and my
    adjudicate-twice test PASSED only because both calls landed in the same
    microsecond. Determinism is a property of the CONTENT."""
    return analysis.model_dump_json(exclude={"created_at", "provenance"})


def test_the_result_does_not_depend_on_input_order() -> None:
    """VL4. If loading order changed the output, the cached observations would
    produce a different analysis every run and re-running would mean nothing."""
    observations = [
        obs(PRO, chunk=0, offset=0.0, screens=[screen("Home", 1.0, 9.0)],
            issues=[issue("Home", 5.0)], summary="a"),
        obs(FLASH, chunk=0, offset=0.0, screens=[screen("home", 2.0, 8.0)], summary="b"),
        obs(PRO, chunk=1, offset=165.0, screens=[screen("Trainers", 10.0, 20.0)]),
        obs(FLASH, chunk=1, offset=165.0, screens=[screen("Trainers", 11.0, 21.0)],
            issues=[issue("Trainers", 12.0)]),
    ]
    baseline = content(adjudicate(observations, "src_1"))

    for seed in range(8):
        shuffled = list(observations)
        random.Random(seed).shuffle(shuffled)
        assert content(adjudicate(shuffled, "src_1")) == baseline


def test_adjudicating_twice_gives_byte_identical_output() -> None:
    observations = [obs(PRO, screens=[screen("Home", 1.0, 9.0)])]

    first = content(adjudicate(observations, "src_1"))
    second = content(adjudicate(observations, "src_1"))

    assert first == second


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
