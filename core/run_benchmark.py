#!/usr/bin/env python3
"""
Run the 10 benchmark problems through a model and record results.
Usage: python3 run_benchmark.py [model_name]
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "forge-gen000"
FORGE_DIR = os.path.dirname(os.path.abspath(__file__))


def generate(prompt, system=None):
    payload = {
        "model": MODEL,
        "prompt": "/no_think\n" + prompt,
        "stream": False,
        "options": {"num_ctx": 4096, "num_predict": 1024},
    }
    if system:
        payload["system"] = system
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate", data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        return f"ERROR: {e}", 0
    text = result.get("response", "")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    tokens = result.get("eval_count", 0)
    return text, tokens


def run_code(code):
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=15,
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0 and "PASS" in result.stdout
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def main():
    with open(os.path.join(FORGE_DIR, "benchmark", "problems.json")) as f:
        problems = json.load(f)

    print(f"{'=' * 70}")
    print(f"  BENCHMARK — Model: {MODEL}")
    print(f"  {len(problems)} problems | {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}")
    print()

    system = "You are a Python problem solver. Write clean, correct code. Always include test cases that print PASS if all assertions pass."

    results = []
    total_pass = 0
    total_time = 0

    for p in problems:
        pid = p["id"]
        cat = p["category"]
        title = p["title"]
        problem = p["problem"]

        print(f"  [{pid:>2}/10] {title} ({cat})")
        print(f"         ", end="", flush=True)

        prompt = f"Solve this Python problem. Write a complete solution with the function and test cases that print PASS.\n\n{problem}"

        t0 = time.time()
        response, tokens = generate(prompt, system=system)
        gen_time = time.time() - t0

        if response.startswith("ERROR:"):
            print(f"ERROR ({gen_time:.0f}s)")
            results.append({"id": pid, "category": cat, "title": title, "passed": False, "error": response})
            continue

        # Extract code blocks
        code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
        if not code_blocks:
            # Try without markdown
            code_blocks = [response] if "def " in response else []

        passed = False
        output = "no code generated"

        for code in code_blocks:
            passed, output = run_code(code)
            if passed:
                break

        total_time += gen_time
        if passed:
            total_pass += 1
            print(f"PASS  ({gen_time:.0f}s, {tokens} tokens)")
        else:
            print(f"FAIL  ({gen_time:.0f}s, {tokens} tokens)")
            # Show first line of error
            err_line = output.split("\n")[-1][:60] if output else "no output"
            print(f"          {err_line}")

        results.append({
            "id": pid,
            "category": cat,
            "title": title,
            "passed": passed,
            "output": output[:200],
            "time": round(gen_time, 1),
            "tokens": tokens,
        })

    # Summary
    print()
    print(f"{'=' * 70}")
    print(f"  RESULTS: {total_pass}/10 passed")
    print(f"  Time: {total_time:.0f}s total ({total_time/10:.0f}s avg)")
    print(f"{'=' * 70}")
    print()

    # Category breakdown
    print("  Category breakdown:")
    for r in results:
        icon = "✓" if r["passed"] else "✗"
        color = "\033[32m" if r["passed"] else "\033[31m"
        print(f"    {color}{icon}\033[0m  {r['category']:<20s} {r['title']}")

    # Save results
    benchmark_result = {
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "score": total_pass,
        "total": 10,
        "time_seconds": round(total_time),
        "details": results,
    }

    results_file = os.path.join(FORGE_DIR, "benchmark", "results.json")
    all_results = {}
    if os.path.exists(results_file):
        with open(results_file) as f:
            all_results = json.load(f)

    all_results[MODEL] = benchmark_result

    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n  Results saved to benchmark/results.json")


if __name__ == "__main__":
    main()
