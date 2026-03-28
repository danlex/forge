"""
Forge — seed.py
Three primitives: think(), run(), file()
One loop: read → think → act → submit → wait → repeat
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
MODEL = os.environ.get("FORGE_MODEL", "qwen3.5:4b")
WORKSPACE = "/workspace"


def think(prompt, system=None):
    """Call Ollama. Strip <think> blocks. Return clean text."""
    payload = {
        "model": MODEL,
        "prompt": "/no_think\n" + prompt,
        "stream": False,
        "options": {"num_ctx": 4096},
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError) as e:
        return f"ERROR: Ollama unreachable — {e}"

    text = result.get("response", "")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text


def run(code):
    """Execute Python code in subprocess. Returns (passed, output).
    passed = exit code 0 AND 'PASS' in stdout."""
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{WORKSPACE}/tools"
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0 and "PASS" in result.stdout
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: execution exceeded 30 seconds"


def file(op, path, content=None):
    """File operations: read / write / append / list / exists.
    Enforces workspace boundary. Blocks writes to core.md."""
    if not path.startswith("/"):
        path = os.path.join(WORKSPACE, path)
    path = os.path.normpath(path)

    if not path.startswith(WORKSPACE):
        return f"ERROR: cannot access files outside {WORKSPACE}"

    if op != "read" and os.path.basename(path) == "core.md":
        return "ERROR: core.md is read-only — hard constraint"

    if op == "read":
        try:
            with open(path) as f:
                return f.read()
        except FileNotFoundError:
            return f"ERROR: {path} not found"

    if op == "write":
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content or "")
        return f"OK: wrote {path}"

    if op == "append":
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(content or "")
        return f"OK: appended to {path}"

    if op == "list":
        try:
            entries = []
            for root, _, files in os.walk(path):
                for fname in files:
                    entries.append(os.path.relpath(os.path.join(root, fname), WORKSPACE))
            return "\n".join(sorted(entries))
        except FileNotFoundError:
            return f"ERROR: {path} not found"

    if op == "exists":
        return str(os.path.exists(path))

    return f"ERROR: unknown operation '{op}'"


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    attempt_count = 0
    last_meta_at = 0      # last attempt count when metacognition ran
    last_soul_at = 0      # last attempt count when soul rewrite ran

    log(f"Forge starting — model={MODEL} ollama={OLLAMA_URL}")

    # Wait for Ollama to be reachable
    while True:
        try:
            urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5)
            break
        except Exception:
            log("Waiting for Ollama...")
            time.sleep(3)

    log("Ollama connected")

    while True:
        try:
            # --- Rebuild system prompt every cycle (catches soul.md rewrites) ---
            # core.md lives at /forge/core.md (baked into image, immutable)
            with open("/forge/core.md") as f:
                core = f.read()
            soul = file("read", "soul.md")
            if soul.startswith("ERROR:"):
                log("Waiting for soul.md...")
                time.sleep(2)
                continue

            system_prompt = f"# Core Laws (immutable)\n{core}\n\n# Your Identity\n{soul}"

            # --- Read goal ---
            goal = file("read", "goal.md")
            if goal.startswith("ERROR:"):
                log("Waiting for goal.md...")
                time.sleep(2)
                continue

            # --- Context ---
            file_list = file("list", WORKSPACE)
            commands = ""
            cmd_path = f"{WORKSPACE}/commands.txt"
            if os.path.exists(cmd_path):
                commands = file("read", "commands.txt")
                if commands.strip():
                    file("write", "commands.txt", "")

            learnings = ""
            if os.path.exists(f"{WORKSPACE}/learnings.md"):
                learnings = file("read", "learnings.md")

            patterns = ""
            if os.path.exists(f"{WORKSPACE}/patterns.md"):
                patterns = file("read", "patterns.md")

            # --- Knowledge base ---
            knowledge = ""
            kb_path = f"{WORKSPACE}/knowledge/algorithms.md"
            if os.path.exists(kb_path):
                knowledge = file("read", "knowledge/algorithms.md")

            # --- Build prompt ---
            user_msg = f"## Current Goal\n{goal}"
            if knowledge.strip():
                user_msg += f"\n\n## Algorithm Reference\n{knowledge}"
            if commands.strip():
                user_msg += f"\n\n## Message from Teacher\n{commands}"
            if learnings.strip():
                user_msg += f"\n\n## Your Learnings (read before coding)\n{learnings}"
            if patterns.strip():
                user_msg += f"\n\n## Your Patterns (apply these)\n{patterns}"

            user_msg += """

## Instructions
1. Read the problem carefully — what are the inputs, outputs, edge cases?
2. State your approach in plain words BEFORE writing code
3. Write ONE ```python code block with your function + test assertions + print("PASS")
4. Keep it concise — function definition, tests, done
5. Do NOT write explanations after the code block"""

            # --- Problem info ---
            goal_title = ""
            for gl in goal.split("\n"):
                gl = gl.strip()
                if gl and not gl.startswith("#"):
                    goal_title = gl[:80]
                    break
            log(f"{'=' * 60}")
            log(f"ATTEMPT CYCLE  (submissions so far: {attempt_count})")
            log(f"Problem: {goal_title}")
            log(f"Prompt size: {len(user_msg)} chars")
            log(f"{'=' * 60}")

            # --- Think ---
            log("Thinking...")
            t0 = time.time()
            response = think(user_msg, system=system_prompt)
            elapsed = time.time() - t0
            if response.startswith("ERROR:"):
                log(f"ERROR after {elapsed:.0f}s: {response}")
                time.sleep(5)
                continue

            log(f"Response received ({len(response)} chars, {elapsed:.1f}s)")

            # Show reasoning preview (first non-empty lines that aren't code)
            reasoning_lines = []
            for rl in response.split("\n"):
                rl = rl.strip()
                if rl.startswith("```"):
                    break
                if rl:
                    reasoning_lines.append(rl)
            if reasoning_lines:
                log(f"--- Reasoning ---")
                for rl in reasoning_lines[:8]:
                    log(f"  {rl[:100]}")
                if len(reasoning_lines) > 8:
                    log(f"  ... ({len(reasoning_lines) - 8} more lines)")

            # --- Execute code blocks ---
            code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
            last_passed = False
            last_output = ""

            if code_blocks:
                log(f"--- Code ({len(code_blocks)} block(s)) ---")
                # Show the main solution code
                main_code = code_blocks[-1]
                for cl in main_code.split("\n")[:15]:
                    log(f"  {cl[:100]}")
                if len(main_code.split("\n")) > 15:
                    log(f"  ... ({len(main_code.split(chr(10)))} total lines)")

            for i, code in enumerate(code_blocks):
                log(f"--- Executing block {i+1}/{len(code_blocks)} ---")
                passed, output = run(code)
                last_passed = passed
                last_output = output
                status = "PASS" if passed else "FAIL"
                log(f"  Result: {status}")
                if output:
                    log(f"--- Output ---")
                    for oline in output.split("\n")[:15]:
                        log(f"  {oline}")

            # If code ran and failed, feed result back for another attempt
            if code_blocks and not last_passed and "SUBMIT:" not in response:
                log(f"--- RETRY (failed, feeding error back) ---")
                feedback = f"Your code produced:\n{last_output}\n\nThis did not pass. Analyze the failure, fix your approach, and try again."
                t0 = time.time()
                retry = think(feedback, system=system_prompt)
                elapsed = time.time() - t0
                log(f"Retry response ({len(retry)} chars, {elapsed:.1f}s)")

                # Show retry reasoning
                retry_reasoning = []
                for rl in retry.split("\n"):
                    rl = rl.strip()
                    if rl.startswith("```"):
                        break
                    if rl:
                        retry_reasoning.append(rl)
                if retry_reasoning:
                    log(f"--- Retry reasoning ---")
                    for rl in retry_reasoning[:5]:
                        log(f"  {rl[:100]}")

                retry_blocks = re.findall(r"```python\n(.*?)```", retry, re.DOTALL)
                for i, code in enumerate(retry_blocks):
                    log(f"--- Executing retry block {i+1} ---")
                    passed, output = run(code)
                    last_passed = passed
                    last_output = output
                    status = "PASS" if passed else "FAIL"
                    log(f"  Result: {status}")
                    if output:
                        log(f"--- Retry output ---")
                        for oline in output.split("\n")[:15]:
                            log(f"  {oline}")

                response = response + "\n\n--- RETRY ---\n" + retry

            # --- Handle FILE_WRITE directives ---
            file_writes = re.findall(
                r"FILE_WRITE:\s*(\S+)\n(.*?)(?=FILE_WRITE:|SUBMIT:|```|$)",
                response,
                re.DOTALL,
            )
            for fpath, fcontent in file_writes:
                result = file("write", fpath.strip(), fcontent.strip() + "\n")
                log(f"  {result}")

            # --- Handle SUBMIT ---
            # Auto-submit if code passed (small models don't always say SUBMIT:)
            should_submit = "SUBMIT:" in response or (code_blocks and last_passed)
            if should_submit:
                attempt_count += 1

                trace = {
                    "attempt": attempt_count,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "problem": goal[:1000],
                    "reasoning": response[:3000],
                    "code": code_blocks[-1] if code_blocks else "",
                    "output": last_output[:1000],
                    "passed": last_passed,
                    "soul": soul[:500],
                }

                file("append", "traces.jsonl", json.dumps(trace) + "\n")

                log(f"{'=' * 60}")
                log(f">>> SUBMITTED #{attempt_count} — {'PASS' if last_passed else 'FAIL'}")
                log(f"    Problem: {goal_title}")
                # Show the function signature
                for cline in (code_blocks[-1] if code_blocks else "").split("\n"):
                    cline = cline.strip()
                    if cline.startswith("def ") or cline.startswith("class "):
                        log(f"    Solution: {cline}")
                        break
                log(f"    Output: {last_output.split(chr(10))[0][:80]}")
                log(f"{'=' * 60}")

                # --- Write solution file ---
                sol_dir = f"{WORKSPACE}/solutions"
                os.makedirs(sol_dir, exist_ok=True)
                # Extract function name from code
                func_name = "attempt"
                for cline in (code_blocks[-1] if code_blocks else "").split("\n"):
                    cline = cline.strip()
                    if cline.startswith("def "):
                        func_name = cline.split("(")[0].replace("def ", "").strip()
                        break
                sol_filename = f"{attempt_count:03d}_{func_name}.py"
                sol_content = f'"""\nAttempt #{attempt_count} — {"PASS" if last_passed else "FAIL"}\nTimestamp: {trace["timestamp"]}\n\nProblem:\n{goal.strip()}\n"""\n\n'
                sol_content += f"# {'=' * 40}\n# Solution\n# {'=' * 40}\n\n"
                sol_content += (code_blocks[-1] if code_blocks else "# no code") + "\n\n"
                sol_content += f"# {'=' * 40}\n# Test Results\n# {'=' * 40}\n"
                sol_content += f"# Result: {'PASS' if last_passed else 'FAIL'}\n"
                sol_content += f"# Output:\n"
                for out_line in last_output.split("\n")[:20]:
                    sol_content += f"#   {out_line}\n"
                file("write", f"solutions/{sol_filename}", sol_content)
                log(f"  Wrote solutions/{sol_filename}")

                # --- Enforce learning entry (don't rely on model doing it) ---
                learning_prompt = (
                    f"You just {'PASSED' if last_passed else 'FAILED'} this problem.\n"
                    f"Problem: {goal[:500]}\n"
                    f"Your output: {last_output[:300]}\n\n"
                    "Write ONE learning entry. Format:\n"
                    "- What I tried: (one line)\n"
                    "- What happened: (one line)\n"
                    "- What I learned: (one line)\n"
                    "Be specific, not generic."
                )
                learning = think(learning_prompt, system=system_prompt)
                if not learning.startswith("ERROR:"):
                    entry = f"\n### Attempt {attempt_count} — {'PASS' if last_passed else 'FAIL'}\n{learning}\n"
                    file("append", "learnings.md", entry)
                    log(f"--- Learning ---")
                    for ll in learning.split("\n")[:5]:
                        if ll.strip():
                            log(f"  {ll.strip()[:100]}")
                    log("Wrote learning entry")

                file("write", "status.md", "submitted")
                log(f">>> SUBMITTED #{attempt_count} — {'PASS' if last_passed else 'FAIL'}")

                # Wait for teacher to reset status
                log("Waiting for teacher...")
                wait_start = time.time()
                while True:
                    status = file("read", "status.md").strip()
                    if status != "submitted":
                        break
                    if time.time() - wait_start > 300:
                        log("Teacher timeout — continuing")
                        file("write", "status.md", "working")
                        break
                    time.sleep(1)
                log("Teacher responded — continuing")

                # --- Metacognition (every 10 attempts, once per threshold) ---
                if attempt_count >= last_meta_at + 10:
                    last_meta_at = attempt_count
                    current_learnings = file("read", "learnings.md")
                    if not current_learnings.startswith("ERROR:") and current_learnings.strip():
                        meta_prompt = (
                            "Read your learnings and reflect on patterns across them.\n"
                            "Not individual lessons — patterns in HOW you think and WHERE you fail.\n"
                            "What conditions produce your best work? What traps do you fall into?\n\n"
                            f"Learnings:\n{current_learnings}\n\n"
                            "Write a metacognition update."
                        )
                        meta = think(meta_prompt, system=system_prompt)
                        if not meta.startswith("ERROR:"):
                            file("write", "metacognition.md", meta)
                            log("Updated metacognition.md")

                # --- Soul rewrite (every 30 attempts, once per threshold) ---
                if attempt_count >= last_soul_at + 30:
                    last_soul_at = attempt_count
                    meta_content = file("read", "metacognition.md")
                    if not meta_content.startswith("ERROR:"):
                        soul_prompt = (
                            "Read your metacognition and current identity.\n"
                            "Has something genuinely shifted in how you approach problems?\n"
                            "If yes, rewrite your identity to reflect who you are now.\n"
                            "If nothing has truly changed, say NO_CHANGE.\n\n"
                            f"Current identity:\n{soul}\n\n"
                            f"Metacognition:\n{meta_content}"
                        )
                        new_soul = think(soul_prompt, system=system_prompt)
                        if not new_soul.startswith("ERROR:") and "NO_CHANGE" not in new_soul and len(new_soul) > 50:
                            file("write", "soul.md", new_soul)
                            log("Rewrote soul.md")

            # --- History management ---
            # No history accumulation — fresh context every cycle
            # Learnings.md and patterns.md carry knowledge forward

            time.sleep(0.5)

        except KeyboardInterrupt:
            log("Interrupted — shutting down")
            sys.exit(0)
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
