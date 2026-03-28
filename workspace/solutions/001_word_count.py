"""
Attempt #1 — PASS
Timestamp: 2026-03-28T10:49:40

Problem:
## GENERATION 0 ENDED — AWAITING SUPERVISOR RESTART

This generation has been ended by the Teacher at attempt #31.

Reason: 14 consecutive wrong-problem submissions due to irreversible
context contamination. Forge's code generation is locked on Kadane's
algorithm regardless of the assigned problem.

Next steps (for supervisor):
1. Restart Forge's Docker container to clear conversation context
2. Teacher will proceed to curation of valid traces (#1-#17)
3. After curation → fine-tuning → evaluation → generation 1
"""

# ========================================
# Solution
# ========================================

def word_count(text):
    counts = {}
    # Convert text to lowercase and split into words
    words = text.lower().split()
    # Count each word
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts

# Test cases
test_cases = [
    ("hello world hello", {"hello": 2, "world": 1}),
    ("The the THE", {"the": 3}),
    ("", {}),
    ("one", {"one": 1}),
    ("Hello   WORLD", {"hello": 1, "world": 1}),
    ("abc", {"abc": 1})
]

passed = 0
for i, (input_text, expected) in enumerate(test_cases):
    result = word_count(input_text)
    if result == expected:
        passed += 1
        print(f"Test {i+1}: PASS")
    else:
        print(f"Test {i+1}: FAIL")
        print(f"  Input: {input_text!r}")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")


# ========================================
# Test Results
# ========================================
# Result: PASS
# Output:
#   Test 1: PASS
#   Test 2: PASS
#   Test 3: PASS
#   Test 4: PASS
#   Test 5: PASS
#   Test 6: PASS
