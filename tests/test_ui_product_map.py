"""Product-map page and learned-frame boundary tests."""

from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from autotester.schema.project import Project
from autotester.schema.screenmap import Journey, MappedScreen, ScreenMap, ScreenVisit
from autotester.store.project_store import ProjectStore
from autotester.ui.app import app
from autotester.ui.routes_product_map import learned_frame


def _store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectStore:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    return store


def test_product_map_renders_screens_and_recorded_journeys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _store(tmp_path, monkeypatch)
    store.save_screen_map(ScreenMap(
        project="demo", source_ids=["src_one"],
        screens=[MappedScreen(id="screen_1", name="Login", purpose="Authenticate",
                              visits=[ScreenVisit(source_id="src_one", t_start=1.2)])],
        journeys=[Journey(source_id="src_one", label="Happy login")],
    ))

    response = TestClient(app).get("/projects/demo/product-map")

    assert response.status_code == 200
    assert "Login" in response.text
    assert "Recorded journeys" in response.text
    assert "Happy login" in response.text


def test_learned_frame_refuses_path_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _store(tmp_path, monkeypatch)
    with pytest.raises(HTTPException) as caught:
        learned_frame("demo", "src_one", "../x.png")
    assert caught.value.status_code == 400
