#!/bin/bash
# SessionStart hook: clone karyandrew/second-brain into .claude/.cache/ so
# agents can read canonical rules as local files, then symlink second-brain's
# skills and commands into the dependent repo's .claude/skills|commands so
# Claude Code discovers and can invoke them (/kickoff, /wrap, /self-report).
#
# Fires on every session (web or local). Self-guards so second-brain's own
# sessions no-op (no need to fetch itself).
#
# Source of truth: karyandrew/second-brain/.claude/hooks/fetch-second-brain-rules.sh
# Dependent repos: drop this file at .claude/hooks/ and wire as a SessionStart
# hook in .claude/settings.json. Gitignore these paths:
#     .claude/.cache/
#     .claude/skills/
#     .claude/commands/
# (the symlinks and cache are per-machine; don't commit them).
#
# Auth sources, in order:
#   1. GITHUB_TOKEN / GH_TOKEN env var (primary — only source in web sandbox)
#   2. `gh auth token` CLI (local fallback — needs gh installed and authed)
#   3. soft-fail so the session still starts if neither works

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
CACHE_DIR="$PROJECT_DIR/.claude/.cache/second-brain"

# Self-guard: if running inside second-brain itself, no-op.
if git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null \
     | grep -qE '[/:]karyandrew/second-brain(\.git)?$'; then
  exit 0
fi

# Prefer env var; fall back to gh CLI on local machines.
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [ -z "$TOKEN" ] && command -v gh >/dev/null 2>&1; then
  TOKEN="$(gh auth token 2>/dev/null || true)"
fi

if [ -z "$TOKEN" ]; then
  echo "fetch-second-brain-rules: no GITHUB_TOKEN and no gh auth; skipping" >&2
  exit 0
fi

# URL-embedded auth works for both PATs (ghp_, github_pat_) and OAuth (gho_).
# http.extraheader rejects gho_ tokens, so we pay the cost of the token landing
# in the cache's .git/config — acceptable because .claude/.cache is gitignored
# and only exists on disk (never pushed).
AUTH_URL="https://x-access-token:${TOKEN}@github.com/karyandrew/second-brain.git"

mkdir -p "$(dirname "$CACHE_DIR")"

if [ -d "$CACHE_DIR/.git" ]; then
  git -C "$CACHE_DIR" remote set-url origin "$AUTH_URL"
  if ! git -C "$CACHE_DIR" fetch --depth 1 origin main >/dev/null 2>&1; then
    echo "fetch-second-brain-rules: fetch failed; using stale cache" >&2
    # Fall through — symlinks may still need a refresh against the stale cache.
  else
    git -C "$CACHE_DIR" reset --hard origin/main >/dev/null
  fi
else
  if ! git clone --depth 1 "$AUTH_URL" "$CACHE_DIR" >/dev/null 2>&1; then
    echo "fetch-second-brain-rules: clone failed" >&2
    exit 0
  fi
fi

# Expose second-brain's skills and commands by symlinking them from the
# canonical discovery paths. Refresh stale cache symlinks each run, then
# recreate from the fresh cache. Preserves any non-symlink entries in the
# dependent repo's own .claude/skills|commands (dependent repo's own
# skills/commands take precedence — the hook warns and skips).
link_from_cache() {
  local kind="$1"  # "skills" or "commands"
  local src_dir="$CACHE_DIR/.claude/$kind"
  local dst_dir="$PROJECT_DIR/.claude/$kind"

  [ -d "$src_dir" ] || return 0
  mkdir -p "$dst_dir"

  # Remove stale symlinks that point into the cache (handles deletions upstream).
  find "$dst_dir" -maxdepth 1 -mindepth 1 -type l -print0 2>/dev/null \
    | while IFS= read -r -d '' link; do
        target="$(readlink "$link")"
        case "$target" in
          *"/.cache/second-brain/"*) rm -f "$link" ;;
        esac
      done

  # Create symlinks for each entry in the cache.
  for entry in "$src_dir"/*; do
    [ -e "$entry" ] || continue
    name="$(basename "$entry")"
    dst="$dst_dir/$name"
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
      echo "fetch-second-brain-rules: $dst already exists (not a symlink); skipping" >&2
      continue
    fi
    ln -sfn "../.cache/second-brain/.claude/$kind/$name" "$dst"
  done
}

link_from_cache skills
link_from_cache commands

echo "fetch-second-brain-rules: second-brain refreshed at $CACHE_DIR; skills/commands linked" >&2
