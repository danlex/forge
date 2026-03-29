#!/bin/bash
# Forge control utility — single entry point
# Usage: ./c <command>
set -euo pipefail

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FORGE_DIR"

CMD="${1:-help}"

# --- Detect current model ---
current_model() {
    local model="forge-gen000"
    local latest=$(ls -d generations/gen*/ 2>/dev/null | sort | tail -1 | grep -o 'gen[0-9]*' || echo "")
    if [ -n "$latest" ] && ollama list 2>/dev/null | grep -q "forge-${latest}"; then
        model="forge-${latest}"
    fi
    echo "$model"
}

# --- Ensure container is running with correct model ---
ensure_container() {
    local model
    model=$(current_model)

    # Container exists and running?
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^forge$'; then
        # Check if model matches
        local running_model
        running_model=$(docker inspect forge --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep FORGE_MODEL | cut -d= -f2)
        if [ "$running_model" = "$model" ]; then
            echo "Container: already running (model=$model)"
            return
        fi
        # Model changed — need to recreate
        echo "Model changed ($running_model -> $model), recreating container..."
        docker stop forge 2>/dev/null || true
        docker rm forge 2>/dev/null || true
    fi

    # Container exists but stopped?
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q '^forge$'; then
        local stopped_model
        stopped_model=$(docker inspect forge --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep FORGE_MODEL | cut -d= -f2)
        if [ "$stopped_model" = "$model" ]; then
            echo "Resuming stopped container (model=$model)"
            docker start forge
            return
        fi
        # Model changed — remove and recreate
        docker rm forge 2>/dev/null || true
    fi

    # Create new container
    docker run -d --name forge \
        -v "$FORGE_DIR/student":/student \
        -e OLLAMA_URL=http://host.docker.internal:11434 \
        -e FORGE_MODEL="$model" \
        forge
    echo "Container: started (model=$model)"
}

# --- Shared: bootstrap everything ---
do_start() {
    echo "=== Forge Bootstrap ==="

    # Claude Code auth check
    if ! command -v claude &>/dev/null; then
        echo "ERROR: claude CLI not found. Install Claude Code first."
        exit 1
    fi

    # Python venv with MLX
    if [ ! -d .venv ]; then
        echo "Creating Python venv..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install mlx mlx-lm 2>&1 | tail -1
    fi
    echo "MLX: OK"

    # Workspace
    mkdir -p student/tools student/experiments student/knowledge generations benchmark
    if [ ! -f student/soul.md ]; then
        echo "ERROR: student/soul.md missing. Cannot start."
        exit 1
    fi
    echo "Workspace: OK"

    # Kill old ticker
    [ -f .ticker.pid ] && kill "$(cat .ticker.pid)" 2>/dev/null || true

    # Start ticker (runs OUTSIDE tmux — the heartbeat)
    touch student/claude_notes.md
    nohup bash "$FORGE_DIR/core/ticker.sh" >> "$FORGE_DIR/ticker.log" 2>&1 &
    echo $! > .ticker.pid
    echo "Ticker: OK (pid=$!)"

    # Wait for ticker to create tmux
    for i in $(seq 1 15); do
        tmux has-session -t forge 2>/dev/null && break
        sleep 1
    done

    echo ""
    echo "========================================="
    echo "  Forge is running!"
    echo ""
    echo "  tmux attach -t forge  — watch"
    echo "  Ctrl+b d              — detach"
    echo "  ./c status            — check health"
    echo "  ./c restart           — restart everything"
    echo "========================================="
    echo ""
    tmux attach -t forge
}

# --- Commands ---
case "$CMD" in
    start)
        do_start
        ;;

    restart)
        echo "=== Restarting Forge ==="
        [ -f .ticker.pid ] && kill "$(cat .ticker.pid)" 2>/dev/null && echo "Killed ticker" || true
        tmux kill-session -t forge 2>/dev/null && echo "Killed tmux session" || true
        docker stop forge 2>/dev/null && echo "Stopped container" || true
        pkill -f "ollama serve" 2>/dev/null || true
        sleep 1
        do_start
        ;;

    stop)
        echo "=== Stopping Forge ==="
        [ -f .ticker.pid ] && kill "$(cat .ticker.pid)" 2>/dev/null && echo "Killed ticker" || true
        tmux kill-session -t forge 2>/dev/null && echo "Killed tmux session" || true
        docker stop forge 2>/dev/null && echo "Stopped container" || true
        echo "Done. Container preserved. Ollama left running."
        ;;

    status)
        echo "=== Forge Status ==="
        echo ""
        echo "Ollama:"
        if curl -s http://localhost:11434/api/tags &>/dev/null; then
            echo "  running"
            ollama list 2>/dev/null | head -5
        else
            echo "  DOWN"
        fi
        echo ""
        echo "Container:"
        docker ps -a --filter name=forge --format "  {{.Names}}: {{.Status}}" 2>/dev/null || echo "  not created"
        echo ""
        echo "tmux:"
        tmux has-session -t forge 2>/dev/null && echo "  session active" || echo "  no session"
        echo ""
        echo "Workspace:"
        echo "  status: $(cat student/status.md 2>/dev/null || echo 'n/a')"
        echo "  traces: $(wc -l < student/traces.jsonl 2>/dev/null || echo '0')"
        echo "  generations: $(ls -d generations/gen*/ 2>/dev/null | wc -l | tr -d ' ')"
        echo ""
        echo "Last 5 notes:"
        tail -5 student/claude_notes.md 2>/dev/null || echo "  none"
        ;;

    logs)
        docker logs -f forge
        ;;

    attach)
        tmux attach -t forge
        ;;

    teacher)
        # Attach directly to Teacher pane, zoomed in
        tmux select-pane -t forge:0.1
        tmux resize-pane -t forge:0.1 -Z
        tmux attach -t forge
        ;;

    supervisor)
        # Attach directly to Supervisor pane, zoomed in
        tmux select-pane -t forge:0.0
        tmux resize-pane -t forge:0.0 -Z
        tmux attach -t forge
        ;;

    monitor)
        python3 "$FORGE_DIR/core/monitor.py"
        ;;

    metrics)
        python3 "$FORGE_DIR/core/metrics.py"
        ;;

    notes)
        tail -f student/claude_notes.md
        ;;

    reset)
        echo "=== Full Reset ==="
        echo "This will delete all student data and generations."
        read -p "Are you sure? (yes/no): " CONFIRM
        if [ "$CONFIRM" = "yes" ]; then
            "$0" stop
            docker rm forge 2>/dev/null || true
            rm -f student/learnings.md student/patterns.md student/metacognition.md
            rm -f student/traces.jsonl student/status.md student/commands.txt
            rm -f student/claude_notes.md student/goal.md
            rm -rf student/tools/* student/experiments/*
            rm -rf generations/*
            rm -f benchmark/results.json
            git checkout student/soul.md 2>/dev/null || true
            echo "Reset complete. Run ./c start to begin fresh."
        else
            echo "Cancelled."
        fi
        ;;

    help|*)
        echo "Forge control utility"
        echo ""
        echo "Usage: ./c <command>"
        echo ""
        echo "Commands:"
        echo "  start     Start Forge (ollama + docker + tmux + orchestrator)"
        echo "  restart   Stop everything and start fresh"
        echo "  stop      Pause everything (container + state preserved)"
        echo "  status    Show system status"
        echo "  monitor   Live dashboard"
        echo "  metrics   Compute and display all metrics"
        echo "  logs      Tail Forge container logs"
        echo "  attach    Attach to tmux session (all panes)"
        echo "  supervisor Attach to Supervisor agent"
        echo "  teacher   Attach to Teacher agent"
        echo "  notes     Tail Claude's decision log"
        echo "  reset     Full reset — deletes all data"
        echo ""
        ;;
esac
