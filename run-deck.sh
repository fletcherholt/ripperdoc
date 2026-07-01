#!/usr/bin/env bash
# Steam Deck / Linux launcher. Runs Ripperdoc as a real native app window
# (pywebview + the Qt/QtWebEngine backend), not a browser tab.
# Auto-updates to the latest version on launch (skip with --no-update).
#
# First run pulls Qt, so give it a minute. If the native window won't start on
# your setup, the app auto-falls back to browser mode; you can also force that
# with:  ./run-deck.sh --web
set -e
cd "$(dirname "$0")"
source ./update.sh "$@"
PY=python3
DEPS="lz4 pywebview PyQt5 PyQtWebEngine qtpy"
if [ ! -d .venv ]; then
  echo "first run: building venv (pulling Qt, this takes a minute)…"
  $PY -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet $DEPS
elif [ -n "$UPDATED" ]; then
  ./.venv/bin/pip install --quiet $DEPS   # refresh deps after update
fi
if [ "$1" = "--web" ]; then
  exec ./.venv/bin/python server.py
fi
exec ./.venv/bin/python app.py "$@"
