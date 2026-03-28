# Forge

A self-improving AI system where a small language model (Qwen 3.5 4B) learns to code
through practice, graded feedback, and fine-tuning on its own attempts.

**Result: 2/10 → 7/10 on a held-out benchmark after one generation of self-play.**

## Architecture

Four agents, three identities:

| Agent | Runtime | Identity | Role |
|-------|---------|----------|------|
| **Architect** | Claude Code (your terminal) | `architect_soul.md` | Design, debug, evolve the system |
| **Supervisor** | Claude Code (tmux pane 0) | `supervisor_soul.md` | Monitor health, manage lifecycle, write research paper |
| **Teacher** | Claude Code (tmux pane 1) | `teacher_soul.md` | Grade attempts, design curriculum, calibrate difficulty |
| **Student** | MLX / Qwen 3.5 4B (tmux pane 2) | `workspace/soul.md` | Solve Python problems, learn from feedback |

```
┌─────────────────────────────┬──────────────────────────┐
│  Pane 0: Supervisor         │  Pane 1: Teacher         │
│  monitors, orchestrates     │  grades, writes goals    │
├─────────────────────────────┼──────────────────────────┤
│  Pane 2: Student            │  Pane 3: Monitor         │
│  thinks, codes, learns      │  live dashboard          │
└─────────────────────────────┴──────────────────────────┘
```

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.12+
- [Claude Code](https://claude.ai/code) CLI installed and authenticated
- ~20GB free disk space

### Start

```bash
git clone https://github.com/danlex/forge.git
cd forge
./c start
```

That's it. The system:
1. Creates a Python venv with MLX
2. Sets up a tmux session with 4 panes
3. Starts the supervisor, teacher, and student
4. Begins autonomous practice

### Watch

```bash
./c attach      # See all 4 panes
./c supervisor  # Zoom into supervisor
./c teacher     # Zoom into teacher
./c monitor     # Dashboard in your terminal
./c status      # Quick health check
```

Detach from tmux: `Ctrl+b d`. System keeps running.

### Stop

```bash
./c stop        # Pause everything (state preserved)
./c restart     # Full restart
./c reset       # Delete all data (asks for confirmation)
```

## How It Works

### The Loop

1. Teacher writes a problem to `workspace/goal.md`
2. Student reads the problem + its learnings + algorithm reference
3. Student reasons, writes code, executes it
4. PASS → submits trace, writes learning entry, writes solution file
5. FAIL → retries once; after 2 consecutive fails, asks teacher for a hint
6. Teacher grades (reasoning/correctness/honesty, 0-10 each)
7. Teacher writes next problem calibrated to the score
8. Repeat

### Context Management

No agent accumulates conversation history:

- **Student**: Fresh context every cycle. Knowledge persists in `learnings.md`, `patterns.md`, and `knowledge/algorithms.md`
- **Teacher**: Session killed and restarted before each grading cycle
- **Supervisor**: Receives short "check system" prompts from the ticker

### Communication

```
Student ↔ Teacher:    questions.txt / answers.txt
Teacher → Supervisor: escalations.txt
All agents:           status.md (working / submitted / question)
```

### Fine-Tuning

After a generation (50 attempts):

```bash
python3 curate.py 0                    # Filter traces into training data
python3 finetune.py 0                  # MLX LoRA fine-tuning (~26 min on M4)
python3 run_benchmark_mlx.py gen000/adapter  # Compare to baseline
```

Uses MLX on Metal GPU — fits in 15.6GB on 24GB machines.

## Results

| Generation | Benchmark | Delta | Training Examples | Time |
|------------|-----------|-------|-------------------|------|
| Baseline | 2/10 | — | 0 | — |
| Gen 0 | **7/10** | **+5** | 27 | 26 min |

See `workspace/research_paper.md` for the full analysis.

## File Structure

```
forge/
├── c                        # CLI entry point
├── CLAUDE.md                # Architect session config
├── architect_soul.md        # Architect identity
├── supervisor_soul.md       # Supervisor identity
├── teacher_soul.md          # Teacher identity
├── core.md                  # Student's 4 immutable laws
├── orchestrate.md           # Teacher's procedure manual
├── seed.py                  # Student runtime (MLX inference + code execution)
├── ticker.sh                # Heartbeat (keeps tmux alive)
├── run_supervisor.sh        # Supervisor launcher
├── run_orchestrator.sh      # Teacher launcher
├── monitor.py               # Live TUI dashboard
├── curate.py                # Trace → training data pipeline
├── finetune.py              # MLX LoRA fine-tuning
├── run_benchmark.py         # Benchmark (Ollama)
├── run_benchmark_mlx.py     # Benchmark (MLX with adapter)
├── simulate.py              # Offline simulation
├── workspace/
│   ├── soul.md              # Student identity (evolves)
│   ├── goal.md              # Current problem (teacher writes)
│   ├── status.md            # Coordination signal
│   ├── traces.jsonl         # All attempts
│   ├── learnings.md         # Student lessons
│   ├── patterns.md          # Reusable approaches
│   ├── metacognition.md     # Student self-reflection
│   ├── questions.txt        # Student → Teacher
│   ├── answers.txt          # Teacher → Student
│   ├── claude_notes.md      # Teacher decision log
│   ├── research_paper.md    # Living research paper
│   ├── solutions/           # One .py per attempt
│   ├── knowledge/
│   │   └── algorithms.md    # Algorithm reference
│   └── tools/               # Student-built tools
├── generations/
│   └── gen000/
│       ├── traces.jsonl     # Raw traces
│       ├── curated.jsonl    # Filtered training data
│       ├── adapter/         # LoRA adapter weights
│       └── report.md        # Training report
└── benchmark/
    ├── problems.json        # 10 held-out test problems
    └── results.json         # Scores per generation
```

## Research Paper

The supervisor maintains a living research paper at `workspace/research_paper.md`.
It documents methodology, results, failure modes, and conclusions — updated
automatically as the system runs.

## License

MIT
