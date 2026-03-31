#!/usr/bin/env python3
"""
Forge Monitor — live dashboard for the Forge system.
No dependencies. Pure ANSI terminal rendering.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import textwrap

FORGE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.join(FORGE_DIR, "student")

# --- ANSI helpers ---
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"

CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def read_file(path):
    try:
        with open(os.path.join(WORKSPACE, path)) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def parse_traces():
    content = read_file("traces.jsonl")
    if not content.strip():
        return []
    traces = []
    for line in content.strip().split("\n"):
        try:
            traces.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return traces


def parse_notes():
    content = read_file("claude_notes.md")
    if not content.strip():
        return []
    return content.strip().split("\n")


def get_generation():
    gen_dir = os.path.join(FORGE_DIR, "generations")
    if os.path.isdir(gen_dir):
        return len([d for d in os.listdir(gen_dir)
                     if d.startswith("gen") and os.path.isdir(os.path.join(gen_dir, d))])
    return 0


        if status.startswith("Up"):
            return status, GREEN
        return status, YELLOW
    except Exception:
        return "unknown", RED




def model_name():
    try:
        result = subprocess.run(
            ["docker", "inspect", "forge", "--format",
             "{{range .Config.Env}}{{println .}}{{end}}"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.split("\n"):
            if line.startswith("FORGE_MODEL="):
                return line.split("=", 1)[1]
    except Exception:
        pass
    return "unknown"


def extract_problem_title(goal_text):
    for line in goal_text.split("\n"):
        if line.startswith("## Problem"):
            idx = goal_text.index(line) + len(line)
            rest = goal_text[idx:].strip()
            first_line = rest.split("\n")[0].strip()
            return first_line[:70] if first_line else ""
    return ""


def extract_concept(goal_text):
    for line in goal_text.split("\n"):
        if line.startswith("## Why"):
            idx = goal_text.index(line) + len(line)
            rest = goal_text[idx:].strip()
            first_line = rest.split("\n")[0].strip()
            return first_line[:70] if first_line else ""
    return ""


def extract_code_snippet(code_str, max_lines=6):
    """Extract the function definition from code."""
    if not code_str:
        return []
    lines = code_str.strip().split("\n")
    # Find the function def and show a few lines
    result = []
    in_func = False
    for l in lines:
        if l.strip().startswith("def ") or l.strip().startswith("class "):
            in_func = True
        if in_func:
            result.append(l)
        if len(result) >= max_lines:
            result.append("    ...")
            break
    # If no function found, show first lines
    if not result:
        result = lines[:max_lines]
        if len(lines) > max_lines:
            result.append("...")
    return result


def extract_learning(learnings_text, attempt_num):
    """Extract a specific attempt's learning entry."""
    marker = f"### Attempt {attempt_num}"
    if marker not in learnings_text:
        return ""
    idx = learnings_text.index(marker) + len(marker)
    rest = learnings_text[idx:]
    # Read until next ### or end
    end = rest.find("\n### ")
    if end != -1:
        rest = rest[:end]
    # Get the "What I learned" line
    for line in rest.split("\n"):
        if "What I learned" in line:
            return line.split(":", 1)[-1].strip() if ":" in line else line.strip()
    return rest.strip()[:100]


def render():
    cols, rows = shutil.get_terminal_size((120, 40))
    w = min(cols, 120)
    indent = "  "

    # --- Gather data ---
    status = read_file("status.md").strip() or "n/a"
    traces = parse_traces()
    notes = parse_notes()
    gen = get_generation()
    goal = read_file("goal.md")
    soul = read_file("soul.md")
    learnings = read_file("learnings.md")
    patterns = read_file("patterns.md")
    meta = read_file("metacognition.md")
    model = model_name()

    attempt_count = len(traces)
    max_attempts = 50

    # --- Render ---
    out = []

    def line(text=""):
        out.append(text)

    def header(text):
        pad = w - len(text) - 4
        out.append(f"{BOLD}{CYAN}┌─ {text} {'─' * max(0, pad)}┐{RESET}")

    def footer():
        out.append(f"{DIM}{CYAN}└{'─' * (w - 2)}┘{RESET}")

    def section(text):
        out.append(f"{DIM}{CYAN}├{'─' * (w - 2)}┤{RESET}")
        out.append(f"{indent}{BOLD}{WHITE}{text}{RESET}")

    def wrap(text, prefix="", max_w=None):
        """Wrap text to fit terminal width."""
        effective_w = (max_w or w) - len(prefix) - 4
        wrapped = textwrap.wrap(text, width=effective_w)
        for i, wl in enumerate(wrapped):
            out.append(f"{indent}{prefix if i == 0 else ' ' * len(prefix)}{wl}")

    # ========== Title ==========
    header("Forge Monitor")
    line()

    # ========== Status bar ==========
    status_icon = "●"
    if status == "working":
        s_color = GREEN
    elif status == "submitted":
        s_color = YELLOW
    else:
        s_color = DIM

    progress = attempt_count / max_attempts if max_attempts else 0
    prog_width = 20
    prog_filled = round(progress * prog_width)
    prog_bar = f"{GREEN}{'█' * prog_filled}{DIM}{'░' * (prog_width - prog_filled)}{RESET}"

    line(f"{indent}{BOLD}Gen {gen}{RESET}  {prog_bar}  {attempt_count}/{max_attempts} attempts  {BOLD}Model:{RESET} {CYAN}{model}{RESET}")
    line(f"{indent}Status: {s_color}{status_icon} {status}{RESET}    

    # ========== Current Problem ==========
    section("Current Problem")
    if goal:
        title = extract_problem_title(goal)
        concept = extract_concept(goal)
        line(f"{indent}{BOLD}{title}{RESET}")
        if concept:
            line(f"{indent}{DIM}Why: {concept}{RESET}")
    else:
        line(f"{indent}{DIM}No goal.md yet{RESET}")

    # ========== Student Trace — verbose ==========
    section("Student Trace")
    if traces:
        # Show last 5 attempts with detail
        visible = traces[-5:]
        for t in visible:
            num = t.get("attempt", 0)
            passed = t.get("passed", False)
            ts = t.get("timestamp", "")
            p_icon = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"

            # Problem title (first meaningful line)
            prob = t.get("problem", "")
            prob_title = ""
            for pline in prob.split("\n"):
                pline = pline.strip()
                if pline and not pline.startswith("#"):
                    prob_title = pline[:60]
                    break

            line(f"{indent}{BOLD}#{num}{RESET}  {p_icon}  {DIM}{ts}{RESET}")
            line(f"{indent}   {DIM}Problem:{RESET} {prob_title}")

            # Code snippet
            code = t.get("code", "")
            if code:
                snippet = extract_code_snippet(code, max_lines=4)
                for cl in snippet:
                    line(f"{indent}   {BLUE}{cl[:w-8]}{RESET}")

            # Output (first line)
            output = t.get("output", "")
            if output:
                out_line = output.split("\n")[0][:60]
                o_color_str = GREEN if passed else RED
                line(f"{indent}   {DIM}Output:{RESET} {o_color_str}{out_line}{RESET}")

            # Learning
            learning = extract_learning(learnings, num)
            if learning:
                line(f"{indent}   {YELLOW}Learned:{RESET} {learning[:w-16]}")

            line("")  # spacer between attempts

        if len(traces) > 5:
            hidden = len(traces) - 5
            line(f"{indent}{DIM}... {hidden} earlier attempts{RESET}")
    else:
        line(f"{indent}{DIM}No attempts yet{RESET}")

    # ========== Teacher Log ==========
    section("Teacher")
    grade_entries = [n for n in notes if "GRADE" in n or "GOAL" in n]
    if grade_entries:
        for entry in grade_entries[-6:]:
            entry = entry.strip()
            # Colorize difficulty arrows
            display = entry
            if "-> harder" in display:
                display = display.replace("-> harder", f"{GREEN}-> harder{RESET}{DIM}")
            elif "-> easier" in display:
                display = display.replace("-> easier", f"{RED}-> easier{RESET}{DIM}")
            elif "-> same" in display:
                display = display.replace("-> same", f"{YELLOW}-> same{RESET}{DIM}")
            # Colorize GRADE keyword
            if "GRADE" in display:
                display = display.replace("GRADE", f"{RESET}{BOLD}GRADE{RESET}{DIM}")
            if "GOAL" in display:
                display = display.replace("GOAL", f"{RESET}{CYAN}GOAL{RESET}{DIM}")
            line(f"{indent}{DIM}{display[:w-4]}{RESET}")
    else:
        recent = notes[-4:] if notes else []
        for n in recent:
            line(f"{indent}{DIM}{n[:w-4]}{RESET}")
        if not recent:
            line(f"{indent}{DIM}No activity yet{RESET}")

    # ========== Knowledge ==========
    section("Knowledge")
    l_count = learnings.count("### Attempt") if learnings else 0
    p_count = patterns.count("\n-") + (1 if patterns.strip().startswith("-") else 0) if patterns else 0
    m_status = "updated" if meta.strip() else "none"
    s_version = "seed"
    if soul and "I am Forge" not in soul[:50]:
        s_version = f"{MAGENTA}rewritten{RESET}"
    else:
        s_version = f"{DIM}seed{RESET}"

    line(f"{indent}Learnings: {BOLD}{l_count}{RESET}    "
         f"Patterns: {BOLD}{p_count}{RESET}    "
         f"Metacognition: {BOLD}{m_status}{RESET}    "
         f"Soul: {s_version}")

    # Pass rate + streak
    if traces:
        passes = sum(1 for t in traces if t.get("passed"))
        total = len(traces)
        rate = passes / total * 100
        rate_color = GREEN if rate >= 70 else YELLOW if rate >= 40 else RED

        streak_pass = 0
        streak_fail = 0
        for t in reversed(traces):
            if t.get("passed"):
                if streak_fail == 0:
                    streak_pass += 1
                else:
                    break
            else:
                if streak_pass == 0:
                    streak_fail += 1
                else:
                    break

        streak_str = ""
        if streak_pass > 0:
            sc = GREEN if streak_pass >= 3 else RESET
            streak_str = f"Streak: {sc}{streak_pass} passes{RESET}"
        elif streak_fail > 0:
            sc = RED if streak_fail >= 3 else YELLOW
            streak_str = f"Streak: {sc}{streak_fail} fails{RESET}"

        line(f"{indent}Pass rate: {rate_color}{rate:.0f}%{RESET} ({passes}/{total})    {streak_str}")

    # ========== Last learning ==========
    if learnings.strip():
        section("Latest Learning")
        # Get last entry
        entries = learnings.strip().split("### Attempt")
        if entries:
            last = entries[-1].strip()
            for ll in last.split("\n")[:4]:
                ll = ll.strip()
                if ll.startswith("- "):
                    key, _, val = ll[2:].partition(":")
                    if val:
                        line(f"{indent}{BOLD}{key}:{RESET}{val[:w-len(key)-8]}")
                    else:
                        line(f"{indent}{ll[:w-4]}")

    footer()
    line()
    line(f"{indent}{DIM}Refreshing every 2s  |  Ctrl+C to exit  |  ./c attach for tmux{RESET}")

    return "\n".join(out)


def main():
    print(HIDE_CURSOR, end="", flush=True)
    try:
        while True:
            screen = render()
            sys.stdout.write(CLEAR + screen + "\n")
            sys.stdout.flush()
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW_CURSOR, end="", flush=True)


if __name__ == "__main__":
    main()
