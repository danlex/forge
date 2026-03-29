#!/bin/bash
# Launches Claude Code as the Teacher agent.
# Restarts on exit. Runs in teacher/ so it reads teacher/CLAUDE.md.
cd "$(dirname "$0")"

while true; do
    echo "=== Teacher session starting ==="
    claude --dangerously-skip-permissions
    echo "[$(date '+%H:%M:%S')] Teacher exited — restarting in 5s..."
    sleep 5
done
