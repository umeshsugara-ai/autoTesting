"""Derive the living docs from code and the ledger. Nothing here is hand-typed.

`render_map` fills the generated sections of ARCHITECTURE.md (directory map from
module docstrings, schema summary from the models). `render_snapshot` writes the
lean session-start digest. `doctor` regenerates both and fails on any diff.
"""

from __future__ import annotations

import ast
import re
from datetime import timedelta
from pathlib import Path

from autotester.core.paths import RepoDocs
from autotester.ledger.store import latest_by_feature, live, load_events, load_goal_tasks
from autotester.schema.enums import FeatureEventKind, UserValue

SNAPSHOT_MAX_LINES = 60
ARCHITECTURE_MAX_LINES = 150
HIGH_FEATURES_SHOWN = 8
RECENT_DAYS = 30
_HEADER_RE = re.compile(r"^## (D-\d+) \| (\d{4}-\d{2}-\d{2}) \| type: (\w+) \| status: (\w+)")
_SUPERSEDES_RE = re.compile(r"^\*\*Supersedes:\*\*\s*(.+?)\s--\s")
_ROUTER_PATH_RE = re.compile(r"`(docs/[\w./-]+)`")


# -- generated sections -----------------------------------------------------

def marker(name: str) -> tuple[str, str]:
    return f"<!-- generated:{name} -->", f"<!-- /generated:{name} -->"


def replace_generated(text: str, name: str, body: str) -> str:
    """Swap the body between `name`'s markers. Markers must already exist."""
    start, end = marker(name)
    if start not in text or end not in text:
        raise ValueError(f"markers for generated section '{name}' not found")
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    return f"{head}{start}\n{body.rstrip()}\n{end}{tail}"


def _first_docstring_line(path: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    except SyntaxError:
        return "(unparseable)"
    return doc.strip().splitlines()[0] if doc.strip() else "(no docstring)"


def _class_summaries(path: Path) -> list[tuple[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            doc = (ast.get_docstring(node) or "").strip().splitlines()
            out.append((node.name, doc[0] if doc else ""))
    return out


def render_map(root: Path) -> dict[str, str]:
    """Bodies for the two generated sections: `map` and `schema`."""
    pkg = root / "src" / "autotester"
    rows = ["| Module | One job |", "|---|---|"]
    for path in sorted(pkg.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "__init__.py":
            continue
        rows.append(f"| `{path.relative_to(pkg).as_posix()}` | {_first_docstring_line(path)} |")
    schema_rows = ["| Model | Meaning |", "|---|---|"]
    for path in sorted((pkg / "schema").glob("*.py")):
        if path.name in ("__init__.py", "enums.py"):
            continue
        for name, doc in _class_summaries(path):
            schema_rows.append(f"| `{name}` (`schema/{path.name}`) | {doc} |")
    return {"map": "\n".join(rows), "schema": "\n".join(schema_rows)}


def apply_map(docs: RepoDocs) -> str:
    """docs/MAP.md with its generated sections refreshed (AT-019: not in ARCHITECTURE)."""
    text = docs.map.read_text(encoding="utf-8")
    for name, body in render_map(docs.root).items():
        text = replace_generated(text, name, body)
    return text


# -- decisions index --------------------------------------------------------

def decision_index(decisions_path: Path) -> list[tuple[str, str, str, str]]:
    """(id, date, type, computed status) for every entry, in file order."""
    if not decisions_path.exists():
        return []
    entries: list[list[str]] = []
    superseded: dict[str, str] = {}
    current: str | None = None
    for line in decisions_path.read_text(encoding="utf-8").splitlines():
        head = _HEADER_RE.match(line)
        if head:
            current = head.group(1)
            entries.append([current, head.group(2), head.group(3), head.group(4)])
            continue
        sup = _SUPERSEDES_RE.match(line)
        if sup and current:
            for target in re.findall(r"D-\d+", sup.group(1)):
                superseded[target] = current
    out = []
    for entry_id, day, kind, status in entries:
        if entry_id in superseded:
            status = f"SUPERSEDED (by {superseded[entry_id]})"
        out.append((entry_id, day, kind, status))
    return out


# -- snapshot ---------------------------------------------------------------

def _product_paragraph(architecture: Path) -> list[str]:
    text = architecture.read_text(encoding="utf-8") if architecture.exists() else ""
    section = text.split("## What it does", 1)[-1].split("\n## ", 1)[0]
    return [line for line in section.strip().splitlines() if line.strip()][:6]


def _feature_lines(docs: RepoDocs) -> list[str]:
    events = load_events(docs.features)
    current = live(events)
    lines = ["## Live features"]
    high = [e for e in current if e.user_value is UserValue.HIGH]
    normal = [e for e in current if e.user_value is not UserValue.HIGH]
    shown = sorted(high, key=lambda x: x.id)
    for e in shown[:HIGH_FEATURES_SHOWN]:
        lines.append(f"- {e.id} **{e.title}** [high] — {e.description} · reason: {e.reason}")
    if len(shown) > HIGH_FEATURES_SHOWN:
        extra_high = len(shown) - HIGH_FEATURES_SHOWN
        lines.append(f"- +{extra_high} more high-value features → docs/FEATURES.jsonl")
    if normal:
        names = ", ".join(f"{e.id} {e.title}" for e in sorted(normal, key=lambda x: x.id)[:8])
        extra = f" (+{len(normal) - 8} more)" if len(normal) > 8 else ""
        lines.append(f"- normal: {names}{extra}")
    if not current:
        lines.append("- none live yet")
    lines.append(f"## Changed in the last {RECENT_DAYS} days")
    anchor = max((e.date for e in events), default=None)
    recent = [e for e in events if anchor and e.date >= anchor - timedelta(days=RECENT_DAYS)
              and e.event in (FeatureEventKind.UPDATED, FeatureEventKind.RETIRED)]
    for e in recent[-8:]:
        lines.append(f"- {e.date} {e.event.value} {e.id} {e.title} — {e.reason}")
    if not recent:
        lines.append("- nothing updated or retired")
    retired = [e for e in latest_by_feature(events).values() if e.event is FeatureEventKind.RETIRED]
    if retired:
        lines.append("## Retired (do not rebuild without the gate)")
        lines.extend(f"- {e.id} {e.title} — {e.reason}" for e in retired[:6])
    return lines


def render_snapshot(docs: RepoDocs) -> str:
    """The ≤60-line digest injected at session start. Deterministic for given inputs."""
    lines = [
        "# AutoTester — snapshot (generated by `autotester snapshot`; do not edit)",
        "",
        "**Purpose:** the whole project in one screen — what it is, what is live and why, "
        "what changed, what is next.",
        "**Open me when:** every session start (the hook injects me); before picking a unit. "
        "For detail go to the router in `CLAUDE.md`.",
        "",
        "## Product",
        *_product_paragraph(docs.architecture),
        *_feature_lines(docs),
        "## Next (open goal tasks)",
    ]
    pending = [t for t in load_goal_tasks(docs.goal) if t.get("status") == "pending"][:5]
    lines.extend(f"- {t['id']} [{t.get('user_value', 'normal')}] {t['title']}" for t in pending)
    if not pending:
        lines.append("- backlog empty")
    lines.append("## Last decisions (computed status)")
    for entry_id, day, kind, status in decision_index(docs.decisions)[-5:]:
        lines.append(f"- {entry_id} {day} {kind} {status}")
    text = "\n".join(lines).rstrip() + "\n"
    if text.count("\n") > SNAPSHOT_MAX_LINES:
        raise ValueError(f"snapshot exceeds {SNAPSHOT_MAX_LINES} lines; tighten the roll-ups")
    return text


# -- self-describing docs + router -----------------------------------------

def doc_header_missing(path: Path) -> bool:
    head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:8])
    return "**Purpose:**" not in head or "**Open me when:**" not in head


def router_paths(router: Path) -> set[str]:
    """Every `docs/...` path the router table names."""
    if not router.exists():
        return set()
    return set(_ROUTER_PATH_RE.findall(router.read_text(encoding="utf-8")))
