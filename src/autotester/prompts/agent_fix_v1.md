# agent_fix_v1 — propose a corrected step for one failing action

You are fixing exactly one broken step in an otherwise-working test case. You do not see the
rest of the case's history or reasoning — only the case's goal, the step that failed, the error
the executor raised, and a screenshot of the page at the moment of failure.

Rules:
- Propose ONE corrected step: `action`, `target` (a semantic locator — role/name/label, never a
  brittle CSS path tied to implementation detail), and `value` if the action needs one.
- Keep the same intent as the original step. Do not invent a different action than what the
  case was trying to do (e.g. do not turn a CLICK into a NAVIGATE) unless the error itself shows
  the original action can no longer make sense on this page.
- `reasoning` must name what in the error or screenshot justifies this specific fix — not a
  generic "this should work."

## Case

Title: {{TITLE}}
Rationale: {{RATIONALE}}

## The step that failed

{{FAILING_STEP}}

## Error

{{ERROR}}

## Screenshot at the moment of failure

{{SCREENSHOT}}

Answer with a JSON object matching the schema you were given (action, target, value, reasoning).
