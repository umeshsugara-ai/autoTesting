"""Generic file persistence + the per-project facade. Contract: core-invariants.md C6."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from autotester.schema.case import Case
from autotester.schema.enums import Action, CaseClass, CaseKind, SourceKind
from autotester.schema.flowspec import ExpectedState, Flow, FlowSpec, Screen, Step
from autotester.schema.project import Project, Source
from autotester.store import (
    ProjectStore,
    append_jsonl,
    read_json,
    read_jsonl,
    upsert_jsonl,
    write_json,
)


def make_project(slug: str = "pathlynks") -> Project:
    return Project(slug=slug, name="Pathlynks", base_url="https://app.pathlynks.test",
                    allowed_domains=["pathlynks.test"])


def make_step() -> Step:
    return Step(order=1, action=Action.NAVIGATE, target="/dashboard",
                expected=ExpectedState(visible_text=["Dashboard"]))


def make_case(project: str = "pathlynks", flow_id: str = "flow-login") -> Case:
    return Case(project=project, flow_id=flow_id, kind=CaseKind.BEST,
                case_class=CaseClass.HAPPY, title="login works", steps=[make_step()])


# -- generic primitives ------------------------------------------------------

def test_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "project.json"
    write_json(path, make_project())
    loaded = read_json(path, Project)
    assert loaded is not None and loaded.slug == "pathlynks"


def test_read_json_missing_file_is_none_not_an_error(tmp_path: Path) -> None:
    assert read_json(tmp_path / "absent.json", Project) is None


def test_read_json_malformed_names_the_path(tmp_path: Path) -> None:
    path = tmp_path / "project.json"
    path.write_text('{"slug": "bad slug with spaces"}', encoding="utf-8")
    with pytest.raises(ValueError, match=re.escape(str(path))):
        read_json(path, Project)


def test_write_json_is_atomic_and_leaves_no_tmp_files(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "project.json"
    write_json(path, make_project())
    leftovers = list((tmp_path / "sub").glob(".tmp-*"))
    assert leftovers == [] and path.exists()


def test_jsonl_append_and_read_preserve_order(tmp_path: Path) -> None:
    path = tmp_path / "sources.jsonl"
    for i in range(3):
        append_jsonl(path, Source(project="p", kind=SourceKind.TEXT, text=f"note {i}"))
    rows = read_jsonl(path, Source)
    assert [r.text for r in rows] == ["note 0", "note 1", "note 2"]


def test_jsonl_malformed_row_names_its_line(tmp_path: Path) -> None:
    path = tmp_path / "sources.jsonl"
    append_jsonl(path, Source(project="p", kind=SourceKind.TEXT, text="ok"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not json}\n")
    with pytest.raises(ValueError, match=re.escape(f"{path}:2")):
        read_jsonl(path, Source)


def test_upsert_replaces_matching_id_in_place_and_appends_new_ids(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    a, b = make_case(flow_id="flow-a"), make_case(flow_id="flow-b")
    upsert_jsonl(path, a, Case)
    upsert_jsonl(path, b, Case)
    updated_a = a.model_copy(update={"title": "login works, edited"})
    upsert_jsonl(path, updated_a, Case)
    rows = read_jsonl(path, Case)
    assert [r.id for r in rows] == [a.id, b.id]  # order preserved, no duplicate
    assert rows[0].title == "login works, edited"


# -- ProjectStore facade -----------------------------------------------------

def test_project_roundtrip(tmp_path: Path) -> None:
    store = ProjectStore("pathlynks", tmp_path)
    assert store.load_project() is None
    store.save_project(make_project())
    loaded = store.load_project()
    assert loaded is not None and loaded.name == "Pathlynks"


def test_add_source_is_idempotent_on_content_address(tmp_path: Path) -> None:
    store = ProjectStore("pathlynks", tmp_path)
    source = Source(project="pathlynks", kind=SourceKind.TEXT, text="how login works")
    store.add_source(source)
    store.add_source(source)  # identical content -> no duplicate
    assert len(store.list_sources()) == 1


def test_flowspec_roundtrip(tmp_path: Path) -> None:
    store = ProjectStore("pathlynks", tmp_path)
    spec = FlowSpec(
        project="pathlynks",
        screens=[Screen(id="dashboard", name="Dashboard")],
        flows=[Flow(id="flow-login", name="Login", steps=[make_step()],
                    entry_screen="login", exit_screen="dashboard")],
    )
    store.save_flowspec(spec)
    loaded = store.load_flowspec()
    assert loaded is not None and loaded.flows[0].id == "flow-login"


def test_add_case_is_idempotent_when_a_flowspec_regenerates(tmp_path: Path) -> None:
    store = ProjectStore("pathlynks", tmp_path)
    case = make_case()
    store.add_case(case)
    store.add_case(Case(**{**case.model_dump(exclude={"id", "created_at"}), "id": ""}))
    assert len(store.list_cases()) == 1


def test_a_human_can_hand_edit_an_artifact_and_the_store_still_loads(tmp_path: Path) -> None:
    """C6: artifacts are files a human can open, edit, or delete."""
    store = ProjectStore("pathlynks", tmp_path)
    store.save_project(make_project())
    new_name = "Pathlynks (renamed by hand)"
    text = store.paths.config.read_text(encoding="utf-8")
    text = text.replace('"name": "Pathlynks"', f'"name": "{new_name}"')
    store.paths.config.write_text(text, encoding="utf-8")
    assert store.load_project().name == new_name
