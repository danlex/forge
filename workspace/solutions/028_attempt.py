"""
Attempt #28 — FAIL
Timestamp: 2026-03-28T09:03:06

Problem:
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
    counts = {}
    for word in text.lower().split():
        counts[word] = counts.get(word, 0) + 1
    return counts

# Tests
assert word_count("hello world hello") == {"hello": 2, "world": 1}
assert word_count("The the THE") == {"the": 3}
assert word_count("") == {}
assert word_count("one") == {"one": 1}
assert word_count("a b c a b a") == {"a": 3, "b": 2, "c": 1}
assert word_count("Python python PYTHON") == {"python": 3}
print("PASS")
```

## Teacher feedback
Your last 10 attempts all submitted Kadane's algorithm instead of word_count.
Your learnings show you CAN reason about word_count — but your code always
reverts to Kadane's. Focus on submitting the code that matches the problem.
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
