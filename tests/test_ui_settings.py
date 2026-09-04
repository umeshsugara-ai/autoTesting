"""Global provider settings. Contract: qa/contracts/ui-settings.md US1-US4."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autotester.ui.app import app
from autotester.ui.env_editor import set_env_value


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_settings_page_shows_only_the_known_provider_keys(
    client: TestClient, scratch_root: Path
) -> None:
    response = client.get("/settings/providers")

    assert response.status_code == 200
    for key in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                "OLLAMA_BASE_URL", "OLLAMA_MODEL", "OPENAI_API_KEY"):
        assert key in response.text
    assert "Not set" in response.text


def test_settings_page_never_renders_a_real_value(
    client: TestClient, scratch_root: Path
) -> None:
    set_env_value(scratch_root / ".env", "GEMINI_API_KEY", "s3cr3t-real-key")

    response = client.get("/settings/providers")

    assert response.status_code == 200
    assert "s3cr3t-real-key" not in response.text
    assert "Set" in response.text


def test_settings_submit_writes_via_env_editor_and_never_echoes(
    client: TestClient, scratch_root: Path
) -> None:
    response = client.post(
        "/settings/providers", data={"key": "OPENAI_API_KEY", "value": "new-real-key"}
    )

    assert response.status_code in (200, 303)
    written = (scratch_root / ".env").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=new-real-key" in written
    assert "new-real-key" not in response.text


def test_settings_refuses_an_unknown_key(client: TestClient, scratch_root: Path) -> None:
    response = client.post(
        "/settings/providers", data={"key": "SOME_RANDOM_KEY", "value": "x"}
    )
    assert response.status_code == 400


def test_settings_refuses_a_value_with_a_newline(client: TestClient, scratch_root: Path) -> None:
    response = client.post("/settings/providers", data={
        "key": "OPENAI_API_KEY", "value": "real-value\nINJECTED_KEY=evil",
    })

    assert response.status_code == 400
    env_path = scratch_root / ".env"
    written = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    assert "INJECTED_KEY" not in written


def test_settings_link_is_reachable_from_the_shared_nav(
    client: TestClient, scratch_root: Path
) -> None:
    response = client.get("/")
    assert "/settings/providers" in response.text
