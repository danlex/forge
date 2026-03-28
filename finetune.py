#!/usr/bin/env python3
"""
Fine-tune Qwen 3.5 4B with LoRA using MLX on Apple Silicon.
Usage: python3 finetune.py [gen_number]

MLX runs natively on Metal — no CPU/GPU transfer, no swap thrashing.
~8GB memory for 4-bit quantized 4B model + LoRA.
"""

import json
import os
import subprocess
import sys
import time

GEN = int(sys.argv[1]) if len(sys.argv) > 1 else 0
GEN_DIR = f"generations/gen{GEN:03d}"
FORGE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "Qwen/Qwen3.5-4B"
ADAPTER_DIR = os.path.join(FORGE_DIR, GEN_DIR, "adapter")
MERGED_DIR = os.path.join(FORGE_DIR, GEN_DIR, "merged")


def prepare_data():
    """Convert curated.jsonl to mlx-lm training format."""
    curated_file = os.path.join(FORGE_DIR, GEN_DIR, "curated.jsonl")
    with open(curated_file) as f:
        examples = [json.loads(l) for l in f if l.strip()]

    print(f"Loaded {len(examples)} curated examples")

    # mlx-lm expects {"messages": [...]} format — already in that format
    # Split 90/10 train/valid
    split = max(1, len(examples) // 10)
    train = examples[:-split] if split > 0 else examples
    valid = examples[-split:] if split > 0 else examples[:1]

    data_dir = os.path.join(FORGE_DIR, GEN_DIR, "mlx_data")
    os.makedirs(data_dir, exist_ok=True)

    train_file = os.path.join(data_dir, "train.jsonl")
    valid_file = os.path.join(data_dir, "valid.jsonl")

    with open(train_file, "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")

    with open(valid_file, "w") as f:
        for ex in valid:
            f.write(json.dumps(ex) + "\n")

    print(f"  Train: {len(train)} examples")
    print(f"  Valid: {len(valid)} examples")
    return data_dir


def train(data_dir):
    """Run LoRA fine-tuning with mlx-lm."""
    num_examples = len(open(os.path.join(data_dir, "train.jsonl")).readlines())

    # Config based on dataset size
    if num_examples < 20:
        iters = num_examples * 3
        lr = 2e-4
    elif num_examples <= 40:
        iters = num_examples * 5
        lr = 1e-4
    else:
        iters = num_examples * 3
        lr = 5e-5

    os.makedirs(ADAPTER_DIR, exist_ok=True)

    print(f"\n{'=' * 50}")
    print(f"  FINE-TUNING Generation {GEN}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Backend: MLX (Metal GPU)")
    print(f"  Examples: {num_examples}")
    print(f"  Iterations: {iters}")
    print(f"  Learning rate: {lr}")
    print(f"  LoRA: r=16, layers=16")
    print(f"{'=' * 50}\n")

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", MODEL_NAME,
        "--train",
        "--data", data_dir,
        "--adapter-path", ADAPTER_DIR,
        "--iters", str(iters),
        "--learning-rate", str(lr),
        "--num-layers", "4",
        "--batch-size", "1",
        "--val-batches", "1",
        "--steps-per-eval", str(max(10, iters // 5)),
        "--steps-per-report", "5",
        "--max-seq-length", "512",
        "--grad-checkpoint",
    ]

    print(f"Running: {' '.join(cmd[-14:])}")
    print()

    t0 = time.time()
    result = subprocess.run(cmd, cwd=FORGE_DIR, timeout=3600)
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"\nERROR: Training failed (exit code {result.returncode})")
        return None

    print(f"\nTraining complete in {elapsed:.0f}s ({elapsed/60:.1f}m)")
    return {
        "iters": iters,
        "lr": lr,
        "time_seconds": round(elapsed),
        "examples": num_examples,
    }


def fuse_and_export():
    """Merge LoRA adapter into base model, then create Ollama model."""
    next_gen = GEN + 1
    model_name = f"forge-gen{next_gen:03d}"

    print(f"\nFusing adapter into base model...")
    os.makedirs(MERGED_DIR, exist_ok=True)

    cmd = [
        sys.executable, "-m", "mlx_lm", "fuse",
        "--model", MODEL_NAME,
        "--adapter-path", ADAPTER_DIR,
        "--save-path", MERGED_DIR,
    ]

    result = subprocess.run(cmd, cwd=FORGE_DIR, timeout=600)
    if result.returncode != 0:
        print(f"ERROR: Fuse failed")
        return None

    print(f"Merged model saved to {MERGED_DIR}")

    # Create Ollama model
    modelfile = os.path.join(FORGE_DIR, GEN_DIR, "Modelfile")
    with open(modelfile, "w") as f:
        f.write(f"FROM {MERGED_DIR}\n")
        f.write("PARAMETER temperature 0.7\n")
        f.write("PARAMETER top_p 0.9\n")
        f.write("PARAMETER num_ctx 4096\n")

    print(f"Creating Ollama model: {model_name}")

    # Start ollama if not running
    subprocess.run(["pgrep", "-x", "ollama"], capture_output=True)
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
    except Exception:
        print("Starting Ollama...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(5)

    result = subprocess.run(
        ["ollama", "create", model_name, "-f", modelfile],
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode == 0:
        print(f"  {model_name} created successfully")
        return model_name
    else:
        print(f"  ERROR: {result.stderr[:300]}")
        return None


def main():
    print(f"Forge Fine-Tuning (MLX) — Generation {GEN}")
    print(f"{'=' * 50}")

    # Step 1: Prepare data
    data_dir = prepare_data()

    # Step 2: Train
    report = train(data_dir)
    if report is None:
        sys.exit(1)

    # Step 3: Fuse and create Ollama model
    model_name = fuse_and_export()

    # Step 4: Write report
    report["model_name"] = model_name
    report_file = os.path.join(FORGE_DIR, GEN_DIR, "report.md")
    with open(report_file, "w") as f:
        f.write(f"# Generation {GEN} Fine-Tuning Report\n\n")
        f.write(f"- Backend: MLX (Metal GPU)\n")
        f.write(f"- Base model: {MODEL_NAME}\n")
        f.write(f"- Examples: {report['examples']}\n")
        f.write(f"- Iterations: {report['iters']}\n")
        f.write(f"- Learning rate: {report['lr']}\n")
        f.write(f"- Time: {report['time_seconds']}s\n")
        f.write(f"- Output model: {model_name}\n")

    print(f"\nReport written to {report_file}")
    print(f"\nNext: python3 run_benchmark.py {model_name}")


if __name__ == "__main__":
    main()
