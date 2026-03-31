#!/bin/bash
# Forge control utility
# Usage: ./c <command>
set -euo pipefail

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$FORGE_DIR"

CMD="${1:-help}"

do_start() {
    echo "=== Forge Bootstrap ==="

    if ! command -v claude &>/dev/null; then
        echo "ERROR: claude CLI not found. Install Claude Code first."
        exit 1
    fi

    if [ ! -d .venv ]; then
        echo "Creating Python venv..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install mlx mlx-lm 2>&1 | tail -1
    fi
    echo "MLX: OK"

    mkdir -p student/knowledge generations
    if [ ! -f student/soul.md ]; then
        echo "ERROR: student/soul.md missing."
        exit 1
    fi
    echo "Student: OK"

    # Kill old ticker + tmux
    [ -f .ticker.pid ] && kill "$(cat .ticker.pid)" 2>/dev/null || true
    tmux kill-session -t forge 2>/dev/null || true

    # Start ticker
    touch student/claude_notes.md student/traces.jsonl
    rm -f ticker.log
    nohup bash "$FORGE_DIR/core/ticker.sh" >> "$FORGE_DIR/ticker.log" 2>&1 &
    echo $! > .ticker.pid
    echo "Ticker: OK (pid=$!)"

    for i in $(seq 1 15); do
        tmux has-session -t forge 2>/dev/null && break
        sleep 1
    done

    echo ""
    echo "========================================="
    echo "  Forge is running!"
    echo ""
    echo "  ./c attach     — watch all panes"
    echo "  ./c supervisor — zoom supervisor"
    echo "  ./c teacher    — zoom teacher"
    echo "  ./c status     — health check"
    echo "  ./c metrics    — full stats"
    echo "  Ctrl+b d       — detach"
    echo "========================================="
    echo ""
    tmux attach -t forge
}

case "$CMD" in
    start)
        do_start
        ;;

    restart)
        echo "=== Restarting Forge ==="
        [ -f .ticker.pid ] && kill "$(cat .ticker.pid)" 2>/dev/null || true
        pkill -f "seed.py" 2>/dev/null || true
        tmux kill-session -t forge 2>/dev/null || true
        sleep 1
        do_start
        ;;

    stop)
        echo "=== Stopping Forge ==="
        [ -f .ticker.pid ] && kill "$(cat .ticker.pid)" 2>/dev/null || true
        pkill -f "seed.py" 2>/dev/null || true
        tmux kill-session -t forge 2>/dev/null || true
        echo "Stopped."
        ;;

    status)
        echo "=== Forge Status ==="
        echo ""
        echo "tmux:"
        tmux has-session -t forge 2>/dev/null && echo "  session active" || echo "  no session"
        echo ""
        echo "Student:"
        echo "  status: $(cat student/status.md 2>/dev/null || echo 'n/a')"
        echo "  traces: $(wc -l < student/traces.jsonl 2>/dev/null || echo '0')"
        echo "  goal: $(head -3 student/goal.md 2>/dev/null | tail -1)"
        echo "  process: $(pgrep -f seed.py > /dev/null 2>&1 && echo 'running' || echo 'stopped')"
        echo ""
        echo "Generations: $(ls -d generations/gen*/ 2>/dev/null | wc -l | tr -d ' ')"
        echo "Benchmark: $(python3 -c 'import json; print(len(json.load(open("core/benchmark/problems.json"))))' 2>/dev/null) problems"
        echo ""
        echo "Last 5 notes:"
        tail -5 student/claude_notes.md 2>/dev/null || echo "  none"
        ;;

    attach)
        tmux attach -t forge
        ;;

    teacher)
        tmux select-pane -t forge:0.1
        tmux resize-pane -t forge:0.1 -Z
        tmux attach -t forge
        ;;

    supervisor)
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

    benchmark)
        echo "Running 100-problem benchmark..."
        source .venv/bin/activate
        ADAPTER=""
        LATEST=$(ls -td generations/gen*/adapter 2>/dev/null | head -1)
        if [ -n "$LATEST" ] && [ -f "$LATEST/adapters.safetensors" ]; then
            ADAPTER="$LATEST"
            echo "Using adapter: $ADAPTER"
        fi
        python3 core/run_benchmark_mlx.py $ADAPTER
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
            rm -f student/learnings.md student/patterns.md student/metacognition.md
            rm -f student/traces.jsonl student/status.md student/goal.md
            rm -f student/claude_notes.md student/questions.txt student/answers.txt
            rm -rf generations/*
            echo '{}' > core/benchmark/results.json
            echo "Reset complete. Run ./c start to begin fresh."
        else
            echo "Cancelled."
        fi
        ;;

    help|*)
        echo "Forge — self-improving code model"
        echo ""
        echo "Usage: ./c <command>"
        echo ""
        echo "  start      Launch all agents (supervisor + teacher + student)"
        echo "  stop       Stop everything"
        echo "  restart    Stop + start"
        echo "  status     Health check"
        echo "  attach     tmux (all panes)"
        echo "  supervisor Zoom into supervisor"
        echo "  teacher    Zoom into teacher"
        echo "  monitor    Live dashboard"
        echo "  metrics    Full statistics from traces"
        echo "  benchmark  Run 100-problem evaluation"
        echo "  notes      Tail teacher/supervisor log"
        echo "  reset      Delete all data"
        echo ""
        ;;
esac
