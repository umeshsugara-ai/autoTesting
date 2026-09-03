#!/usr/bin/env bash
# Contract: qa/contracts/docker.md D2-D3. Starts a virtual display, shares it over VNC, exposes
# that VNC feed through noVNC's web client, then starts the app itself -- in that order, so the
# app never launches a browser before a display exists for it to render into.
set -euo pipefail

Xvfb :99 -screen 0 1280x800x24 &
sleep 1

x11vnc -display :99 -forever -shared -nopw -quiet &
sleep 1

websockify --web=/usr/share/novnc 6080 localhost:5900 &

exec uv run uvicorn autotester.ui.app:app --host 0.0.0.0 --port 8000
