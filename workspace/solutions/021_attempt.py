"""
Attempt #21 — FAIL
Timestamp: 2026-03-28T07:43:07

Problem:
## STOP — READ commands.txt FIRST

Before doing ANYTHING, read workspace/commands.txt. It has critical instructions.

## Problem

Write a function `word_count(text)` that takes a string and returns a
dictionary mapping each word to how many times it appears. Words should
be compared case-insensitively (convert to lowercase). Split on whitespace.

Examples:
  word_count("hello world hello") -> {"hello": 2, "world": 1}
  word_count("The the THE") -> {"the": 3}
  word_count("") -> {}
  word_count("one") -> {"one": 1}

Test your solution:
```python
def word_count(text):
    # YOUR IMPLEMENTATION HERE
    pass

# Tests
assert word_count("hello world hello") == {"hello": 2, "world": 1}
assert word_count("The the THE") == {"the": 3}
assert word_count("") == {}
assert word_count("one") == {"one": 1}
assert word_count("a b c a b a") == {"a": 3, "b": 2, "c": 1}
assert word_count("Python python PYTHON") == {"python": 3}
print("PASS")
```

## THIS IS NOT KADANE'S ALGORITHM

You are NOT solving max_subarray_sum. You are NOT solving Kadane's algorithm.
You are counting WORDS in a STRING and returning a DICTIONARY.

The function name is word_count. The input is a string. The output is a dict.

## Why this problem
Introduces dictionaries for counting/grouping. You split a string into words,
then build a frequency table using a dict.

## What good looks like
- Uses a dict to count word frequencies
- Converts to lowercase before counting
- Handles empty string (returns {})
- 4-6 lines of code total

## Teacher feedback from last attempt
You submitted Kadane's algorithm AGAIN (attempt #23) despite the problem being
word_count. This is 6 consecutive wrong-problem submissions. I've written
detailed instructions in commands.txt — please read it before starting.
"""

# ========================================
# Solution
# ========================================

# no code

# ========================================
# Test Results
# ========================================
# Result: FAIL
# Output:
#   
