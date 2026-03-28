#!/bin/bash
# Launches Claude Code as the Supervisor agent in this tmux pane.
# If Claude exits, restarts it.
set -euo pipefail

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FORGE_DIR"

while true; do
    echo "=== Starting Supervisor agent ==="
    claude --dangerously-skip-permissions
    echo "[$(date '+%H:%M:%S')] Supervisor exited — restarting in 5s..."
    sleep 5
done
