"""
Forge — seed.py
Student agent. Uses MLX for inference (no Ollama, no Docker).
Fresh context every cycle. Asks teacher when stuck.
"""

import json
import os
import re
import subprocess
import sys
import time

MODEL_NAME = os.environ.get("FORGE_MODEL", "Qwen/Qwen3-1.7B")
ADAPTER_PATH = os.environ.get("FORGE_ADAPTER", None)
WORKSPACE = os.environ.get("FORGE_WORKSPACE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "student"))
CORE_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "laws.md")

# MLX model (loaded once)
_model = None
_tokenizer = None


def load_model():
    global _model, _tokenizer
    if _model is not None:
        return
    from mlx_lm import load
    log(f"Loading model: {MODEL_NAME}")
    if ADAPTER_PATH and os.path.exists(ADAPTER_PATH):
        log(f"With adapter: {ADAPTER_PATH}")
        _model, _tokenizer = load(MODEL_NAME, adapter_path=ADAPTER_PATH)
    else:
        _model, _tokenizer = load(MODEL_NAME)
    log("Model loaded")


def think(prompt, system=None, max_tokens=1024):
    """Call MLX model. Strip <think> blocks. Return clean text."""
    load_model()
    from mlx_lm import generate

    full_prompt = ""
    if system:
        full_prompt += f"<|im_start|>system\n{system}<|im_end|>\n"
    full_prompt += f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

    text = generate(_model, _tokenizer, prompt=full_prompt, max_tokens=max_tokens, verbose=False)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    # Handle unclosed <think> tags — keep content, just strip the tag
    if "<think>" in text and "</think>" not in text:
        text = text.replace("<think>", "", 1).strip()
    return text


def run(code):
    """Execute Python code in subprocess. Returns (passed, output)."""
    # Sanitize Unicode characters the model copies from problem descriptions
    code = code.replace("→", "->").replace("←", "<-")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(WORKSPACE, "tools")
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=30, env=env,
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0 and "PASS" in result.stdout
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: execution exceeded 30 seconds"


def file(op, path, content=None):
    """File operations: read / write / append / list / exists."""
    if not path.startswith("/"):
        path = os.path.join(WORKSPACE, path)
    path = os.path.normpath(path)

    if not path.startswith(WORKSPACE) and path != CORE_MD:
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


def ask_teacher(question, goal_title):
    """Ask the teacher a question. Write to questions.txt, set status, wait for answer."""
    log(f"--- ASKING TEACHER ---")
    log(f"  Q: {question[:100]}")
    file("write", "questions.txt", question)
    file("write", "status.md", "question")

    # Wait for answer
    wait_start = time.time()
    while True:
        status = file("read", "status.md").strip()
        if status != "question":
            break
        if time.time() - wait_start > 300:
            log("Teacher didn't answer — continuing without help")
            file("write", "status.md", "working")
            return ""
        time.sleep(2)

    answer = file("read", "answers.txt")
    if answer.strip():
        log(f"--- TEACHER ANSWERED ---")
        log(f"  A: {answer.strip()[:200]}")
    return answer.strip()


def main():
    attempt_count = 0
    last_meta_at = 0
    last_soul_at = 0
    consecutive_fails = 0

    log(f"Forge starting — model={MODEL_NAME}")
    if ADAPTER_PATH:
        log(f"Adapter: {ADAPTER_PATH}")

    while True:
        try:
            # --- Read context (fresh every cycle) ---
            core = file("read", CORE_MD)
            soul = file("read", "soul.md")
            if soul.startswith("ERROR:"):
                log("Waiting for soul.md...")
                time.sleep(2)
                continue

            system_prompt = f"# Core Laws (immutable)\n{core}\n\n# Your Identity\n{soul}"

            goal = file("read", "goal.md")
            if goal.startswith("ERROR:"):
                log("Waiting for goal.md...")
                time.sleep(2)
                continue

            # Knowledge
            learnings = file("read", "learnings.md") if os.path.exists(os.path.join(WORKSPACE, "learnings.md")) else ""
            patterns = file("read", "patterns.md") if os.path.exists(os.path.join(WORKSPACE, "patterns.md")) else ""
            knowledge = ""
            kb_path = os.path.join(WORKSPACE, "knowledge", "algorithms.md")
            if os.path.exists(kb_path):
                knowledge = file("read", "knowledge/algorithms.md")

            # Check if teacher left an answer
            answer = ""
            if os.path.exists(os.path.join(WORKSPACE, "answers.txt")):
                answer = file("read", "answers.txt").strip()
                if answer:
                    file("write", "answers.txt", "")  # clear after reading

            # --- Build prompt ---
            user_msg = f"## Current Goal\n{goal}"
            if knowledge.strip():
                user_msg += f"\n\n## Algorithm Reference\n{knowledge}"
            if learnings.strip():
                user_msg += f"\n\n## Your Learnings (apply these)\n{learnings[-3000:]}"
            if patterns.strip():
                user_msg += f"\n\n## Your Patterns\n{patterns}"
            if answer:
                user_msg += f"\n\n## Teacher's Answer to Your Question\n{answer}"

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
            log(f"ATTEMPT CYCLE  (submissions: {attempt_count}, fails: {consecutive_fails})")
            log(f"Problem: {goal_title}")
            log(f"{'=' * 60}")

            # --- Think ---
            log("Thinking...")
            t0 = time.time()
            response = think(user_msg, system=system_prompt, max_tokens=2048)
            elapsed = time.time() - t0

            if not response or response.startswith("ERROR:"):
                log(f"ERROR after {elapsed:.0f}s: {response}")
                time.sleep(5)
                continue

            log(f"Response ({len(response)} chars, {elapsed:.1f}s)")

            # Show reasoning preview
            reasoning_lines = []
            for rl in response.split("\n"):
                rl = rl.strip()
                if rl.startswith("```"):
                    break
                if rl:
                    reasoning_lines.append(rl)
            if reasoning_lines:
                log(f"--- Reasoning ---")
                for rl in reasoning_lines[:6]:
                    log(f"  {rl[:100]}")

            # --- Execute code ---
            code_blocks = re.findall(r"```python\n(.*?)```", response, re.DOTALL)
            # Fallback: extract raw code starting with 'def ' if no fenced blocks
            if not code_blocks:
                m = re.search(r"(def \w+\(.*?print\([\"']PASS[\"']\))", response, re.DOTALL)
                if m:
                    code_blocks = [m.group(1)]
                    log("--- Extracted raw code (no fences) ---")
            last_passed = False
            last_output = ""

            if code_blocks:
                log(f"--- Code ({len(code_blocks)} block(s)) ---")
                for cl in code_blocks[-1].split("\n")[:12]:
                    log(f"  {cl[:100]}")

            # Auto-prepend TreeNode class if code uses it but doesn't define it
            TREENODE_DEF = (
                "class TreeNode:\n"
                "    def __init__(self, val=0, left=None, right=None):\n"
                "        self.val = val\n"
                "        self.left = left\n"
                "        self.right = right\n\n"
            )
            for i in range(len(code_blocks)):
                if "TreeNode" in code_blocks[i] and "class TreeNode" not in code_blocks[i]:
                    code_blocks[i] = TREENODE_DEF + code_blocks[i]

            for i, code in enumerate(code_blocks):
                log(f"--- Executing block {i+1}/{len(code_blocks)} ---")
                passed, output = run(code)
                last_passed = passed
                last_output = output
                log(f"  Result: {'PASS' if passed else 'FAIL'}")
                if output:
                    for oline in output.split("\n")[:10]:
                        log(f"  {oline}")

            # --- Retry on failure ---
            if code_blocks and not last_passed:
                log(f"--- RETRY ---")
                feedback = f"Your code produced:\n{last_output}\n\nAnalyze the failure, fix it, try again. Write ONE ```python code block."
                t0 = time.time()
                retry = think(feedback, system=system_prompt)
                elapsed = time.time() - t0
                log(f"Retry response ({len(retry)} chars, {elapsed:.1f}s)")

                retry_blocks = re.findall(r"```python\n(.*?)```", retry, re.DOTALL)
                for j in range(len(retry_blocks)):
                    if "TreeNode" in retry_blocks[j] and "class TreeNode" not in retry_blocks[j]:
                        retry_blocks[j] = TREENODE_DEF + retry_blocks[j]
                for i, code in enumerate(retry_blocks):
                    passed, output = run(code)
                    last_passed = passed
                    last_output = output
                    log(f"  Retry {i+1}: {'PASS' if passed else 'FAIL'}")
                    if output:
                        for oline in output.split("\n")[:10]:
                            log(f"  {oline}")

                response = response + "\n\n--- RETRY ---\n" + retry

            # --- Handle FILE_WRITE ---
            file_writes = re.findall(
                r"FILE_WRITE:\s*(\S+)\n(.*?)(?=FILE_WRITE:|SUBMIT:|```|$)",
                response, re.DOTALL,
            )
            for fpath, fcontent in file_writes:
                result = file("write", fpath.strip(), fcontent.strip() + "\n")
                log(f"  {result}")

            # --- Submit or ask for help ---
            should_submit = code_blocks and last_passed

            if should_submit:
                attempt_count += 1
                consecutive_fails = 0

                trace = {
                    "attempt": attempt_count,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "problem": goal[:1000],
                    "reasoning": response[:3000],
                    "code": code_blocks[-1] if code_blocks else "",
                    "output": last_output[:1000],
                    "passed": True,
                    "soul": soul[:500],
                }

                file("append", "traces.jsonl", json.dumps(trace) + "\n")

                log(f"{'=' * 60}")
                log(f">>> SUBMITTED #{attempt_count} — PASS")
                log(f"    Problem: {goal_title}")
                for cline in (code_blocks[-1] if code_blocks else "").split("\n"):
                    cline = cline.strip()
                    if cline.startswith("def ") or cline.startswith("class "):
                        log(f"    Solution: {cline}")
                        break
                log(f"{'=' * 60}")

                # Solutions are NOT stored in workspace (prevents cheating)

                # Learning entry
                learning_prompt = (
                    f"You PASSED this problem.\nProblem: {goal[:300]}\n"
                    f"Your output: {last_output[:200]}\n\n"
                    "Write ONE learning entry:\n"
                    "- What I tried: (one line)\n"
                    "- What happened: (one line)\n"
                    "- What I learned: (one specific thing)\n"
                )
                learning = think(learning_prompt, system=system_prompt, max_tokens=256)
                if learning and not learning.startswith("ERROR:"):
                    entry = f"\n### Attempt {attempt_count} — PASS\n{learning}\n"
                    file("append", "learnings.md", entry)
                    log(f"--- Learning ---")
                    for ll in learning.split("\n")[:3]:
                        if ll.strip():
                            log(f"  {ll.strip()[:100]}")

                # Signal teacher
                file("write", "status.md", "submitted")
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

            else:
                # Failed — track consecutive failures
                consecutive_fails += 1
                attempt_count += 1

                # Write FAIL trace
                trace = {
                    "attempt": attempt_count,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "problem": goal[:1000],
                    "reasoning": response[:3000],
                    "code": code_blocks[-1] if code_blocks else "",
                    "output": last_output[:1000],
                    "passed": False,
                    "soul": soul[:500],
                }
                file("append", "traces.jsonl", json.dumps(trace) + "\n")

                log(f"{'=' * 60}")
                log(f">>> SUBMITTED #{attempt_count} — FAIL (consecutive: {consecutive_fails})")
                log(f"    Problem: {goal_title}")
                log(f"    Error: {last_output.split(chr(10))[-1][:80] if last_output else 'no output'}")
                log(f"{'=' * 60}")

                # Write learning from failure (failures are data too)
                fail_learning_prompt = (
                    f"You FAILED this problem.\nProblem: {goal[:300]}\n"
                    f"Your error: {last_output[:200]}\n\n"
                    "Write ONE learning entry:\n"
                    "- What I tried: (one line)\n"
                    "- What went wrong: (one line)\n"
                    "- What I should try differently: (one specific thing)\n"
                )
                fail_learning = think(fail_learning_prompt, system=system_prompt, max_tokens=256)
                if fail_learning and not fail_learning.startswith("ERROR:"):
                    entry = f"\n### Attempt {attempt_count} — FAIL\n{fail_learning}\n"
                    file("append", "learnings.md", entry)
                    log(f"--- Learning (from failure) ---")
                    for ll in fail_learning.split("\n")[:3]:
                        if ll.strip():
                            log(f"  {ll.strip()[:100]}")

                # After 2 consecutive fails: ask teacher for help
                if consecutive_fails >= 2:
                    question = (
                        f"I've failed {consecutive_fails} times on this problem.\n"
                        f"Problem: {goal_title}\n"
                        f"My last error: {last_output[:300]}\n"
                        f"My approach: {reasoning_lines[0] if reasoning_lines else 'unknown'}\n\n"
                        f"Can you give me a hint? Not the answer — just point me in the right direction."
                    )
                    answer = ask_teacher(question, goal_title)
                    # Answer will be picked up next cycle via answers.txt

                # Always submit to teacher (teacher sees failures too)
                file("write", "status.md", "submitted")
                log("Waiting for teacher...")
                wait_start = time.time()
                while True:
                    status = file("read", "status.md").strip()
                    if status != "submitted":
                        break
                        if time.time() - wait_start > 300:
                            file("write", "status.md", "working")
                            break
                        time.sleep(1)

            # --- Metacognition (every 10 attempts) ---
            if attempt_count >= last_meta_at + 10:
                last_meta_at = attempt_count
                current_learnings = file("read", "learnings.md")
                if current_learnings.strip():
                    meta = think(
                        "Read your learnings and reflect on patterns in HOW you think and WHERE you fail.\n\n"
                        f"Learnings:\n{current_learnings[-3000:]}\n\n"
                        "Write a metacognition update.",
                        system=system_prompt, max_tokens=512,
                    )
                    if meta and not meta.startswith("ERROR:"):
                        file("write", "metacognition.md", meta)
                        log("Updated metacognition.md")

            # --- Soul rewrite (every 30 attempts) ---
            if attempt_count >= last_soul_at + 30:
                last_soul_at = attempt_count
                meta_content = file("read", "metacognition.md")
                if not meta_content.startswith("ERROR:"):
                    new_soul = think(
                        f"Current identity:\n{soul}\n\nMetacognition:\n{meta_content}\n\n"
                        "Has something genuinely shifted? If yes, rewrite. If not, say NO_CHANGE.",
                        system=system_prompt, max_tokens=512,
                    )
                    if new_soul and "NO_CHANGE" not in new_soul and len(new_soul) > 50:
                        file("write", "soul.md", new_soul)
                        log("Rewrote soul.md")

            time.sleep(0.5)

        except KeyboardInterrupt:
            log("Interrupted — shutting down")
            sys.exit(0)
        except Exception as e:
            log(f"Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
