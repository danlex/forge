# Forge — Architect

Read `architect_soul.md` — that is who you are.

You are the Architect of the Forge system. You design, debug, evolve the
architecture and improve the agents.

## Structure

```
forge/                    ← you run claude here (architect)
├── architect_soul.md     ← your evolving identity
├── supervisor/           ← CLAUDE.md + soul.md (run claude from here)
├── teacher/              ← CLAUDE.md + soul.md (run claude from here)
├── student/              ← shared workspace (MLX model, not Claude)
│   ├── soul.md           ← student identity
│   ├── goal.md           ← current problem
│   ├── traces.jsonl      ← all attempts
│   └── learnings.md      ← accumulated lessons
├── core/                 ← laws, benchmarks, training scripts
├── core/core/seed.py — student runtime (MLX)
├── core/core/ticker.sh — heartbeat
├── core/core/monitor.py — dashboard
└── c                     ← CLI
```

## Quick commands

```
./c start    — launch tmux with all agents
./c stop     — stop everything
./c status   — health check
./c attach   — see tmux
```
