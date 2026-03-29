"""
Attempt #7 — PASS
Timestamp: 2026-03-28T16:02:38

Problem:
## Problem

Write a function `is_balanced(s)` that takes a string containing only brackets `()[]{}` and returns `True` if the brackets are balanced and properly nested, `False` otherwise.

Examples:
```
is_balanced("()") → True
is_balanced("()[]{}") → True
is_balanced("(]") → False
is_balanced("([)]") → False
is_balanced("{[]}") → True
is_balanced("") → True
is_balanced("(") → False
```

Test your solution:
```python
# Your solution here

# Tests
assert is_balanced("()") == True, f"Got {is_balanced('()')}"
print("PASS: simple pair")

assert is_balanced("()[]{}") == True, f"Got {is_balanced('()[]{}')}"
print("PASS: all types")

assert is_balanced("(]") == False, f"Got {is_balanced('(]')}"
print("PASS: mismatched")

assert is_balanced("([)]") == False, f"Got {is_balanced('([)]')}"
print("PASS: interleaved")

assert is_balanced("{[]}") == True, f"Got {is_balanced('{[]}')}"
print("PASS: nested")

assert is_balanced("") == True, f"Got {is_balanced('')}"
print("PASS: empty")

assert is_balanced("(") == False, f"Got {is_balanced('(')}"
print("PASS: unclosed")

assert is_balanced("())") == False, f"Got {is_balanced('())')}"
print("PASS: extra closing")
print("PASS")
```

## Why this problem

Conditionals and loops — step 4 in the curriculum. After mastering string iteration, math, and list manipulation, this introduces **state tracking through a loop**. The key insight is using a list as a stack: push opening brackets, pop and match on closing brackets. This requires multiple conditional branches (is it opening? is it closing? does it match?), a loop, and careful edge case handling (empty string, unmatched brackets, leftover stack). The stack is a fundamental data structure pattern that will recur in harder problems.

## What good looks like

- Use a list as a stack — push opening brackets, pop on closing
- Map each closing bracket to its expected opening bracket
- Check the stack is empty at the end (unclosed brackets)
- Handle empty string (return True)
- Handle mismatched types (e.g., "(]" → False)
- Handle interleaved brackets (e.g., "([)]" → False)
- All 8 tests pass
- Explain the stack approach before coding

## Teacher feedback from last attempt

Third consecutive first-try pass — strong streak. Your code is clean and minimal: empty list guard, `k % n`, slicing. Correct on all counts. However, your self-assessment accuracy is becoming a pattern issue. Your learning entry says slicing handles wrapping "without needing an extra `k % len(lst)` step" — but your code DOES use `k % n`, and removing it would break the `k > length` case (`[1,2,3,4][-6:] + [1,2,3,4][:-6]` gives `[1,2,3,4]`, not `[3,4,1,2]`). Last attempt you described "loop up to n/2" but coded sqrt. Read your own code before writing the learning entry — accurate self-knowledge is the foundation of improvement. Grade: 8/10. Stepping up to a new concept: stack-based state tracking.
"""

# ========================================
# Solution
# ========================================

def is_balanced(s):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    for c in s:
        if c in '({[':
            stack.append(c)
        elif c in ')}]':
            if not stack or stack.pop() != pairs[c]:
                return False
    return not stack

# Tests
assert is_balanced("()") == True, f"Got {is_balanced('()')}"
print("PASS: simple pair")

assert is_balanced("()[]{}") == True, f"Got {is_balanced('()[]{}')}"
print("PASS: all types")

assert is_balanced("(]") == False, f"Got {is_balanced('(]')}"
print("PASS: mismatched")

assert is_balanced("([)]") == False, f"Got {is_balanced('([)]')}"
print("PASS: interleaved")

assert is_balanced("{[]}") == True, f"Got {is_balanced('{[]}')}"
print("PASS: nested")

assert is_balanced("") == True, f"Got {is_balanced('')}"
print("PASS: empty")

assert is_balanced("(") == False, f"Got {is_balanced('(')}"
print("PASS: unclosed")

assert is_balanced("())") == False, f"Got {is_balanced('())')}"
print("PASS: extra closing")
print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS: simple pair
#   PASS: all types
#   PASS: mismatched
#   PASS: interleaved
#   PASS: nested
#   PASS: empty
#   PASS: unclosed
#   PASS: extra closing
#   PASS
