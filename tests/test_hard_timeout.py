"""The hard watchdog (crawl-live-hang): a blocked body fails fast instead of holding the suite."""

from __future__ import annotations

import subprocess
import sys
import time

import pytest
from hard_timeout import WatchdogTripped, hard_timeout

BOUND_S = 2.0
SLACK_S = 120.0  # child lookup runs PowerShell on Windows, slow on a busy host


def test_a_body_that_finishes_in_time_is_untouched() -> None:
    with hard_timeout(30.0, "quick body"):
        value = 1 + 1
    assert value == 2


def test_an_error_inside_the_bound_propagates_unchanged() -> None:
    with pytest.raises(ValueError, match="plain"), hard_timeout(30.0, "raising body"):
        raise ValueError("plain")


def test_a_sleeping_body_is_interrupted_and_fails_within_the_bound() -> None:
    started = time.monotonic()
    bound = hard_timeout(BOUND_S, "sleeping body")
    with pytest.raises(WatchdogTripped, match="sleeping body"), bound:
        time.sleep(10**6)
    assert time.monotonic() - started < BOUND_S + SLACK_S


def test_a_body_blocked_on_a_child_process_is_freed_by_killing_the_child() -> None:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10**6)"])
    try:
        with pytest.raises(WatchdogTripped), hard_timeout(BOUND_S, "child wait"):
            child.wait()
        assert child.poll() is not None, "the watchdog must kill the child it is blocked on"
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=30)
