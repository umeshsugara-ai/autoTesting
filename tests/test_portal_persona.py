"""The durable Portal Persona (T-164). Contract: qa/contracts/portal-persona.md,
one test per criterion PP1-PP6.

Fully offline: no browser, network, or model. Every test builds a persona in a
temp project dir (`ProjectStore(slug, tmp_path)`), so the real repo tree is
never touched.
"""

from __future__ import annotations

from pathlib import Path

from autotester.core.redact import Redactor
from autotester.schema.flowspec import Flow, FlowSpec, InputField, Screen
from autotester.schema.portal_persona import FlowRunRef, PersonaScreen
from autotester.schema.project import Project
from autotester.stages.portal_persona import build_portal_persona
from autotester.stages.portal_persona_view import render_knowledge

SLUG = "demo"


def _store(tmp_path: Path):
    from autotester.store.project_store import ProjectStore

    store = ProjectStore(SLUG, tmp_path)
    store.save_project(Project(slug=SLUG, name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    return store


def _screen(sid: str, name: str, url: str | None = None,
            fields: list[InputField] | None = None) -> Screen:
    return Screen(id=sid, name=name, url_pattern=url, fields=fields or [])


def _save_spec(store, *screens: Screen, flows: list[Flow] | None = None,
               overview: str | None = None) -> None:
    store.save_flowspec(FlowSpec(project=SLUG, screens=list(screens),
                                 flows=flows or [], app_overview=overview))


# -- PP1: durable, one model, one store --------------------------------------

def test_pp1_persona_is_one_json_store_and_knowledge_is_its_view(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _save_spec(store, _screen("scr_a", "Login", "https://demo.test/login"))

    persona = build_portal_persona(store)

    assert store.paths.portal_persona.name == "portal_persona.json"
    assert store.paths.portal_persona.exists()
    reloaded = store.load_portal_persona()
    assert reloaded is not None and reloaded.project == SLUG
    assert [s.name for s in reloaded.screens] == ["Login"]
    # knowledge.md exists and is a VIEW of the JSON — it reflects the persona's screens
    knowledge = store.paths.knowledge.read_text(encoding="utf-8")
    assert "Login" in knowledge
    assert persona.screens[0].name == "Login"


# -- PP2: cross-run accumulation, never silent loss --------------------------

def test_pp2_a_second_run_never_drops_a_known_screen(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _save_spec(store, _screen("scr_a", "Login", "https://demo.test/login"))
    build_portal_persona(store)

    # Second run's material OMITS Login entirely and introduces only Dashboard.
    _save_spec(store, _screen("scr_b", "Dashboard", "https://demo.test/home"))
    persona = build_portal_persona(store)

    names = {s.name for s in persona.screens}
    assert "Login" in names, "a known screen must survive a run that omits it (PP2)"
    assert "Dashboard" in names, "new material must be added (PP2)"


# -- PP3: dated history with change detection --------------------------------

def test_pp3_a_real_change_appends_one_dated_named_revision(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _save_spec(store, _screen("scr_a", "Login", "https://demo.test/login"))
    build_portal_persona(store)  # initial revision

    _save_spec(store, _screen("scr_a", "Login", "https://demo.test/login"),
               _screen("scr_b", "Dashboard", "https://demo.test/home"))
    persona = build_portal_persona(store)

    assert len(persona.history) == 2, "a change must append exactly one revision"
    latest = persona.history[-1]
    assert latest.at, "the revision carries a timestamp (PP3)"
    assert "Dashboard" in latest.summary, "the summary names what changed (PP3)"


def test_pp3_an_identical_rerun_appends_no_revision(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _save_spec(store, _screen("scr_a", "Login", "https://demo.test/login"))
    build_portal_persona(store)
    before = len(store.load_portal_persona().history)

    persona = build_portal_persona(store)  # nothing changed

    assert len(persona.history) == before, "an unchanged re-run must not fabricate a revision (PP3)"


# -- PP4: knowledge page is a faithful regenerated view ----------------------

def test_pp4_knowledge_view_reflects_the_json(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _save_spec(store, _screen("scr_a", "Login", "https://demo.test/login"))
    persona = build_portal_persona(store)

    # Mutate the model and regenerate: the page must reflect the new screen.
    persona.screens.append(PersonaScreen(id="scr_x", name="Settings Panel"))
    page = render_knowledge(persona)

    assert "Settings Panel" in page, "knowledge.md must reflect the persona's screens (PP4)"


# -- PP5: credentials never leak into the persona or page --------------------

def test_pp5_a_secret_token_never_reaches_the_persona_or_page(tmp_path: Path) -> None:
    store = _store(tmp_path)
    token = "sk-demo-SUPERSECRET-9f8e7d6c5b4a"
    # Material that (wrongly) carries the raw secret in a free-text field.
    _save_spec(store, _screen("scr_a", f"Login ({token})", "https://demo.test/login",
                              fields=[InputField(name="password", type="password",
                                                 secret_key="DEMO_PASSWORD")]))
    redactor = Redactor({"DEMO_PASSWORD": token})

    build_portal_persona(store, redactor=redactor)

    json_text = store.paths.portal_persona.read_text(encoding="utf-8")
    page = store.paths.knowledge.read_text(encoding="utf-8")
    assert token not in json_text, "a raw secret must never reach portal_persona.json (PP5)"
    assert token not in page, "a raw secret must never reach knowledge.md (PP5)"
    # the SHAPE survives — the SecretRef key, never the value
    assert "DEMO_PASSWORD" in json_text


# -- PP6: Quick Re-Run pointer -----------------------------------------------

def test_pp6_a_taught_flow_carries_a_resolvable_runnable_reference(tmp_path: Path) -> None:
    store = _store(tmp_path)
    flow = Flow(id="flow_login", name="Sign in", entry_screen="scr_a")
    _save_spec(store, _screen("scr_a", "Login", "https://demo.test/login"), flows=[flow])

    persona = build_portal_persona(store)

    taught = persona.taught_flow("flow_login")
    assert taught is not None
    resolved = persona.resolve_run(taught.run_ref)
    assert resolved is taught, "a Quick Re-Run reference must resolve to its flow (PP6)"
    # a reference the persona cannot place is not runnable
    assert persona.resolve_run(
        FlowRunRef(project=SLUG, flow_id="nope", entry_screen="scr_a")) is None
