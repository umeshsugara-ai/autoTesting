# ingest_video_v1 — turn a demo video into screens and flows

You are watching a screen-recording demo of a web product. Your job is to produce a structured,
timestamped map of what you saw — not to judge the product, not to guess at things off-screen.

Rules:
- **Every screen you list must actually appear in the video.** Give each one a short, human name
  (e.g. "Sign-in page", "Dashboard") and the second it first appears (`t_start`).
- **Every flow is a sequence of concrete actions a person took**, in the order they happened.
  Each step needs: the action type (navigate/click/fill/select/upload/wait/assert), a plain-
  language description of the target (a button's visible label, a field's visible name — never a
  guess at a CSS selector or an internal id), the value typed if any, and the second it starts
  (`t_start`) and, if you can tell, ends (`t_end`).
- If a field looks like it takes a password, email, or other credential, still describe the
  target the same plain way — do not invent a value, and never write down a real-looking
  credential even as an example.
- Do not invent screens, flows, or steps you did not actually observe. If the video is too short
  or unclear for a section, describe less rather than guess more.

## Source

{{SOURCE_LABEL}}

Answer with a JSON object matching the schema you were given (screens[], flows[]).
