"""AT-383 part A (D-048): `qa/hooks/mc-sessionstart.ps1` calls `autotester
loop-status --strict` and prints its report at session start.

Two layers, same split as `tests/test_session_start_hook.py`:

- Static, pure-Python parsing of the REAL `.ps1` on disk (portable -- runs on
  any host, including a Linux container with no PowerShell). This is what
  catches a regression that strips the `--strict` call, the exit-code check,
  or the try/catch entirely, even where PowerShell itself cannot run.
- Behavioural, real-PowerShell subprocess tests (Windows only, skipped
  elsewhere) that actually run the hook end to end against a healthy and an
  asleep `qa/.last-tick`, plus the tool-missing path with `uv` off PATH.

LS4 (qa/contracts/loop-status.md): `loop-status` is read-only and never part
of `doctor`'s verify chain. This hook call must not change that -- it only
prints; it must never make the session-start hook itself fail or hang.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "qa" / "hooks" / "mc-sessionstart.ps1"

_WINDOWS = sys.platform == "win32"
_PWSH = shutil.which("powershell") or shutil.which("pwsh")
_UV = shutil.which("uv")

windows_only = pytest.mark.skipif(
    not (_WINDOWS and _PWSH and _UV),
    reason="real PowerShell/uv subprocess test; needs Windows + powershell/pwsh + uv on PATH",
)


def hook_source() -> str:
    return HOOK.read_text(encoding="utf-8")


def hook_code() -> str:
    """The hook with comment lines stripped, mirroring test_session_start_hook.py's
    `hook_code()` -- the docstring above deliberately quotes the mechanism it
    protects, and that quoting must not itself satisfy the assertions below."""
    return "\n".join(
        line for line in hook_source().splitlines() if not line.lstrip().startswith("#")
    )


def test_the_hook_exists_where_the_protocol_expects_it() -> None:
    assert HOOK.exists(), f"enforcement path missing: {HOOK}"


_ARGS_RE = re.compile(r'\$lsPsi\.Arguments\s*=\s*"(.+)"\s*$', re.MULTILINE)


def loop_status_invocation() -> str:
    """The exact `Arguments` line the hook builds for the child process --
    not just "does --strict appear anywhere", since that word also appears
    (correctly) inside the unrelated `LOOP UNHEALTHY (loop-status --strict
    exit ...)` message string, which would make a loose substring check blind
    to the actual invocation losing `--strict` (row (a) must hit THIS line).
    PowerShell backtick-escapes the embedded `"$ROOT"` quotes, so this grabs
    the rest of the line rather than stopping at the first `"`."""
    match = _ARGS_RE.search(hook_code())
    assert match is not None, (
        "no $lsPsi.Arguments assignment found -- the invocation moved or was removed"
    )
    return match.group(1)


def test_the_hook_calls_loop_status_strict() -> None:
    """Row (a) of the C7 falsification: remove the --strict call, this fails."""
    invocation = loop_status_invocation()
    assert "loop-status" in invocation, "the hook no longer invokes loop-status at all"
    assert "--strict" in invocation, "the hook invokes loop-status but dropped --strict"


def test_the_hook_checks_the_exit_code() -> None:
    """Row (b): drop the exit-code check, this fails."""
    code = hook_code()
    assert "ExitCode" in code, "the hook no longer inspects the loop-status process exit code"
    assert "LOOP UNHEALTHY" in code, "the hook no longer prints the unhealthy warning line"


def test_the_hook_wraps_the_call_so_a_failure_cannot_propagate() -> None:
    """Row (c): let a failure propagate (no try/catch), this fails. A liveness
    probe that can crash or hang session start is worse than the silence it
    replaces -- same reasoning loop_status.py itself states for LS4."""
    code = hook_code()
    assert "try {" in code and "catch {" in code, (
        "the loop-status call is not wrapped in try/catch -- an unavailable uv/autotester "
        "would propagate and could fail the whole session-start hook"
    )
    assert "WaitForExit" in code, "the loop-status call has no bounded timeout"


def test_the_hooks_own_exit_code_is_unconditional_zero() -> None:
    """The new block must not touch the hook's existing `exit 0` contract."""
    tail = hook_source().rstrip().splitlines()[-1]
    assert tail.strip() == "exit 0", f"hook no longer ends on an unconditional exit 0: {tail!r}"


def _run_hook(cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell.exe" if shutil.which("powershell") else "pwsh",
         "-NoProfile", "-NonInteractive", "-File", str(HOOK)],
        cwd=cwd, env=env, capture_output=True, text=True, timeout=60,
    )


def _base_env(**overrides: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update(overrides)
    return env


@windows_only
def test_hook_prints_the_report_and_exits_zero_on_a_healthy_log(tmp_path: Path) -> None:
    qa = tmp_path / "qa"
    qa.mkdir()
    (qa / "manifests").mkdir()
    recent = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    (qa / ".last-tick").write_text(recent + " . TICK . healthy\n", encoding="utf-8")

    result = _run_hook(REPO, _base_env(AUTOTESTER_ROOT=str(tmp_path)))

    assert result.returncode == 0, result.stderr
    assert "ticks: 1" in result.stdout
    assert "LOOP UNHEALTHY" not in result.stdout


@windows_only
def test_hook_prints_unhealthy_line_only_on_an_asleep_log_and_still_exits_zero(
    tmp_path: Path,
) -> None:
    qa = tmp_path / "qa"
    qa.mkdir()
    (qa / "manifests").mkdir()
    stale = (datetime.now(UTC) - timedelta(hours=10)).isoformat()
    (qa / ".last-tick").write_text(stale + " . TICK . asleep\n", encoding="utf-8")

    result = _run_hook(REPO, _base_env(AUTOTESTER_ROOT=str(tmp_path)))

    assert result.returncode == 0, result.stderr
    assert "LOOP UNHEALTHY (loop-status --strict exit 1)" in result.stdout


@windows_only
def test_hook_skips_cleanly_when_uv_is_unavailable(tmp_path: Path) -> None:
    qa = tmp_path / "qa"
    qa.mkdir()
    (qa / "manifests").mkdir()
    recent = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    (qa / ".last-tick").write_text(recent + " . TICK . healthy\n", encoding="utf-8")

    # A PATH with no uv on it, but still enough for powershell.exe itself and
    # Windows' own base commands to run (System32 stays).
    stripped_path = r"C:\Windows\System32;C:\Windows"
    env = _base_env(AUTOTESTER_ROOT=str(tmp_path), Path=stripped_path, PATH=stripped_path)

    result = _run_hook(REPO, env)

    assert result.returncode == 0, result.stderr
    assert "loop-status: skipped (uv/autotester unavailable)" in result.stdout
    assert "LOOP UNHEALTHY" not in result.stdout
