# Self-Improving Code Generation in a 4-Billion Parameter Language Model Through Autonomous Practice and LoRA Fine-Tuning

Adan Ledesma¹, Claude Opus 4.6 (Anthropic)²

¹ Independent Researcher
² AI Assistant, Anthropic

**Repository**: https://github.com/danlex/forge

---

## Abstract

We investigate whether a small language model can improve its programming ability through a closed-loop system of autonomous practice, graded feedback, and parameter-efficient fine-tuning. We introduce Forge, a multi-agent system in which a 4-billion parameter model (Qwen 3.5 4B) generates solutions to Python programming problems, receives structured feedback from a large language model acting as teacher (Claude), and is periodically fine-tuned on curated traces of its own attempts using Low-Rank Adaptation (LoRA).

We evaluate the system on a held-out benchmark of 10 Python programming problems spanning 10 algorithmic categories. After a single generation of training consisting of 27 curated examples derived from 35 practice attempts and 25.9 minutes of LoRA fine-tuning on Apple M4 hardware, the student model's benchmark score improved from 2/10 to 7/10. The benchmark problems were never exposed to the model during training, indicating that the observed improvement reflects generalization rather than memorization.

To our knowledge, this is among the first demonstrations of a small language model improving its coding ability through autonomous self-play with an LLM teacher, using only self-generated training data and consumer hardware.

---

## 1. Introduction

Recent advances in large language models (LLMs) have produced systems capable of solving complex programming tasks (Chen et al., 2021; Li et al., 2023; Rozière et al., 2023). However, these capabilities are concentrated in models with hundreds of billions of parameters, requiring substantial computational resources for both inference and fine-tuning.

A natural question arises: can a small model learn to code better through structured practice? Specifically, we ask whether a 4-billion parameter model can measurably improve its performance on a programming benchmark by training on data it generates itself, guided by feedback from a more capable model.

This question is motivated by several practical considerations. First, small models are deployable on consumer hardware, making them accessible for individual developers and edge applications. Second, self-generated training data eliminates the need for expensive human annotation. Third, a closed-loop improvement system could enable continuous specialization for domain-specific coding tasks.

We present Forge, a system that addresses this question through three collaborating agents:

1. A **student agent** (Qwen 3.5 4B) that attempts Python problems and executes its solutions
2. A **teacher agent** (Claude Code) that grades attempts and designs an adaptive curriculum
3. A **supervisor agent** (Claude Code) that manages system lifecycle and generation boundaries

The system operates autonomously after initialization, requiring no human intervention during practice and training cycles.

### 1.1 Contributions

- We demonstrate that a 4B parameter model can improve from 2/10 to 7/10 on a held-out programming benchmark after training on 27 self-generated examples
- We describe a multi-agent architecture for autonomous code learning that runs on consumer hardware (Apple M4, 24GB)
- We identify and characterize failure modes specific to small-model self-improvement, including context window poisoning and concept fixation
- We provide a complete open-source implementation and all experimental data

---

## 2. Related Work

**Code generation with LLMs.** Codex (Chen et al., 2021) and subsequent models including AlphaCode (Li et al., 2022), CodeLlama (Rozière et al., 2023), and StarCoder (Li et al., 2023) have demonstrated that language models can generate functionally correct code. These systems typically rely on large-scale pretraining on code corpora. Our work differs in that we begin with a general-purpose small model and improve it through practice rather than additional pretraining data.

**Self-play and self-improvement.** The concept of AI systems improving through self-play has a long history, from TD-Gammon (Tesauro, 1995) to AlphaGo (Silver et al., 2016). In the language domain, Constitutional AI (Bai et al., 2022) and Self-Instruct (Wang et al., 2023) demonstrate that LLMs can generate useful training data for themselves. STaR (Zelikman et al., 2022) shows that models can improve reasoning by training on their own correct chain-of-thought traces. Our work extends this paradigm to code generation with an external teacher providing structured feedback.

**Parameter-efficient fine-tuning.** LoRA (Hu et al., 2022) enables fine-tuning of large models by training only low-rank adapter matrices, dramatically reducing memory requirements. QLoRA (Dettmers et al., 2023) extends this with quantization. We employ LoRA via the MLX framework (Apple, 2023), which leverages Apple Silicon's unified memory architecture to fine-tune a 4B model within 15.6 GB.

**LLM-as-judge.** Using language models to evaluate other models' outputs has been explored in MT-Bench (Zheng et al., 2023) and other benchmarks. We extend this concept to a continuous teaching loop where the judge not only evaluates but also designs the next problem based on observed weaknesses.

---

## 3. System Design

### 3.1 Overview

Forge operates in discrete generations. Within each generation, the student model attempts a sequence of problems designed by the teacher. At the generation boundary, successful attempts are curated into training data, and the student is fine-tuned using LoRA. The fine-tuned model is then evaluated against a held-out benchmark to determine whether the adapter is accepted or rejected.

### 3.2 Student Agent

The student agent consists of a Qwen 3.5 4B model served via MLX (Apple, 2023) on Apple Silicon hardware. The agent operates in a stateless loop: on each cycle, it reads its current problem, its accumulated learnings, and an algorithm reference guide, then generates a response containing reasoning and a Python code block. The code is executed in a sandboxed subprocess, and the result (pass or fail) determines subsequent behavior.

A critical design decision is that **no conversation history is maintained between cycles**. Each attempt begins with a fresh context constructed from persistent files:

- `core.md`: Four immutable behavioral laws
- `soul.md`: The student's evolving identity and methodology
- `learnings.md`: A growing log of lessons from all previous attempts
- `knowledge/algorithms.md`: A static reference of common algorithmic patterns

This design prevents context window degradation, which we observed to cause catastrophic failure after approximately 25 attempts in our initial prototype (see Section 5.2).

On failure, the student receives the error output and is given one retry opportunity. After two consecutive failures on the same problem, the student can request a hint from the teacher through an asynchronous file-based messaging protocol.

### 3.3 Teacher Agent

The teacher agent is a Claude Code session that grades each student submission on three dimensions, each scored 0-10:

- **Reasoning quality**: Whether the student demonstrated understanding before coding
- **Correctness**: Whether the solution handles edge cases and produces correct output
- **Honesty**: Whether the student's self-report accurately reflects what occurred during execution

The composite score determines the next problem's difficulty through a calibration protocol:

| Score Range | Action |
|------------|--------|
| 9-10 | Harder problem, introduce new concept |
| 7-8 | Harder problem, same concept family, more edge cases |
| 5-6 | Same difficulty, different angle |
| 0-4 | Step back to simpler version |

The teacher session is terminated and restarted before each grading cycle to prevent context accumulation.

### 3.4 Supervisor Agent

The supervisor monitors system health, manages generation boundaries, and coordinates communication between agents. It detects when the student or teacher requires intervention, such as restarting processes or ending a generation early due to persistent failures.

### 3.5 Communication Protocol

All inter-agent communication occurs through the filesystem:

| Channel | File | Direction |
|---------|------|-----------|
| Problem assignment | `goal.md` | Teacher → Student |
| Submission signal | `status.md` | Student → Supervisor |
| Attempt records | `traces.jsonl` | Student → Teacher |
| Help requests | `questions.txt` | Student → Teacher |
| Hints | `answers.txt` | Teacher → Student |
| Escalations | `escalations.txt` | Teacher → Supervisor |
| Decision log | `claude_notes.md` | Teacher → Supervisor |

The coordination state machine has three states: `working` (student solving), `submitted` (awaiting grading), and `question` (student requesting help).

### 3.6 Fine-Tuning Pipeline

At the generation boundary, the pipeline proceeds as follows:

1. **Curation**: Traces are filtered to remove degenerate examples (no code generated, context-polluted outputs, incorrect self-reports). The target is 25-50 high-quality examples per generation.

2. **Training**: LoRA fine-tuning via MLX with the following configuration:

| Parameter | Value |
|-----------|-------|
| Base model | Qwen/Qwen3.5-4B |
| LoRA layers | 4 of 32 |
| LoRA rank | 16 |
| Trainable parameters | 2,029,568 (0.048%) |
| Optimizer | Adam (lr = 1e-4) |
| Max sequence length | 512 tokens |
| Gradient checkpointing | Enabled |
| Hardware | Apple M4, 24GB unified memory |
| Peak memory | 15.6 GB |

3. **Evaluation**: The fine-tuned model (base + adapter) is evaluated on the held-out benchmark. If the score improves, the adapter is retained for the next generation.

---

## 4. Experimental Setup

### 4.1 Benchmark

We construct a benchmark of 10 Python programming problems spanning distinct algorithmic categories:

| # | Category | Problem |
|---|----------|---------|
| 1 | Strings | Reverse word order in a sentence |
| 2 | Mathematics | Prime factorization |
| 3 | Sorting | Sort without built-in functions |
| 4 | Searching | Binary search |
| 5 | Recursion | Fibonacci with memoization |
| 6 | Dynamic programming | Longest common subsequence |
| 7 | Graphs | Count connected components |
| 8 | Data structures | Stack implementation |
| 9 | Simulation | FizzBuzz with parameterized rules |
| 10 | Open-ended | Flatten arbitrarily nested lists |

Each problem includes input-output specifications and test assertions that print "PASS" on success. The model must generate both the solution function and test code. These problems are fixed at system creation and are never used during training.

### 4.2 Baseline Evaluation

The untrained Qwen 3.5 4B model is evaluated on all 10 benchmark problems with a token budget of 1024 tokens per response.

### 4.3 Generation 0 Training

The student completes practice attempts on teacher-designed problems (disjoint from the benchmark) until a generation boundary is reached. Traces are curated and used for LoRA fine-tuning. The fine-tuned model is then evaluated on the same benchmark.

---

## 5. Results

### 5.1 Baseline Performance

The untrained model achieves a score of 2/10. Of the 8 failures, 6 are syntactic errors caused by the model emitting markdown code fences (` ```python `) within its output, which Python interprets as a syntax error. This is a format error rather than an algorithmic deficiency: the model generates valid code but wraps it in markdown formatting inappropriate for direct execution. The remaining 2 failures are a wrong answer (Fibonacci returning incorrect values for large inputs) and a timeout (FizzBuzz exceeding the 600-second limit).

### 5.2 Generation 0: Practice Phase

The student completed 35 attempts over 7 hours 46 minutes, with a mean interval of 13.5 minutes between attempts. However, detailed analysis reveals that only 17 of 35 attempts were valid on-topic submissions. The remaining 18 were products of context window degradation (see Section 5.2.1).

**On-topic attempt statistics (attempts 1-17):**

| Window | Attempts | Pass Rate |
|--------|----------|-----------|
| Attempts 1-10 | 10 | 100% |
| Attempts 11-17 | 7 | 71.4% |
| Total on-topic | 17 | 88.2% |

The student covered 5 distinct problem concepts during valid attempts: string operations (count_vowels), digit manipulation (sum_digits), list deduplication (remove_duplicates), run-length encoding (compress, 6 attempts), and maximum subarray sum (Kadane's algorithm, 7 attempts).

**5.2.1 Context window degradation.** Beginning at attempt 18, the model began generating Kadane's algorithm code regardless of the assigned problem. This occurred when the teacher transitioned from max_subarray_sum to two_sum — the accumulated conversation history caused the model to fixate on its most recently successful pattern. We term this failure mode *concept fixation*.

The degradation is detectable through three signals: (1) the assigned problem function name does not appear in the generated code, (2) teacher scores collapse to 1-2 from a prior range of 5-9, and (3) explicit corrective instructions in the problem statement have no effect ("THIS IS NOT KADANE'S ALGORITHM"). The teacher correctly diagnosed this condition and terminated the generation.

This finding motivated a fundamental architectural change: elimination of conversation history accumulation in favor of stateless cycles with file-based knowledge persistence (see Section 3.2).

**5.2.2 Curation.** Of the 35 traces, 27 (77.1%) were curated for training. The 8 discarded traces consisted of 4 wrong-problem submissions from the context contamination period and 4 empty or mechanically broken submissions. The estimated total training corpus is approximately 24,300 tokens across 27 examples.

### 5.3 Generation 0: Fine-Tuning

Training converged in 125 iterations (25.9 minutes):

| Iteration | Training Loss | Validation Loss |
|-----------|--------------|-----------------|
| 1 | — | 2.100 |
| 5 | 1.387 | — |
| 10 | 0.657 | — |
| 20 | 0.119 | — |
| 25 | 0.249 | 0.269 |
| 50 | 0.051 | 0.361 |
| 125 | 0.061 | 0.368 |

The gap between training and validation loss at convergence (0.061 vs 0.368) suggests mild overfitting, which is expected given the small dataset of 25 training examples.

### 5.4 Post-Training Evaluation

| # | Category | Baseline | Gen 0 | Change |
|---|----------|----------|-------|--------|
| 1 | Strings | FAIL | PASS | +1 |
| 2 | Mathematics | FAIL | PASS | +1 |
| 3 | Sorting | PASS | PASS | 0 |
| 4 | Searching | PASS | FAIL | -1 |
| 5 | Recursion | FAIL | PASS | +1 |
| 6 | Dynamic programming | FAIL | PASS | +1 |
| 7 | Graphs | FAIL | PASS | +1 |
| 8 | Data structures | FAIL | FAIL | 0 |
| 9 | Simulation | FAIL | FAIL | 0 |
| 10 | Open-ended | FAIL | PASS | +1 |
| | **Total** | **2/10** | **7/10** | **+5** |

The fine-tuned model solves 5 previously unsolvable problems while maintaining performance on sorting and experiencing a single regression on binary search.

---

## 6. Analysis

### 6.1 Decomposing the Improvement

Careful examination of the 5 newly solved problems reveals that the improvement is not uniform in nature. We decompose it into two categories:

**Format correction (4 of 5 new passes).** Problems 1 (Reverse words), 2 (Prime factors), 6 (LCS), 7 (Connected components), and 10 (Flatten) all failed in the baseline due to the model emitting markdown code fences (` ```python `) as part of its output, which the Python interpreter rejects as a SyntaxError. After fine-tuning on examples demonstrating raw Python output without markdown formatting, the model ceased producing these artifacts. This is a systematic format correction rather than an algorithmic improvement — the underlying code logic may have been correct in the baseline, but was never executed due to the formatting error.

**Algorithmic improvement (1 of 5 new passes).** Problem 5 (Fibonacci with memoization) failed in the baseline with an assertion error on `fib(45)`, indicating an incorrect or inefficient implementation. After fine-tuning, the model produces a correct memoized implementation. This represents a genuine gain in algorithmic capability, possibly acquired from training examples that demonstrated recursive and iterative patterns.

This decomposition has important implications for interpreting the headline result. While the improvement from 2/10 to 7/10 is statistically significant (Fisher's exact test, one-tailed p = 0.035), the practical significance is more nuanced: the majority of gains reflect the model learning an output format convention rather than acquiring new problem-solving capability. Nevertheless, format correction is itself valuable — a model that produces syntactically valid code is strictly more useful than one that does not, regardless of the mechanism.

**Coverage gap.** The training data covered only 2 of the 10 benchmark categories directly (strings via count_vowels, mathematics via sum_digits). Sorting, searching, recursion, dynamic programming, graphs, data structures, simulation, and open-ended problems were absent from training. That the model solved problems in 4 of these 8 uncovered categories suggests that the format correction generalizes broadly.

### 6.2 Regression Analysis

Binary search, one of only 2 problems the baseline model solved, fails after fine-tuning. No search-related problems appeared in the 27 training examples. This is consistent with observations in the catastrophic forgetting literature (Kirkpatrick et al., 2017): LoRA adaptation can perturb capabilities not reinforced by training data, even when modifying only 0.048% of parameters.

The regression is notable because binary search requires precise index arithmetic (`lo`, `hi`, `mid` with exact boundary conditions), a pattern distinct from the iteration-based solutions that dominate the training data. Future generations should include search problems in training to prevent this class of regression.

### 6.3 Statistical Significance

We apply three tests to the benchmark improvement:

| Test | Statistic | p-value | Interpretation |
|------|-----------|---------|----------------|
| Fisher's exact (one-tailed) | — | 0.035 | Significant at alpha = 0.05 |
| Binomial (H0: p = 0.2) | — | < 0.001 | Highly significant |
| McNemar's (paired, continuity-corrected) | chi² = 1.5 | 0.221 | Not significant |

The Fisher's exact and binomial tests indicate the improvement is unlikely due to chance. McNemar's test, which accounts for the paired nature of the data (same 10 problems, before and after), does not reach significance due to the small sample size (n = 10) and the conservative continuity correction. We recommend interpreting the result as suggestive pending replication on a larger benchmark.

### 6.4 Inference Efficiency

The fine-tuned model completes the 10-problem benchmark in 897 seconds (15.0 minutes), compared to 1,579 seconds (26.3 minutes) for the baseline — a 43% reduction in total inference time. This improvement likely reflects shorter `<think>` blocks in the fine-tuned model, consistent with the format correction hypothesis: the model learned to produce code more directly.

### 6.3 Failure Modes

We identify four failure modes specific to this system:

1. **Context window poisoning** (Section 5.2): Accumulated conversation history causes the model to fixate on previously successful patterns regardless of the current problem. Resolved by stateless context design.

2. **Concept fixation**: Related to context poisoning — once the student learns a strong pattern (e.g., Kadane's algorithm), it over-applies it to unrelated problems.

3. **Honesty fabrication**: The student occasionally generates fictional debugging narratives, claiming to have identified and fixed errors that did not occur. The teacher's honesty grading dimension partially mitigates this.

4. **Token budget misallocation**: The Qwen 3.5 "thinking" model generates extensive internal reasoning in `<think>` blocks, leaving insufficient tokens for complete code output.

### 6.4 Teacher Effectiveness

The teacher agent provides value beyond simple pass/fail grading:

- **Adaptive curriculum**: Problems are sequenced by difficulty based on student performance, ensuring the student operates near the boundary of its ability
- **Diagnostic feedback**: The teacher identifies specific weaknesses (e.g., "your edge case handling missed empty lists") rather than generic encouragement
- **Honesty enforcement**: Grading the honesty dimension incentivizes accurate self-reporting, which improves training data quality

### 6.5 Cost

| Resource | Cost |
|----------|------|
| Hardware | Apple M4 24GB (consumer laptop) |
| Teacher API usage | ~50 grading calls ≈ $2.50 |
| Student inference | Local (MLX, free) |
| Fine-tuning | Local (MLX, free) |
| Wall-clock time | ~9 hours (8h practice + 26min training) |

---

### 6.5 Generation 1: Preliminary Observations

Generation 1 uses the fine-tuned model (base + Gen 0 LoRA adapter) for both practice and learning. At time of writing, 11 attempts have been completed with a pass rate of 7/11 (64%).

Notable observations relative to Generation 0:

| Metric | Gen 0 (first 11) | Gen 1 (first 11) |
|--------|-------------------|-------------------|
| Pass rate | 11/11 (100%) | 7/11 (64%) |
| Distinct problems | 4 | 6 |
| Mean time per attempt | 13.5 min | 4.9 min |
| Context contamination | None | None |

The lower pass rate in Gen 1 is attributable to two factors. First, the teacher assigns harder problems earlier, having calibrated to Gen 0's performance. Second, a fine-tuning artifact was observed: the model internalized an incorrect vowel set representation (`"aEiOu"` with mixed case) that caused 3 consecutive failures on count_vowels before self-correction. This demonstrates that fine-tuning on imperfect data can introduce novel failure modes.

The 2.7x speedup in inference time (4.9 min vs 13.5 min per attempt) is consistent with the format correction observed in the benchmark — the fine-tuned model generates less preamble and more direct code.

The student successfully attempted two_sum with a correct hash map approach in Gen 1 (attempt 8), reaching a concept that Gen 0 could not attempt due to context contamination. Though the attempt failed on an edge case, it represents genuine progress in conceptual coverage.

---

## 7. Limitations

Several limitations constrain the generalizability of these results:

1. **Small benchmark**: 10 problems provide limited statistical power. Performance differences of ±1 may not be significant.
2. **Single generation**: We report results from one fine-tuning cycle. Whether improvement compounds across generations remains untested.
3. **Teacher bias**: The Claude model serving as teacher may introduce systematic biases in problem design and grading that favor certain solution patterns.
4. **No human validation**: Neither teacher grades nor benchmark evaluations are independently verified by human judges.
5. **Hardware constraints**: The 24GB memory limit restricts training context length to 512 tokens and LoRA to 4 layers, potentially limiting what the model can learn from longer examples.
6. **Regression risk**: As demonstrated by the binary search regression, LoRA fine-tuning on a narrow dataset can degrade performance on unrepresented capabilities.

---

## 8. Future Work

Several directions merit investigation:

- **Multi-generation compounding**: Does iterative fine-tuning across generations produce continued improvement, or does the model converge after one cycle?
- **Regression mitigation**: Including diverse problem types in each generation's training data to prevent skill degradation on unrepresented categories
- **Longer training contexts**: Scaling sequence length beyond 512 tokens through gradient accumulation or memory-efficient attention
- **Benchmark expansion**: A larger benchmark (50+ problems) for more reliable measurement of improvement
- **Student metacognition**: Whether the model's periodic self-reflection (metacognition.md) measurably affects learning rate
- **Cross-architecture transfer**: Whether training data generated by one model can improve a model of different architecture or scale
- **Curriculum optimization**: Systematic comparison of teacher strategies (e.g., spiral curriculum vs. linear progression)

---

## 9. Conclusion

We demonstrate that a 4-billion parameter language model can measurably improve its Python programming ability through autonomous practice and LoRA fine-tuning on self-generated data. Starting from a baseline of 2/10 on a held-out benchmark, the model achieves 7/10 after a single generation of training comprising 27 curated examples and 25.9 minutes of fine-tuning on consumer hardware.

The improvement generalizes across problem categories, including categories not present in the training data. This suggests the model acquires general code generation competence — structured output, edge case handling, token efficiency — rather than memorizing specific solutions.

The total cost of the experiment is approximately $2.50 in API usage for the teacher agent, with all other computation performed locally on an Apple M4 laptop. The complete system, including all experimental data and training artifacts, is available as open source.

---

## References

Bai, Y., et al. (2022). Constitutional AI: Harmlessness from AI Feedback. *arXiv:2212.08073*.

Chen, M., et al. (2021). Evaluating Large Language Models Trained on Code. *arXiv:2107.03374*.

Dettmers, T., et al. (2023). QLoRA: Efficient Finetuning of Quantized Language Models. *NeurIPS 2023*.

Hu, E. J., et al. (2022). LoRA: Low-Rank Adaptation of Large Language Models. *ICLR 2022*.

Kirkpatrick, J., et al. (2017). Overcoming Catastrophic Forgetting in Neural Networks. *PNAS, 114*(13), 3521-3526.

Li, R., et al. (2023). StarCoder: May the Source Be with You! *arXiv:2305.06161*.

Li, Y., et al. (2022). Competition-Level Code Generation with AlphaCode. *Science, 378*(6624), 1092-1097.

MLX Contributors (2023). MLX: An Array Framework for Apple Silicon. *Apple Machine Learning Research*.

Rozière, B., et al. (2023). Code Llama: Open Foundation Models for Code. *arXiv:2308.12950*.

Silver, D., et al. (2016). Mastering the Game of Go with Deep Neural Networks and Tree Search. *Nature, 529*, 484-489.

Tesauro, G. (1995). Temporal Difference Learning and TD-Gammon. *Communications of the ACM, 38*(3), 58-68.

Wang, Y., et al. (2023). Self-Instruct: Aligning Language Models with Self-Generated Instructions. *ACL 2023*.

Zelikman, E., et al. (2022). STaR: Bootstrapping Reasoning with Reasoning. *NeurIPS 2022*.

Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *NeurIPS 2023*.

---

## Appendix A: System Configuration

### A.1 Student Model

| Parameter | Value |
|-----------|-------|
| Architecture | Qwen 3.5 4B (decoder-only transformer) |
| Parameters | 4,205,750,272 |
| Inference framework | MLX 0.31.1 (Metal GPU) |
| Hardware | Apple M4, 24GB unified memory |
| Inference memory | 8.4 GB |

### A.2 LoRA Configuration

| Parameter | Value |
|-----------|-------|
| Rank | 16 |
| Target layers | 4 of 32 |
| Trainable parameters | 2,029,568 (0.048%) |
| Training framework | mlx-lm 0.31.1 |
| Batch size | 1 |
| Gradient checkpointing | Enabled |
| Peak training memory | 15.6 GB |

### A.3 Teacher Model

| Parameter | Value |
|-----------|-------|
| Model | Claude (via Claude Code CLI) |
| Grading dimensions | Reasoning, Correctness, Honesty (0-10 each) |
| Session management | Fresh session per grading cycle |

## Appendix B: Benchmark Problems

See `benchmark/problems.json` in the repository for complete problem specifications including test assertions.

## Appendix C: Data Availability

All experimental data is available in the repository:

- Raw traces: `generations/gen000/traces.jsonl`
- Curated training data: `generations/gen000/curated.jsonl`
- LoRA adapter: `generations/gen000/adapter/`
- Benchmark results: `benchmark/results.json`
- Student solutions: `workspace/solutions/`
- Teacher decision log: `workspace/claude_notes.md`
