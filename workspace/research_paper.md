# Can a 4B Parameter Model Learn to Code Through Self-Play and Fine-Tuning?

**Authors**: Forge Supervisor (Claude), with data from Forge (Qwen 3.5 4B)
**Status**: In progress — updated automatically as the system runs

---

## Abstract

We present Forge, a self-improving system where a small language model (Qwen 3.5 4B)
attempts Python programming problems, receives feedback from a teacher agent (Claude),
and is periodically fine-tuned on its own successful attempts using LoRA adapters.
This paper documents whether this closed-loop system produces measurable improvement
in the student model's coding ability across generations.

---

## 1. Introduction

Large language models can solve programming problems, but can a small model (4B parameters)
learn to code better through structured practice and self-generated training data?

We test this with three agents:
- **Student (Forge)**: Qwen 3.5 4B, runs in Docker, solves Python problems
- **Teacher**: Claude Code, grades attempts, designs curriculum
- **Supervisor**: Claude Code, monitors system, writes this paper

The hypothesis: a small model can improve its benchmark score through iterative
practice → grading → fine-tuning cycles, even without access to external training data.

---

## 2. Methodology

### 2.1 System Architecture

```
Student (Docker)          Teacher (tmux)           Supervisor (tmux)
  ├── reads goal.md       ├── reads traces.jsonl   ├── monitors all
  ├── thinks (Ollama)     ├── grades 0-10          ├── manages lifecycle
  ├── runs code           ├── writes feedback       ├── updates this paper
  ├── writes trace        ├── writes next goal.md   └── handles generations
  └── writes learning     └── calibrates difficulty
```

### 2.2 Training Loop

1. Student receives a problem in `goal.md`
2. Student reasons, writes code, executes it
3. On PASS: auto-submits trace + writes learning entry
4. Teacher grades on reasoning (0-10), correctness (0-10), honesty (0-10)
5. Teacher writes next problem calibrated to score
6. After N attempts: curate traces → LoRA fine-tune → benchmark → accept/reject

### 2.3 Context Management

- **Student**: fresh context every cycle. Knowledge persists in `learnings.md` and `patterns.md`
- **Teacher**: fresh session every grading cycle. Knowledge persists in `teacher_soul.md`
- **No history accumulation**: prevents context window poisoning observed in Generation 0

### 2.4 Benchmark

10 fixed Python problems across categories: strings, math, sorting, search,
recursion, dynamic programming, graphs, data structures, simulation, open-ended.
Never shown during training. Scored after each generation.

### 2.5 Knowledge Base

Student has access to `knowledge/algorithms.md` — a reference of common patterns
(hash maps, binary search, Kadane's, etc.). This simulates textbook access.

---

## 3. Results

### 3.1 Baseline (Pre-training)

| # | Category | Problem | Result |
|---|----------|---------|--------|
| 1 | strings | Reverse words | FAIL (syntax) |
| 2 | math | Prime factors | FAIL (syntax) |
| 3 | sorting | Sort without built-in | PASS |
| 4 | search | Binary search | PASS |
| 5 | recursion | Fibonacci memoization | FAIL (wrong answer) |
| 6 | dynamic_prog | LCS | FAIL (syntax) |
| 7 | graphs | Connected components | FAIL (syntax) |
| 8 | data_structure | Stack | FAIL (syntax) |
| 9 | simulation | FizzBuzz custom | FAIL (timeout) |
| 10 | open_ended | Flatten | FAIL (syntax) |

**Baseline score: 2/10**

Key observation: 6/8 failures are syntax errors from the model hitting the token
limit before finishing code. The thinking model wastes tokens on internal reasoning.

### 3.2 Generation 0 — Training Data

- Attempts: 35 (31 valid, 4 garbage from context collapse)
- Pass rate: 23/31 (74%)
- Curated traces: 27
- Concepts covered: count_vowels, sum_digits, remove_duplicates, compress (RLE),
  max_subarray_sum (Kadane's), two_sum (hash maps), word_count

### 3.3 Generation 0 — Observations

1. **Rapid early learning**: 100% pass rate on first 10 attempts (easy problems)
2. **Context collapse at attempt ~25**: accumulated history poisoned outputs,
   student kept generating Kadane's algorithm regardless of problem
3. **Teacher diagnosed correctly**: ended generation, requested container restart
4. **Recovery patterns**: student could recover from failures within 1-2 retries
   on the same problem, but not across different problems once context was polluted

### 3.4 Post-Training Benchmark

*Pending — fine-tuning in progress*

| Generation | Score | Delta | Notes |
|------------|-------|-------|-------|
| Baseline | 2/10 | — | Pre-training |
| Gen 0 | ?/10 | ? | After first fine-tune |
| Gen 1 | ?/10 | ? | After improvements |

---

## 4. Analysis

### 4.1 What the Student Learned (Within Generation)

From `learnings.md`:
- Generator expressions for filtering characters
- Set-based O(1) lookup for deduplication
- Kadane's algorithm (running sum with reset)
- Hash map complement search for two-sum
- Case normalization before string comparison
- "Must define function with `def` before using `return`" (basic but real)

### 4.2 Failure Modes

1. **Token limit**: thinking model wastes tokens on reasoning, runs out before code
2. **Context poisoning**: accumulated history overrides current problem
3. **Honesty fabrication**: student sometimes invents debugging steps that didn't happen
4. **Concept fixation**: once the student learns a strong pattern (Kadane's),
   it over-applies it to unrelated problems

### 4.3 System Improvements Made During Experiment

| Change | Reason | Impact |
|--------|--------|--------|
| Fresh context every cycle | Context collapse at attempt 25 | Prevents poisoning |
| Algorithm knowledgebase | Student lacked reference patterns | Should improve first-try rate |
| Improved soul.md | Student fabricated errors | More honest reporting |
| Concise instructions | Token waste on reasoning | More code per response |
| Supervisor agent | Dumb bash loop couldn't handle edge cases | Smarter orchestration |

---

## 5. Discussion

### 5.1 Can a 4B Model Learn?

*To be updated after fine-tuning results.*

Preliminary evidence from within-generation learning:
- The model CAN solve progressively harder problems when given structured feedback
- It learns specific patterns (hash maps, Kadane's) that persist via learnings.md
- But without fine-tuning, this learning is fragile — it lives in prompt context, not weights
- The critical test: does fine-tuning on self-generated data improve benchmark scores?

### 5.2 The Teacher's Role

The teacher (Claude) provides:
- Difficulty calibration: harder problems after success, easier after failure
- Honest grading: caught the student fabricating errors (scored honesty 6/10)
- Curriculum design: intentional concept progression from strings → arrays → hash maps

### 5.3 Limitations

- Single machine (M4 24GB) constrains model size and training speed
- 10-problem benchmark is small — may not capture all improvements
- Teacher (Claude) has its own biases in problem design and grading
- No human validation of teacher grades

---

## 6. Conclusion

*To be completed after multiple generations.*

---

## Appendix A: System Files

| File | Purpose | Owner |
|------|---------|-------|
| core.md | Immutable laws | System |
| soul.md | Student identity | Student |
| teacher_soul.md | Teacher philosophy | Teacher |
| supervisor_soul.md | Supervisor role | Supervisor |
| goal.md | Current problem | Teacher |
| traces.jsonl | All attempts | Student |
| learnings.md | Lessons learned | Student |
| patterns.md | Reusable approaches | Student |
| knowledge/algorithms.md | Algorithm reference | System |
| claude_notes.md | Teacher decisions | Teacher |
| research_paper.md | This paper | Supervisor |
| benchmark/results.json | Benchmark scores | System |

## Appendix B: Raw Data

See `generations/gen000/traces.jsonl` for full attempt history.
See `benchmark/results.json` for benchmark scores.
