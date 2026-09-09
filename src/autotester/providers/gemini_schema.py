"""Turn a Pydantic model into a schema Gemini's `response_schema` will accept.

**AT-230.** Passing the Pydantic class straight through failed every real call
with `400 INVALID_ARGUMENT: Unknown name "additional_properties" at
'generation_config.response_schema'`. The cause is this codebase's own C1
invariant: every schema model sets `extra="forbid"`, which Pydantic emits as
`additionalProperties: false`, and Gemini's schema dialect has no such field.
`$defs`/`$ref` are rejected for the same reason — the dialect is a subset of
OpenAPI 3.0, not full JSON Schema.

**Why this survived a checker-PASS.** The T-131 provider unit was verified
against a *fake* client that accepted any config object, so the one thing that
could only fail against Google's actual endpoint was the one thing never
exercised. It surfaced within a second of the first real call. The lesson is not
"add a test" — it is that a seam whose whole purpose is talking to someone else's
API cannot be proven by a double that agrees with us.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

DROPPED_KEYS = ("additionalProperties", "title", "default", "examples", "$schema",
                "discriminator", "exclusiveMinimum", "exclusiveMaximum")
"""Schema KEYWORDS Gemini's dialect rejects or ignores. `additionalProperties` is
the one that actually 400s; the rest are noise in a response schema and each is a
chance to trip the same validator.

**These are only ever stripped in keyword position.** Dropping them everywhere
deleted `ObservedIssue.title` -- a real field that happens to share its name with
a JSON-Schema annotation -- and Gemini answered
`required[3]: property is not defined`, because `required` still named a property
the schema no longer had. Inside a `properties` map the keys are FIELD NAMES, and
a field called `title`, `default` or `examples` is just a field."""

MAX_REF_DEPTH = 20
"""A ceiling on `$ref` EXPANSION, not on structural nesting.

My first version counted every nested dict and list and capped at 12, which
`VideoObservation` blew through immediately -- a JSON schema is many levels deep
before any model nesting happens (`properties` -> each field -> its `items` ->
its type). It refused a schema that was perfectly fine. Only `$ref` resolution
can actually recurse forever, so that is the thing worth counting."""


class SchemaTooDeep(ValueError):
    """A model nested (or self-referential) past what inlining can flatten."""


def _resolve(node: Any, defs: dict[str, Any], refs: int) -> Any:
    """Inline `$ref`s and strip the keys Gemini will not take.

    Inlined rather than passed through because Gemini's dialect has no `$defs`:
    a reference it cannot resolve is not a warning, it is a 400 on every call.

    `refs` counts only `$ref` expansions -- structural depth is unbounded and
    fine."""
    if isinstance(node, list):
        return [_resolve(item, defs, refs) for item in node]
    if not isinstance(node, dict):
        return node

    if "$ref" in node:
        if refs >= MAX_REF_DEPTH:
            # AT-267: name the reference, as the unresolvable branch below
            # already does. A deep-but-finite acyclic model 20 refs deep trips
            # this too, and 'is it self-referential?' with nothing to check
            # against just sent the reader looking for a cycle that may not
            # exist.
            raise SchemaTooDeep(
                f"$ref expanded {refs} deep at {node['$ref']!r} — "
                f"is a model self-referential?")
        name = str(node["$ref"]).rsplit("/", 1)[-1]
        if name not in defs:
            raise SchemaTooDeep(f"unresolvable $ref: {node['$ref']}")
        merged = {k: v for k, v in node.items() if k != "$ref"}
        return _resolve({**defs[name], **merged}, defs, refs + 1)

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key in DROPPED_KEYS or key == "$defs":
            continue
        if key == "properties" and isinstance(value, dict):
            # Field names, not keywords -- every key here is kept verbatim.
            out[key] = {name: _resolve(sub, defs, refs) for name, sub in value.items()}
            continue
        out[key] = _resolve(value, defs, refs)

    # `anyOf: [X, null]` is how Pydantic writes `X | None`. Gemini takes
    # `nullable`, so collapse it rather than sending a union it will reject.
    options = out.get("anyOf")
    if isinstance(options, list):
        concrete = [o for o in options if isinstance(o, dict) and o.get("type") != "null"]
        if len(concrete) == 1 and len(options) == 2:
            out.pop("anyOf")
            out = {**concrete[0], **out, "nullable": True}
    return out


def gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    """The model's JSON schema, in the dialect Gemini's `response_schema` takes."""
    raw = model.model_json_schema()
    defs = raw.get("$defs", {})
    resolved = _resolve(raw, defs, 0)
    if not isinstance(resolved, dict):        # pragma: no cover - a model is always an object
        raise SchemaTooDeep(f"{model.__name__} did not resolve to an object schema")
    return resolved
