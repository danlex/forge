# Skill: String Case Handling in Python

## The Rule

When comparing strings case-insensitively, the case of your input and
the case of your comparison values MUST match.

## Pattern 1: Lowercase everything

```python
# CORRECT — input lowered, comparison values lowercase
for c in s.lower():
    if c in "aeiou":       # all lowercase ✓
        ...

# WRONG — input lowered, comparison values mixed case
for c in s.lower():
    if c in "aEiOu":       # mixed case ✗ — 'e' != 'E'
        ...
```

## Pattern 2: Check both cases

```python
# CORRECT — no case conversion, check both
for c in s:
    if c in "aeiouAEIOU":  # both cases ✓
        ...
```

## Why this matters

Python treats 'e' and 'E' as completely different characters:
- 'e' == 'E' → False
- 'e' in {'a', 'E', 'i', 'O', 'u'} → False
- 'e' in {'a', 'e', 'i', 'o', 'u'} → True

## The mental check

Before running your code, ask: "Did I normalize case in the same way
for BOTH the input AND the values I'm comparing against?"

If you .lower() the input → your set/string must be all lowercase.
If you .upper() the input → your set/string must be all uppercase.
If you don't convert → include both cases in your comparison.
