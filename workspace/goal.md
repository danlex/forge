## Problem

Write a function `max_sliding_window(nums, k)` that takes a list of integers and a window size `k`, and returns a list of the maximum value in each sliding window of size `k`.

The window slides one position at a time from left to right.

Examples:
```
max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) -> [3, 3, 5, 5, 6, 7]
  Window [1, 3, -1] -> max 3
  Window [3, -1, -3] -> max 3
  Window [-1, -3, 5] -> max 5
  Window [-3, 5, 3] -> max 5
  Window [5, 3, 6] -> max 6
  Window [3, 6, 7] -> max 7

max_sliding_window([1], 1) -> [1]
max_sliding_window([4, 2], 2) -> [4]
max_sliding_window([], 3) -> []
```

Test your solution:
```python
# Your solution here

# Tests
result = max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3)
assert result == [3, 3, 5, 5, 6, 7], f"Test 1 failed: got {result}"
print("PASS: basic sliding window")

result = max_sliding_window([1], 1)
assert result == [1], f"Test 2 failed: got {result}"
print("PASS: single element")

result = max_sliding_window([], 3)
assert result == [], f"Test 3 failed: got {result}"
print("PASS: empty list")

result = max_sliding_window([4, 2], 2)
assert result == [4], f"Test 4 failed: got {result}"
print("PASS: window equals list size")

result = max_sliding_window([5, 5, 5, 5], 2)
assert result == [5, 5, 5], f"Test 5 failed: got {result}"
print("PASS: all same values")

result = max_sliding_window([9, 8, 7, 6, 5], 1)
assert result == [9, 8, 7, 6, 5], f"Test 6 failed: got {result}"
print("PASS: window size 1")

result = max_sliding_window([1, 2, 3, 4, 5], 3)
assert result == [3, 4, 5], f"Test 7 failed: got {result}"
print("PASS: ascending")

result = max_sliding_window([5, 4, 3, 2, 1], 3)
assert result == [5, 4, 3], f"Test 8 failed: got {result}"
print("PASS: descending")

print("PASS")
```

## Why this problem

You've mastered two pointers (sort_colors) and accumulator patterns (Kadane's). Sliding window is the next step: instead of one pass with a running state, you maintain a **fixed-size view** that moves through the data. The simplest approach: for each window position, take `max()` of the slice. A more advanced approach uses a deque to track candidates efficiently. Start simple — get the tests passing first.

## What good looks like

- Function takes `nums` and `k`, returns a list of max values
- Handles edge cases: empty list, k=1, window equals list length
- Correct number of windows: `len(nums) - k + 1`
- All 8 tests pass
- Reasoning explains the sliding window concept before coding

## Teacher feedback from last attempt

**Grade: 4/10 (reasoning=3, correctness=5, honesty=4)**

You PASSED two_pointer_sort_colors — all 9 tests passed, correct Dutch National Flag algorithm. But here's the honest assessment:

1. **You needed the full skeleton.** The hint section contained the complete solution — every line of the function body. You copied it verbatim. That's following instructions, not solving.

2. **Two degenerate failures first.** Both times you wrote the correct code in your reasoning but submitted a learnings entry as code. This is the SAME pattern from binary_search. You must put `def function_name():` in the code field, not `# What I learned:`.

3. **The algorithm is correct** — Dutch National Flag with three-pointer partition. You DO understand two pointers. But I can't give high marks when the solution was handed to you and the first two attempts were submission errors.

What you should take away:
- You CAN write two-pointer algorithms. Your reasoning proves it.
- Your recurring failure is putting code in the wrong field. CODE goes in code. LEARNINGS go in learnings.
- Next problem is harder: no skeleton provided. You have to write it yourself.
