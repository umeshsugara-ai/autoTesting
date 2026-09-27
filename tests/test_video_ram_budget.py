"""T-191/AT-587 V6(a): recording costs resident memory per browser context
beyond `DEFAULT_PER_CONTEXT_MB`, so `plan_parallel_run`'s concurrency decision
must actually change when video is on, at the same measured free RAM -- never
silently plan the same width as an unrecorded run. Contract:
qa/contracts/run-video.md V6. Fixture-only: `cpu_count`/`free_ram_mb` are
injected (never this host's live memory), the same discipline
`test_parallel_run.py` itself uses.
"""

from __future__ import annotations

from autotester.browser.video import VIDEO_OVERHEAD_MB
from autotester.schema.enums import WritePolicy
from autotester.schema.project import Project
from autotester.stages.parallel_run import DEFAULT_PER_CONTEXT_MB, plan_parallel_run


def _project(max_parallel: int = 8) -> Project:
    return Project(slug="p1", name="P1", base_url="https://p1.test", max_parallel=max_parallel,
                   write_policy=WritePolicy.READ_ONLY)


def test_video_enabled_plans_fewer_concurrent_slots_than_video_disabled_at_the_same_ram() -> None:
    # Exactly 5 slots' worth of free RAM for the unrecorded (512MB/context) case.
    free_ram_mb = 2048.0 + 5 * DEFAULT_PER_CONTEXT_MB

    off = plan_parallel_run(_project(), cpu_count=8, free_ram_mb=free_ram_mb)
    on = plan_parallel_run(_project(), cpu_count=8, free_ram_mb=free_ram_mb, video_enabled=True)

    assert off.n == 5
    assert on.n < off.n, "recording overhead must shrink the plan at the same measured RAM"
    assert on.measured_budget == int(
        (free_ram_mb - 2048.0) // (DEFAULT_PER_CONTEXT_MB + VIDEO_OVERHEAD_MB)
    )


def test_video_disabled_is_unchanged_from_before_this_unit() -> None:
    """C2: an unrecorded run's plan must be bit-for-bit what it already was --
    `video_enabled` defaults to False, so every existing caller (and every
    pre-T-191 test) sees no behavior change."""
    free_ram_mb = 2048.0 + 3 * DEFAULT_PER_CONTEXT_MB

    implicit = plan_parallel_run(_project(), cpu_count=8, free_ram_mb=free_ram_mb)
    explicit_off = plan_parallel_run(_project(), cpu_count=8, free_ram_mb=free_ram_mb,
                                     video_enabled=False)

    assert implicit == explicit_off


def test_video_overhead_constant_is_a_real_positive_number_not_a_placeholder() -> None:
    assert VIDEO_OVERHEAD_MB > 0
