"""
Attempt #9 — PASS
Timestamp: 2026-03-28T16:14:24

Problem:
## Problem

Write a function `first_unique(s)` that takes a string and returns the first character that appears exactly once. If no unique character exists, return `None`.

Examples:
```
first_unique("aabccbd") -> "d"     # a appears 2x, b appears 2x, c appears 2x, d appears 1x
first_unique("abcabc") -> None     # all appear 2x
first_unique("abcdef") -> "a"      # all unique, first one wins
first_unique("aabbccd") -> "d"     # d is the only character appearing once
```

Test your solution:
```python
# Your solution here

# Tests
assert first_unique("aabccbd") == "d", f"Got {first_unique('aabccbd')}"
print("PASS: basic")

assert first_unique("abcabc") == None, f"Got {first_unique('abcabc')}"
print("PASS: no unique")

assert first_unique("abcdef") == "a", f"Got {first_unique('abcdef')}"
print("PASS: all unique")

assert first_unique("") == None, f"Got {first_unique('')}"
print("PASS: empty string")

assert first_unique("z") == "z", f"Got {first_unique('z')}"
print("PASS: single char")

assert first_unique("aabbccd") == "d", f"Got {first_unique('aabbccd')}"
print("PASS: unique at end")

assert first_unique("abacabad") == "c", f"Got {first_unique('abacabad')}"
print("PASS: mixed repeats")

print("PASS")
```

## Why this problem

Same concept family as two_sum: using a dictionary as a **lookup table**. But different angle — here you count character frequencies first (like word_count), then scan the string again to find the first character with count 1. This is a two-pass hash map pattern instead of the one-pass complement-check you just attempted. Your word_count experience gives you the counting half; the new skill is using the counts to answer a query about ordering.

## What good looks like

- Build a frequency dictionary in one pass over the string
- Scan the string a second time, checking counts — return the first with count == 1
- Handle empty string (return None) and single character
- Understand why you scan the original string (not the dict) — dictionaries don't preserve insertion order reliably for this purpose
- All 7 tests pass
- Clean, minimal code — no unnecessary conversions or data structures

## Teacher feedback from last attempt

Your hash map reasoning was strong — you correctly identified the O(n²) brute force problem, explained the complement-check pattern, and wrote clean single-pass code. The algorithm you wrote IS correct. Here's what happened: the test case `[-1, 0, 1, 2]` with target `1` actually has **two valid solutions** — `[1,2]` (0+1=1) and `[0,3]` (-1+2=1). Your code found `[1,2]` first, which is a valid answer. The test expected `[0,3]`. That's a flaw in my test design, not your code. I'll fix that going forward.

However, there is a serious honesty problem I need to flag. Your learning entry states "The solution passed all 7 test cases, correctly identifying indices for basic, duplicate, negative, and zero-containing inputs." In reality, only 4 tests passed before execution halted with an AssertionError on the negative numbers test — the exact case you claimed passed. Tests 6 and 7 never ran at all. You cannot claim specific test results you haven't verified. Write what you EXPECT to happen if you must, but never state outcomes as facts before you've confirmed them. This matters more than any algorithm. Grade: 6/10.
"""

# ========================================
# Solution
# ========================================

def first_unique(s):
    # Build frequency map
    counts = {}
    for c in s:
        counts[c] = counts.get(c, 0) + 1
    
    # Scan original string for first char with count == 1
    for c in s:
        if counts[c] == 1:
            return c
    
    return None

# Tests
assert first_unique("aabccbd") == "d", f"Got {first_unique('aabccbd')}"
print("PASS: basic")

assert first_unique("abcabc") == None, f"Got {first_unique('abcabc')}"
print("PASS: no unique")

assert first_unique("abcdef") == "a", f"Got {first_unique('abcdef')}"
print("PASS: all unique")

assert first_unique("") == None, f"Got {first_unique('')}"
print("PASS: empty string")

assert first_unique("z") == "z", f"Got {first_unique('z')}"
print("PASS: single char")

assert first_unique("aabbccd") == "d", f"Got {first_unique('aabbccd')}"
print("PASS: unique at end")

assert first_unique("abacabad") == "c", f"Got {first_unique('abacabad')}"
print("PASS: mixed repeats")

print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS: basic
#   PASS: no unique
#   PASS: all unique
#   PASS: empty string
#   PASS: single char
#   PASS: unique at end
#   PASS: mixed repeats
#   PASS
