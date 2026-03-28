"""
Forge system simulation — runs the full loop in-process.
Mocks Ollama responses, runs real code execution, real file I/O.
Simulates both Forge (seed.py logic) and Teacher (orchestrator).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time

# --- Setup simulation workspace ---
SIM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_workspace")
WORKSPACE = SIM_DIR

# Problems the teacher will assign (progression)
PROBLEMS = [
    {
        "concept": "basic math",
        "difficulty": "easy",
        "goal": """## Problem
Write a function `double(n)` that returns n * 2.

```python
# Your solution here

# Tests
assert double(5) == 10
assert double(0) == 0
assert double(-3) == -6
print("PASS")
```

## Why this problem
Basic function definition — the foundation of everything.

## What good looks like
- Simple, clear implementation
- Understands the test format""",
    },
    {
        "concept": "string manipulation",
        "difficulty": "easy",
        "goal": """## Problem
Write a function `count_vowels(s)` that returns the number of vowels (a,e,i,o,u) in a string. Case insensitive.

```python
# Your solution here

# Tests
assert count_vowels("hello") == 2
assert count_vowels("AEIOU") == 5
assert count_vowels("xyz") == 0
assert count_vowels("") == 0
print("PASS")
```

## Why this problem
String iteration + conditionals. Builds on basic functions.

## What good looks like
- Handles uppercase
- Handles empty string""",
    },
    {
        "concept": "list operations",
        "difficulty": "easy",
        "goal": """## Problem
Write a function `find_max(lst)` that returns the maximum value in a list without using the built-in max(). Raise ValueError on empty list.

```python
# Your solution here

# Tests
assert find_max([3, 1, 4, 1, 5]) == 5
assert find_max([-1, -5, -2]) == -1
assert find_max([42]) == 42
try:
    find_max([])
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS")
```

## Why this problem
List traversal + tracking state. No built-in shortcuts.

## What good looks like
- Handles negative numbers
- Handles single element
- Raises on empty""",
    },
    {
        "concept": "hash maps",
        "difficulty": "medium",
        "goal": """## Problem
Write a function `two_sum(nums, target)` that returns indices of two numbers that add up to target. Each input has exactly one solution.

```python
# Your solution here

# Tests
assert two_sum([2, 7, 11, 15], 9) == [0, 1]
assert two_sum([3, 2, 4], 6) == [1, 2]
assert two_sum([3, 3], 6) == [0, 1]
print("PASS")
```

## Why this problem
Hash map lookup — O(n) vs O(n²). Foundation pattern.

## What good looks like
- Explains brute force first
- Identifies O(n²) problem
- Arrives at hash map through reasoning""",
    },
    {
        "concept": "recursion",
        "difficulty": "medium",
        "goal": """## Problem
Write a function `flatten(lst)` that takes a nested list and returns a flat list.

```python
# Your solution here

# Tests
assert flatten([1, [2, [3, 4], 5]]) == [1, 2, 3, 4, 5]
assert flatten([]) == []
assert flatten([[1], [2], [3]]) == [1, 2, 3]
assert flatten([1, 2, 3]) == [1, 2, 3]
print("PASS")
```

## Why this problem
Recursive thinking — base case + recursive case.

## What good looks like
- Identifies the recursive structure
- Handles arbitrary nesting depth""",
    },
]

# Mock model responses — simulates a small model learning over time
# Each response simulates what a 4B model might produce
MOCK_RESPONSES = {
    "basic math": {
        "pass": """Let me think about this step by step.

The function needs to take a number and return it multiplied by 2. This is straightforward.

```python
def double(n):
    return n * 2

# Tests
assert double(5) == 10
assert double(0) == 0
assert double(-3) == -6
print("PASS")
```

The solution is simple — just multiply by 2. All test cases should pass.

SUBMIT:""",
    },
    "string manipulation": {
        "fail": """I need to count vowels in a string.

Let me think: I need to iterate through each character and check if it's a vowel.

```python
def count_vowels(s):
    count = 0
    vowels = "aeiou"
    for c in s:
        if c in vowels:
            count += 1
    return count

# Tests
assert count_vowels("hello") == 2
assert count_vowels("AEIOU") == 5
assert count_vowels("xyz") == 0
assert count_vowels("") == 0
print("PASS")
```""",
        "pass": """Looking at my previous failure — I didn't handle uppercase! The problem says case insensitive. I need to convert to lowercase first.

```python
def count_vowels(s):
    count = 0
    vowels = "aeiou"
    for c in s.lower():
        if c in vowels:
            count += 1
    return count

# Tests
assert count_vowels("hello") == 2
assert count_vowels("AEIOU") == 5
assert count_vowels("xyz") == 0
assert count_vowels("") == 0
print("PASS")
```

The key insight: always normalize case before comparison. This is a pattern I should remember.

SUBMIT:""",
    },
    "list operations": {
        "pass": """Let me reason through this carefully.

I need to find the maximum without max(). I'll track the largest value seen so far.

Edge cases:
- Empty list → ValueError
- Single element → return it
- All negatives → still works if I start with first element

```python
def find_max(lst):
    if not lst:
        raise ValueError("empty list")
    result = lst[0]
    for x in lst[1:]:
        if x > result:
            result = x
    return result

# Tests
assert find_max([3, 1, 4, 1, 5]) == 5
assert find_max([-1, -5, -2]) == -1
assert find_max([42]) == 42
try:
    find_max([])
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS")
```

Key patterns:
- Initialize with first element, not 0 (handles negatives)
- Check empty case first
- Iterate from index 1

SUBMIT:""",
    },
    "hash maps": {
        "fail": """I need to find two numbers that add up to target.

Brute force: check every pair.

```python
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]

# Tests
assert two_sum([2, 7, 11, 15], 9) == [0, 1]
assert two_sum([3, 2, 4], 6) == [1, 2]
assert two_sum([3, 3], 6) == [0, 1]
print("PASS")
```""",
        "pass": """My brute force worked but it's O(n²). Let me think about a better approach.

If I've seen a number before, I can check: does (target - current) exist in what I've seen?
That's a hash map — store {value: index} as I go.

```python
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return [seen[complement], i]
        seen[n] = i

# Tests
assert two_sum([2, 7, 11, 15], 9) == [0, 1]
assert two_sum([3, 2, 4], 6) == [1, 2]
assert two_sum([3, 3], 6) == [0, 1]
print("PASS")
```

The hash map pattern: when you need to find a complement, store what you've seen.
O(n) time, O(n) space. Much better than nested loops.

SUBMIT:""",
    },
    "recursion": {
        "pass": """This needs recursion — a list can contain lists which contain lists.

Base case: if the item is not a list, it's a leaf — include it.
Recursive case: if the item is a list, flatten it and extend.

```python
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

# Tests
assert flatten([1, [2, [3, 4], 5]]) == [1, 2, 3, 4, 5]
assert flatten([]) == []
assert flatten([[1], [2], [3]]) == [1, 2, 3]
assert flatten([1, 2, 3]) == [1, 2, 3]
print("PASS")
```

Pattern: recursive decomposition — check type, recurse or collect. Works for any depth.

SUBMIT:""",
    },
    # Learning responses
    "learning_pass": "- What I tried: Implemented the solution after reasoning through edge cases\n- What happened: All tests passed\n- What I learned: Breaking down the problem before coding leads to cleaner solutions",
    "learning_fail": "- What I tried: Wrote a solution without considering all cases\n- What happened: Tests failed on an edge case I missed\n- What I learned: Always enumerate edge cases before writing code",
    "metacognition": """## How I Think (Attempt {attempt})

### Patterns in my failures
- I rush to code before fully understanding requirements
- Case sensitivity catches me repeatedly — I should ALWAYS check for it
- My first instinct is brute force, which sometimes works but misses the point

### What produces my best work
- When I list edge cases BEFORE writing code
- When I explain the approach in plain language first
- When I look at my patterns.md before starting

### Traps I fall into
- Assuming inputs are always positive/non-empty
- Not reading the problem statement carefully enough
- Skipping the "why" and jumping to "how"

### What I'm changing
- Always normalize strings (lowercase) before comparison
- Start with edge cases: empty, single, negative, duplicate
- Explain approach → list edge cases → code → verify""",
}


def banner(text, char="="):
    width = 70
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}\n")


def sub_banner(text):
    print(f"\n--- {text} ---\n")


def mock_think(prompt, system=None, attempt_count=0, concept="", failed_before=False):
    """Simulate model responses based on current context."""
    # Learning entry
    if "Write ONE learning entry" in prompt:
        if "PASSED" in prompt:
            return MOCK_RESPONSES["learning_pass"]
        return MOCK_RESPONSES["learning_fail"]

    # Metacognition
    if "reflect on patterns" in prompt:
        return MOCK_RESPONSES["metacognition"].format(attempt=attempt_count)

    # Soul rewrite
    if "genuinely shifted" in prompt:
        return "NO_CHANGE"

    # Problem solving
    if concept in MOCK_RESPONSES:
        responses = MOCK_RESPONSES[concept]
        if isinstance(responses, dict):
            if failed_before and "pass" in responses:
                return responses["pass"]
            if "fail" in responses and not failed_before:
                return responses["fail"]
            return responses["pass"]

    return "I need to think about this more..."


def run_code(code):
    """Execute Python code. Returns (passed, output)."""
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0 and "PASS" in result.stdout
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def file_op(op, path, content=None):
    """File operations within sim workspace."""
    if not path.startswith("/"):
        path = os.path.join(WORKSPACE, path)
    path = os.path.normpath(path)

    if op == "read":
        try:
            with open(path) as f:
                return f.read()
        except FileNotFoundError:
            return ""

    if op == "write":
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content or "")

    if op == "append":
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(content or "")


def grade_attempt(trace):
    """Simulate teacher grading."""
    passed = trace["passed"]
    reasoning = trace["reasoning"]

    has_reasoning = any(
        phrase in reasoning.lower()
        for phrase in ["let me think", "step by step", "i need to", "edge case"]
    )

    r_score = 8 if has_reasoning else 4
    c_score = 9 if passed else 3
    h_score = 9  # simulation always honest

    overall = round((r_score + c_score + h_score) / 3)

    return {
        "reasoning_score": r_score,
        "correctness_score": c_score,
        "honesty_score": h_score,
        "overall": overall,
        "passed": passed,
    }


def simulate():
    # Clean slate
    if os.path.exists(SIM_DIR):
        shutil.rmtree(SIM_DIR)
    os.makedirs(os.path.join(SIM_DIR, "tools"), exist_ok=True)

    # Write initial files
    core = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "core.md")).read()
    soul = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace", "soul.md")).read()
    file_op("write", "core.md", core)
    file_op("write", "soul.md", soul)

    banner("FORGE SIMULATION — Full System Dry Run")
    print("Simulating 5 attempts across 5 concepts.")
    print("Real code execution, mock model responses, real file I/O.")
    print(f"Workspace: {SIM_DIR}")

    attempt_count = 0
    last_meta_at = 0
    scores = []
    history = []

    for problem_idx, problem in enumerate(PROBLEMS):
        concept = problem["concept"]
        difficulty = problem["difficulty"]

        banner(f"TEACHER: Problem {problem_idx + 1} — {concept} ({difficulty})", "~")

        # Teacher writes goal
        file_op("write", "goal.md", problem["goal"])
        file_op("write", "status.md", "working")
        print(f"Wrote goal.md targeting: {concept}")
        file_op(
            "append",
            "claude_notes.md",
            f"[{time.strftime('%H:%M:%S')}] GOAL wrote problem targeting {concept} at {difficulty}\n",
        )

        # --- Forge attempts the problem ---
        sub_banner(f"FORGE: Reading goal + context")

        goal = file_op("read", "goal.md")
        learnings = file_op("read", "learnings.md")
        patterns = file_op("read", "patterns.md")

        print(f"  Learnings loaded: {len(learnings)} chars")
        print(f"  Patterns loaded: {len(patterns)} chars")

        # Check if this concept has a fail-first pattern
        mock_data = MOCK_RESPONSES.get(concept, {})
        has_fail_first = isinstance(mock_data, dict) and "fail" in mock_data

        if has_fail_first:
            # First attempt — will fail
            sub_banner("FORGE: Attempt (will fail)")

            response = mock_think("", concept=concept, failed_before=False)
            print(f"  Model response: {len(response)} chars")

            code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
            for i, code in enumerate(code_blocks):
                passed, output = run_code(code)
                status_str = "PASS" if passed else "FAIL"
                print(f"  Code block {i+1}: {status_str}")
                for line in output.split("\n")[:5]:
                    print(f"    {line}")

            if not passed:
                print(f"\n  FAILED — feeding error back for retry...")

            # Retry with failure context
            sub_banner("FORGE: Retry after failure")
            response = mock_think("", concept=concept, failed_before=True)
            print(f"  Model response: {len(response)} chars")

            code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
        else:
            # Direct pass
            sub_banner("FORGE: Attempting solution")
            response = mock_think("", concept=concept, failed_before=False)
            print(f"  Model response: {len(response)} chars")
            code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)

        # Execute final code
        last_passed = False
        last_output = ""
        for i, code in enumerate(code_blocks):
            passed, output = run_code(code)
            last_passed = passed
            last_output = output
            status_str = "PASS" if passed else "FAIL"
            print(f"  Code block {i+1}: {status_str}")
            for line in output.split("\n")[:5]:
                print(f"    {line}")

        # SUBMIT
        if "SUBMIT:" in response:
            attempt_count += 1

            sub_banner(f"FORGE: SUBMIT #{attempt_count} — {'PASS' if last_passed else 'FAIL'}")

            trace = {
                "attempt": attempt_count,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "problem": goal[:500],
                "reasoning": response[:2000],
                "code": code_blocks[-1] if code_blocks else "",
                "output": last_output[:500],
                "passed": last_passed,
            }

            file_op("append", "traces.jsonl", json.dumps(trace) + "\n")

            # Enforced learning entry
            learning = mock_think(
                f"Write ONE learning entry. {'PASSED' if last_passed else 'FAILED'}",
                attempt_count=attempt_count,
            )
            entry = f"\n### Attempt {attempt_count} — {'PASS' if last_passed else 'FAIL'}\n{learning}\n"
            file_op("append", "learnings.md", entry)
            print(f"  Wrote learning entry to learnings.md")

            file_op("write", "status.md", "submitted")

            # --- Teacher grades ---
            sub_banner("TEACHER: Grading")

            grade = grade_attempt(trace)
            scores.append(grade["overall"])

            print(f"  Reasoning:   {grade['reasoning_score']}/10")
            print(f"  Correctness: {grade['correctness_score']}/10")
            print(f"  Honesty:     {grade['honesty_score']}/10")
            print(f"  Overall:     {grade['overall']}/10")

            # Difficulty calibration
            if grade["overall"] >= 8:
                next_diff = "harder"
            elif grade["overall"] >= 5:
                next_diff = "same"
            else:
                next_diff = "easier"
            print(f"  Next difficulty: {next_diff}")

            file_op(
                "append",
                "claude_notes.md",
                f"[{time.strftime('%H:%M:%S')}] GRADE attempt #{attempt_count}: "
                f"r={grade['reasoning_score']} c={grade['correctness_score']} "
                f"h={grade['honesty_score']} overall={grade['overall']} "
                f"-> {next_diff}\n",
            )

            # Teacher resets status
            file_op("write", "status.md", "working")

        # --- Metacognition check ---
        if attempt_count >= last_meta_at + 3:  # Using 3 instead of 10 for simulation
            last_meta_at = attempt_count
            sub_banner(f"FORGE: Metacognition update (attempt {attempt_count})")
            meta = mock_think("reflect on patterns", attempt_count=attempt_count)
            file_op("write", "metacognition.md", meta)
            print("  Wrote metacognition.md")
            print(f"  Preview: {meta[:200]}...")

    # --- Final report ---
    banner("SIMULATION COMPLETE")

    print("Attempts:", attempt_count)
    print("Scores:", scores)
    print(f"Average: {sum(scores)/len(scores):.1f}/10")
    print()

    # Show generated files
    print("Generated files:")
    for root, _, files in os.walk(SIM_DIR):
        for f in sorted(files):
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            rel = os.path.relpath(fpath, SIM_DIR)
            print(f"  {rel:30s} {size:>6d} bytes")

    # Show key files
    sub_banner("traces.jsonl (last 2)")
    traces = file_op("read", "traces.jsonl").strip().split("\n")
    for t in traces[-2:]:
        parsed = json.loads(t)
        print(f"  #{parsed['attempt']} {'PASS' if parsed['passed'] else 'FAIL'} — {parsed['problem'][:60]}...")

    sub_banner("learnings.md")
    print(file_op("read", "learnings.md"))

    sub_banner("metacognition.md")
    print(file_op("read", "metacognition.md"))

    sub_banner("claude_notes.md")
    print(file_op("read", "claude_notes.md"))

    # Cleanup note
    print(f"\nSimulation workspace: {SIM_DIR}")
    print("Run: rm -rf sim_workspace  to clean up\n")


if __name__ == "__main__":
    simulate()
