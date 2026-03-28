"""
Attempt #4 — PASS
Timestamp: 2026-03-28T15:47:32

Problem:
## Problem

Write a function `count_vowels(s)` that takes a string and returns the number of vowels (a, e, i, o, u) in it. The function should be case-insensitive.

Examples:
```
count_vowels("hello") → 2
count_vowels("AEIOU") → 5
count_vowels("xyz") → 0
count_vowels("") → 0
```

Test your solution:
```python
# Your solution here

# Tests
assert count_vowels("hello") == 2, f"Expected 2, got {count_vowels('hello')}"
print("PASS: hello")

assert count_vowels("AEIOU") == 5, f"Expected 5, got {count_vowels('AEIOU')}"
print("PASS: AEIOU")

assert count_vowels("xyz") == 0, f"Expected 0, got {count_vowels('xyz')}"
print("PASS: xyz")

assert count_vowels("") == 0, f"Expected 0, got {count_vowels('')}"
print("PASS: empty string")

assert count_vowels("Beautiful Day") == 6, f"Expected 6, got {count_vowels('Beautiful Day')}"
print("PASS: Beautiful Day")
print("PASS")
```

## Why this problem

Basic string iteration with case handling. You solved this in Gen 0 — this is a check that you can still do it cleanly. The key concept is making sure your vowel-checking logic is consistent with any case conversion you apply to the input.

## What good looks like

- If you lowercase the input with `.lower()`, your vowel set/string must also be all lowercase: `"aeiou"`, not `"aEiOu"`
- Alternatively, check both cases without converting: `c in "aeiouAEIOU"`
- Either approach works, but the case of your comparison values must match the case of your input characters
- All 5 tests pass
- No hallucinated test results — if a test fails, say so

## Teacher feedback from last attempt

Your last attempt failed because of a casing inconsistency. You wrote `vowels = set("aEiOu")` — that set contains uppercase `'E'` and `'O'`. But you also wrote `for c in s.lower()` which converts all characters to lowercase. So when checking `'e' in {'a', 'E', 'i', 'O', 'u'}`, it returns False — lowercase `'e'` does not equal uppercase `'E'`. That's why `count_vowels("hello")` returned 0 instead of 2.

The fix is simple: if you lowercase the input, use all-lowercase vowels: `set("aeiou")`. Your approach was correct — the implementation had a one-character class of bug. Also: your reasoning claimed "All tests passed" but the output was an AssertionError. Report what actually happened, not what you expected to happen.
"""

# ========================================
# Solution
# ========================================

def count_vowels(s):
    vowels = "aeiou"
    count = 0
    for c in s.lower():
        if c in vowels:
            count += 1
    return count

# Tests
assert count_vowels("hello") == 2, f"Expected 2, got {count_vowels('hello')}"
print("PASS: hello")

assert count_vowels("AEIOU") == 5, f"Expected 5, got {count_vowels('AEIOU')}"
print("PASS: AEIOU")

assert count_vowels("xyz") == 0, f"Expected 0, got {count_vowels('xyz')}"
print("PASS: xyz")

assert count_vowels("") == 0, f"Expected 0, got {count_vowels('')}"
print("PASS: empty string")

assert count_vowels("Beautiful Day") == 6, f"Expected 6, got {count_vowels('Beautiful Day')}"
print("PASS: Beautiful Day")
print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS: hello
#   PASS: AEIOU
#   PASS: xyz
#   PASS: empty string
#   PASS: Beautiful Day
#   PASS
