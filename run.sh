#!/usr/bin/env bash
# Native-window launcher (macOS / Linux desktop). Opens the editor in its own
# window via pywebview. On the Steam Deck use run-deck.sh instead.
# Auto-updates to the latest version on launch (skip with --no-update).
set -e
cd "$(dirname "$0")"
source ./update.sh "$@"
PY=python3
if [ ! -d .venv ]; then
  echo "first run: building venv…"
  $PY -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
elif [ -n "$UPDATED" ]; then
  ./.venv/bin/pip install --quiet -r requirements.txt   # refresh deps after update
fi
exec ./.venv/bin/python app.py "$@"
