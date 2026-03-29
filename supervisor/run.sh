#!/bin/bash
cd "$(dirname "$0")"
while true; do
    echo "=== Supervisor session starting ==="
    claude --dangerously-skip-permissions
    echo "[$(date '+%H:%M:%S')] Supervisor exited — restarting in 5s..."
    sleep 5
done
