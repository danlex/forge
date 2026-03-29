#!/bin/bash
# Ticker — heartbeat. Runs OUTSIDE tmux.
# Ensures tmux alive. Sends "check system" to supervisor every 30s.
set -u

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FORGE_DIR"

SUPERVISOR_PANE="forge:0.0"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] TICKER: $*"
    echo "$msg"
    echo "$msg" >> student/claude_notes.md 2>/dev/null || true
}

setup_tmux() {
    log "Creating tmux session"
    tmux kill-session -t forge 2>/dev/null || true

    tmux new-session -d -s forge -n main
    tmux split-window -h -p 40 -t forge:0.0
    tmux split-window -v -p 50 -t forge:0.1

    # Pane 0 (left): Supervisor agent
    tmux send-keys -t forge:0.0 "cd $FORGE_DIR/supervisor && bash run.sh" Enter
    # Pane 1 (top-right): Teacher agent
    tmux send-keys -t forge:0.1 "cd $FORGE_DIR/teacher && bash run.sh" Enter
    # Pane 2 (bottom-right): Student (MLX)
    ADAPTER_FLAG=""
    LATEST_ADAPTER=$(ls -td "$FORGE_DIR"/generations/gen*/adapter 2>/dev/null | head -1)
    if [ -n "$LATEST_ADAPTER" ] && [ -f "$LATEST_ADAPTER/adapters.safetensors" ]; then
        ADAPTER_FLAG="FORGE_ADAPTER=$LATEST_ADAPTER"
    fi
    tmux send-keys -t forge:0.2 "cd $FORGE_DIR && source .venv/bin/activate && $ADAPTER_FLAG python3 seed.py 2>&1 | tee student/student.log" Enter

    log "tmux: supervisor(0) teacher(1) student(2)"
}

# --- Startup ---
log "Ticker started (pid=$$)"

if ! tmux has-session -t forge 2>/dev/null; then
    setup_tmux
    sleep 15
fi

INITIALIZED=false

# --- Main loop: send "check system" to supervisor ---
while true; do
    # tmux alive?
    if ! tmux has-session -t forge 2>/dev/null; then
        log "tmux dead — rebuilding"
        setup_tmux
        sleep 15
        INITIALIZED=false
        continue
    fi

    # First run: init supervisor
    if [ "$INITIALIZED" = false ]; then
        sleep 10
        STATUS=$(cat student/status.md 2>/dev/null || echo "none")
        TRACES=$(wc -l < student/traces.jsonl 2>/dev/null || echo "0")
        log "Init: status=$STATUS traces=$TRACES"
        tmux send-keys -t "$SUPERVISOR_PANE" "Read soul.md and CLAUDE.md. Check system: student/status.md=$STATUS, traces=$TRACES. If no ../student/goal.md exists, send a prompt to teacher (pane 1) to write the first problem. Log to ../student/claude_notes.md." Enter
        INITIALIZED=true
        sleep 30
        continue
    fi

    # Read state
    STATUS=$(cat student/status.md 2>/dev/null || echo "none")
    TRACES=$(wc -l < student/traces.jsonl 2>/dev/null || echo "0")
    TRACES=$(echo "$TRACES" | tr -d ' ')

    # Send check to supervisor
    tmux send-keys -t "$SUPERVISOR_PANE" "Check system. status=$STATUS traces=$TRACES. Act per your CLAUDE.md instructions." Enter

    # Sleep based on state
    if [ "$STATUS" = "submitted" ] || [ "$STATUS" = "question" ]; then
        sleep 45  # give supervisor + teacher time
    else
        sleep 30
    fi
done
