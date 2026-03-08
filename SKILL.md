---
name: runcomfy-lora-training
description: >
  End-to-end workflow for training a custom LoRA (style or subject) on RunComfy using the
  ai-toolkit trainer (ostris). Covers image auditing, dataset preparation, RunComfy job
  configuration, training monitoring, test generation, and quality evaluation. Use this skill
  whenever someone wants to: train a LoRA from their own images, create a custom AI image style,
  fine-tune an image generation model on a moodboard or photo collection, or use RunComfy to
  generate images in a specific aesthetic. Trigger on phrases like "train a LoRA", "create a
  custom style", "RunComfy training", "fine-tune on my images", "style LoRA", "moodboard LoRA",
  "ai-toolkit", "train on my photos", or any variation of wanting AI to learn a particular
  visual style or subject from example images.
---

# RunComfy LoRA Training

This skill walks through the complete workflow for training a custom LoRA style model on [RunComfy](https://www.runcomfy.com) using the ai-toolkit (ostris) trainer. It's based on a real training run that produced a working solarpunk aesthetic LoRA in ~52 minutes for ~$3.75.

---

## Step 1 — Audit and Prepare Your Images

Quality of your dataset is the single biggest lever on quality of the final LoRA. Run the bundled preparation script first.

### Run the prep script

```bash
python scripts/prepare_dataset.py /path/to/your/source/images
```

This will:
1. Scan all image files in the source directory
2. Exclude any image where the smallest dimension is under 1024px (too small to center-crop cleanly)
3. Convert all valid images to JPEG at quality 90
4. Center-crop each to 1024×1024 (preserving the center of the composition)
5. Save results to a `lora-ready-jpg/` subfolder inside the source directory
6. Print a summary report: included count, excluded count, and reasons for exclusions

### What makes a good training image

- **Quantity:** 20–25 images is the practical minimum. 40–60 gives the model enough variation to generalize rather than memorize. More is better up to ~200.
- **Diversity:** Each image should teach the model something the others don't. Vary: camera distance (closeups, medium shots, wide establishing shots), lighting conditions, time of day, subjects within the style, architectural or compositional forms.
- **Consistency:** All images should share the core aesthetic you're trying to capture. If your moodboard has 30 solarpunk images and 5 brutalist ones, the 5 outliers will confuse the model.
- **Format:** JPEG, PNG, WebP work well. AVIF and HEIC may have compatibility issues — the script will skip files it can't open.

---

## Step 2 — Create a RunComfy Dataset

1. Go to [runcomfy.com](https://www.runcomfy.com) and sign in
2. Navigate to **Datasets** in the top navigation (not Trainer — you need to create the dataset first)
3. Click **New Dataset**, give it a name matching your trigger word convention (e.g., `solarpunk-style`)
4. Upload all images from your `lora-ready-jpg/` folder
5. After upload, verify the count matches what the prep script reported

---

## Step 3 — Configure Your Training Job

Navigate to **Trainer → ai-toolkit** and click **New Job**.

### Recommended settings

| Parameter | Recommended Value | Notes |
|---|---|---|
| Job name | `your-style-name` | Kebab-case, descriptive |
| Base model | **Flex.1** (ostris/Flex.1-alpha) | FLUX family, strong style transfer |
| Dataset | (your dataset from Step 2) | |
| **Trigger word** | `yourname_style` | Underscore convention; this is the activation word |
| **Steps** | 1500 (for ~20 images) | Scale up: ~2000–2500 for 40–60 images |
| **Learning rate** | `1e-4` | Safe default; drop to `8e-5` for larger datasets |
| Optimizer | AdamW8Bit | Best balance of speed and quality |
| LoRA rank | 32 | Good default; 16 for faster/smaller, 64 for richer |
| Save dtype | BF16 | Standard |
| Batch size | 1 | Use 1 for small datasets (< 50 images) |
| Save checkpoint every | 250 steps | Gives you 4–6 checkpoints to compare |
| Keep last N checkpoints | 4 | Saves storage; keeps recent history |
| Validation samples | 10 | Generated at each checkpoint save |

### Trigger word convention

The trigger word is the phrase you'll include in prompts to activate the LoRA's style. Format: `descriptive_style` (lowercase, underscore). Good examples: `solarpunk_style`, `vintage_poster_style`, `brutalist_arch`, `watercolor_portrait`. Avoid generic words that conflict with base model vocabulary.

### Caption strategy

For style LoRAs (teaching an aesthetic rather than a subject), using just the trigger word as the caption often works well — it forces all the style into that one activation. For subject LoRAs (teaching a specific person or object), more descriptive captions help the model understand what varies across images vs. what's the subject.

---

## Step 4 — Start Training

### GPU selection

Launch with an **H100 PCIe (80GB)** — this is the current best value on RunComfy for ai-toolkit runs. At ~$4.49/hr and ~1.4 seconds/step, 1500 steps takes around 35–55 minutes (including model load and checkpoint saves).

### Confirming the job started

Look for in the training log:
```
Starting training...
step: 1/1500
```

The first few seconds may show just model loading. If you see `step: 1/1500` within 90 seconds, training is proceeding normally.

---

## Step 5 — Monitor Training

### What to watch

- **Loss values:** These will be noisy (range ~0.2–0.8) with small datasets and batch_size=1. This is normal. Look for a general downward trend over time, not smoothness.
- **Checkpoint saves:** The log will say `checkpoint saved: yourname_000000250.safetensors` every 250 steps. These are opportunities to test intermediate checkpoints.
- **Validation samples:** 10 images are generated at each checkpoint save — visible in the RunComfy job page. These give you visual feedback on how the model is progressing.
- **GPU telemetry:** The GPU stats panel may occasionally show 0% load / low temperature while training is actively running. This is a polling lag, not a real issue. Always check the training log, not the telemetry.

### Training is complete when:
```
training loop finished, wait_for_everyone done
```
Status changes to **"stopped"** — this is RunComfy's term for "completed successfully."

---

## Step 6 — Generate Test Images

After training completes:

1. Navigate to **Run LoRA** (or the inference playground for your base model)
2. Select your final checkpoint (`yourname_000001500.safetensors`)
3. **Important gotcha:** After selecting a checkpoint, verify the **LoRA Scale** field. It may default to `-1` (which would invert the style). Triple-click the field and type `1`.
4. Set your test prompt (always include the trigger word at the start):
   ```
   yourname_style, [describe the scene or subject], [style descriptors]
   ```
5. Resolution: 1024×1024 matches training data
6. Generate 3–5 test images with different seeds to see the distribution

**Prompt field gotcha:** If you're using browser automation and the prompt field isn't clearing properly with keyboard shortcuts, use `form_input` on the textarea element directly to set the value.

---

## Step 7 — Evaluate and Report

### Quick quality checklist

- **Does the trigger word matter?** Generate one image with the trigger word and one without. If they look the same, the LoRA didn't capture the style in the trigger word (try lower LR or more diverse captions).
- **Is it consistent?** 3 images with different seeds should all have recognizable stylistic similarity. High variance = the model didn't learn a tight style.
- **Is it too rigid?** If all 3 images look nearly identical (same composition), the model may have overfit. Try an earlier checkpoint (1000 or 1250).
- **Does it respond to prompting?** You should be able to change the subject (`a solarpunk_style house` vs. `a solarpunk_style garden`) while preserving the aesthetic.

### Standard results report template

```
## LoRA Training Results

**Model:** [checkpoint filename]
**Trigger word:** [trigger_word]
**Total cost:** ~$X.XX
**Training time:** ~X minutes

### What it learned well
[Describe the aesthetic elements the model reliably produces]

### Limitations
[Describe inconsistencies, overfit patterns, missing elements]

### Recommended LoRA scales
- Full style: 1.0
- Blended (recommended for most use): 0.7–0.85
- Subtle accent: 0.4–0.6

### Next iteration recommendations
- [ ] More images? (current count: X; target 40–60 for better generalization)
- [ ] Different checkpoint? (test 1000 vs 1250 vs 1500)
- [ ] More steps? (suggest X for next run)
- [ ] Caption changes?
```

---

## Quick Reference: Full Settings Cheatsheet

```
Base model: ostris/Flex.1-alpha
Optimizer: AdamW8Bit
LoRA rank: 32
Save dtype: BF16
Steps: 1500 (scale with dataset size)
Learning rate: 1e-4
Batch size: 1
Save every: 250 steps
Keep last: 4 checkpoints
Validation: 10 samples per checkpoint
GPU: H100 PCIe (80GB)
Image target: 1024×1024 JPEG, center-cropped
```

---

## Common Issues

| Problem | Cause | Fix |
|---|---|---|
| LoRA Scale shows `-1` | RunComfy default after checkpoint select | Triple-click field, type `1` |
| Prompt field won't clear | React-controlled textarea | Use `form_input` tool directly on the textarea ref |
| GPU telemetry shows 0% during training | Polling lag | Check training log, not telemetry panel |
| All test images look the same | Overfit / dominant composition in dataset | Test earlier checkpoint (1000 or 1250) |
| Style not activating | Trigger word not in prompt | Always start prompt with trigger word |
| Loss not decreasing | LR too low, or too few steps | Increase LR slightly or run more steps |
| Images too blurry / noisy | LR too high | Drop LR to 5e-5 and retrain |
