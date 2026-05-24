#!/usr/bin/env bash
# Stub — dispatches to canonical worktree-preflight in second-brain cache.
# The cache is refreshed at SessionStart by fetch-second-brain-rules.sh.
# Fails open if the cache is missing (first-session bootstrap, offline, etc.)
# so a missing cache can't brick the session.
set -euo pipefail
impl="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/.cache/second-brain/.claude/hooks/worktree-preflight.sh"
if [[ -x "$impl" ]]; then
  exec "$impl"
fi
exit 0
