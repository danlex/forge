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
        -v "$FORGE_DIR/workspace":/workspace \
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

    # Ollama
    if ! command -v ollama &>/dev/null; then
        echo "Installing Ollama..."
        brew install ollama
    fi
    if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
        echo "Starting Ollama..."
        ollama serve &>/dev/null &
        for i in $(seq 1 30); do
            curl -s http://localhost:11434/api/tags &>/dev/null && break
            sleep 1
        done
    fi
    echo "Ollama: OK"

    # Model
    if ! ollama list 2>/dev/null | grep -q "qwen3.5:4b"; then
        echo "Pulling qwen3.5:4b (this takes a few minutes)..."
        ollama pull qwen3.5:4b
    fi
    if ! ollama list 2>/dev/null | grep -q "forge-gen"; then
        ollama cp qwen3.5:4b forge-gen000
    fi
    echo "Model: OK"

    # Workspace
    mkdir -p workspace/tools workspace/experiments generations benchmark
    if [ ! -f workspace/soul.md ]; then
        echo "ERROR: workspace/soul.md missing. Cannot start."
        exit 1
    fi
    echo "Workspace: OK"

    # Docker image
    echo "Building image..."
    docker build -t forge -q .

    # Container (reuse if possible)
    ensure_container

    # Kill old ticker
    [ -f .ticker.pid ] && kill "$(cat .ticker.pid)" 2>/dev/null || true

    # Start ticker (runs OUTSIDE tmux — the heartbeat)
    touch workspace/claude_notes.md
    nohup bash "$FORGE_DIR/ticker.sh" >> "$FORGE_DIR/ticker.log" 2>&1 &
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
        echo "  status: $(cat workspace/status.md 2>/dev/null || echo 'n/a')"
        echo "  traces: $(wc -l < workspace/traces.jsonl 2>/dev/null || echo '0')"
        echo "  generations: $(ls -d generations/gen*/ 2>/dev/null | wc -l | tr -d ' ')"
        echo ""
        echo "Last 5 notes:"
        tail -5 workspace/claude_notes.md 2>/dev/null || echo "  none"
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
        python3 "$FORGE_DIR/monitor.py"
        ;;

    notes)
        tail -f workspace/claude_notes.md
        ;;

    reset)
        echo "=== Full Reset ==="
        echo "This will delete all workspace data and generations."
        read -p "Are you sure? (yes/no): " CONFIRM
        if [ "$CONFIRM" = "yes" ]; then
            "$0" stop
            docker rm forge 2>/dev/null || true
            rm -f workspace/learnings.md workspace/patterns.md workspace/metacognition.md
            rm -f workspace/traces.jsonl workspace/status.md workspace/commands.txt
            rm -f workspace/claude_notes.md workspace/goal.md
            rm -rf workspace/tools/* workspace/experiments/*
            rm -rf generations/*
            rm -f benchmark/results.json
            git checkout workspace/soul.md 2>/dev/null || true
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
        echo "  logs      Tail Forge container logs"
        echo "  attach    Attach to tmux session (all panes)"
        echo "  supervisor Attach to Supervisor agent"
        echo "  teacher   Attach to Teacher agent"
        echo "  notes     Tail Claude's decision log"
        echo "  reset     Full reset — deletes all data"
        echo ""
        ;;
esac
