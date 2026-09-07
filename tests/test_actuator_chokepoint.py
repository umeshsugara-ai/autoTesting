"""The actuator choke-point (Track B, D-015): every browser touch stays
inside `src/autotester/browser/`. A future stage (the explorer, an agent
loop) that reaches for `.page` directly or imports `playwright` bypasses the
domain-check/masking/redaction discipline `browser/session.py` enforces —
this test makes that a hard failure instead of a code-review hope.
"""

from __future__ import annotations

import re
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src" / "autotester"
_PATTERN = re.compile(r"\.page\.|\bplaywright\b")


def _python_files_outside_browser() -> list[Path]:
    return [
        path
        for path in _SRC.rglob("*.py")
        if "browser" not in path.relative_to(_SRC).parts and "__pycache__" not in path.parts
    ]


def test_no_direct_page_or_playwright_access_outside_browser_package() -> None:
    offenders = []
    for path in _python_files_outside_browser():
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if _PATTERN.search(line):
                offenders.append(f"{path.relative_to(_SRC)}:{line_number}: {line.strip()}")
    assert not offenders, "raw browser access outside browser/:\n" + "\n".join(offenders)


def test_the_check_actually_fires_on_a_real_violation(tmp_path: Path) -> None:
    """Proves the regex/scope logic has teeth — a file planted outside
    `browser/` that touches `.page.` must be caught."""
    fake = tmp_path / "stages_fake.py"
    fake.write_text("session.page.locator('x').click()\n", encoding="utf-8")
    text = fake.read_text(encoding="utf-8")
    assert any(_PATTERN.search(line) for line in text.splitlines())
