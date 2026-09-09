"""Product-map folding tests for Track A5.1."""

from pathlib import Path

from autotester.schema.analysis import AnalysedScreen, JourneyStop, VideoAnalysis
from autotester.schema.enums import SourceKind
from autotester.schema.flowspec import FlowSpec, Screen
from autotester.schema.project import Project, Source
from autotester.stages.product_map import attach_screenshots, build_screen_map
from autotester.store.project_store import ProjectStore


def test_two_analyses_sharing_a_screen_become_one_screen_with_two_visits(
    tmp_path: Path,
) -> None:
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    for source_id, name, second in (("src_one", "Login", 1.0),
                                    ("src_two", "  login  ", 8.0)):
        store.add_source(Source(id=source_id, project="demo", kind=SourceKind.VIDEO,
                                path=f"{source_id}.mp4", label=source_id))
        screen = AnalysedScreen(name=name, t_start=second, fields=["Email"])
        store.save_analysis(VideoAnalysis(
            source_id=source_id, screens=[screen],
            journey=[JourneyStop(name=name, t_start=second, what_user_does="signs in")],
        ))

    screen_map = build_screen_map(store)

    assert len(screen_map.screens) == 1
    assert [visit.source_id for visit in screen_map.screens[0].visits] == ["src_one", "src_two"]
    assert len(screen_map.journeys) == 2


def test_map_references_a_frame_only_when_the_png_exists(tmp_path: Path) -> None:
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    source = Source(id="src_one", project="demo", kind=SourceKind.VIDEO, path="one.mp4")
    store.add_source(source)
    store.save_analysis(VideoAnalysis(
        source_id=source.id,
        screens=[AnalysedScreen(name="Login", t_start=1.0, screenshot_ts=[1.5])],
    ))

    assert build_screen_map(store).screens[0].frame_ref is None
    frame = store.paths.source_frames_dir(source.id) / "00001500.png"
    frame.parent.mkdir(parents=True)
    frame.write_bytes(bytes.fromhex("89504e470d0a1a0a") + bytes.fromhex("49454e44ae426082"))
    assert build_screen_map(store).screens[0].frame_ref == (
        "sources/src_one/frames/00001500.png")


def test_map_templates_urls_and_attach_screenshots_does_not_mutate_input(tmp_path: Path) -> None:
    store = ProjectStore("demo", tmp_path)
    store.add_source(Source(id="src_one", project="demo", kind=SourceKind.VIDEO, path="one.mp4"))
    store.save_analysis(VideoAnalysis(
        source_id="src_one",
        screens=[AnalysedScreen(name="Trainer", t_start=0,
                                url="https://demo.test/trainers/123?token=secret#edit")],
    ))
    screen_map = build_screen_map(store)
    spec = FlowSpec(project="demo", screens=[Screen(id="s1", name="Trainer")])

    attached = attach_screenshots(spec, screen_map)

    assert "?" not in (screen_map.screens[0].url_pattern or "")
    assert "#" not in (screen_map.screens[0].url_pattern or "")
    assert spec.screens[0].screenshot_ref is None
    assert attached is not spec
