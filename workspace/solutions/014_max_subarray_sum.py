"""
Attempt #14 — FAIL
Timestamp: 2026-03-28T06:00:43

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

def max_subarray_sum(arr):
    """
    Kadane's Algorithm - Maximum Contiguous Subarray Sum
    Time: O(n), Space: O(1)
    """
    # Handle edge case of empty array
    if not arr:
        return 0
    
    # Initialize with first element
    max_sum = arr[0]
    current_sum = arr[0]
    
    # Iterate through the rest of the array
    for num in arr[1:]:
        # Either add to current or start fresh with current num
        current_sum = max(num, current_sum + num)
        # Track the maximum seen so far
        max_sum = max(max_sum, current_sum)
    
    return max_sum

# Test cases
test_cases = [
    (['[1, -2, 3, -1, 2, -1, 3]', 6, 6], "Test 1: Mixed positives/negatives"),
    (['[5, -3, 5]', 7, 7], "Test 2: Positive with negative"),
    (['[-2, 1, -3, 4, -1, 2, 1, -5, 4]', 6, 6], "Test 3: Multiple positives/negatives"),
    (['[-2, -3, -1, -4]', -1, -1], "Test 4: All negatives"),
    (['[1]', 1, 1], "Test 5: Single positive"),
    (['[1, -1, 1, -1, 1, -1]', 1, 1], "Test 6: Alternating pattern"),
]

results = []
for test in test_cases:
    # Parse the test input
    input_str, expected, got = test[0]
    input_arr = [int(x) for x in input_str.split(',')]
    
    actual = max_subarray_sum(input_arr)
    passed = actual == expected
    
    result = "PASS" if passed else "FAIL"
    results.append((result, input_str, expected, actual))
    print(f"{result}: Input {input_str} | Expected {expected} | Got {actual}")

# Print summary
print("\n=== Summary ===")
all_passed = all(r[0] == "PASS" for r in results)
for i, (result, input_str, expected, actual) in enumerate(results, 1):
    print(f"Test {i}: {result} | Expected {expected}, Got {actual}")

print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")


# ========================================
# Test Results
# ========================================
# Result: FAIL
# Output:
#   Traceback (most recent call last):
#     File "<string>", line 37, in <module>
#   ValueError: invalid literal for int() with base 10: '[1'
