# runcomfy-lora-training

A Claude skill for training custom LoRA style models on [RunComfy](https://www.runcomfy.com) — from raw image folder to working checkpoint. Covers image preparation, job configuration, training monitoring, test generation, and quality evaluation.

Built from a real training run that produced a solarpunk aesthetic LoRA in ~52 minutes for ~$3.75.

---

## Before You Start

**You'll need:**

- A **RunComfy account** with a positive credit balance. Sign up at [runcomfy.com](https://www.runcomfy.com). Training 1500 steps on an H100 costs roughly $3–5 in credits — load at least $10 to have headroom.
- **20–60 images** that share the visual style you want to teach. JPEGs and PNGs both work. Each image should be at least 1024px on its shortest side (the prep script will flag anything smaller).
- **~1 hour** of time. Training itself takes 35–55 minutes, plus a few minutes for image prep and job setup. Claude will monitor the run but you don't need to babysit it.

---

## What It Does

When you tell Claude something like *"I want to train a LoRA from my moodboard"* or *"create a custom style on RunComfy"*, this skill kicks in and walks through:

1. **Image audit and preparation** — runs a bundled Python script that filters, converts, and center-crops your images to 1024×1024 JPEG
2. **RunComfy setup** — creates a dataset and configures a training job with proven defaults (Flex.1 base model, AdamW8Bit, rank 32, 1e-4 LR)
3. **Training monitoring** — watches the job log for checkpoints, loss, and completion
4. **Test generation** — runs sample images with your trigger word to verify the style transferred
5. **Results report** — quality assessment and recommendations for the next iteration

---

## Installing the Skill

In Claude Code or Cowork, install `runcomfy-lora-training.skill` via the Skills panel. Once installed, it triggers automatically on relevant prompts — no slash command needed.

---

## Usage

Just describe what you want:

> *"I have a folder of brutalist architecture photos at ~/Desktop/brutalist-refs/. Help me train a LoRA on RunComfy."*

> *"My LoRA training finished but all the test images look the same. What should I do?"*

> *"Can you prep my moodboard images for LoRA training and tell me how many are usable?"*

---

## Cost & Time Reference

| Dataset size | Recommended steps | Est. time | Est. cost |
|---|---|---|---|
| 20–25 images | 1500 | ~50 min | ~$3.75 |
| 40–60 images | 2000–2500 | ~70 min | ~$5.25 |

Costs are for H100 PCIe at RunComfy's current rate (~$4.49/hr). Prices may change — check RunComfy's pricing page before training.

---

## Requirements

- Python with Pillow installed (`pip install Pillow`) — used by the image prep script
- A RunComfy account with credits loaded
- Claude with browser automation enabled (for navigating RunComfy)
