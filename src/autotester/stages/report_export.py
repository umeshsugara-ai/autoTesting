"""Tester-style run reports: an Excel summary and a screen-by-screen HTML
report with embedded screenshots. Contract: qa/contracts/report-export.md.

Both read only what `ProjectStore` already has (cases, RawResults, Verdicts)
— exporting is presentation over existing evidence, never a new source of
truth (design principle 8, same discipline as `ui/`).
"""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path

from openpyxl import Workbook

from autotester.schema.case import Case
from autotester.schema.enums import EvidenceKind
from autotester.store import ProjectStore

_BADGE_COLOR = {
    "PASS": "#16a34a", "FAIL": "#dc2626", "BLOCKED": "#b45309", "INCONCLUSIVE": "#6b7280",
}


def _latest_run_id(store: ProjectStore) -> str:
    runs_dir = store.paths.runs_dir
    run_ids = sorted(p.name for p in runs_dir.iterdir() if p.is_dir()) if runs_dir.exists() else []
    if not run_ids:
        raise ValueError(f"no runs exist yet for '{store.paths.slug}'")
    return run_ids[-1]


def _case_lookup(store: ProjectStore) -> dict[str, Case]:
    return {c.id: c for c in store.list_cases()}


def export_excel(
    project_slug: str, run_id: str | None, out_path: Path, root: Path | None = None
) -> Path:
    """One row per case: what ran, what it was checked against, what happened."""
    store = ProjectStore(project_slug, root)
    run_id = run_id or _latest_run_id(store)
    cases = _case_lookup(store)
    verdicts = {v.case_id: v for v in store.load_verdicts(run_id)}

    wb = Workbook()
    ws = wb.active
    ws.title = "Run report"
    ws.append(["Case", "Kind", "Class", "Outcome", "Result", "Criteria met",
               "Duration (s)", "Grader", "Notes"])
    for result in store.load_results(run_id):
        case = cases.get(result.case_id)
        verdict = verdicts.get(result.case_id)
        ws.append([
            case.title if case else result.case_id,
            case.kind.value if case else "",
            case.case_class.value if case else "",
            result.outcome.value,
            verdict.result.value if verdict else "",
            f"{verdict.criteria_met}/{verdict.criteria_total}" if verdict else "",
            round(result.duration_s, 2),
            verdict.grader_provider if verdict else "",
            (verdict.scoreboard if verdict else "") or (result.error or ""),
        ])
    for column in ws.columns:
        width = max(len(str(cell.value)) for cell in column if cell.value is not None)
        ws.column_dimensions[column[0].column_letter].width = min(width + 2, 60)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def _b64_png(path: Path) -> str | None:
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _case_section(store: ProjectStore, run_id: str, case: Case | None, result, verdict) -> str:
    run_dir = store.paths.run_dir(run_id)
    title = escape(case.title if case else result.case_id)
    color = _BADGE_COLOR.get(verdict.result.value if verdict else "", "#6b7280")
    badge_text = escape(verdict.result.value) if verdict else escape(result.outcome.value)
    shots = [e for e in result.evidence if e.kind is EvidenceKind.SCREENSHOT]
    figures = "".join(
        f"<figure><img src='data:image/png;base64,{data}'>"
        f"<figcaption>{escape(shot.label or shot.path)}</figcaption></figure>"
        for shot in shots
        for data in [_b64_png(run_dir / shot.path)] if data is not None
    )
    scoreboard = escape(verdict.scoreboard) if verdict and verdict.scoreboard else ""
    error = escape(result.error) if result.error else ""
    no_shots = "<p class='meta'>no screenshots captured</p>"
    return (
        f"<section><h2>{title} "
        f"<span class='badge' style='background:{color}'>{badge_text}</span></h2>"
        f"<p class='meta'>{scoreboard}{error}</p>"
        f"<div class='shots'>{figures or no_shots}</div>"
        "</section>"
    )


def export_html(
    project_slug: str, run_id: str | None, out_path: Path, root: Path | None = None
) -> Path:
    """One section per case, in run order, each with its own screenshots
    embedded inline (base64) so the file is a single portable artifact."""
    store = ProjectStore(project_slug, root)
    run_id = run_id or _latest_run_id(store)
    cases = _case_lookup(store)
    verdicts = {v.case_id: v for v in store.load_verdicts(run_id)}
    results = store.load_results(run_id)

    sections = "".join(
        _case_section(store, run_id, cases.get(r.case_id), r, verdicts.get(r.case_id))
        for r in results
    )
    style = (
        "body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:900px;"
        "margin:2rem auto;padding:0 1rem;color:#16181d}"
        "h1{margin-bottom:.2rem}.meta{color:#667085;font-size:.85rem}"
        "section{border:1px solid #e2e5ea;border-radius:10px;padding:1.2rem 1.4rem;"
        "margin-bottom:1.2rem}"
        ".badge{color:#fff;padding:.15rem .6rem;border-radius:999px;font-size:.75rem}"
        ".shots{display:flex;flex-wrap:wrap;gap:1rem;margin-top:.8rem}"
        "figure{margin:0;max-width:320px}img{max-width:100%;border:1px solid #e2e5ea;"
        "border-radius:6px}figcaption{font-size:.75rem;color:#667085;margin-top:.3rem}"
    )
    html = (
        "<!doctype html><meta charset='utf-8'>"
        f"<title>{escape(project_slug)} — {escape(run_id)} report</title>"
        f"<style>{style}</style>"
        f"<h1>{escape(project_slug)} — run report</h1>"
        f"<p class='meta'>Run <code>{escape(run_id)}</code> · {len(results)} case(s)</p>"
        f"{sections}"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path
