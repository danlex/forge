#!/bin/bash
# Ticker — the heartbeat. Runs OUTSIDE tmux.
# Ensures tmux is alive and sends "check system" to the supervisor.
set -u

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FORGE_DIR"

SUPERVISOR_PANE="forge:0.0"
TEACHER_PANE="forge:0.1"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] TICKER: $*"
}

setup_tmux() {
    log "Creating tmux session"
    tmux kill-session -t forge 2>/dev/null || true

    tmux new-session -d -s forge -n main
    # Pane 0 (left): Supervisor agent
    # Pane 1 (top-right): Teacher agent
    tmux split-window -h -p 40 -t forge:0.0
    # Pane 2 (bottom-right top): Student logs
    tmux split-window -v -p 50 -t forge:0.1
    # Pane 3 (bottom-right bottom): Monitor
    tmux split-window -v -p 50 -t forge:0.2

    # Pane 0: Supervisor agent (Claude Code)
    tmux send-keys -t forge:0.0 "cd $FORGE_DIR && bash run_supervisor.sh" Enter
    # Pane 1: Teacher agent (Claude Code)
    tmux send-keys -t forge:0.1 "cd $FORGE_DIR && bash run_orchestrator.sh" Enter
    # Pane 2: Student container logs
    tmux send-keys -t forge:0.2 "docker logs -f forge 2>&1" Enter
    # Pane 3: Monitor
    tmux send-keys -t forge:0.3 "cd $FORGE_DIR && python3 monitor.py" Enter

    log "tmux session created (4 panes)"
}

# --- Startup ---
log "Ticker started (pid=$$)"

# Ensure tmux exists
if ! tmux has-session -t forge 2>/dev/null; then
    setup_tmux
    sleep 10  # let agents boot
fi

INITIALIZED=false

# --- Main loop ---
while true; do
    # 1. tmux alive?
    if ! tmux has-session -t forge 2>/dev/null; then
        log "tmux dead — rebuilding"
        setup_tmux
        sleep 10
        INITIALIZED=false
        continue
    fi

    # 2. First run — tell supervisor to initialize
    if [ "$INITIALIZED" = false ]; then
        log "Sending init prompt to supervisor"
        tmux send-keys -t "$SUPERVISOR_PANE" "Read supervisor_soul.md — that is who you are. Read orchestrate.md for system procedures. Check: is Ollama running? Is the forge container running? Is there a workspace/goal.md? If not, send a prompt to the teacher (pane 1) to write the first problem. Log your actions to workspace/claude_notes.md with [SUPERVISOR] prefix." Enter
        INITIALIZED=true
        sleep 30
        continue
    fi

    # 3. Send periodic check
    STATUS=$(cat workspace/status.md 2>/dev/null || echo "none")
    TRACES=$(wc -l < workspace/traces.jsonl 2>/dev/null || echo "0")

    # Build check prompt based on state
    PROMPT="Check system. status.md=$STATUS, traces=$TRACES."
    PROMPT="$PROMPT If submitted: kill teacher context (tmux send-keys -t forge:0.1 /exit Enter, wait 8s), then send grading prompt to teacher pane."
    PROMPT="$PROMPT If working: check container+ollama health."
    PROMPT="$PROMPT If traces>=50 or goal.md contains GENERATION ENDED: handle generation boundary, update workspace/research_paper.md with results."
    PROMPT="$PROMPT Log to workspace/claude_notes.md."

    tmux send-keys -t "$SUPERVISOR_PANE" "$PROMPT" Enter

    # 4. Wait — longer if student is working, shorter if submitted
    if [ "$STATUS" = "submitted" ]; then
        sleep 40  # give supervisor + teacher time to grade
    else
        sleep 30  # polling interval
    fi
done
