#!/usr/bin/env python3
"""
Curate traces from a generation into training data.
Usage: python3 curate.py [gen_number]
"""

import json
import os
import sys

GEN = int(sys.argv[1]) if len(sys.argv) > 1 else 0
GEN_DIR = f"generations/gen{GEN:03d}"
FORGE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    traces_file = os.path.join(FORGE_DIR, GEN_DIR, "traces.jsonl")
    with open(traces_file) as f:
        traces = [json.loads(l) for l in f if l.strip()]

    print(f"Generation {GEN}: {len(traces)} total traces")

    # Read core.md for system prompt
    with open(os.path.join(FORGE_DIR, "core.md")) as f:
        core = f.read()

    curated = []
    removed = 0
    reasons = []

    for t in traces:
        problem = t.get("problem", "")
        reasoning = t.get("reasoning", "")
        code = t.get("code", "")
        passed = t.get("passed", False)
        output = t.get("output", "")
        soul = t.get("soul", "")

        # --- Filter bad traces ---

        # Remove wrong-problem traces
        if "generation has been ended" in problem.lower():
            removed += 1
            reasons.append("wrong problem (generation-end message)")
            continue

        # Remove traces with no code
        if not code.strip():
            removed += 1
            reasons.append("no code generated")
            continue

        # Remove traces with syntax errors in the code itself
        if "SyntaxError" in output and passed:
            removed += 1
            reasons.append("claimed PASS but had SyntaxError")
            continue

        # Remove very short reasoning (model didn't think)
        if len(reasoning) < 50:
            removed += 1
            reasons.append("no reasoning")
            continue

        # --- Build training example ---
        system_prompt = f"# Core Laws\n{core}\n\n# Identity\n{soul}" if soul else core

        # Clean the reasoning — remove <think> blocks, keep useful content
        clean_reasoning = reasoning.strip()

        if passed:
            # Clean pass: problem → solution
            user_content = problem.strip()
            assistant_content = clean_reasoning
        else:
            # Failure: still valuable for learning what NOT to do
            # But only if there's a subsequent pass on similar problem
            user_content = problem.strip()
            assistant_content = clean_reasoning

        example = {
            "messages": [
                {"role": "system", "content": system_prompt[:2000]},
                {"role": "user", "content": user_content[:2000]},
                {"role": "assistant", "content": assistant_content[:3000]},
            ]
        }

        curated.append(example)

    # Write curated data
    output_file = os.path.join(FORGE_DIR, GEN_DIR, "curated.jsonl")
    with open(output_file, "w") as f:
        for example in curated:
            f.write(json.dumps(example) + "\n")

    print(f"\nCuration results:")
    print(f"  Kept:    {len(curated)}")
    print(f"  Removed: {removed}")
    if reasons:
        from collections import Counter
        for reason, count in Counter(reasons).most_common():
            print(f"    - {reason}: {count}")
    print(f"\nWritten to: {output_file}")


if __name__ == "__main__":
    main()
