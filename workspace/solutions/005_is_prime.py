"""
Attempt #5 — PASS
Timestamp: 2026-03-28T15:52:09

Problem:
## Problem

Write a function `is_prime(n)` that returns `True` if `n` is a prime number, `False` otherwise. A prime number is greater than 1 and divisible only by 1 and itself.

Examples:
```
is_prime(2) → True
is_prime(7) → True
is_prime(1) → False
is_prime(0) → False
is_prime(4) → False
is_prime(15) → False
is_prime(-3) → False
```

Test your solution:
```python
# Your solution here

# Tests
assert is_prime(2) == True, f"Expected True, got {is_prime(2)}"
print("PASS: 2")

assert is_prime(7) == True, f"Expected True, got {is_prime(7)}"
print("PASS: 7")

assert is_prime(1) == False, f"Expected False, got {is_prime(1)}"
print("PASS: 1")

assert is_prime(0) == False, f"Expected False, got {is_prime(0)}"
print("PASS: 0")

assert is_prime(4) == False, f"Expected False, got {is_prime(4)}"
print("PASS: 4")

assert is_prime(15) == False, f"Expected False, got {is_prime(15)}"
print("PASS: 15")

assert is_prime(-3) == False, f"Expected False, got {is_prime(-3)}"
print("PASS: -3")

assert is_prime(97) == True, f"Expected True, got {is_prime(97)}"
print("PASS: 97")
print("PASS")
```

## Why this problem

Simple math with conditionals and loops. After mastering string iteration with count_vowels, this moves to numeric reasoning: edge cases (0, 1, negatives), loop bounds (only need to check up to √n), and early returns. It tests whether you can handle boundary conditions cleanly.

## What good looks like

- Handle edge cases first: n <= 1 returns False immediately
- Only check divisors up to √n (or n**0.5) — not up to n
- Return False as soon as any divisor is found (early exit)
- All 8 tests pass
- Honest reporting of results

## Teacher feedback from last attempt

You nailed it on attempt 4 — `vowels = "aeiou"` with `s.lower()` is exactly right. That was a 3-attempt struggle with a one-character class of bug, and you persisted through it. The fix shows you understood the core issue: when you normalize case in one place, your comparison values must match. Your code was clean, your approach was correct from the start — it was just the implementation detail that tripped you up. Grade: 8/10. Moving you to a new concept now.
"""

# ========================================
# Solution
# ========================================

def is_prime(n):
    if n <= 1:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True

# Tests
assert is_prime(2) == True, f"Expected True, got {is_prime(2)}"
print("PASS: 2")

assert is_prime(7) == True, f"Expected True, got {is_prime(7)}"
print("PASS: 7")

assert is_prime(1) == False, f"Expected False, got {is_prime(1)}"
print("PASS: 1")

assert is_prime(0) == False, f"Expected False, got {is_prime(0)}"
print("PASS: 0")

assert is_prime(4) == False, f"Expected False, got {is_prime(4)}"
print("PASS: 4")

assert is_prime(15) == False, f"Expected False, got {is_prime(15)}"
print("PASS: 15")

assert is_prime(-3) == False, f"Expected False, got {is_prime(-3)}"
print("PASS: -3")

assert is_prime(97) == True, f"Expected True, got {is_prime(97)}"
print("PASS: 97")
print("PASS")


# ========================================
# Test Results: PASS
# ========================================
#   PASS: 2
#   PASS: 7
#   PASS: 1
#   PASS: 0
#   PASS: 4
#   PASS: 15
#   PASS: -3
#   PASS: 97
#   PASS
