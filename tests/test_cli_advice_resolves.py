"""Every command this codebase tells an operator to run must actually exist.

AT-163 → AT-172. Three fix cycles of T-132 went on one message naming
`autotester media prep`, a command the CLI does not expose. The cycle-3 checker
then found `autotester ingest analyze` — the *same dead end, one command over,
in the same file*, and it survived precisely because the contract criterion was
scoped to the one message that had been caught.

Fixing instances of that was not working. This tests the SHAPE: it finds every
`autotester …` string in `src/` and asks the CLI to resolve it. A message that
sends someone to a command that does not exist is worse than no message —
it costs them the time to try it and the doubt about whether they typed it
wrong.

Contract: qa/contracts/video-learning.md VL1d, generalised.
"""

from __future__ import annotations

import ast
import re
import shlex
from pathlib import Path

import pytest
from typer.testing import CliRunner

from autotester.cli import app

SRC = Path(__file__).resolve().parents[1] / "src" / "autotester"
ADVICE = re.compile(r"`autotester ([^`{}\n]+)`")
"""Backtick-quoted advice only. A string carrying `{...}` is a template whose
arguments are interpolated at runtime; the COMMAND part of those is checked
separately by the caller's own test, and guessing their values here would test
a fiction."""

runner = CliRunner()


def _runtime_strings(source: str) -> list[str]:
    """Only strings the program can actually PRINT — via `ast`, not regex.

    Comments and docstrings are prose about the code, not advice to an
    operator, and both legitimately quote dead commands while explaining that
    they are dead. My first cut scanned raw text and failed on my own AT-163
    comment; my second stripped `#` lines and still failed on the `PREP_COMMAND`
    docstring, which documents the very bug it names.

    An AST walk draws the line exactly where it belongs: a docstring is the
    first statement of a module, class or function and is skipped; every other
    string constant is something the program might hand a human."""
    tree = ast.parse(source)
    # A string that is an ENTIRE STATEMENT is documentation by construction:
    # evaluating it does nothing, so the program can never hand it to anyone.
    # That covers real docstrings and the variable-docstring convention this
    # codebase uses (a bare string under an assignment), which the narrower
    # module/class/function rule missed -- `PREP_COMMAND`'s own docstring, which
    # exists to explain that `autotester media prep` is dead, was collected as
    # if it advised running it.
    docstrings = {
        id(node.value) for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and id(n) not in docstrings]


def advice_in_source() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for path in sorted(SRC.rglob("*.py")):
        for literal in _runtime_strings(path.read_text(encoding="utf-8")):
            for match in ADVICE.finditer(literal):
                found.append((path.relative_to(SRC), match.group(1).strip()))
    return found


def test_the_codebase_actually_offers_advice_to_check() -> None:
    """A collector that silently finds nothing would make every assertion below
    vacuously true — the exact failure mode this file exists to catch."""
    assert len(advice_in_source()) >= 3


@pytest.mark.parametrize("where,command", advice_in_source(),
                         ids=lambda v: str(v).replace("/", "_"))
def test_every_command_the_code_names_is_one_the_cli_exposes(
    where: Path, command: str,
) -> None:
    """click prints its `Usage:` banner for an unregistered command, an
    unregistered subcommand and the wrong arity alike, so its absence is one
    oracle covering all three. Measured, not assumed (AT-171)."""
    # The regex captures what follows "autotester", so the whole capture IS the
    # argv. My first version sliced [1:] as if the binary name were still
    # there, which turned `ingest run` into `run` -- a test failing on its own
    # bug, reported as the code's.
    argv = [*shlex.split(command), "--help"]

    result = runner.invoke(app, argv)

    assert "Usage:" not in result.output or "--help" in result.output, (
        f"{where} tells an operator to run `autotester {command}`, "
        f"which the CLI does not expose: {' '.join(result.output.split())[:140]!r}")
    assert "No such command" not in result.output, (
        f"{where} names a command that does not exist: `autotester {command}`")
