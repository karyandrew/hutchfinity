#!/usr/bin/env bash
# guard-second-brain-present.sh — PreToolUse hook template.
#
# Verifies the session inherits second-brain rules, skills, and commands
# via the canonical launch pattern (claude-sb wrapper). Warns to stderr if
# not detected; always exits 0 — never blocks tool use.
#
# Copy this file into .claude/hooks/ of each project repo and wire into
# settings.json under PreToolUse. See
# docs/cross-repo-second-brain-inheritance.md in second-brain for the full
# setup and rationale.

set -eu

SECOND_BRAIN_PATH="${SECOND_BRAIN_PATH:-$HOME/second-brain}"
env_ok=true
file_ok=true

if [ "${CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD:-}" != "1" ]; then
  env_ok=false
fi

if [ ! -f "$SECOND_BRAIN_PATH/CLAUDE.md" ]; then
  file_ok=false
fi

if ! $env_ok || ! $file_ok; then
  env_state="${CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD:-<unset>}"
  file_state=$([ -f "$SECOND_BRAIN_PATH/CLAUDE.md" ] && echo present || echo MISSING)
  cat >&2 <<EOF
WARN: second-brain inheritance not detected in this session.
  CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD: $env_state
  $SECOND_BRAIN_PATH/CLAUDE.md: $file_state

Canonical launch: claude-sb (wrapper from second-brain/bin/claude-sb, symlinked into PATH).
Agent: pause and flag this to Andrew before substantive work. Do not proceed silently.
EOF
fi

exit 0
