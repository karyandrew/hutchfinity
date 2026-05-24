#!/bin/bash
# PreToolUse hook: block edits to CLAUDE.md and .claude/ without showing Andrew first.
# Covers local Edit/Write AND MCP GitHub write tools (push_files,
# create_or_update_file, delete_file) that would otherwise bypass the guard.
set -euo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Each tool's input shape is different; collect target paths one per line.
case "$TOOL" in
  Edit|Write)
    PATHS=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
    ;;
  mcp__github__create_or_update_file|mcp__github__delete_file)
    PATHS=$(echo "$INPUT" | jq -r '.tool_input.path // empty')
    ;;
  mcp__github__push_files)
    PATHS=$(echo "$INPUT" | jq -r '.tool_input.files[]?.path // empty')
    ;;
  *)
    exit 0
    ;;
esac

[ -z "$PATHS" ] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"

while IFS= read -r RAW; do
  [ -z "$RAW" ] && continue
  # Local tools send absolute paths; MCP tools send repo-relative. Normalize.
  REL="${RAW#${PROJECT_DIR}/}"
  REL="${REL#./}"
  case "$REL" in
    CLAUDE.md|.claude|.claude/*)
      echo "BLOCKED: $TOOL on $REL requires showing Andrew the proposed diff first."
      exit 2
      ;;
  esac
done <<< "$PATHS"

exit 0
