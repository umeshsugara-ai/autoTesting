"""ADJUDICATE: merge every model's chunked observations into one reading.

Contract: qa/contracts/video-learning.md VL3/VL4. **Pure and deterministic — no
provider, no clock, no randomness.** Given the same cached observations in any
order it produces byte-identical output, which is what makes the on-disk
observation cache worth having: re-running the analysis costs nothing and
changes nothing.

Two jobs, and they are separate on purpose:

* **seams** — chunks overlap by design, so the same click is seen twice. What
  the model reports in an overlap is shifted into whole-video time here (in
  code, never by the model) and the duplicate dropped.
* **cross-model** — two models watching the same footage describe it slightly
  differently. Agreement raises confidence; disagreement is kept, not averaged.

The merge is deliberately dumb: casefolded names, overlapping intervals, a
fixed window. A cleverer matcher would be a second model, unauditable, and
would put the determinism this stage exists for at risk.
"""

from __future__ import annotations

from autotester.schema.analysis import AnalysedIssue, AnalysedScreen, JourneyStop, VideoAnalysis
from autotester.schema.enums import Confidence, Severity
from autotester.schema.observation import ModelObservation, ObservedIssue, ObservedScreen

SEAM_WINDOW_S = 10.0
"""How far apart two reports of the same thing can be and still be one thing.

Chunks overlap by 15s, so a click near a boundary is seen by both chunks at
timestamps that differ by however much the two models disagree about when it
happened — not by the overlap. 10s is wide enough for that disagreement and
narrower than the overlap, so a genuine repeat 15s later is not swallowed."""


def shift(observation: ModelObservation) -> ModelObservation:
    """Move a chunk's timestamps into whole-video time.

    In code, never by the model: a model asked to add its own offset gets it
    wrong occasionally and silently, and every issue's reported second depends
    on this being exact."""
    offset = observation.offset_s
    if not offset:
        return observation
    obs = observation.observation.model_copy(deep=True)
    for screen in obs.screens:
        screen.t_start += offset
        if screen.t_end is not None:
            screen.t_end += offset
        screen.screenshot_ts = [t + offset for t in screen.screenshot_ts]
    for flow in obs.flows:
        for step in flow.steps:
            step.t_start += offset
            if step.t_end is not None:
                step.t_end += offset
    for issue in obs.issues:
        issue.t_start += offset
        if issue.t_end is not None:
            issue.t_end += offset
    return observation.model_copy(update={"observation": obs})


def screen_key(screen: ObservedScreen) -> str:
    """What makes two reported screens the same screen.

    Casefolded name only. Not the URL — a model reads it from a screenshot and
    misreads it often enough that URL-keying splits one screen into several,
    which was the prior attempt's failure. Not the timestamps either: the same
    screen legitimately appears at different seconds in different chunks."""
    return " ".join(screen.name.casefold().split())


def issue_key(issue: ObservedIssue) -> tuple[str, str]:
    return (" ".join(issue.screen.casefold().split()), issue.category.value)


def _overlaps(a: ObservedScreen, b: ObservedScreen) -> bool:
    a_end = a.t_end if a.t_end is not None else a.t_start
    b_end = b.t_end if b.t_end is not None else b.t_start
    return a.t_start <= b_end and b.t_start <= a_end


def join_screens(screens: list[tuple[str, ObservedScreen]]) -> list[AnalysedScreen]:
    """One `AnalysedScreen` per screen, with the labels that saw it.

    Two reports merge when they share a key AND their intervals overlap. The
    interval matters: a product often shows one screen twice in a recording,
    and merging those would erase the second visit from the journey."""
    merged: list[AnalysedScreen] = []
    for label, screen in screens:
        for existing in merged:
            if screen_key(existing) == screen_key(screen) and _overlaps(existing, screen):
                existing.t_start = min(existing.t_start, screen.t_start)
                if screen.t_end is not None:
                    existing.t_end = max(existing.t_end or screen.t_end, screen.t_end)
                if label not in existing.model_labels:
                    existing.model_labels.append(label)
                    existing.models_agreeing = len(existing.model_labels)
                _merge_lists(existing, screen)
                break
        else:
            merged.append(AnalysedScreen(**screen.model_dump(),
                                         models_agreeing=1, model_labels=[label]))
    return sorted(merged, key=lambda s: (s.t_start, screen_key(s)))


def _merge_lists(into: AnalysedScreen, other: ObservedScreen) -> None:
    """Union the descriptive lists, preserving first-seen order.

    A union rather than a choice: if one model noticed a field the other
    missed, the field exists — the disagreement is about attention, not fact."""
    for attr in ("signals", "fields", "ui_elements", "screenshot_ts"):
        seen = list(getattr(into, attr))
        for value in getattr(other, attr):
            if value not in seen:
                seen.append(value)
        setattr(into, attr, seen)
    if not into.url and other.url:
        into.url = other.url
    if not into.purpose and other.purpose:
        into.purpose = other.purpose


def worst(*severities: Severity) -> Severity:
    """The most severe of several, where S1 is the WORST.

    `max()` on this enum is backwards and reads as if it were right, which is
    how I first wrote it: `Severity` is declared S1, S2, S3 in DESCENDING
    severity (S1 blocks a core flow, S3 is cosmetic), so the highest index is
    the mildest. A named function makes the intent unmistakable — an inverted
    comparison here would quietly downgrade every issue two models disagreed
    about, and disagreement is exactly when severity matters most."""
    order = list(Severity)
    return min(severities, key=order.index)


def _same_model_duplicate(existing: AnalysedIssue, label: str, issue: ObservedIssue) -> bool:
    """AT-231: the SAME provider's own second prompt, reporting the same
    category in the same seam window, is that model repeating itself under a
    different question -- not independent corroboration, and not two separate
    faults that happen to share a category and a moment.

    Screen name is deliberately NOT part of this check. `screen_key`'s own
    docstring says a model's read of a screen is unreliable enough that this
    stage never keys on the URL; it is exactly as unreliable across a model's
    OWN two prompts on one chunk as it is across two different chunks. The
    first real run measured this precisely: two prompts of one provider
    described the same fault on the same screen using different enough names
    that `issue_key` (which DOES include the screen) never matched, and the
    ensemble's central premise -- agreement raises confidence -- reported the
    fault twice instead of once.

    Requiring `label in existing.model_labels` keeps this from ever firing
    across two DIFFERENT models: a genuinely independent second model whose
    screen name also fails to match stays unmerged, exactly as before."""
    return (
        label in existing.model_labels
        and existing.category == issue.category
        and abs(existing.t_start - issue.t_start) <= SEAM_WINDOW_S
    )


def join_issues(issues: list[tuple[str, ObservedIssue]]) -> list[AnalysedIssue]:
    """One `AnalysedIssue` per real problem, with agreement counted.

    Same screen, same category, within `SEAM_WINDOW_S` — one issue (cross-model
    corroboration). Agreement raises `confidence` to HIGH because two models
    describing the same fault independently is the strongest signal this
    pipeline can produce without a human; it never raises `severity`, which is
    a property of the product and not of how many models noticed.

    A SECOND report from a model already credited for this issue also merges
    (`_same_model_duplicate`), even when the screen name differs — see its
    docstring. That merge never raises `models_agreeing`/`confidence`: the same
    model saying the same thing twice is not two models agreeing.

    **The title/what_is_wrong that SURVIVES a merge is the LONGER of the two,
    not the first-seen** (`_apply_merge`). My first version kept whichever
    text arrived first — `ingest_video_v1`'s by construction, since it sorts
    before `video_issues_v1` alphabetically — so a same-model duplicate let
    the MAPPING prompt's terser aside beat the BUG-SWEEP prompt's dedicated
    finding. Measured on the first real reading: that turned a matched issue
    into a missed one, because the surviving wording fell below the scorer's
    similarity threshold. Length is a blunt, deterministic, auditable proxy —
    the discipline this module's own docstring already asks for."""
    merged: list[AnalysedIssue] = []
    for label, issue in issues:
        for existing in merged:
            cross_model_match = (issue_key(existing) == issue_key(issue)
                                 and abs(existing.t_start - issue.t_start) <= SEAM_WINDOW_S)
            if cross_model_match or _same_model_duplicate(existing, label, issue):
                _apply_merge(existing, label, issue)
                break
        else:
            merged.append(AnalysedIssue(**issue.model_dump(),
                                        models_agreeing=1, model_labels=[label]))
    return sorted(merged, key=lambda i: (i.t_start, issue_key(i)))


def _apply_merge(existing: AnalysedIssue, label: str, issue: ObservedIssue) -> None:
    """Fold one more report into an already-merged issue, in place.

    Split out of `join_issues` when it crossed the 50-line cap — this is the
    body of the merge, not a second decision; `join_issues` still owns WHICH
    pairs merge."""
    if label not in existing.model_labels:
        existing.model_labels.append(label)
        existing.models_agreeing = len(existing.model_labels)
        existing.confidence = Confidence.HIGH
    existing.severity = worst(existing.severity, issue.severity)
    # The LONGER title/what_is_wrong survives, not the first-seen -- see
    # join_issues' own docstring for why first-seen was measurably wrong.
    incoming_len = len(issue.title) + len(issue.what_is_wrong)
    existing_len = len(existing.title) + len(existing.what_is_wrong)
    if incoming_len > existing_len:
        existing.title = issue.title
        existing.what_is_wrong = issue.what_is_wrong
    # `narration` is the tester's own words; `Issue.said_verbatim` is the
    # derived artifact's field, populated from it later by stages/issues.py.
    # Keeping the first non-empty one means a quote survives even when only
    # one model transcribed it.
    if not existing.narration and issue.narration:
        existing.narration = issue.narration
    if not existing.on_screen_text and issue.on_screen_text:
        existing.on_screen_text = issue.on_screen_text


def _collect(shifted: list[ModelObservation]) -> tuple[list, list, list, list[str], list[str]]:
    """Fold every observation's parts into flat, labelled lists.

    Split out of `adjudicate` when it crossed the 50-line cap: this is pure
    gathering, and keeping it separate leaves `adjudicate` reading as the four
    decisions it actually makes (sort, shift, join, record coverage)."""
    screens: list[tuple[str, ObservedScreen]] = []
    issues: list[tuple[str, ObservedIssue]] = []
    flows: list = []
    summaries: list[str] = []
    questions: list[str] = []
    for obs in shifted:
        label = obs.provider_label
        screens += [(label, s) for s in obs.observation.screens]
        issues += [(label, i) for i in obs.observation.issues]
        flows += obs.observation.flows
        if obs.observation.summary and obs.observation.summary not in summaries:
            summaries.append(obs.observation.summary)
        for question in obs.observation.open_questions:
            if question not in questions:
                questions.append(question)
    return screens, issues, flows, summaries, questions


def adjudicate(observations: list[ModelObservation], source_id: str, *,
               expected: int | None = None) -> VideoAnalysis:
    """Every model's every chunk, merged into one reading of one recording.

    `expected` is how many model calls the caller PLANNED. Omitting it records
    **0, meaning unknown** — never a flattering guess (AT-208).

    Sorted before merging so the result does not depend on the order the
    observations happened to be loaded in — the property VL4 asks for, and the
    one a test can actually check by shuffling the input.

    **The sort key must leave no ties.** My first version omitted `prompt_name`,
    so one model's two prompts on one chunk tied and Python's stable sort handed
    the merge back to caller order — determinism held for every fixture I wrote
    (all single-prompt) and failed in the shipped two-prompt shape. A tie in the
    key IS the caller's order leaking back in, so the key names every field that
    distinguishes one observation from another.

    **AT-208 — why `expected=None` records 0 rather than the count present.** It
    used to default to `len(shifted)`, so any caller that did not pass `expected`
    got an artifact declaring itself COMPLETE: a default-value fallback inside
    the very field added to stop one. `analyze` always passes the real product;
    T-136's scorer re-adjudicates cached observations and is the caller this
    protects, because a fragment reading as a full run would corrupt the one
    number the north star is measured by."""
    ordered = sorted(observations, key=lambda o: (o.offset_s, o.provider_label,
                                                  o.prompt_name, o.chunk_index))
    shifted = [shift(o) for o in ordered]

    screens, issues, flows, summaries, questions = _collect(shifted)
    joined = join_screens(screens)
    return VideoAnalysis(
        source_id=source_id,
        observations_used=len(shifted),
        observations_expected=0 if expected is None else expected,
        provider_labels=sorted({o.provider_label for o in shifted}),
        prompt_names=sorted({o.prompt_name for o in shifted}),
        screens=joined,
        flows=flows,
        journey=[JourneyStop(**s.model_dump(exclude={"models_agreeing", "model_labels"}))
                 for s in joined],
        issues=join_issues(issues),
        summary=" ".join(summaries),
        open_questions=questions,
    )
