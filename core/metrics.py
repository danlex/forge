#!/usr/bin/env python3
"""
Forge Metrics — computes everything from traces.jsonl and claude_notes.md.
Run: python3 core/metrics.py
"""

import json
import os
import re
import sys
import time

FORGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STUDENT_DIR = os.path.join(FORGE_DIR, "student")


def load_traces():
    path = os.path.join(STUDENT_DIR, "traces.jsonl")
    if not os.path.exists(path):
        return []
    traces = []
    for line in open(path):
        if line.strip():
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return traces


def load_notes():
    path = os.path.join(STUDENT_DIR, "claude_notes.md")
    if not os.path.exists(path):
        return []
    return open(path).read().strip().split("\n")


def extract_function_name(problem_text):
    for line in problem_text.split("\n"):
        line = line.strip()
        if "`" in line and "function" in line.lower():
            parts = line.split("`")
            if len(parts) >= 2:
                name = parts[1].split("(")[0]
                return name
    return "unknown"


def compute_metrics(traces):
    if not traces:
        return {"total": 0}

    total = len(traces)
    passes = sum(1 for t in traces if t.get("passed"))
    fails = total - passes

    # Pass rate
    pass_rate = passes / total if total else 0

    # Rolling pass rate (last 10)
    last_10 = traces[-10:]
    rolling_pass = sum(1 for t in last_10 if t.get("passed")) / len(last_10)

    # Concepts covered
    concepts = {}
    for t in traces:
        name = extract_function_name(t.get("problem", ""))
        if name not in concepts:
            concepts[name] = {"attempts": 0, "passes": 0, "first_seen": t.get("attempt", 0)}
        concepts[name]["attempts"] += 1
        if t.get("passed"):
            concepts[name]["passes"] += 1

    # Unique concepts
    unique_concepts = len(concepts)

    # First-try pass rate
    first_tries = {}
    for t in traces:
        name = extract_function_name(t.get("problem", ""))
        if name not in first_tries:
            first_tries[name] = t.get("passed", False)
    first_try_passes = sum(1 for v in first_tries.values() if v)
    first_try_rate = first_try_passes / len(first_tries) if first_tries else 0

    # Streaks
    current_streak_pass = 0
    current_streak_fail = 0
    max_streak_pass = 0
    max_streak_fail = 0
    for t in traces:
        if t.get("passed"):
            current_streak_pass += 1
            current_streak_fail = 0
            max_streak_pass = max(max_streak_pass, current_streak_pass)
        else:
            current_streak_fail += 1
            current_streak_pass = 0
            max_streak_fail = max(max_streak_fail, current_streak_fail)

    # Timing
    timestamps = []
    for t in traces:
        ts = t.get("timestamp", "")
        try:
            timestamps.append(time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S")))
        except (ValueError, TypeError):
            continue

    avg_time = 0
    if len(timestamps) >= 2:
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_time = sum(intervals) / len(intervals)

    # Code length stats
    pass_code_lens = [len(t.get("code", "")) for t in traces if t.get("passed") and t.get("code")]
    fail_code_lens = [len(t.get("code", "")) for t in traces if not t.get("passed") and t.get("code")]
    avg_pass_code = sum(pass_code_lens) / len(pass_code_lens) if pass_code_lens else 0
    avg_fail_code = sum(fail_code_lens) / len(fail_code_lens) if fail_code_lens else 0

    # Progress windows
    windows = []
    window_size = 5
    for i in range(0, total, window_size):
        chunk = traces[i:i+window_size]
        p = sum(1 for t in chunk if t.get("passed"))
        windows.append({"start": i+1, "end": i+len(chunk), "passes": p, "total": len(chunk)})

    # Hardest concepts (most failures)
    hardest = sorted(concepts.items(), key=lambda x: x[1]["attempts"] - x[1]["passes"], reverse=True)

    # Curriculum diversity (unique concepts in last 10 attempts)
    last_10_concepts = set()
    for t in traces[-10:]:
        last_10_concepts.add(extract_function_name(t.get("problem", "")))
    curriculum_diversity = len(last_10_concepts)

    return {
        "total": total,
        "passes": passes,
        "fails": fails,
        "pass_rate": round(pass_rate * 100, 1),
        "rolling_pass_rate": round(rolling_pass * 100, 1),
        "unique_concepts": unique_concepts,
        "first_try_rate": round(first_try_rate * 100, 1),
        "current_streak_pass": current_streak_pass,
        "current_streak_fail": current_streak_fail,
        "max_streak_pass": max_streak_pass,
        "max_streak_fail": max_streak_fail,
        "avg_time_between_attempts": round(avg_time),
        "avg_pass_code_length": round(avg_pass_code),
        "avg_fail_code_length": round(avg_fail_code),
        "curriculum_diversity_last_10": curriculum_diversity,
        "windows": windows,
        "concepts": concepts,
        "hardest": [(k, v) for k, v in hardest[:5]],
    }


def parse_grades(notes):
    """Extract teacher grades from claude_notes.md."""
    grades = []
    for line in notes:
        m = re.search(r"reasoning[=:]?\s*(\d+).*correctness[=:]?\s*(\d+).*honesty[=:]?\s*(\d+)", line, re.IGNORECASE)
        if m:
            grades.append({
                "reasoning": int(m.group(1)),
                "correctness": int(m.group(2)),
                "honesty": int(m.group(3)),
            })
    return grades


def print_report(metrics, grades):
    m = metrics
    if m["total"] == 0:
        print("No traces yet.")
        return

    print(f"{'=' * 60}")
    print(f"  FORGE METRICS REPORT")
    print(f"{'=' * 60}")
    print()

    # Overview
    print(f"  Attempts:          {m['total']}")
    print(f"  Pass / Fail:       {m['passes']} / {m['fails']}")
    print(f"  Pass rate:         {m['pass_rate']}%")
    print(f"  Rolling (last 10): {m['rolling_pass_rate']}%")
    print(f"  First-try rate:    {m['first_try_rate']}%")
    print()

    # Streaks
    print(f"  Current streak:    {'pass ' + str(m['current_streak_pass']) if m['current_streak_pass'] else 'fail ' + str(m['current_streak_fail'])}")
    print(f"  Best pass streak:  {m['max_streak_pass']}")
    print(f"  Worst fail streak: {m['max_streak_fail']}")
    print()

    # Timing
    if m["avg_time_between_attempts"]:
        print(f"  Avg time/attempt:  {m['avg_time_between_attempts']}s ({m['avg_time_between_attempts']//60}m {m['avg_time_between_attempts']%60}s)")
    print(f"  Avg code (pass):   {m['avg_pass_code_length']} chars")
    print(f"  Avg code (fail):   {m['avg_fail_code_length']} chars")
    print()

    # Curriculum
    print(f"  Unique concepts:   {m['unique_concepts']}")
    print(f"  Diversity (last10): {m['curriculum_diversity_last_10']} concepts")
    print()

    # Progress windows
    print(f"  Progress:")
    for w in m["windows"]:
        bar = "█" * w["passes"] + "░" * (w["total"] - w["passes"])
        print(f"    #{w['start']:>2}-{w['end']:>2}  {bar}  {w['passes']}/{w['total']}")
    print()

    # Hardest concepts
    print(f"  Hardest concepts:")
    for name, info in m["hardest"]:
        fails = info["attempts"] - info["passes"]
        print(f"    {name:<25s}  {info['passes']}/{info['attempts']} pass  ({fails} fails)")
    print()

    # Teacher grades
    if grades:
        avg_r = sum(g["reasoning"] for g in grades) / len(grades)
        avg_c = sum(g["correctness"] for g in grades) / len(grades)
        avg_h = sum(g["honesty"] for g in grades) / len(grades)
        print(f"  Teacher grades ({len(grades)} graded):")
        print(f"    Avg reasoning:   {avg_r:.1f}/10")
        print(f"    Avg correctness: {avg_c:.1f}/10")
        print(f"    Avg honesty:     {avg_h:.1f}/10")
    print()
    print(f"{'=' * 60}")


def save_metrics(metrics, grades):
    """Save metrics as JSON for other tools to read."""
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "metrics": metrics,
        "grades": grades,
    }
    path = os.path.join(STUDENT_DIR, "metrics.json")
    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)


if __name__ == "__main__":
    traces = load_traces()
    notes = load_notes()
    metrics = compute_metrics(traces)
    grades = parse_grades(notes)
    print_report(metrics, grades)
    save_metrics(metrics, grades)
    print(f"  Saved to student/metrics.json")
