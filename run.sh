#!/usr/bin/env bash
# Native-window launcher (macOS / Linux desktop). Opens the editor in its own
# window via pywebview. On the Steam Deck use run-deck.sh instead.
set -e
cd "$(dirname "$0")"
PY=python3
if [ ! -d .venv ]; then
  echo "first run: building venv…"
  $PY -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi
exec ./.venv/bin/python app.py "$@"
