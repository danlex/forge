#!/bin/bash
# Forge supervisor — runs OUTSIDE tmux.
# Monitors health, feeds prompts to Claude, rebuilds tmux every 10 sessions.
set -u

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FORGE_DIR"

CLAUDE_PANE="forge:0.0"
SESSION_FILE="$FORGE_DIR/.claude_sessions"
MAX_SESSIONS=10
LAST_ATTEMPT=0
INITIALIZED=false

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] SUPERVISOR: $*"
    echo "$msg"
    echo "$msg" >> workspace/claude_notes.md 2>/dev/null || true
}

# --- tmux setup ---
setup_tmux() {
    log "Setting up tmux session"
    tmux kill-session -t forge 2>/dev/null || true

    # Create 3-pane layout: Teacher (left, tall) | Logs + Monitor (right, stacked)
    tmux new-session -d -s forge -n main
    # Pane 0: Claude Code Teacher (left, 60%)
    # Split right for logs
    tmux split-window -h -p 40 -t forge:0.0
    # Pane 1 is now right side — split it vertically for monitor below
    tmux split-window -v -p 40 -t forge:0.1

    # Pane 0 (left):        Claude Code Teacher
    # Pane 1 (top-right):   Forge container logs
    # Pane 2 (bottom-right): Monitor

    tmux send-keys -t forge:0.0 "cd $FORGE_DIR && bash run_orchestrator.sh" Enter
    tmux send-keys -t forge:0.1 "docker logs -f forge 2>&1" Enter
    tmux send-keys -t forge:0.2 "cd $FORGE_DIR && python3 monitor.py" Enter

    # Reset session counter
    echo "0" > "$SESSION_FILE"
    INITIALIZED=false

    log "tmux session created"
}

# --- Health check ---
check_tmux() {
    tmux has-session -t forge 2>/dev/null
}

check_claude_pane() {
    # Verify pane 0 exists and has a running process
    tmux list-panes -t forge:0 -F '#{pane_index}:#{pane_pid}' 2>/dev/null | grep -q '^0:'
}

# --- Send prompt to Claude ---
send() {
    local msg="$1"
    log ">>> sending prompt to Claude"
    tmux send-keys -t "$CLAUDE_PANE" "$msg" Enter
}

wait_for_claude() {
    sleep "${1:-15}"
}

# --- Recovery state ---
recover_state() {
    if [ -f workspace/traces.jsonl ]; then
        LAST_ATTEMPT=$(wc -l < workspace/traces.jsonl | tr -d ' ')
    else
        LAST_ATTEMPT=0
    fi
    log "Recovered state: last_attempt=$LAST_ATTEMPT"
}

# --- Init ---
log "Supervisor started (pid=$$)"
recover_state

# Initial tmux setup if not already running
if ! check_tmux; then
    setup_tmux
fi

GEN=$(ls -d generations/gen*/ 2>/dev/null | wc -l | tr -d ' ' || echo "0")
GEN=${GEN:-0}

# =====================
#  Main supervisor loop
# =====================
while true; do

    # --- 1. tmux alive? ---
    if ! check_tmux; then
        log "tmux session dead — rebuilding"
        setup_tmux
        sleep 8  # let Claude boot
        continue
    fi

    # --- 2. Claude pane alive? ---
    if ! check_claude_pane; then
        log "Claude pane dead — rebuilding tmux"
        setup_tmux
        sleep 8
        continue
    fi

    # --- 3. Session count check — rebuild every N sessions ---
    SESSIONS=$(cat "$SESSION_FILE" 2>/dev/null || echo "0")
    if [ "$SESSIONS" -ge "$MAX_SESSIONS" ]; then
        log "Session limit reached ($SESSIONS/$MAX_SESSIONS) — fresh tmux rebuild"
        setup_tmux
        sleep 8
        continue
    fi

    # --- 4. Docker container alive? ---
    if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^forge$'; then
        log "Forge container down — restarting"
        docker start forge 2>/dev/null || (
            MODEL=$(cd "$FORGE_DIR" && source c 2>/dev/null; current_model 2>/dev/null || echo "forge-gen000")
            docker run -d --name forge \
                -v "$FORGE_DIR/workspace":/workspace \
                -e OLLAMA_URL=http://host.docker.internal:11434 \
                -e FORGE_MODEL="$MODEL" \
                forge
        )
        sleep 3
    fi

    # --- 5. Ollama alive? ---
    if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
        log "Ollama down — restarting"
        ollama serve &>/dev/null &
        sleep 5
        continue
    fi

    # --- 6. Teacher requested container restart? ---
    if grep -qi "GENERATION.*ENDED\|RESTART.*CONTAINER\|AWAITING.*SUPERVISOR" workspace/goal.md 2>/dev/null; then
        log "Teacher requested generation end / restart"

        # Save generation
        GEN_STR=$(printf '%03d' $GEN)
        mkdir -p "generations/gen${GEN_STR}"
        cp workspace/traces.jsonl "generations/gen${GEN_STR}/traces.jsonl" 2>/dev/null

        # Restart container to clear Forge's context
        docker stop forge 2>/dev/null
        docker rm forge 2>/dev/null
        MODEL=$(current_model 2>/dev/null || echo "forge-gen000")
        docker run -d --name forge \
            -v "$FORGE_DIR/workspace":/workspace \
            -e OLLAMA_URL=http://host.docker.internal:11434 \
            -e FORGE_MODEL="$MODEL" \
            forge
        log "Container restarted with $MODEL"

        # Reset for next generation
        GEN=$((GEN + 1))
        LAST_ATTEMPT=0
        > workspace/traces.jsonl
        rm -f workspace/goal.md workspace/status.md

        # Tell teacher to start fresh
        send "Container restarted. Generation $GEN starting fresh. Write the first goal.md for this generation — an easy problem. Set status.md to working."
        wait_for_claude 30
        continue
    fi

    # --- 7. Ensure goal.md exists ---
    if [ ! -f workspace/goal.md ] || [ ! -s workspace/goal.md ]; then
        if [ "$INITIALIZED" = false ]; then
            sleep 5
            INITIALIZED=true
        fi
        send "Write workspace/goal.md with an easy Python problem. Include test cases that print PASS or FAIL. Use the format from orchestrate.md. Then write 'working' to workspace/status.md. Then append a log line to workspace/claude_notes.md. Do it now — use the Write tool or bash echo/cat."
        wait_for_claude 30
        continue
    fi

    # --- 7. Poll status.md ---
    STATUS=$(cat workspace/status.md 2>/dev/null || echo "none")

    # Ensure status.md exists
    if [ "$STATUS" = "none" ]; then
        echo "working" > workspace/status.md
        STATUS="working"
    fi

    if [ "$STATUS" != "submitted" ]; then
        sleep 2
        continue
    fi

    # New submission?
    CURRENT=$(wc -l < workspace/traces.jsonl 2>/dev/null | tr -d ' ')
    if [ "$CURRENT" -le "$LAST_ATTEMPT" ]; then
        sleep 2
        continue
    fi

    LAST_ATTEMPT=$CURRENT

    # --- 8. Grade (fresh Claude session each time) ---
    # Kill current Claude session so it starts fresh — no context bloat
    tmux send-keys -t "$CLAUDE_PANE" "/exit" Enter 2>/dev/null
    sleep 8  # wait for run_orchestrator.sh to restart claude

    send "Read teacher_soul.md. Read the last line of workspace/traces.jsonl — that is attempt #$CURRENT. Read workspace/learnings.md. Grade it (reasoning/correctness/honesty 0-10). Write specific one-paragraph feedback. Design next problem per difficulty calibration in orchestrate.md. Write workspace/goal.md. Write 'working' to workspace/status.md. Append grade + decision to workspace/claude_notes.md."
    wait_for_claude 30

    # --- 9. Generation boundary ---
    MAX=50
    STREAK_PASS=0
    STREAK_FAIL=0

    if [ -f workspace/traces.jsonl ]; then
        STREAK_PASS=$(python3 -c "
import json
traces = [json.loads(l) for l in open('workspace/traces.jsonl') if l.strip()]
s = 0
for t in reversed(traces):
    if t.get('passed'): s += 1
    else: break
print(s)
" 2>/dev/null || echo "0")

        STREAK_FAIL=$(python3 -c "
import json
traces = [json.loads(l) for l in open('workspace/traces.jsonl') if l.strip()]
s = 0
for t in reversed(traces):
    if not t.get('passed'): s += 1
    else: break
print(s)
" 2>/dev/null || echo "0")
    fi

    [ "$STREAK_PASS" -ge 8 ] && MAX=75
    [ "$STREAK_FAIL" -ge 5 ] && CURRENT=$MAX

    if [ "$CURRENT" -ge "$MAX" ]; then
        GEN_STR=$(printf '%03d' $GEN)
        NEXT_GEN_STR=$(printf '%03d' $((GEN + 1)))

        log "Generation $GEN complete ($CURRENT attempts)"

        # Teacher reflection
        send "Generation $GEN complete ($CURRENT attempts). Read teacher_soul.md and workspace/claude_notes.md. Reflect: what teaching strategies worked? Where did calibration fail? If your understanding shifted, rewrite teacher_soul.md. Log reflection."
        wait_for_claude 25

        # Curation
        mkdir -p "generations/gen${GEN_STR}"
        cp workspace/traces.jsonl "generations/gen${GEN_STR}/traces.jsonl"
        send "Curate generation $GEN. Read generations/gen${GEN_STR}/traces.jsonl. Remove bad reasoning, keep fail-then-pass arcs, check diversity. Write curated JSONL to generations/gen${GEN_STR}/curated.jsonl. Log what you kept/removed."
        wait_for_claude 30

        # Fine-tuning
        send "Fine-tune for generation $GEN. Read orchestrate.md fine-tuning section. Write and run a Python script: load base weights, train LoRA on generations/gen${GEN_STR}/curated.jsonl, save adapter to generations/gen${GEN_STR}/adapter/, merge, create Ollama model forge-gen${NEXT_GEN_STR}. Log training details."
        wait_for_claude 900

        # Evaluation
        send "Evaluate generation $GEN. Run benchmark/problems.json through old model forge-gen${GEN_STR} and new model forge-gen${NEXT_GEN_STR}. Compare scores. If new wins by 1+: accept and restart container with new model. If not: reject, keep old. Write report to generations/gen${GEN_STR}/report.md. Log decision."
        wait_for_claude 60

        # Reset
        GEN=$((GEN + 1))
        LAST_ATTEMPT=0
        > workspace/traces.jsonl

        send "Generation $GEN starting. Write first goal for new generation."
        wait_for_claude 20
    fi

done
