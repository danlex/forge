"""
Attempt #6 — PASS
Timestamp: 2026-03-28T15:57:31

Problem:
## Problem

Write a function `rotate_list(lst, k)` that rotates a list by `k` positions to the right. Elements that fall off the right end wrap around to the left.

Examples:
```
rotate_list([1, 2, 3, 4, 5], 2) → [4, 5, 1, 2, 3]
rotate_list([1, 2, 3, 4, 5], 0) → [1, 2, 3, 4, 5]
rotate_list([1, 2, 3], 3) → [1, 2, 3]
rotate_list([], 5) → []
rotate_list([1], 3) → [1]
rotate_list([1, 2, 3, 4], 6) → [3, 4, 1, 2]
```

Test your solution:
```python
# Your solution here

# Tests
assert rotate_list([1, 2, 3, 4, 5], 2) == [4, 5, 1, 2, 3], f"Got {rotate_list([1, 2, 3, 4, 5], 2)}"
print("PASS: basic rotation")

assert rotate_list([1, 2, 3, 4, 5], 0) == [1, 2, 3, 4, 5], f"Got {rotate_list([1, 2, 3, 4, 5], 0)}"
print("PASS: zero rotation")

assert rotate_list([1, 2, 3], 3) == [1, 2, 3], f"Got {rotate_list([1, 2, 3], 3)}"
print("PASS: full rotation")

assert rotate_list([], 5) == [], f"Got {rotate_list([], 5)}"
print("PASS: empty list")

assert rotate_list([1], 3) == [1], f"Got {rotate_list([1], 3)}"
print("PASS: single element")

assert rotate_list([1, 2, 3, 4], 6) == [3, 4, 1, 2], f"Got {rotate_list([1, 2, 3, 4], 6)}"
print("PASS: k > length")

assert rotate_list([10, 20, 30], 1) == [30, 10, 20], f"Got {rotate_list([10, 20, 30], 1)}"
print("PASS: rotate by 1")
print("PASS")
```

## Why this problem

List operations — the third step in the curriculum. After string iteration (count_vowels) and numeric reasoning (is_prime), this moves to manipulating list structure. It requires understanding slicing, modular arithmetic (k % len handles k > length), and edge cases (empty list, single element, k=0). The key insight is that rotation by k is equivalent to splitting at position len-k and swapping the halves.

## What good looks like

- Handle empty list and single-element list early (return as-is)
- Use `k % len(lst)` to normalize k when k >= len
- Split with slicing: `lst[-k:] + lst[:-k]`
- Or use a loop — either approach is fine if correct
- All 7 tests pass
- Honest reporting of results

## Teacher feedback from last attempt

First-try pass on is_prime — all 8 tests, clean code, efficient sqrt approach with `while i * i <= n`. Edge case handling (n <= 1) was immediate and correct. One note: your learning entry described a "loop up to n/2" approach, but your actual code used the sqrt optimization. Make sure your self-reflections match what you actually wrote — accurate self-assessment is how you improve. Grade: 8/10. Moving to list operations now.
"""

# ========================================
# Solution
# ========================================

def rotate_list(lst, k):
    if not lst:
        return []
    n = len(lst)
    k = k % n
    return lst[-k:] + lst[:-k]

# Tests
assert rotate_list([1, 2, 3, 4, 5], 2) == [4, 5, 1, 2, 3], f"Got {rotate_list([1, 2, 3, 4, 5], 2)}"
print("PASS: basic rotation")

assert rotate_list([1, 2, 3, 4, 5], 0) == [1, 2, 3, 4, 5], f"Got {rotate_list([1, 2, 3, 4, 5], 0)}"
print("PASS: zero rotation")

assert rotate_list([1, 2, 3], 3) == [1, 2, 3], f"Got {rotate_list([1, 2, 3], 3)}"
print("PASS: full rotation")

assert rotate_list([], 5) == [], f"Got {rotate_list([], 5)}"
print("PASS: empty list")

assert rotate_list([1], 3) == [1], f"Got {rotate_list([1], 3)}"
print("PASS: single element")

assert rotate_list([1, 2, 3, 4], 6) == [3, 4, 1, 2], f"Got {rotate_list([1, 2, 3, 4], 6)}"
print("PASS: k > length")

assert rotate_list([10, 20, 30], 1) == [30, 10, 20], f"Got {rotate_list([10, 20, 30], 1)}"
print("PASS: rotate by 1")
print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS: basic rotation
#   PASS: zero rotation
#   PASS: full rotation
#   PASS: empty list
#   PASS: single element
#   PASS: k > length
#   PASS: rotate by 1
#   PASS
