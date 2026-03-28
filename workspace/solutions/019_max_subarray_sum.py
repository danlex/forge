"""
Attempt #19 — FAIL
Timestamp: 2026-03-28T07:13:23

Problem:
## Problem

Write a function `two_sum(nums, target)` that returns the indices of
two numbers in the list that add up to the target. Return them as a
tuple `(i, j)` where `i < j`. Each input has exactly one solution.
You may not use the same element twice.

Examples:
  two_sum([2, 7, 11, 15], 9)   -> (0, 1)   # 2 + 7 = 9
  two_sum([3, 2, 4], 6)        -> (1, 2)    # 2 + 4 = 6
  two_sum([3, 3], 6)           -> (0, 1)    # 3 + 3 = 6
  two_sum([1, 5, 3, 7, 2], 8)  -> (1, 3)    # 5 + 3 = 8? No: 1+7=8 → (0,3)

Wait — that last one: 1+7=8, so it's (0, 3). Be careful to check your
examples by hand before trusting them.

Test your solution:
```python
# Your solution here

# Tests
assert two_sum([2, 7, 11, 15], 9) == (0, 1)
assert two_sum([3, 2, 4], 6) == (1, 2)
assert two_sum([3, 3], 6) == (0, 1)
assert two_sum([1, 5, 3, 7, 2], 8) == (0, 3)
assert two_sum([0, 4, 3, 0], 0) == (0, 3)
assert two_sum([-1, -2, -3, -4, -5], -8) == (2, 4)
assert two_sum([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 19) == (8, 9)
print("PASS")
```

## Why this problem
This introduces dictionaries as a core data structure. The brute-force
approach is O(n²) — check every pair. The insight is that for each number,
you know exactly what complement you need (target - num), and a dict gives
O(1) lookup. This is the same "use a hash structure for fast lookup" pattern
you learned with sets in remove_duplicates, but now you're storing
key→value pairs (complement→index) instead of just membership.

This also tests whether you can think about WHAT to store in the dict.
The key is the complement (the number you're looking for), and the value
is the index where you saw it. Building the dict as you scan means you
only need one pass.

## What good looks like
- Considers brute force O(n²) first, then identifies the O(n) dict approach
- Explains what the dict maps: complement → index (not number → index)
- Handles the [3, 3] case: stores index AFTER checking, so you find the
  complement from an earlier position, not the same element
- Returns (i, j) with i < j consistently
- Doesn't over-engineer — this is 5-8 lines of code

## Teacher feedback from last attempt
You've mastered Kadane's algorithm — the accumulator-with-reset pattern is
clearly internalized. Your best attempt (#13) showed excellent reasoning:
identifying a wrong test case, correcting it with explanation, and connecting
back to the compress pattern. Score 9.

BUT: you had two mechanical failures (#12 NameError, #17 ValueError) where
the algorithm was correct but the submitted code was broken. #12 forgot the
function definition entirely. #17 used strings instead of actual lists in
test cases. These aren't conceptual gaps — they're submission quality issues.

For this problem: BEFORE you submit, mentally trace through your submitted
code top to bottom. Does the function exist? Are the test inputs actual
Python objects (lists, ints), not strings? Does the code run as a standalone
script? The algorithm is the easy part for you now — the hard part is clean
submission.
"""

# ========================================
# Solution
# ========================================

def max_subarray_sum(arr):
    if not arr:
        return 0
    
    current_max = global_max = arr[0]
    
    for i in range(1, len(arr)):
        current_max = max(arr[i], current_max + arr[i])
        global_max = max(global_max, current_max)
    
    return global_max


# ========================================
# Test Results
# ========================================
# Result: FAIL
# Output:
#   
