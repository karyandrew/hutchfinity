#!/usr/bin/env bash
# Stub — dispatches to canonical session-start-plan-check in second-brain cache.
# Fails open if cache missing so a fresh clone can still start.
set -euo pipefail
impl="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/.cache/second-brain/.claude/hooks/session-start-plan-check.sh"
if [[ -x "$impl" ]]; then
  exec "$impl"
fi
exit 0
