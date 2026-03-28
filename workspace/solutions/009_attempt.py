"""
Attempt #9 — FAIL
Timestamp: 2026-03-28T04:50:06

Problem:
## Problem

Write a function `max_subarray_sum(nums)` that returns the largest sum
of any contiguous subarray within the list.

A subarray is a consecutive sequence of elements. The list will contain
at least one element.

Examples:
  max_subarray_sum([1, -3, 2, 1, -1]) -> 3       # subarray [2, 1]
  max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]) -> 6  # [4, -1, 2, 1]
  max_subarray_sum([5, 4, -1, 7, 8]) -> 23        # entire array
  max_subarray_sum([-1]) -> -1                     # single negative
  max_subarray_sum([-3, -2, -1, -4]) -> -1         # all negatives: pick least bad

Test your solution:
```python
# Your solution here

# Tests
assert max_subarray_sum([1, -3, 2, 1, -1]) == 3
assert max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
assert max_subarray_sum([5, 4, -1, 7, 8]) == 23
assert max_subarray_sum([-1]) == -1
assert max_subarray_sum([-3, -2, -1, -4]) == -1
assert max_subarray_sum([1]) == 1
assert max_subarray_sum([0, 0, 0]) == 0
assert max_subarray_sum([100, -1, 100]) == 199
print("PASS")
```

## Why this problem
This is the accumulator pattern taken to the next level. In compress, you
tracked a value and count, resetting when the value changed — a STRUCTURAL
reset. Here, you track a running sum and reset when it goes negative — a
MATHEMATICAL reset. The key insight is: a negative running sum can never
help a future subarray, so you discard it and start fresh.

This is called Kadane's algorithm and it appears everywhere: stock prices,
signal processing, optimization. It tests whether you truly understand the
accumulator pattern or just memorized the compress template.

## What good looks like
- Considers the brute force O(n²) approach first, then identifies why O(n) is possible
- Explains WHY a negative running sum should be discarded (not just "reset when negative")
- Handles the all-negatives case explicitly — the answer is the largest single element
- Tracks TWO values: current_sum (the accumulator) and max_sum (the best seen so far)
- Initializes max_sum correctly (not to 0, which would break for all-negatives)
- Shows understanding that this is the SAME pattern as compress but with a different reset trigger

## Teacher feedback from last attempt
You've solved compress 6 times now — the accumulator-with-reset pattern is
clearly internalized. Your code got slightly cleaner over iterations (nice use
of lst[1:] slicing), and your reasoning correctly identifies the flush-after-loop
requirement every time. Honesty was solid — no hallucinated errors.

The problem: there was no growth after your first solve. Solving the same problem
6 times with the same approach teaches nothing. The real test is whether you can
TRANSFER the pattern to a new context. This problem uses the same accumulator
logic but the reset condition is mathematical, not structural. If you truly
understand the pattern, you'll see the connection. If you memorized the template,
you'll struggle. Show me which it is.
"""

# ========================================
# Solution
# ========================================

# Test cases
assert max_subarray_sum([1, -3, 2, 1, -1]) == 3
assert max_subarray_sum([-3, -2, -1, -4]) == -1
assert max_subarray_sum([1, 2, 3, 4]) == 10
assert max_subarray_sum([1, -1, 1, -1, 1]) == 3
assert max_subarray_sum([5]) == 5
assert max_subarray_sum([-1, -2, -3]) == -1
assert max_subarray_sum([100]) == 100
print("Test 1:", max_subarray_sum([1, -3, 2, 1, -1]) == 3)
print("Test 2:", max_subarray_sum([-3, -2, -1, -4]) == -1)
print("Test 3:", max_subarray_sum([1, 2, 3, 4]) == 10)
print("Test 4:", max_subarray_sum([1, -1, 1, -1, 1]) == 3)
print("Test 5:", max_subarray_sum([5]) == 5)
print("Test 6:", max_subarray_sum([-1, -2, -3]) == -1)
print("Test 7:", max_subarray_sum([100]) == 100)


# ========================================
# Test Results
# ========================================
# Result: FAIL
# Output:
#   Traceback (most recent call last):
#     File "<string>", line 2, in <module>
#   NameError: name 'max_subarray_sum' is not defined
