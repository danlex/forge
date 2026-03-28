#!/usr/bin/env python3
"""
Fine-tune Qwen 3.5 4B with LoRA on curated traces.
Usage: python3 finetune.py [gen_number]
"""

import json
import os
import sys
import time

GEN = int(sys.argv[1]) if len(sys.argv) > 1 else 0
GEN_DIR = f"generations/gen{GEN:03d}"
FORGE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_MODEL = "Qwen/Qwen3.5-4B"
BASE_WEIGHTS_DIR = os.path.join(FORGE_DIR, "base_weights", "qwen3.5-4b")
ADAPTER_DIR = os.path.join(FORGE_DIR, GEN_DIR, "adapter")
MERGED_DIR = os.path.join(FORGE_DIR, GEN_DIR, "merged")


def download_base():
    """Download base weights if not cached."""
    if os.path.exists(os.path.join(BASE_WEIGHTS_DIR, "config.json")):
        print(f"Base weights found at {BASE_WEIGHTS_DIR}")
        return

    print(f"Downloading {BASE_MODEL}...")
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.makedirs(BASE_WEIGHTS_DIR, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.save_pretrained(BASE_WEIGHTS_DIR)
    print("Tokenizer saved")

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, torch_dtype="bfloat16", trust_remote_code=True
    )
    model.save_pretrained(BASE_WEIGHTS_DIR)
    print("Model saved")


def load_data():
    """Load curated JSONL into training format."""
    data_file = os.path.join(FORGE_DIR, GEN_DIR, "curated.jsonl")
    examples = []
    with open(data_file) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    print(f"Loaded {len(examples)} training examples")
    return examples


def format_for_training(examples, tokenizer):
    """Convert chat format to tokenized training data."""
    formatted = []
    for ex in examples:
        messages = ex["messages"]
        # Build a single text: system + user + assistant
        text = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                text += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                text += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                text += f"<|im_start|>assistant\n{content}<|im_end|>\n"

        tokens = tokenizer(
            text,
            truncation=True,
            max_length=2048,
            padding="max_length",
            return_tensors="pt",
        )
        tokens["labels"] = tokens["input_ids"].clone()
        formatted.append({
            "input_ids": tokens["input_ids"].squeeze(),
            "attention_mask": tokens["attention_mask"].squeeze(),
            "labels": tokens["labels"].squeeze(),
        })

    return formatted


def train(examples):
    """Run LoRA fine-tuning."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
    from peft import LoraConfig, get_peft_model, TaskType

    print(f"\n{'=' * 50}")
    print(f"  FINE-TUNING Generation {GEN}")
    print(f"  {len(examples)} examples")
    print(f"  Device: MPS" if torch.backends.mps.is_available() else "  Device: CPU")
    print(f"{'=' * 50}\n")

    # Load tokenizer and model
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_WEIGHTS_DIR, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_WEIGHTS_DIR,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    # LoRA config
    num_examples = len(examples)
    if num_examples < 20:
        epochs = 3
        lr = 2e-4
    elif num_examples <= 40:
        epochs = 5
        lr = 1e-4
    else:
        epochs = 3
        lr = 5e-5

    print(f"Config: {epochs} epochs, lr={lr}, {num_examples} examples")

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    )

    model = get_peft_model(model, lora_config)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable: {trainable:,} / {total:,} ({trainable/total*100:.1f}%)")

    # Prepare data
    print("Tokenizing...")
    train_data = format_for_training(examples, tokenizer)

    # Training
    os.makedirs(ADAPTER_DIR, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=ADAPTER_DIR,
        num_train_epochs=epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=lr,
        weight_decay=0.01,
        logging_steps=1,
        save_strategy="no",
        bf16=True,
        use_mps_device=torch.backends.mps.is_available(),
        report_to="none",
        dataloader_pin_memory=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
    )

    print("\nTraining started...")
    t0 = time.time()
    result = trainer.train()
    elapsed = time.time() - t0

    print(f"\nTraining complete in {elapsed:.0f}s")
    print(f"  Loss: {result.training_loss:.4f}")
    print(f"  Steps: {result.global_step}")

    # Save adapter
    model.save_pretrained(ADAPTER_DIR)
    tokenizer.save_pretrained(ADAPTER_DIR)
    print(f"Adapter saved to {ADAPTER_DIR}")

    # Merge adapter into base
    print("Merging adapter into base weights...")
    merged_model = model.merge_and_unload()
    os.makedirs(MERGED_DIR, exist_ok=True)
    merged_model.save_pretrained(MERGED_DIR)
    tokenizer.save_pretrained(MERGED_DIR)
    print(f"Merged model saved to {MERGED_DIR}")

    return {
        "loss": result.training_loss,
        "steps": result.global_step,
        "epochs": epochs,
        "lr": lr,
        "time_seconds": round(elapsed),
        "examples": num_examples,
        "trainable_params": trainable,
    }


def create_ollama_model():
    """Create an Ollama model from the merged weights."""
    import subprocess

    next_gen = GEN + 1
    model_name = f"forge-gen{next_gen:03d}"
    modelfile = os.path.join(FORGE_DIR, GEN_DIR, "Modelfile")

    with open(modelfile, "w") as f:
        f.write(f"FROM {MERGED_DIR}\n")
        f.write("PARAMETER temperature 0.7\n")
        f.write("PARAMETER top_p 0.9\n")
        f.write("PARAMETER num_ctx 4096\n")

    print(f"\nCreating Ollama model: {model_name}")
    result = subprocess.run(
        ["ollama", "create", model_name, "-f", modelfile],
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode == 0:
        print(f"  {model_name} created successfully")
        return model_name
    else:
        print(f"  ERROR: {result.stderr[:200]}")
        return None


def main():
    print(f"Forge Fine-Tuning — Generation {GEN}")
    print(f"{'=' * 50}")

    # Step 1: Ensure base weights
    download_base()

    # Step 2: Load curated data
    examples = load_data()

    # Step 3: Train
    report = train(examples)

    # Step 4: Create Ollama model
    model_name = create_ollama_model()

    # Step 5: Write report
    report["model_name"] = model_name
    report_file = os.path.join(FORGE_DIR, GEN_DIR, "report.md")
    with open(report_file, "w") as f:
        f.write(f"# Generation {GEN} Fine-Tuning Report\n\n")
        f.write(f"- Examples: {report['examples']}\n")
        f.write(f"- Epochs: {report['epochs']}\n")
        f.write(f"- Learning rate: {report['lr']}\n")
        f.write(f"- Final loss: {report['loss']:.4f}\n")
        f.write(f"- Training steps: {report['steps']}\n")
        f.write(f"- Time: {report['time_seconds']}s\n")
        f.write(f"- Trainable params: {report['trainable_params']:,}\n")
        f.write(f"- Output model: {model_name}\n")

    print(f"\nReport written to {report_file}")
    print(f"\nNext step: python3 run_benchmark.py {model_name}")


if __name__ == "__main__":
    main()
