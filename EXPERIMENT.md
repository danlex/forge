# Experimental Protocol

## Research Question

Can a 1.7B general-purpose language model improve its score on a 100-problem
Python programming benchmark through autonomous practice and LoRA fine-tuning
on self-generated data?

## Model

- Qwen3-1.7B (base, general-purpose, not code-specialized)
- HuggingFace: `Qwen/Qwen3-1.7B`
- Inference: MLX on Apple M4 24GB

## Benchmark

100 Python problems, 10 categories × 10 problems (29 easy, 41 medium, 30 hard).
Categories: strings, math, arrays, sorting, searching, recursion, DP, graphs,
data structures, design. All tests verified passing. Problems are original
(not from HumanEval/MBPP). File: `core/benchmark/problems.json`.

## Experiments

### E1: Baseline
Run benchmark on base Qwen3-1.7B. No adapter. Record score per category.

### E2: Prompt-only control
Run benchmark with an improved system prompt (algorithm reference, code format
instructions) but no fine-tuning. If this matches E3, fine-tuning adds nothing.

### E3: Self-play + LoRA (main experiment)
1. Run 50 practice attempts with teacher-designed curriculum
2. Curate traces (remove garbage, keep pass + fail-then-succeed arcs)
3. LoRA fine-tune via MLX
4. Run benchmark with adapter
5. Repeat for 3 generations

### E4: Random curriculum control
Same as E3 but problems are randomly selected (no adaptive teacher).
If E3 >> E4, the teacher's curriculum matters. If E3 ≈ E4, it doesn't.

### E5: Human-written solutions control
Same as E3 but train on correct reference solutions from the benchmark's
test field instead of self-generated traces. If E5 >> E3, self-generated
data is worse than curated solutions. If E3 ≈ E5, self-play matches.

## Measurements per generation

| Metric | Source | Purpose |
|--------|--------|---------|
| Benchmark score (X/100) | run_benchmark_mlx.py | Primary outcome |
| Score per category (X/10) | run_benchmark_mlx.py | Where did it improve? |
| Pass rate during practice | traces.jsonl | Is it learning within generation? |
| First-try pass rate | traces.jsonl | Is it solving new problems? |
| Curriculum diversity | metrics.py | Is teacher advancing? |
| Training loss curve | finetune.py | Is model fitting the data? |
| Inference time | run_benchmark_mlx.py | Is it getting more efficient? |

## Statistical tests

- **McNemar's test** (paired): same 100 problems before/after. Appropriate for
  binary outcomes on paired data.
- **Fisher's exact test**: if McNemar's has low power.
- **Per-category chi-square**: which categories improved?
- **95% confidence intervals** on pass rate: Wilson score interval.

With n=100: a change from 20/100 to 30/100 gives McNemar's p ≈ 0.04 (significant).

## Reproducibility

Record for every run:
- Model: exact HuggingFace ID + commit hash
- MLX version: `pip show mlx mlx-lm`
- Adapter: path + config
- Benchmark: file hash `sha256sum core/benchmark/problems.json`
- System: macOS version, chip, RAM
- Timestamp

## Stopping criteria

- Each generation: 50 attempts or 10 consecutive failures
- Experiment ends after 3 generations OR if benchmark score plateaus
  (< 2 point improvement between generations)

## What would falsify the hypothesis?

- E3 score ≤ E1 score (fine-tuning didn't help)
- E3 score ≤ E2 score (prompting alone is enough)
- E3 score ≤ E4 score (adaptive curriculum doesn't matter)
- Score improves but only on categories present in training data
  (no generalization, just memorization)
