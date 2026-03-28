#!/usr/bin/env python3
"""
Run benchmark using mlx_lm with LoRA adapter.
Usage: python3 run_benchmark_mlx.py [adapter_path]
"""

import json
import os
import re
import subprocess
import sys
import time

FORGE_DIR = os.path.dirname(os.path.abspath(__file__))
ADAPTER_PATH = sys.argv[1] if len(sys.argv) > 1 else None
MODEL_NAME = "Qwen/Qwen3.5-4B"
LABEL = f"forge-gen001 (adapter)" if ADAPTER_PATH else "forge-gen000 (base)"


def generate(prompt, system=None):
    from mlx_lm import load, generate as mlx_generate

    # Cache model loading
    if not hasattr(generate, '_model'):
        print(f"Loading model: {MODEL_NAME}")
        if ADAPTER_PATH:
            print(f"With adapter: {ADAPTER_PATH}")
            generate._model, generate._tokenizer = load(
                MODEL_NAME, adapter_path=ADAPTER_PATH
            )
        else:
            generate._model, generate._tokenizer = load(MODEL_NAME)
        print("Model loaded")

    full_prompt = f"<|im_start|>system\n{system or 'You are a Python problem solver.'}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

    response = mlx_generate(
        generate._model,
        generate._tokenizer,
        prompt=full_prompt,
        max_tokens=1024,
        verbose=False,
    )
    # Strip think blocks
    clean = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    return clean


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
    # Kill Ollama to free GPU memory
    subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
    time.sleep(3)

    with open(os.path.join(FORGE_DIR, "benchmark", "problems.json")) as f:
        problems = json.load(f)

    print(f"{'=' * 70}")
    print(f"  BENCHMARK — {LABEL}")
    print(f"  {len(problems)} problems | {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}")
    print()

    system = "You are a Python problem solver. Write a complete solution with the function definition and test cases that print PASS. Output ONLY a python code block."

    results = []
    total_pass = 0

    for p in problems:
        pid = p["id"]
        cat = p["category"]
        title = p["title"]
        problem = p["problem"]

        print(f"  [{pid:>2}/10] {title} ({cat})", end="", flush=True)

        prompt = f"Solve this. Write ONE python code block with the function and tests that print PASS.\n\n{problem}"

        t0 = time.time()
        response = generate(prompt, system=system)
        gen_time = time.time() - t0

        # Extract code
        code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
        if not code_blocks:
            # Try raw response
            if "def " in response:
                code_blocks = [response]

        passed = False
        output = "no code"

        for code in code_blocks:
            passed, output = run_code(code)
            if passed:
                break

        total_pass += int(passed)
        status = "PASS" if passed else "FAIL"
        print(f"  {status}  ({gen_time:.0f}s)")
        if not passed:
            err = output.split("\n")[-1][:60] if output else "no output"
            print(f"          {err}")

        results.append({
            "id": pid, "category": cat, "title": title,
            "passed": passed, "time": round(gen_time, 1),
        })

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {total_pass}/10")
    print(f"{'=' * 70}\n")

    for r in results:
        icon = "+" if r["passed"] else "x"
        print(f"    [{icon}] {r['category']:<20s} {r['title']}")

    # Save
    results_file = os.path.join(FORGE_DIR, "benchmark", "results.json")
    all_results = {}
    if os.path.exists(results_file):
        with open(results_file) as f:
            all_results = json.load(f)
    all_results[LABEL] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "score": total_pass,
        "details": results,
    }
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n  Saved to benchmark/results.json")


if __name__ == "__main__":
    main()
