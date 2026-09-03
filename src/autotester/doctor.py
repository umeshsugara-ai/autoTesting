"""Design enforcement. Runs the rules that keep this repo readable.

These limits are not style preferences. They exist because the previous project
(d:/erp) lost human control when files, duplicated concepts, and root-level
scratch grew unchecked. `autotester doctor` fails the build before that starts.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from autotester.core.paths import repo_root

MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50
BANNED_NAME_HINTS = ("_v2", "_new", "_old", "_copy", "_final", "_temp")
ALLOWED_ROOT_ENTRIES = {
    ".claude", ".git", ".gitignore", ".goal", ".python-version", ".venv", ".work",
    "CLAUDE.md", "README.md", "docs", "goal.md", "profiles", "projects",
    "pyproject.toml", "qa", "scripts", "src", "tests", "uv.lock",
}


@dataclass(frozen=True)
class Violation:
    rule: str
    location: str
    detail: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.location} — {self.detail}"


def _python_files(root: Path) -> list[Path]:
    return [
        p
        for p in (root / "src").rglob("*.py")
        if ".venv" not in p.parts and "__pycache__" not in p.parts
    ]


def check_file_sizes(root: Path) -> list[Violation]:
    out = []
    for path in _python_files(root) + list((root / "tests").glob("*.py")):
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > MAX_FILE_LINES:
            out.append(Violation("file-too-long", str(path.relative_to(root)),
                                 f"{lines} lines > {MAX_FILE_LINES}; split by responsibility"))
    return out


def check_function_sizes(root: Path) -> list[Violation]:
    out = []
    for path in _python_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno:
                length = node.end_lineno - node.lineno
                if length > MAX_FUNCTION_LINES:
                    out.append(Violation("function-too-long",
                                         f"{path.relative_to(root)}:{node.lineno}",
                                         f"{node.name} is {length} lines > {MAX_FUNCTION_LINES}"))
    return out


def check_file_names(root: Path) -> list[Violation]:
    out = []
    for path in _python_files(root):
        if any(hint in path.stem for hint in BANNED_NAME_HINTS):
            out.append(Violation("drift-filename", str(path.relative_to(root)),
                                 "edit the original in place instead of versioning the filename"))
    return out


def check_root_clean(root: Path) -> list[Violation]:
    out = []
    for entry in root.iterdir():
        if entry.name not in ALLOWED_ROOT_ENTRIES and not entry.name.startswith("."):
            out.append(Violation("root-clutter", entry.name,
                                 "scratch and evidence belong in .work/, not the repo root"))
    return out


def check_duplicate_definitions(root: Path) -> list[Violation]:
    """Same class or top-level function name defined in two modules = drift."""
    seen: dict[str, str] = {}
    out = []
    for path in _python_files(root):
        rel = str(path.relative_to(root))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and not node.name.startswith("_"):
                if node.name in seen and seen[node.name] != rel:
                    out.append(Violation("duplicate-concept", f"{rel}:{node.lineno}",
                                         f"'{node.name}' also defined in {seen[node.name]}"))
                seen.setdefault(node.name, rel)
    return out


def run(root: Path | None = None) -> list[Violation]:
    """All checks, in reporting order."""
    base = root or repo_root()
    violations: list[Violation] = []
    for check in (check_file_sizes, check_function_sizes, check_file_names,
                  check_root_clean, check_duplicate_definitions):
        violations.extend(check(base))
    return violations
