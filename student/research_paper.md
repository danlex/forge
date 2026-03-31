# What Happens When You Build a Self-Play Coding System for a 1.7B Model on a Laptop?

Adan Ledesma

Independent Researcher — https://github.com/danlex/forge

---

## Abstract

We build Forge, a complete closed-loop system in which a 1.7-billion parameter general-purpose language model (Qwen3-1.7B) practices Python programming problems, receives graded feedback from a larger model acting as teacher (Claude), and is fine-tuned on curated traces of its own attempts using LoRA via MLX on Apple Silicon. The entire system runs autonomously on a consumer laptop (M4, 24GB) for approximately $2.50 in API costs.

Rather than claiming a breakthrough in self-improvement, we report what we observed: what works, what breaks, and what the improvement actually consists of. We evaluate on a 100-problem benchmark spanning 10 algorithmic categories and present controlled comparisons against prompt engineering alone (E2), random curriculum (E4), and human-written solutions (E5).

Our primary findings are: (1) a prompt-engineering baseline achieves approximately 20% on the benchmark without any fine-tuning, establishing the floor; (2) [E3 result pending]; (3) context window poisoning causes catastrophic concept fixation after approximately 25 accumulated conversation turns, requiring stateless cycle design; and (4) the system design itself — multi-agent coordination via file-based communication on consumer hardware — is a reproducible template for small-model self-improvement research.

---

## 1. Introduction

Self-play for code generation is a rapidly growing field. In the past month alone, GASP (Jana et al., 2026), Code-A1 (Wang et al., 2026), and Sol-Ver (2026) have demonstrated self-play improvements at scales from 1.5B to 8B parameters. Liu et al. (2026) provide a theoretical framework explaining when self-play sustains improvement and when it collapses.

These systems share a common characteristic: they require GPU clusters and hundreds of training runs. We ask a simpler question: what happens when you try to build the entire self-play loop on a consumer laptop, with a tiny model, minimal budget, and full transparency about what works and what doesn't?

This paper is not a claim of state-of-the-art results. It is a practitioner's report on building and operating a self-play coding system for a 1.7B model, with rigorous measurement of what the improvement actually consists of.

### 1.1 Contributions

1. A complete, reproducible self-play system for code that runs on Apple Silicon for $2.50, using MLX for both inference and LoRA training. To our knowledge, no prior work publishes MLX-based self-play training for code.

2. A controlled experimental protocol with five conditions (baseline, prompt-only, self-play, random curriculum, human solutions), 100-problem benchmark, and proper statistical tests.

3. A taxonomy of failure modes specific to small-model online self-play: context window poisoning, concept fixation, honesty fabrication, and format-versus-algorithmic improvement decomposition.

4. Honest decomposition of improvement sources. In a preliminary experiment with a 4B model, 4 of 5 benchmark gains were format corrections (the model learned to not emit markdown fences), not algorithmic improvements. We report this finding rather than burying it.

---

## 2. Related Work

**Self-play for code (March 2026).** GASP (Jana et al., 2026) uses guided asymmetric self-play with benchmark problems as "goalposts," improving pass@20 on LiveCodeBench by 2.5%. Code-A1 (Wang et al., 2026) co-evolves code and test generation models adversarially at 1.5B-7B scale, showing that a 3B trained model surpasses a 7B base. Sol-Ver (2026) trains a single model as both solver and verifier, achieving +19.6% on MBPP with Llama 3.1 8B. Our work differs in operating at 1.7B scale with LoRA on consumer hardware, using an external teacher rather than self-verification.

**Theory of self-play collapse.** Liu et al. (2026) formalize self-play as requiring three conditions for sustained improvement: asymmetric co-evolution (verifier more capable than solver), capacity growth, and proactive information seeking. Our architecture instantiates asymmetric co-evolution through the Claude teacher, which is orders of magnitude more capable than the 1.7B student.

**Curriculum learning.** Liu et al. (2026b) prove that easy-to-hard curricula provably outperform fixed mixtures for iterative self-improvement. E2H Reasoner (2026) demonstrates curriculum RL at 1.5B-3B scale with convergence guarantees. Our teacher implements adaptive curriculum design, though without formal convergence guarantees.

**Self-improvement foundations.** STaR (Zelikman et al., 2022) bootstraps reasoning by training on correct chain-of-thought traces. V-STaR (Hosseini et al., 2024) extends this with DPO verifiers trained on both correct and incorrect solutions. SPIN (Chen et al., 2024) demonstrates self-play without external feedback. Our work adds an external teacher, which Liu et al.'s theory predicts should sustain improvement longer than pure self-play.

**Parameter-efficient fine-tuning.** LoRA (Hu et al., 2022) enables fine-tuning with minimal memory. Biderman et al. (2024) show LoRA "learns less and forgets less" than full fine-tuning — relevant to our regression analysis. MeSP (Park et al., 2026) achieves 62% memory reduction for LoRA on Apple Silicon with an MLX implementation. We use standard LoRA via mlx-lm.

**LLM-generated training data.** WizardCoder (Luo et al., 2023) uses 20K Evol-Instruct examples; Magicoder (Wei et al., 2023) uses 75K OSS-Instruct examples; OpenCodeInterpreter (Zheng et al., 2024) uses 68K multi-turn examples. Our self-play approach generates training data online and adaptively, requiring orders of magnitude fewer examples — though this comparison is confounded by benchmark differences.

---

## 3. System Design

### 3.1 Architecture

Forge consists of four roles coordinated through the filesystem:

```
Ticker (bash, 30s heartbeat)
  → Supervisor (Claude Code, monitors teacher quality)
    → Teacher (Claude Code, grades attempts, designs curriculum)
      ↔ Student (Qwen3-1.7B via MLX, solves problems)
```

All inter-agent communication occurs through files in the `student/` directory. No network calls between agents. The student model runs entirely locally via MLX; only the teacher and supervisor require API access to Claude.

### 3.2 Student

The student is Qwen3-1.7B, a general-purpose (not code-specialized) model served via MLX on Apple M4 hardware. Each cycle:

1. Read `soul.md` (identity), `goal.md` (current problem), `learnings.md` (accumulated lessons), `knowledge/algorithms.md` (reference patterns)
2. Generate reasoning and code via MLX
3. Execute code in a sandboxed subprocess
4. On pass: write trace, write learning entry, set status to "submitted"
5. On fail: write trace, write learning entry, retry once, then submit
6. After 2 consecutive failures: request hint from teacher

**Stateless design.** No conversation history is maintained between cycles. Each attempt starts from a fresh prompt constructed from persistent files. This prevents context window poisoning (Section 5.3).

### 3.3 Teacher

The teacher is a Claude Code session that grades each submission on three dimensions (0-10): reasoning quality, correctness, and honesty. It designs the next problem according to a difficulty calibration protocol: score 9-10 advances to a harder concept; 7-8 increases difficulty within the same concept; 5-6 maintains difficulty; 0-4 steps back. The teacher session is terminated and restarted before each grading cycle to prevent context accumulation.

### 3.4 Supervisor

The supervisor monitors the teacher's behavior: detecting curriculum stagnation (same problem assigned 3+ times), grade inflation, student death spirals (5+ consecutive failures), and generation boundaries. It can override the teacher by writing directly to `goal.md`.

### 3.5 Training Pipeline

After a generation (~50 attempts):
1. **Curate:** Filter traces — remove degenerate outputs, keep passes and fail-then-succeed arcs
2. **Train:** LoRA fine-tuning via MLX. 4 layers, rank 16, gradient checkpointing. Peak memory: 15.6 GB.
3. **Evaluate:** Run 100-problem benchmark with adapter. Compare to baseline and prompt-only control.

---

## 4. Experimental Design

### 4.1 Benchmark

100 Python programming problems across 10 categories (strings, math, arrays, sorting, searching, recursion, dynamic programming, graphs, data structures, design), with 10 problems per category (29 easy, 41 medium, 30 hard). All problems include test assertions that print "PASS." All 100 tests verified correct. Problems are original (not from HumanEval or MBPP).

### 4.2 Conditions

| ID | Condition | Description | Purpose |
|----|-----------|-------------|---------|
| E1 | Baseline | Qwen3-1.7B, no prompt engineering | Floor |
| E2 | Prompt-only | Enhanced system prompt, no fine-tuning | Controls for prompt effects |
| E3 | Self-play + LoRA | 50 attempts → curate → LoRA → benchmark | Main experiment |
| E4 | Random curriculum | Same as E3 but randomly selected problems | Controls for teacher's curriculum |
| E5 | Human solutions | Train on reference solutions, not self-generated | Controls for data source |

### 4.3 Measurements

Per generation:
- Benchmark score (X/100) with per-category breakdown
- Pass rate during practice (rolling, first-try)
- Curriculum diversity
- Training loss
- Inference time

### 4.4 Statistical Analysis

- **Primary test:** McNemar's test (paired binary outcomes, n=100)
- **Secondary:** Per-category Fisher's exact, Wilson confidence intervals
- **Multiple runs:** E3 repeated 3 times for error bars
- **Significance threshold:** alpha = 0.05 with Holm-Bonferroni correction

### 4.5 Falsification Criteria

The hypothesis is falsified if:
- E3 ≤ E1 (fine-tuning didn't help)
- E3 ≤ E2 (prompting alone is sufficient)
- E3 ≤ E4 (adaptive curriculum doesn't matter)
- Improvement limited to format correction with no algorithmic gains

---

## 5. Results

### 5.1 Preliminary: E2 Prompt-Only Control (Sample)

On the first 20 benchmark problems, Qwen3-1.7B with an enhanced system prompt ("output raw Python, no markdown") achieves 4/20 (20%). This establishes that prompt engineering alone provides modest capability. The remaining experiments will determine whether self-play and LoRA add meaningful improvement above this floor.

### 5.2 Preliminary: 4B Pilot Experiment

A pilot experiment with Qwen 3.5 4B on a 10-problem benchmark showed improvement from 2/10 to 7/10 after LoRA fine-tuning on 27 self-generated traces. However, decomposition revealed that 4 of 5 new passes were format corrections (the model learned to suppress markdown code fences) rather than algorithmic improvements. Only 1 pass (Fibonacci with memoization) represented genuine algorithmic learning. McNemar's test on this pilot was not significant (p = 0.221).

This finding motivates the current experiment: a larger benchmark (100 problems), proper controls (E2 establishes the format-correction ceiling), and a model (1.7B) where format correction alone is less likely to dominate.

### 5.3 Failure Modes Observed in Pilot

**Context window poisoning.** When conversation history accumulated across attempts, the student model began generating Kadane's maximum subarray algorithm regardless of the assigned problem after approximately 25 attempts. We term this *concept fixation.* It was resolved by eliminating history accumulation: each cycle starts from a fresh prompt with knowledge persisted in files.

**Honesty fabrication.** The student occasionally generated fictional debugging narratives, claiming to have identified and fixed errors that did not occur. The teacher's honesty grading dimension (0-10) partially addresses this, but it remains a challenge for training data quality.

**Curriculum stagnation.** The teacher assigned the same problem (group_by_sign) for 51 consecutive attempts due to context bloat in the teacher's session. Resolved by killing and restarting the teacher session before each grading cycle, and by adding supervisor oversight.

### 5.4 Main Experiment Results

*Pending. Protocol defined. Experiments not yet run.*

| Condition | Score (/100) | Categories Improved | Notes |
|-----------|-------------|--------------------|----|
| E1: Baseline | — | — | |
| E2: Prompt-only | ~20 (projected from 4/20 sample) | — | |
| E3: Self-play + LoRA (gen 0) | — | — | |
| E3: Self-play + LoRA (gen 1) | — | — | |
| E3: Self-play + LoRA (gen 2) | — | — | |
| E4: Random curriculum | — | — | |
| E5: Human solutions | — | — | |

---

## 6. Analysis

*To be completed after experiments.*

### 6.1 Format Correction vs Algorithmic Improvement

All results will be decomposed into format improvements (model produces syntactically valid code where it previously emitted markdown artifacts) versus algorithmic improvements (model produces correct logic where it previously produced incorrect logic). The E2 prompt-only control establishes the ceiling for format-only improvement.

### 6.2 Curriculum Effect

Comparison of E3 (adaptive teacher) vs E4 (random problems) isolates the teacher's contribution. If E3 significantly outperforms E4, the adaptive curriculum — grounded in Liu et al.'s (2026b) easy-to-hard principle — provides measurable value.

### 6.3 Self-Generated vs Human Data

Comparison of E3 vs E5 tests whether self-generated traces at the student's capability boundary are more effective than human-written reference solutions, as hypothesized by the self-play literature.

### 6.4 Multi-Generation Compounding

If E3 is run for 3 generations, does improvement compound? The self-play theory (Liu et al., 2026) predicts 2-3 iterations before plateau for systems without capacity growth.

---

## 7. Discussion

### 7.1 Positioning

This work is not competitive with GASP, Code-A1, or Sol-Ver on benchmark performance — those systems use GPU clusters and larger models. Our contribution is the complete, reproducible system on consumer hardware, the controlled experimental design, and the honest analysis of what improvement actually consists of.

### 7.2 The Format Correction Finding

The pilot finding that 80% of benchmark gains were format correction has practical implications. Before investing in expensive RL or fine-tuning pipelines, practitioners should check whether a simple output format instruction in the system prompt resolves most failures. The E2 control makes this check explicit.

### 7.3 Failure Mode Taxonomy

Context poisoning, concept fixation, honesty fabrication, and curriculum stagnation are failure modes specific to online self-play with small models. These are absent from the STaR/SPIN literature because those systems use batch offline training. Our stateless cycle design and supervisor oversight are engineering solutions that may generalize to other online self-play systems.

### 7.4 Cost and Accessibility

The system costs approximately $2.50 in Claude API usage and runs entirely on a consumer laptop. In an era where competitive self-play research requires GPU clusters, a reproducible $2.50 experiment lowers the barrier to entry for self-improvement research.

---

## 8. Limitations

1. **Custom benchmark.** 100 original problems, not HumanEval or MBPP. Results are not directly comparable to published work. Future work should include standard benchmarks.

2. **Single model.** Results from Qwen3-1.7B may not generalize to other architectures or scales.

3. **Teacher bias.** Claude as teacher may introduce systematic biases in grading and curriculum design that favor certain patterns.

4. **Data contamination uncertainty.** Qwen3-1.7B may have encountered similar problems during pretraining. Fine-tuning may activate latent knowledge rather than teaching new capability.

5. **Apple Silicon specific.** MLX training pipeline is specific to Apple hardware. Reproducibility on other platforms requires porting to PyTorch/CUDA.

6. **No standard benchmark evaluation.** HumanEval/MBPP evaluation would strengthen comparability.

---

## 9. Conclusion

*To be completed after experiments.*

We will report: (a) whether LoRA fine-tuning on self-generated traces improves benchmark score above the prompt-only control, (b) whether the adaptive curriculum outperforms random problem selection, (c) whether self-generated data outperforms human-written solutions, and (d) the decomposition of improvement into format correction versus algorithmic learning.

Regardless of the magnitude of improvement, we contribute a complete, reproducible system design, a controlled experimental protocol, and a taxonomy of failure modes for small-model self-play — findings that are useful to the field independent of the headline number.

---

## References

Biderman, D., et al. (2024). LoRA Learns Less and Forgets Less. *TMLR (Featured).* arXiv:2405.09673.

Chen, Z., et al. (2024). SPIN: Self-Play Fine-Tuning Converts Weak Language Models to Strong. *ICML 2024.* arXiv:2401.01335.

Hosseini, A., et al. (2024). V-STaR: Training Verifiers for Self-Taught Reasoners. *COLM 2024.* arXiv:2402.06457.

Hu, E. J., et al. (2022). LoRA: Low-Rank Adaptation of Large Language Models. *ICLR 2022.*

Jana, S., et al. (2026). GASP: Guided Asymmetric Self-Play for Coding LLMs. arXiv:2603.15957.

Liu, W., et al. (2026). Self-Play Only Evolves When Self-Synthetic Pipeline Ensures Learnable Information Gain. arXiv:2603.02218.

Liu, C., et al. (2026b). A Task-Centric Theory for Iterative Self-Improvement with Easy-to-Hard Curricula. arXiv:2602.10014.

Luo, Z., et al. (2023). WizardCoder: Empowering Code LLMs with Evol-Instruct. *ICLR 2024.* arXiv:2306.08568.

Park, J., et al. (2026). MeSP: Memory-Efficient Structured Backpropagation for On-Device LLM Fine-Tuning. arXiv:2602.13069.

Wang, A., et al. (2026). Code-A1: Adversarial Evolving of Code LLM and Test LLM via RL. arXiv:2603.15611.

Wei, Y., et al. (2023). Magicoder: Empowering Code Generation with OSS-Instruct. *ICML 2024.* arXiv:2312.02120.

Yang, H., et al. (2026). Self-Improvement of Large Language Models: A Technical Overview. arXiv:2603.25681.

Zelikman, E., et al. (2022). STaR: Bootstrapping Reasoning with Reasoning. *NeurIPS 2022.*

Zheng, T., et al. (2024). OpenCodeInterpreter. arXiv:2402.14658.

---

## Appendix A: System Configuration

| Component | Value |
|-----------|-------|
| Student model | Qwen/Qwen3-1.7B (general-purpose) |
| Inference | MLX 0.31.1, Apple M4 24GB |
| Training | mlx-lm LoRA, 4 layers, rank 16 |
| Teacher | Claude via Claude Code CLI |
| Benchmark | 100 problems, 10 categories, verified |
| Cost | ~$2.50 Claude API |

## Appendix B: Benchmark Distribution

| Category | Easy | Medium | Hard | Total |
|----------|------|--------|------|-------|
| strings | 3 | 4 | 3 | 10 |
| math | 3 | 4 | 3 | 10 |
| arrays | 3 | 4 | 3 | 10 |
| sorting | 3 | 4 | 3 | 10 |
| searching | 3 | 4 | 3 | 10 |
| recursion | 3 | 4 | 3 | 10 |
| dynamic_programming | 3 | 4 | 3 | 10 |
| graphs | 3 | 4 | 3 | 10 |
| data_structures | 3 | 4 | 3 | 10 |
| design | 2 | 5 | 3 | 10 |
| **Total** | **29** | **41** | **30** | **100** |
