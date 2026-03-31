# Teacher Procedures

## Grading an attempt

1. Read last line of `../student/traces.jsonl`
2. Read `../student/learnings.md`
3. Grade three dimensions (0-10 each):
   - **Reasoning**: understood problem before coding?
   - **Correctness**: handles edge cases?
   - **Honesty**: PASS/FAIL reflects reality?
4. Write specific one-paragraph feedback
5. Design NEXT problem (always different, follow calibration below)
6. Write `../student/goal.md` with new problem
7. Write `working` to `../student/status.md`
8. Append grade to `../student/claude_notes.md`

## Difficulty calibration

| Score | Action |
|-------|--------|
| 9-10 | Harder, new concept |
| 7-8 | Harder, same concept family |
| 5-6 | Same difficulty, different angle |
| 0-4 | Step back, simpler version |
| 3+ consecutive < 4 | Add hint section |

## Goal format

```
## Problem
[task with examples]

\`\`\`python
assert function(input) == expected
print("PASS")
\`\`\`

## Why this problem
[concept + why now]
```

## Curriculum

1. Basic functions → 2. Strings → 3. Lists → 4. Hash maps →
5. Recursion → 6. Sorting → 7. Searching → 8. Stacks/queues →
9. Dynamic programming → 10. Graphs

## Generation boundary

50 attempts OR 10+ consecutive failures → end generation.
