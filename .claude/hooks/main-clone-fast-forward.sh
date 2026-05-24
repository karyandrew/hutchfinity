#!/usr/bin/env bash
# Stub — dispatches to canonical main-clone-fast-forward in second-brain cache.
# The cache is refreshed at SessionStart by fetch-second-brain-rules.sh.
# Fails open if the cache is missing (first-session bootstrap, offline, etc.)
# so a missing cache can't brick the session.
# Pattern documented in second-brain/wiki/cross-repo-hook-stubs.md.
set -euo pipefail
impl="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/.cache/second-brain/.claude/hooks/main-clone-fast-forward.sh"
if [[ -x "$impl" ]]; then
  exec "$impl"
fi
exit 0
