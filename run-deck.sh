#!/usr/bin/env bash
# Steam Deck / any-browser launcher. No native webview backend needed — runs a
# tiny local server and opens the editor in your browser. This is the reliable
# path on SteamOS. Add it to Steam as a non-Steam game to launch from Game Mode.
set -e
cd "$(dirname "$0")"
PY=python3
if [ ! -d .venv ]; then
  echo "first run: building venv…"
  $PY -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet lz4
fi
exec ./.venv/bin/python server.py "$@"
