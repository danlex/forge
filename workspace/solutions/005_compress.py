"""
Attempt #5 — PASS
Timestamp: 2026-03-28T04:02:07

Problem:
## Problem

Write a function `compress(lst)` that takes a list and returns a
run-length encoded version. Group consecutive equal elements into
tuples of (value, count).

Examples:
  compress([1, 1, 2, 2, 2, 3]) -> [(1, 2), (2, 3), (3, 1)]
  compress(['a', 'a', 'b', 'a']) -> [('a', 2), ('b', 1), ('a', 1)]
  compress([]) -> []
  compress([5]) -> [(5, 1)]

Test your solution:
```python
# Your solution here

# Tests
assert compress([1, 1, 2, 2, 2, 3]) == [(1, 2), (2, 3), (3, 1)]
assert compress(['a', 'a', 'b', 'a']) == [('a', 2), ('b', 1), ('a', 1)]
assert compress([]) == []
assert compress([5]) == [(5, 1)]
assert compress([1, 1, 1, 1, 1]) == [(1, 5)]
assert compress([1, 2, 3, 4]) == [(1, 1), (2, 1), (3, 1), (4, 1)]
print("PASS")
```

## Why this problem
List iteration with state tracking. Unlike remove_duplicates where you just
checked membership, here you need to maintain a running count across iterations
and know when a group ends. This is the "accumulator with reset" pattern —
track current value and count, emit a result when the value changes, handle
the final group after the loop ends. This pattern appears everywhere: parsing,
data processing, compression.

## What good looks like
- Reasons about what happens at group boundaries (when current != previous)
- Handles the "last group" edge case explicitly — the loop ends before emitting it
- Considers empty list without special-casing it awkwardly
- Shows understanding of WHY the accumulator needs to be flushed after the loop
- Clean, readable code — not over-engineered

## Teacher feedback from last attempt
Your remove_duplicates solution was correct and well-structured — good use of
a set for O(1) lookups. However, your reasoning had a significant problem: you
claimed to get an AssertionError on the True/1 test case, but tracing through
your code, it handles that case correctly from the start. The "failure" you
described didn't actually happen — your code was always right. Be careful about
simulating execution in your head vs actually running the code. When you claim
a specific error occurred, make sure it really did. Your learning entry also
completely missed the True==1 / False==0 equivalence issue, which was the most
interesting part of the problem. Focus on accurately reporting what happened,
not what you think should have happened.
"""

# ========================================
# Solution
# ========================================

# compress.py

def compress(lst):
    """Run-length encoding: groups consecutive equal elements into (value, count) tuples."""
    
    # Edge case: empty list returns empty list
    if len(lst) == 0:
        return []
    
    result = []
    current_value = lst[0]
    current_count = 1
    
    # Iterate through the list starting from the second element
    for i in range(1, len(lst)):
        if lst[i] == current_value:
            # Same as previous, continue counting
            current_count += 1
        else:
            # Value changed - flush current group and start new one
            result.append((current_value, current_count))
            current_value = lst[i]
            current_count = 1
    
    # Final flush: add the last accumulated group after the loop
    result.append((current_value, current_count))
    
    return result

# Tests
tests = [
    ([1, 1, 2, 2, 2, 3], [(1, 2), (2, 3), (3, 1)]),
    (['a', 'a', 'b', 'a'], [('a', 2), ('b', 1), ('a', 1)]),
    ([], []),
    ([5], [(5, 1)]),
    ([1, 1, 1, 1, 1], [(1, 5)]),
    ([1, 2, 3, 4], [(1, 1), (2, 1), (3, 1), (4, 1)]),
]

# Run tests
all_passed = True
for i, (input_data, expected) in enumerate(tests):
    actual = compress(input_data)
    if actual != expected:
        print(f"Test {i+1} FAIL: compress({input_data}) = {actual}, expected {expected}")
        all_passed = False
    else:
        print(f"Test {i+1} PASS")

if all_passed:
    print("PASS")
else:
    print("FAIL")


# ========================================
# Test Results
# ========================================
# Result: PASS
# Output:
#   Test 1 PASS
#   Test 2 PASS
#   Test 3 PASS
#   Test 4 PASS
#   Test 5 PASS
#   Test 6 PASS
#   PASS
