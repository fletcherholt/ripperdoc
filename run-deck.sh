#!/usr/bin/env bash
# Steam Deck / Linux launcher. Runs Ripperdoc as a real native app window
# (pywebview + the Qt/QtWebEngine backend), not a browser tab.
#
# First run pulls Qt, so give it a minute. If the native window won't start on
# your setup, the app auto-falls back to browser mode; you can also force that
# with:  ./run-deck.sh --web
set -e
cd "$(dirname "$0")"
PY=python3
if [ ! -d .venv ]; then
  echo "first run: building venv (pulling Qt, this takes a minute)…"
  $PY -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet lz4 pywebview PySide6
fi
if [ "$1" = "--web" ]; then
  exec ./.venv/bin/python server.py
fi
exec ./.venv/bin/python app.py "$@"
