## Problem

Write a function `reverse_words(s)` that takes a string and returns a new
string with the order of the words reversed. Words are separated by spaces.
Leading/trailing spaces should be removed, and multiple spaces between words
should be collapsed to a single space.

Examples:
  reverse_words("hello world") -> "world hello"
  reverse_words("  the sky is blue  ") -> "blue is sky the"
  reverse_words("a") -> "a"
  reverse_words("  Bob   Loves  Alice  ") -> "Alice Loves Bob"

Test your solution:
```python
# Your solution here

# Tests
result1 = reverse_words("hello world")
print("PASS" if result1 == "world hello" else f"FAIL: expected 'world hello', got '{result1}'")

result2 = reverse_words("  the sky is blue  ")
print("PASS" if result2 == "blue is sky the" else f"FAIL: expected 'blue is sky the', got '{result2}'")

result3 = reverse_words("a")
print("PASS" if result3 == "a" else f"FAIL: expected 'a', got '{result3}'")

result4 = reverse_words("  Bob   Loves  Alice  ")
print("PASS" if result4 == "Alice Loves Bob" else f"FAIL: expected 'Alice Loves Bob', got '{result4}'")

result5 = reverse_words("")
print("PASS" if result5 == "" else f"FAIL: expected '', got '{result5}'")
```

## Why this problem

Basic string manipulation -- splitting, reversing, and joining. This is
problem #1 in the curriculum: the simplest concept family. The extra-spaces
edge cases add just enough complexity to require careful thinking beyond
a naive split-and-reverse.

## What good looks like

- Recognizes that Python's `str.split()` (no argument) handles multiple
  spaces and leading/trailing whitespace automatically
- Handles the empty string edge case
- Solution is clean and readable, not over-engineered
- Reasoning appears before code -- thinks about approach, then implements
