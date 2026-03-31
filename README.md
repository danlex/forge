# Forge

A 1.7B model that dreams of IOI. It practices Python problems, gets coached by
Claude, and is fine-tuned on its own attempts via LoRA. Each generation, it gets
measurably better.

## Quick Start

```bash
git clone https://github.com/danlex/forge.git
cd forge
./c start
```

Requires: macOS Apple Silicon, Python 3.12+, Claude Code CLI.

## Architecture

```
Ticker (bash, 30s) → Supervisor (Claude, pane 0) → Teacher (Claude, pane 1)
                                                         ↕
                                                   Student (Qwen3 1.7B, pane 2)
```

| Agent | What | Where |
|-------|------|-------|
| Architect | You + Claude Code | root (CLAUDE.md) |
| Supervisor | Monitors teacher quality | supervisor/ |
| Teacher | Grades attempts, designs curriculum | teacher/ |
| Student | Qwen3 1.7B via MLX, solves problems | student/ + core/seed.py |

All communication through files in `student/`. Each Claude agent gets fresh
context per cycle.

## Commands

```
./c start      — launch all agents in tmux
./c stop       — stop everything
./c status     — health check
./c metrics    — full statistics
./c benchmark  — run 100-problem evaluation
./c attach     — see all panes
./c teacher    — zoom into teacher
./c supervisor — zoom into supervisor
```

## The Loop

1. Student reads goal.md + learnings.md + algorithms.md → thinks → writes code → runs it
2. PASS or FAIL → writes trace → sets status=submitted
3. Supervisor detects → resets teacher context → sends grading prompt
4. Teacher grades (reasoning/correctness/honesty 0-10) → writes new goal.md → resets status
5. Student reads new goal → cycle repeats
6. After 50 attempts → curate traces → LoRA fine-tune via MLX → benchmark → next generation

## Results

| Experiment | Model | Baseline | After Gen 0 | Notes |
|------------|-------|----------|-------------|-------|
| Exp 1 | Qwen 3.5 4B | 2/10 | 7/10 | 80% was format correction |
| Exp 2 | Qwen3 1.7B | 0/100 | ? | In progress |

## File Structure

```
forge/
├── CLAUDE.md              ← architect (this session)
├── architect_soul.md      ← architect identity
├── supervisor/            ← CLAUDE.md + soul.md + run.sh
├── teacher/               ← CLAUDE.md + soul.md + run.sh
├── student/               ← student's world
│   ├── soul.md            ← "I dream of IOI"
│   ├── goal.md            ← current problem
│   ├── status.md          ← working / submitted / question
│   ├── traces.jsonl       ← all attempts
│   ├── learnings.md       ← accumulated lessons
│   ├── knowledge/algorithms.md
│   └── claude_notes.md    ← teacher + supervisor log
├── core/
│   ├── seed.py            ← student runtime (MLX)
│   ├── ticker.sh          ← heartbeat
│   ├── monitor.py         ← TUI dashboard
│   ├── metrics.py         ← statistics
│   ├── curate.py          ← trace → training data
│   ├── finetune.py        ← MLX LoRA training
│   ├── run_benchmark_mlx.py
│   ├── laws.md            ← 4 immutable laws
│   ├── orchestrate.md     ← teacher procedures
│   └── benchmark/problems.json (100 problems)
├── generations/           ← one dir per generation
└── c                      ← CLI
```

## Research Paper

See `student/research_paper.md` (maintained by supervisor).

## License

MIT
