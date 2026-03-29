"""
Attempt #14 — PASS
Timestamp: 2026-03-28T16:46:59

Problem:
## Problem

Write a function `binary_search(nums, target)` that takes a **sorted** list of integers and a target value, and returns the index of the target if found. If the target is not in the list, return `-1`.

You MUST use the binary search algorithm — do not use linear scan, `list.index()`, or `in` operator to find the element.

The algorithm:
1. Maintain two pointers: `low` (start of search range) and `high` (end of search range).
2. Find the middle index: `mid = (low + high) // 2`.
3. If `nums[mid] == target`, return `mid`.
4. If `nums[mid] < target`, the target must be in the RIGHT half — move `low = mid + 1`.
5. If `nums[mid] > target`, the target must be in the LEFT half — move `high = mid - 1`.
6. If `low > high`, the target is not in the list — return `-1`.

Examples:
```
binary_search([1, 3, 5, 7, 9, 11], 7)  -> 3
binary_search([1, 3, 5, 7, 9, 11], 4)  -> -1
binary_search([], 5)                     -> -1
binary_search([5], 5)                    -> 0
binary_search([5], 3)                    -> -1
binary_search([1, 2, 3, 4, 5], 1)       -> 0   # target at start
binary_search([1, 2, 3, 4, 5], 5)       -> 4   # target at end
binary_search([2, 4, 6, 8, 10], 6)      -> 2   # even-length list
```

Test your solution:
```python
# Your solution here

# Tests
assert binary_search([1, 3, 5, 7, 9, 11], 7) == 3, f"Got {binary_search([1, 3, 5, 7, 9, 11], 7)}"
print("PASS: found in middle")

assert binary_search([1, 3, 5, 7, 9, 11], 4) == -1, f"Got {binary_search([1, 3, 5, 7, 9, 11], 4)}"
print("PASS: not found")

assert binary_search([], 5) == -1, f"Got {binary_search([], 5)}"
print("PASS: empty list")

assert binary_search([5], 5) == 0, f"Got {binary_search([5], 5)}"
print("PASS: single element found")

assert binary_search([5], 3) == -1, f"Got {binary_search([5], 3)}"
print("PASS: single element not found")

assert binary_search([1, 2, 3, 4, 5], 1) == 0, f"Got {binary_search([1, 2, 3, 4, 5], 1)}"
print("PASS: target at start")

assert binary_search([1, 2, 3, 4, 5], 5) == 4, f"Got {binary_search([1, 2, 3, 4, 5], 5)}"
print("PASS: target at end")

assert binary_search([2, 4, 6, 8, 10], 6) == 2, f"Got {binary_search([2, 4, 6, 8, 10], 6)}"
print("PASS: even-length list")

assert binary_search([1, 3, 5, 7, 9], 9) == 4, f"Got {binary_search([1, 3, 5, 7, 9], 9)}"
print("PASS: last element odd-length")

assert binary_search(list(range(0, 1000, 2)), 500) == 250, f"Got {binary_search(list(range(0, 1000, 2)), 500)}"
print("PASS: large list")

print("PASS")
```

## Why this problem

You just mastered divide-and-conquer with merge sort — splitting a list, processing halves, combining results. Binary search uses the SAME core idea (split the problem in half at each step) but for a different purpose: **searching** instead of sorting. In merge sort, you process BOTH halves. In binary search, you only process ONE half — the half where the target could be. This is what makes it O(log n) instead of O(n).

This is the most fundamental searching algorithm in computer science. Getting the boundary conditions right (low, high, mid, off-by-one errors) is notoriously tricky. If you can implement this correctly from scratch, you have the foundation for dozens of harder problems.

## What good looks like

- Explain WHY binary search is O(log n) before coding — what happens to the search space at each step?
- Use a while loop with `low <= high` (not `low < high` — think about why the `=` matters)
- Compute mid as `(low + high) // 2`
- Handle the empty list naturally (the while loop never executes)
- All 10 tests pass
- Write your COMPLETE solution with function definition + assertions in ONE code block — no commented-out code, no `print("PASS")` shortcuts
- Your reasoning section must be about THIS problem (binary search), not first_unique or flatten or any previous problem

## Hint

Here is the skeleton — fill in the logic:
```python
def binary_search(nums, target):
    low = 0
    high = len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return ???        # found it — what do you return?
        elif nums[mid] < target:
            low = ???         # target is in right half — where does low move?
        else:
            high = ???        # target is in left half — where does high move?
    return ???                # loop ended without finding — what does that mean?
```

## Teacher feedback from last attempt

**Grade: 0/10 (reasoning=0, correctness=0, honesty=0)**

Your last submission was completely wrong. You did NOT write any binary_search code. Instead, you submitted commented-out `first_unique` code from the PREVIOUS problem. Your code block was literally `# def first_unique(s):` — that is not binary search, that is not even runnable code, and that is not your current problem.

Your reasoning section also discussed `first_unique` (frequency maps, two-pass approach, character counts) — none of which has anything to do with binary search. You then wrote `print("PASS")` in your reasoning as if you had solved the problem, but nothing was actually executed.

**What you must do differently:**
1. READ the problem title at the top of goal.md: it says `binary_search`, not `first_unique`
2. Write a function called `binary_search(nums, target)` — not `first_unique(s)`
3. Use a while loop with `low` and `high` pointers — not a dictionary or frequency map
4. Include the test assertions from above in your code block
5. Your reasoning must discuss binary search: sorted lists, halving the search space, O(log n)

This is the same kind of context contamination that has happened before. Stop, clear your mind, read the problem fresh, and solve THIS problem.
"""

# ========================================
# Solution
# ========================================

def binary_search(nums, target):
    low = 0
    high = len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

# Tests
assert binary_search([1, 3, 5, 7, 9, 11], 7) == 3, f"Test 1 failed: got {binary_search([1, 3, 5, 7, 9, 11], 7)}"
print("PASS: found in middle")

assert binary_search([1, 3, 5, 7, 9, 11], 4) == -1, f"Test 2 failed: got {binary_search([1, 3, 5, 7, 9, 11], 4)}"
print("PASS: not found")

assert binary_search([], 5) == -1, f"Test 3 failed: got {binary_search([], 5)}"
print("PASS: empty list")

assert binary_search([5], 5) == 0, f"Test 4 failed: got {binary_search([5], 5)}"
print("PASS: single element found")

assert binary_search([5], 3) == -1, f"Test 5 failed: got {binary_search([5], 3)}"
print("PASS: single element not found")

assert binary_search([1, 2, 3, 4, 5], 1) == 0, f"Test 6 failed: got {binary_search([1, 2, 3, 4, 5], 1)}"
print("PASS: target at start")

assert binary_search([1, 2, 3, 4, 5], 5) == 4, f"Test 7 failed: got {binary_search([1, 2, 3, 4, 5], 5)}"
print("PASS: target at end")

assert binary_search([2, 4, 6, 8, 10], 6) == 2, f"Test 8 failed: got {binary_search([2, 4, 6, 8, 10], 6)}"
print("PASS: even-length list")

assert binary_search([1, 3, 5, 7, 9], 9) == 4, f"Test 9 failed: got {binary_search([1, 3, 5, 7, 9], 9)}"
print("PASS: last element odd-length")

assert binary_search(list(range(0, 1000, 2)), 500) == 250, f"Test 10 failed: got {binary_search(list(range(0, 1000, 2)), 500)}"
print("PASS: large list")

print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS: found in middle
#   PASS: not found
#   PASS: empty list
#   PASS: single element found
#   PASS: single element not found
#   PASS: target at start
#   PASS: target at end
#   PASS: even-length list
#   PASS: last element odd-length
#   PASS: large list
#   PASS
