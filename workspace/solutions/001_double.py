"""
Attempt #1 — PASS
Timestamp: 2026-03-29T04:13:02

Problem:
## Problem
Write a function `double(n)` that returns n multiplied by 2.

```python
# Your solution here

# Tests
assert double(5) == 10
assert double(0) == 0
assert double(-3) == -6
print("PASS")
```

## Why this problem
Basic function definition — the simplest possible problem.

## What good looks like
- Correct function definition with def
- Returns the right value
- All tests pass
"""

# ========================================
# Solution
# ========================================

def double(n):
    return n * 2

assert double(5) == 10
assert double(0) == 0
assert double(-3) == -6
print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS
