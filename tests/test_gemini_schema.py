"""The Gemini response-schema sanitiser — AT-230.

Every assertion here corresponds to something that **400'd against Google's real
endpoint** and could not have failed against the fake client the provider unit
was originally verified with. That is the point of the file: a seam whose only
job is talking to someone else's API cannot be proven by a double that agrees
with us, so these tests encode what the real API actually refused.

Contract: qa/contracts/ingest.md (provider seam), C8.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ConfigDict, Field

from autotester.providers.gemini_schema import (
    MAX_REF_DEPTH,
    SchemaTooDeep,
    gemini_schema,
)
from autotester.schema.observation import VideoObservation


class Inner(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    note: str | None = None


class Outer(BaseModel):
    """Deliberately shaped like the real models: `extra="forbid"`, a nested
    model (so Pydantic emits `$defs`/`$ref`), an optional (so it emits
    `anyOf: [X, null]`), and a field literally called `title`."""

    model_config = ConfigDict(extra="forbid")
    title: str = Field(description="a FIELD named title, not the schema keyword")
    inner: Inner
    items: list[Inner] = Field(default_factory=list)
    maybe: str | None = None


def keys_anywhere(node: object) -> set[str]:
    """Every dict KEY in the tree.

    Structural, not a substring search over the rendered JSON: my first version
    grepped the JSON text and matched `$ref` inside a model DOCSTRING, which
    Pydantic copies into `description`. The property I actually mean is that no
    dict uses these as keys -- a description that mentions one is harmless."""
    found: set[str] = set()
    if isinstance(node, dict):
        found |= set(node)
        for value in node.values():
            found |= keys_anywhere(value)
    elif isinstance(node, list):
        for item in node:
            found |= keys_anywhere(item)
    return found


def test_additionalProperties_is_gone_everywhere() -> None:
    """The literal 400: `Unknown name "additional_properties" at
    'generation_config.response_schema'`. It comes from this repo's own C1
    invariant (`extra="forbid"`), so every schema in the codebase carries it."""
    assert "additionalProperties" not in keys_anywhere(gemini_schema(Outer))


def test_refs_are_inlined_because_the_dialect_has_no_defs() -> None:
    """Gemini's dialect is an OpenAPI 3.0 subset: a `$ref` it cannot resolve is
    not a warning, it is a 400 on every call."""
    keys = keys_anywhere(gemini_schema(Outer))

    assert "$ref" not in keys
    assert "$defs" not in keys


def test_a_FIELD_named_title_survives() -> None:
    """The sharpest one. `title` is both a JSON-Schema annotation and a real
    field on `ObservedIssue`. Stripping it everywhere deleted the field while
    leaving it in `required`, and Gemini answered
    `required[3]: property is not defined`. Inside a `properties` map the keys
    are FIELD NAMES; a field called `title` is just a field."""
    schema = gemini_schema(Outer)

    assert "title" in schema["properties"], "the field was stripped as a keyword"
    assert schema["properties"]["title"]["type"] == "string"


def test_every_required_name_exists_in_properties() -> None:
    """The invariant behind that 400, stated directly: `required` may never name
    a property the schema does not have."""
    def check(node: object) -> None:
        if isinstance(node, dict):
            for name in node.get("required", []) or []:
                assert name in node.get("properties", {}), f"required {name!r} is not a property"
            for value in node.values():
                check(value)
        elif isinstance(node, list):
            for item in node:
                check(item)

    check(gemini_schema(Outer))
    check(gemini_schema(VideoObservation))


def test_the_keyword_is_still_stripped_in_keyword_position() -> None:
    """The other half — keeping field names must not mean keeping annotations.
    Pydantic writes a `title` annotation on the schema root."""
    schema = gemini_schema(Inner)

    assert "title" not in schema, "the ROOT annotation should still be dropped"


def test_an_optional_becomes_nullable_not_a_union() -> None:
    """`X | None` is `anyOf: [X, null]` in Pydantic and a union Gemini rejects."""
    maybe = gemini_schema(Outer)["properties"]["maybe"]

    assert "anyOf" not in maybe
    assert maybe.get("nullable") is True
    assert maybe.get("type") == "string"


def test_the_real_observation_schema_renders_clean() -> None:
    """The model actually sent on every vision call. If this regresses, every
    real call 400s and the failure surfaces as `NoObservations` — which reads
    as "the model saw nothing", not as "the request was malformed"."""
    schema = gemini_schema(VideoObservation)
    keys = keys_anywhere(schema)

    assert "additionalProperties" not in keys
    assert "$ref" not in keys
    assert "issues" in schema["properties"]


def test_a_self_referential_model_is_refused_not_expanded_forever() -> None:
    """`$ref` expansion is the only thing here that can recurse without end, so
    it is the only thing counted. Structural nesting is unbounded and fine —
    my first version capped THAT and refused a perfectly valid schema."""
    deep = {"$ref": "#/$defs/Loop"}
    defs = {"Loop": {"type": "object", "properties": {"next": {"$ref": "#/$defs/Loop"}}}}

    from autotester.providers.gemini_schema import _resolve

    with pytest.raises(SchemaTooDeep, match="self-referential"):
        _resolve(deep, defs, 0)


def test_deep_but_finite_structure_is_not_refused() -> None:
    """The guard must not fire on ordinary nesting. `VideoObservation` is
    several models deep and is the shape that ships."""
    assert gemini_schema(VideoObservation)["type"] == "object"
    assert MAX_REF_DEPTH >= 5, "a real model nests further than a couple of levels"


def test_an_unresolvable_ref_is_named_rather_than_passed_through() -> None:
    """Passing it through would 400 at Google with a message about our schema;
    failing here says which reference, locally, before a call is paid for."""
    from autotester.providers.gemini_schema import _resolve

    with pytest.raises(SchemaTooDeep, match="unresolvable"):
        _resolve({"$ref": "#/$defs/Missing"}, {}, 0)


def test_the_PROVIDER_actually_sends_the_sanitised_schema() -> None:
    """The wiring, which nothing here could see.

    Sabotage FF — reverting `providers/gemini.py` to pass the raw Pydantic class
    to `response_schema`, i.e. restoring AT-230 exactly — failed **zero** tests.
    Every other assertion in this file calls `gemini_schema()` directly and never
    constructs a provider, so the sanitiser was covered and the one line that
    uses it was not. That is how the original defect shipped past a PASS.

    I previously recorded this as "INCONCLUSIVE, then pinned". It was not: the
    test never landed (AT-256). Asserting on the config the provider builds, with
    no client and no network — `response_schema` must be a sanitised dict, never
    the model class."""
    from autotester.providers.gemini import GeminiProvider

    sent = GeminiProvider(api_key="fake-key")._config(VideoObservation, None).response_schema

    assert not isinstance(sent, type), "the raw Pydantic class was sent (AT-230)"
    assert isinstance(sent, dict)
    assert "additionalProperties" not in keys_anywhere(sent)
    assert "$ref" not in keys_anywhere(sent)
