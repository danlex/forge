#!/bin/bash
# Launches Claude Code interactively in this tmux pane.
# Tracks session count. Restarts on exit.
set -euo pipefail

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FORGE_DIR"

SESSION_FILE="$FORGE_DIR/.claude_sessions"
[ -f "$SESSION_FILE" ] || echo "0" > "$SESSION_FILE"

while true; do
    COUNT=$(cat "$SESSION_FILE")
    COUNT=$((COUNT + 1))
    echo "$COUNT" > "$SESSION_FILE"
    echo "=== Claude Code Teacher — session #$COUNT ==="
    claude --dangerously-skip-permissions
    echo "[$(date '+%H:%M:%S')] Session #$COUNT ended — restarting in 5s..."
    sleep 5
done
