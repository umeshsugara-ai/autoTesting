"""Host-side media handling: probe, chunk, transcribe, extract frames.

Subprocess-only ffmpeg and whisper. Runs on the HOST, never in the container:
the container has no ffmpeg and no GPU, and the corpus is never mounted into it.
"""
