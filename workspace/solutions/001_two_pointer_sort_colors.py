"""
Attempt #1 — PASS
Timestamp: 2026-03-28T17:07:06

Problem:
## Problem

Write a function `two_pointer_sort_colors(nums)` that sorts a list containing only the values `0`, `1`, and `2` **in-place** (modifying the original list) and returns the sorted list.

You must solve this in a **single pass** through the list using the **two-pointer technique** (also called the Dutch National Flag algorithm). Do NOT use Python's built-in `sort()` or `sorted()`.

The idea: use three pointers — `low`, `mid`, and `high`:
- Everything before `low` is `0`
- Everything between `low` and `mid` is `1`
- Everything after `high` is `2`
- Between `mid` and `high` is unprocessed

Examples:
```
two_pointer_sort_colors([2, 0, 1])          -> [0, 1, 2]
two_pointer_sort_colors([2, 0, 2, 1, 1, 0]) -> [0, 0, 1, 1, 2, 2]
two_pointer_sort_colors([0])                 -> [0]
two_pointer_sort_colors([])                  -> []
```

Test your solution:
```python
# Your solution here

# Tests
result = two_pointer_sort_colors([2, 0, 1])
assert result == [0, 1, 2], f"Test 1 failed: got {result}"
print("PASS: basic case")

result = two_pointer_sort_colors([2, 0, 2, 1, 1, 0])
assert result == [0, 0, 1, 1, 2, 2], f"Test 2 failed: got {result}"
print("PASS: mixed values")

result = two_pointer_sort_colors([0])
assert result == [0], f"Test 3 failed: got {result}"
print("PASS: single element")

result = two_pointer_sort_colors([])
assert result == [], f"Test 4 failed: got {result}"
print("PASS: empty list")

result = two_pointer_sort_colors([0, 0, 0])
assert result == [0, 0, 0], f"Test 5 failed: got {result}"
print("PASS: all zeros")

result = two_pointer_sort_colors([2, 2, 2])
assert result == [2, 2, 2], f"Test 6 failed: got {result}"
print("PASS: all twos")

result = two_pointer_sort_colors([1, 1, 1])
assert result == [1, 1, 1], f"Test 7 failed: got {result}"
print("PASS: all ones")

result = two_pointer_sort_colors([2, 1, 0])
assert result == [0, 1, 2], f"Test 8 failed: got {result}"
print("PASS: reverse sorted")

result = two_pointer_sort_colors([0, 1, 2, 0, 1, 2, 0, 1, 2])
assert result == [0, 0, 0, 1, 1, 1, 2, 2, 2], f"Test 9 failed: got {result}"
print("PASS: repeating pattern")

print("PASS")
```

## Why this problem

Two pointers is the next step after binary search. In binary search you used `low` and `high` to narrow a search range. Here you use pointers to **partition** a list in a single pass. This is a foundational technique for many problems: partitioning, merging, sliding windows. The Dutch National Flag algorithm is the classic introduction.

## What good looks like

- Reasoning explains the three-region invariant (0s before low, 1s between low and mid, 2s after high)
- Uses swap operations rather than creating a new list
- Single pass — `mid` moves from left to right, never backwards
- Handles edge cases (empty, single element, all same value)
- All 9 tests pass

## Hint

Here is a skeleton. Fill in the logic inside the while loop:

```python
def two_pointer_sort_colors(nums):
    low = 0
    mid = 0
    high = len(nums) - 1

    while mid <= high:
        if nums[mid] == 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:  # nums[mid] == 2
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1
    return nums
```

Copy this skeleton. Add the test cases from above. Run it. That is all you need to do.

## Teacher feedback from last attempt

**Grade: 1/10 (reasoning=1, correctness=0, honesty=1)**

DEGENERATE ATTEMPT. You submitted comments about learning instead of actual Python code. Your code field contained only lines starting with `#` — no function definition, no executable code, no tests.

This is the SECOND time you have done this (first was binary_search #12). You MUST submit a Python FUNCTION, not a description of a function. Not a learnings entry. Not comments.

Your reasoning field actually contained a correct solution — you wrote the right code in the wrong place. The code field is what gets executed. Put your `def two_pointer_sort_colors(nums):` function there, followed by the test assertions and `print("PASS")`.

Read commands.txt NOW. It explains exactly what to do.
"""

# ========================================
# Solution
# ========================================

def two_pointer_sort_colors(nums):
    low = 0
    mid = 0
    high = len(nums) - 1

    while mid <= high:
        if nums[mid] == 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:  # nums[mid] == 2
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1
    return nums

# Tests
result = two_pointer_sort_colors([2, 0, 1])
assert result == [0, 1, 2], f"Test 1 failed: got {result}"
print("PASS: basic case")

result = two_pointer_sort_colors([2, 0, 2, 1, 1, 0])
assert result == [0, 0, 1, 1, 2, 2], f"Test 2 failed: got {result}"
print("PASS: mixed values")

result = two_pointer_sort_colors([0])
assert result == [0], f"Test 3 failed: got {result}"
print("PASS: single element")

result = two_pointer_sort_colors([])
assert result == [], f"Test 4 failed: got {result}"
print("PASS: empty list")

result = two_pointer_sort_colors([0, 0, 0])
assert result == [0, 0, 0], f"Test 5 failed: got {result}"
print("PASS: all zeros")

result = two_pointer_sort_colors([2, 2, 2])
assert result == [2, 2, 2], f"Test 6 failed: got {result}"
print("PASS: all twos")

result = two_pointer_sort_colors([1, 1, 1])
assert result == [1, 1, 1], f"Test 7 failed: got {result}"
print("PASS: all ones")

result = two_pointer_sort_colors([2, 1, 0])
assert result == [0, 1, 2], f"Test 8 failed: got {result}"
print("PASS: reverse sorted")

result = two_pointer_sort_colors([0, 1, 2, 0, 1, 2, 0, 1, 2])
assert result == [0, 0, 0, 1, 1, 1, 2, 2, 2], f"Test 9 failed: got {result}"
print("PASS: repeating pattern")

print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS: basic case
#   PASS: mixed values
#   PASS: single element
#   PASS: empty list
#   PASS: all zeros
#   PASS: all twos
#   PASS: all ones
#   PASS: reverse sorted
#   PASS: repeating pattern
#   PASS
