#!/usr/bin/env bash
# Auto-update helper, sourced by run.sh / run-deck.sh. Fast-forwards this git
# clone to the latest commit on its tracked branch before the app starts. Sets
# UPDATED=1 if it actually pulled (so the launcher can refresh dependencies).
#
# Skips silently and safely if: this isn't a git clone, git isn't installed,
# there's no network, or the user passed --no-update.
UPDATED=""
ripperdoc_update() {
  case " $* " in *" --no-update "*) return 0 ;; esac
  [ -d .git ] || return 0
  command -v git >/dev/null 2>&1 || return 0
  git rev-parse '@{u}' >/dev/null 2>&1 || return 0   # no upstream tracked
  git fetch --quiet 2>/dev/null || return 0          # offline etc.
  local local_rev remote_rev
  local_rev=$(git rev-parse @ 2>/dev/null)
  remote_rev=$(git rev-parse '@{u}' 2>/dev/null)
  [ -n "$remote_rev" ] && [ "$local_rev" != "$remote_rev" ] || return 0
  echo "ripperdoc: new version found, updating…"
  if git pull --ff-only --quiet 2>/dev/null; then
    echo "ripperdoc: updated to $(git rev-parse --short @)."
    UPDATED=1
  else
    echo "ripperdoc: couldn't auto-update (local changes?); running current version."
  fi
  return 0
}
ripperdoc_update "$@" || true
