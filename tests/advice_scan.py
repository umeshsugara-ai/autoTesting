"""Find every command this codebase tells a human to run — a helper, not a test.

The naive version of this scanned string *literals* and missed the one site the
whole class exists for. `stages/media_prep.py` builds its advice as

    f"... run `{PREP_COMMAND} " f"{slug} {source_id}` on the HOST first"

so the backtick lives in one f-string part and the command name in a module
constant somewhere else. Two different AST nodes, no single literal containing
both — invisible to any regex over constants (AT-176, filed after a checker
pointed `PREP_COMMAND` back at the dead `autotester media prep` and the guard
returned **zero** failures).

So this does not scan literals. It **renders** each string the way Python will:
adjacent parts joined, and an interpolated name substituted when it refers to a
module-level string constant. Then it reads commands out of the rendered text,
backticked or not (AT-178).

It is still static — no import, no execution — so a value that only exists at
runtime stays a hole, and `UNRESOLVED` marks it rather than pretending.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

UNRESOLVED = "\x00"
"""Stands in for an interpolation this cannot resolve. Chosen so it can never
appear in a real command name, and so a partially-rendered string is visibly
partial rather than quietly wrong."""

COMMAND = re.compile(r"autotester ((?:[a-z][a-z-]*)(?: [a-z][a-z-]*)*)")
"""`autotester` followed by lowercase words. Not anchored on backticks: the
un-backticked advice at `core/consent.py` was invisible to the version that
required them (AT-178), and a message is no less wrong for lacking quotes."""


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level `NAME = "literal"` bindings, which is how this codebase
    holds command names (`PREP_COMMAND`) so they live in one place."""
    out: dict[str, str] = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            out[node.targets[0].id] = node.value.value
    return out


def _render(node: ast.expr, constants: dict[str, str]) -> str:
    """The text this expression will produce, as far as it can be known."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else UNRESOLVED
    if isinstance(node, ast.JoinedStr):
        return "".join(_render(part, constants) for part in node.values)
    if isinstance(node, ast.FormattedValue):
        inner = node.value
        if isinstance(inner, ast.Name) and inner.id in constants:
            return constants[inner.id]
        return UNRESOLVED
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _render(node.left, constants) + _render(node.right, constants)
    return UNRESOLVED


def _is_documentation(tree: ast.Module) -> set[int]:
    """Ids of strings that are an ENTIRE statement.

    Evaluating one does nothing, so the program can never hand it to anyone.
    That covers real docstrings and this codebase's variable-docstring
    convention — including `PREP_COMMAND`'s own, which exists to explain that
    `autotester media prep` is dead and must not be read as advising it."""
    return {id(node.value) for node in ast.walk(tree)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)}


def advice_in(source: str) -> list[str]:
    """Every command named in a string this module could actually print."""
    tree = ast.parse(source)
    constants = _module_constants(tree)
    documentation = _is_documentation(tree)

    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant | ast.JoinedStr | ast.BinOp):
            continue
        if id(node) in documentation:
            continue
        text = _render(node, constants)
        for match in COMMAND.finditer(text):
            command = match.group(1).strip()
            if command and UNRESOLVED not in command:
                found.append(command)
    return found


def advice_in_source(src_dir: Path) -> list[tuple[Path, str]]:
    """Deduped: one row per (file, command). A JoinedStr and the Constant inside
    it both render the same advice, and reporting it twice would only make the
    parametrized ids noisier."""
    seen: set[tuple[str, str]] = set()
    out: list[tuple[Path, str]] = []
    for path in sorted(src_dir.rglob("*.py")):
        where = path.relative_to(src_dir)
        for command in advice_in(path.read_text(encoding="utf-8")):
            if (str(where), command) in seen:
                continue
            seen.add((str(where), command))
            out.append((where, command))
    return out
