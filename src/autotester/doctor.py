"""Design enforcement. Runs the rules that keep this repo readable.

These limits are not style preferences. They exist because the previous project
(d:/erp) lost human control when files, duplicated concepts, and root-level
scratch grew unchecked. `autotester doctor` fails the build before that starts.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from autotester.core.paths import RepoDocs, repo_root

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


def check_generated_fresh(root: Path) -> list[Violation]:
    """L1: ARCHITECTURE generated sections and SNAPSHOT must equal a fresh regeneration."""
    from autotester.ledger.render import apply_map, render_snapshot

    docs = RepoDocs(root)
    out = []
    if docs.map.exists():
        try:
            if apply_map(docs) != docs.map.read_text(encoding="utf-8"):
                out.append(Violation("stale-generated", "docs/MAP.md",
                                     "generated sections differ; run `autotester map`"))
        except ValueError as exc:
            out.append(Violation("stale-generated", "docs/MAP.md", str(exc)))
    if docs.snapshot.exists() or docs.features.exists():
        current = docs.snapshot.read_text(encoding="utf-8") if docs.snapshot.exists() else ""
        try:
            fresh = render_snapshot(docs)
        except Exception as exc:  # a broken ledger is reported by check_ledger, not raised here
            out.append(Violation("stale-generated", "docs/SNAPSHOT.md",
                                 f"cannot regenerate: {type(exc).__name__}"))
            return out
        if fresh != current:
            out.append(Violation("stale-generated", "docs/SNAPSHOT.md",
                                 "differs from regeneration; run `autotester snapshot`"))
    return out


def check_ledger(root: Path) -> list[Violation]:
    """L2/L3: every FEATURES.jsonl row validates; closed high-value tasks have a row."""
    from autotester.ledger.store import check_rows_on_pass, load_events, load_goal_tasks

    docs = RepoDocs(root)
    try:
        events = load_events(docs.features)
    except Exception as exc:  # a doctor reports, it never tracebacks (AT-021)
        return [Violation("ledger-invalid", "docs/FEATURES.jsonl", f"{type(exc).__name__}: {exc}")]
    missing = check_rows_on_pass(events, load_goal_tasks(docs.goal))
    return [Violation("ledger-row-missing", task, "closed high-value task has no live/updated row")
            for task in missing]


def check_architecture_budget(root: Path) -> list[Violation]:
    """C2: ARCHITECTURE.md stays within its line budget (AT-019)."""
    from autotester.ledger.render import ARCHITECTURE_MAX_LINES

    path = RepoDocs(root).architecture
    if not path.exists():
        return []
    lines = len(path.read_text(encoding="utf-8").splitlines())
    if lines > ARCHITECTURE_MAX_LINES:
        return [Violation("architecture-too-long", "docs/ARCHITECTURE.md",
                          f"{lines} lines > {ARCHITECTURE_MAX_LINES}; move detail to a routed doc")]
    return []


def check_docs_routed(root: Path) -> list[Violation]:
    """L6: every docs/*.md self-describes and is listed in the CLAUDE.md router, and vice versa."""
    from autotester.ledger.render import doc_header_missing, router_paths

    docs = RepoDocs(root)
    if not docs.docs_dir.exists():
        return []
    out = []
    routed = router_paths(docs.router)
    on_disk = {p.relative_to(root).as_posix() for p in docs.docs_dir.rglob("*.md")}
    for path in sorted(on_disk):
        if doc_header_missing(root / path):
            out.append(Violation("doc-header-missing", path,
                                 "needs **Purpose:** and **Open me when:**"))
        if path not in routed:
            out.append(Violation("doc-unrouted", path,
                                 "add a row to the router table in CLAUDE.md"))
    for path in sorted(routed - on_disk):
        if path.endswith(".md"):
            out.append(Violation("router-dangling", path, "router names a doc that does not exist"))
    return out


def run(root: Path | None = None) -> list[Violation]:
    """All checks, in reporting order."""
    base = root or repo_root()
    violations: list[Violation] = []
    for check in (check_file_sizes, check_function_sizes, check_file_names,
                  check_root_clean, check_duplicate_definitions,
                  check_ledger, check_generated_fresh, check_architecture_budget,
                  check_docs_routed):
        violations.extend(check(base))
    return violations
