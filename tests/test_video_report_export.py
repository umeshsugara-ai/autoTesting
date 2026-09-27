"""T-191/AT-587 V8: a kept video is LINKED in the exported report, never
base64-embedded the way a screenshot is -- the named RE3 exception `docs/
DECISIONS.md` D-050 added for exactly this evidence kind. Contract:
qa/contracts/run-video.md V8; qa/contracts/report-export.md RE3 (as amended).
No real browser needed: this is a fixture `RawResult` carrying one
`EvidenceKind.VIDEO` item, run straight through `export_html`.
"""

from __future__ import annotations

from pathlib import Path

from autotester.schema.case import Case
from autotester.schema.enums import Action, CaseClass, CaseKind, EvidenceKind, Outcome, Result
from autotester.schema.flowspec import Step
from autotester.schema.project import Project
from autotester.schema.run import Evidence, RawResult, Run
from autotester.schema.verdict import Verdict
from autotester.stages import report_export
from autotester.store import ProjectStore

RUN_ID = "run-video-test"


def _seed_with_video(tmp_path: Path) -> tuple[ProjectStore, str]:
    store = ProjectStore("demo", tmp_path)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                allowed_domains=["demo.test"])
    )
    case = Case(
        project="demo", flow_id="flow-login", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Login attempt", steps=[Step(order=1, action=Action.NAVIGATE, target="/login")],
    )
    store.add_case(case)
    store.save_run(Run(id=RUN_ID, project="demo", case_ids=[case.id]))
    run_dir = store.paths.run_dir(RUN_ID)
    video_rel = f"{case.id}.webm"
    (run_dir / video_rel).write_bytes(b"FAKE-WEBM-BYTES-NOT-A-REAL-VIDEO")
    raw = RawResult(
        case_id=case.id, outcome=Outcome.COMPLETED, duration_s=12.3,
        evidence=[Evidence(kind=EvidenceKind.VIDEO, path=video_rel, masked=True)],
    )
    store.save_result(RUN_ID, raw)
    store.save_verdict(RUN_ID, Verdict(
        run_id=RUN_ID, case_id=case.id, result=Result.FAIL, criteria_met=0, criteria_total=1,
        scoreboard="Criteria 0/1 met.", grader_provider="mock",
    ))
    return store, video_rel


def test_video_evidence_renders_as_a_link_never_embedded_as_base64(tmp_path: Path) -> None:
    _, video_rel = _seed_with_video(tmp_path)

    out = report_export.export_html("demo", RUN_ID, tmp_path / "out.html", tmp_path)
    html = out.read_text(encoding="utf-8")

    assert f'href="{video_rel}"' in html or f"href='{video_rel}'" in html
    # RE3's exception is a LINK, not an embed: no data: URI carries this video's bytes.
    assert "data:video" not in html
    assert "FAKE-WEBM-BYTES-NOT-A-REAL-VIDEO" not in html


def test_a_case_with_no_video_evidence_renders_no_video_link(tmp_path: Path) -> None:
    """The existing screenshot-only path (every other test in
    test_report_export.py) must render exactly as before -- no stray video
    markup appears when a case simply has none."""
    store = ProjectStore("demo", tmp_path)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                allowed_domains=["demo.test"])
    )
    case = Case(
        project="demo", flow_id="flow-home", kind=CaseKind.BEST, case_class=CaseClass.HAPPY,
        title="Homepage loads", steps=[Step(order=1, action=Action.NAVIGATE, target="/")],
    )
    store.add_case(case)
    store.save_run(Run(id=RUN_ID, project="demo", case_ids=[case.id]))
    store.save_result(RUN_ID, RawResult(case_id=case.id, outcome=Outcome.COMPLETED))
    store.save_verdict(RUN_ID, Verdict(run_id=RUN_ID, case_id=case.id, result=Result.PASS,
                                       criteria_met=1, criteria_total=1, grader_provider="mock"))

    out = report_export.export_html("demo", RUN_ID, tmp_path / "out.html", tmp_path)

    assert ".webm" not in out.read_text(encoding="utf-8")
