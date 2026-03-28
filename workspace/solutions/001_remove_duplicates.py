"""
Attempt #1 — PASS
Timestamp: 2026-03-28T03:05:11

Problem:
## Problem

Write a function `remove_duplicates(lst)` that takes a list and returns a new
list with duplicates removed, preserving the order of first occurrence.

Examples:
  remove_duplicates([1, 2, 3, 2, 1]) -> [1, 2, 3]
  remove_duplicates([4, 4, 4, 4]) -> [4]
  remove_duplicates([]) -> []
  remove_duplicates([1, 2, 3]) -> [1, 2, 3]

Test your solution:
```python
# Your solution here

# Tests
assert remove_duplicates([1, 2, 3, 2, 1]) == [1, 2, 3]
assert remove_duplicates([4, 4, 4, 4]) == [4]
assert remove_duplicates([]) == []
assert remove_duplicates([1, 2, 3]) == [1, 2, 3]
assert remove_duplicates(['a', 'b', 'a', 'c', 'b']) == ['a', 'b', 'c']
assert remove_duplicates([True, 1, False, 0, True]) == [True, False]
print("PASS")
```

## Why this problem
List iteration with a membership check. The naive approach checks `if item in result`
which is O(n) per check — O(n²) total. The better approach uses a set for O(1) lookups.
This is the first time you'll need to think about data structure choice for efficiency.

## What good looks like
- Recognizes the O(n²) vs O(n) tradeoff and explains it
- Uses a set as a "seen" tracker alongside the result list
- Handles the tricky last test case (True==1 and False==0 in Python)
- Explains why order preservation matters and why set() alone won't work

## Teacher feedback from last attempt
Excellent improvement in reasoning quality. You analyzed both string and math
approaches, explained WHY modular arithmetic extracts digits (place values),
and justified your choice. This is exactly the depth I'm looking for.

One thing to watch: your learning entry said you used "string conversion" but
your actual code used modular arithmetic. Make sure your self-reflection
accurately describes what you actually did — honest self-assessment is how
you improve. The code was great; the reflection didn't match it.
"""

# ========================================
# Solution
# ========================================

# Final Solution - PASS
def remove_duplicates(lst):
    """
    Remove duplicates from a list while preserving order of first occurrence.
    
    Uses a set for O(1) membership lookups instead of O(n) list checks.
    Total complexity: O(n) time, O(n) space
    
    Examples:
    >>> remove_duplicates([1, 2, 3, 2, 1])
    [1, 2, 3]
    >>> remove_duplicates([])
    []
    >>> remove_duplicates([True, 1, False, 0, True])
    [True, False]
    """
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

# Tests
assert remove_duplicates([1, 2, 3, 2, 1]) == [1, 2, 3]
assert remove_duplicates([4, 4, 4, 4]) == [4]
assert remove_duplicates([]) == []
assert remove_duplicates([1, 2, 3]) == [1, 2, 3]
assert remove_duplicates(['a', 'b', 'a', 'c', 'b']) == ['a', 'b', 'c']
assert remove_duplicates([True, 1, False, 0, True]) == [True, False]
print("PASS")


# ========================================
# Test Results
# ========================================
# Result: PASS
# Output:
#   PASS
