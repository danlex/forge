# Experimental Protocol v2

## Research Question

How does self-play code learning scale with model size? What do models actually
learn (format vs algorithms) at each scale? When does the teacher's curriculum
matter?

## Models

| Model | Size | Type | HumanEval (est.) |
|-------|------|------|-----------------|
| Qwen3-0.6B | 0.6B | General | ~20% |
| Qwen3-1.7B | 1.7B | General | ~52% |
| Qwen3.5-4B | 4B | General + thinking | ~63% |

All general-purpose (not code-specialized) to isolate what self-play teaches.

## Benchmark

100 Python problems. 10 categories × 10 problems (29 easy, 41 medium, 30 hard).
All verified. Original problems (not HumanEval/MBPP).

## Experiments (per model size)

| ID | Condition | Description |
|----|-----------|-------------|
| E1 | Baseline | Raw model, no prompt help |
| E2 | Prompt-only | Enhanced system prompt ("output raw Python, no markdown") |
| E3 | Self-play + LoRA | 50 attempts → curate → LoRA → benchmark (×3 runs) |
| E4 | Random curriculum | Same as E3, random problems instead of adaptive teacher |
| E5 | Human solutions | Train on reference solutions instead of self-generated |

## Measurements

Per condition:
- Benchmark score /100 with per-category breakdown
- Decomposition: format fixes vs algorithmic improvements
- Pass rate during practice (if applicable)
- Training loss curve (if applicable)
- Inference time

Per model size:
- At what difficulty level does improvement begin?
- Which categories improve? Which don't?
- What failure modes appear?

## Key Comparisons

1. **E3 vs E2** → Does fine-tuning add value beyond prompting? (per model size)
2. **E3 vs E4** → Does adaptive curriculum matter? (per model size)
3. **E3 vs E5** → Is self-generated data better than human data? (per model size)
4. **E3(0.6B) vs E3(1.7B) vs E3(4B)** → Scaling law for self-play learning
5. **Format % at each scale** → Does format correction dominate equally at all sizes?

## Statistical Tests

- McNemar's test per condition pair (n=100, paired)
- Per-category Fisher's exact
- Wilson confidence intervals
- Holm-Bonferroni correction for multiple comparisons
- 3 runs of E3 for error bars (mean ± std)

## Falsification

The hypothesis (self-play improves coding ability) is falsified if:
- E3 ≤ E2 at ALL model sizes (prompting alone is sufficient)
- E3 = E4 at ALL sizes (curriculum doesn't matter)
- All improvement is format correction at ALL sizes (no algorithmic learning)

## What Would Make This SOTA

1. First scaling study of self-play for code (0.6B → 1.7B → 4B)
2. First controlled decomposition of format vs algorithmic improvement
3. First replication of self-play code learning on consumer hardware
4. First failure mode taxonomy for online small-model self-play
5. All experiments reproducible for $2.50 per model size

## Timeline

Each model requires ~12 hours:
- E1 + E2: 4 hours (100 problems × 2 conditions)
- E3 ×3: 24 hours (50 attempts + train + benchmark, 3 runs)
- E4: 8 hours
- E5: 4 hours

Total: ~40 hours per model, ~120 hours for all three.
Can run in parallel if memory allows (0.6B + 1.7B simultaneously).

## Venue Target

ICLR 2026 Workshop on Recursive Self-Improvement (April 26-27, Rio)
— if deadline allows, otherwise: NeurIPS 2026 workshops
