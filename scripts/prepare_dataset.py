#!/usr/bin/env python3
"""
prepare_dataset.py — Prepare images for LoRA training on RunComfy

Usage:
    python scripts/prepare_dataset.py /path/to/source/images [--min-size 1024] [--output-dir lora-ready-jpg]

What it does:
  1. Scans the source directory for image files
  2. Excludes images where the smallest dimension is below --min-size
  3. Converts all valid images to JPEG at quality 90
  4. Center-crops each image to a square (min_size × min_size)
  5. Saves to a output directory (default: lora-ready-jpg/ inside source dir)
  6. Prints a summary report

Requirements: Pillow (pip install Pillow)
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow --break-system-packages")
    sys.exit(1)

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
JPEG_QUALITY = 90


def center_crop_square(img: Image.Image, size: int) -> Image.Image:
    """Center-crop an image to a square of the given size."""
    w, h = img.size
    # Scale so that the short side equals `size`
    scale = size / min(w, h)
    new_w = round(w * scale)
    new_h = round(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Crop center
    left = (new_w - size) // 2
    top = (new_h - size) // 2
    return img.crop((left, top, left + size, top + size))


def audit_and_prepare(source_dir: Path, output_dir: Path, min_size: int) -> dict:
    """
    Process all images in source_dir.
    Returns a dict with 'included', 'excluded', 'errors' lists.
    """
    included = []
    excluded = []
    errors = []

    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        image_files.extend(source_dir.glob(f'*{ext}'))
        image_files.extend(source_dir.glob(f'*{ext.upper()}'))
    # Deduplicate (glob is case-sensitive on Linux but not always on Mac)
    image_files = sorted(set(image_files))

    if not image_files:
        print(f"No supported image files found in {source_dir}")
        print(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
        return {'included': included, 'excluded': excluded, 'errors': errors}

    output_dir.mkdir(parents=True, exist_ok=True)

    for img_path in image_files:
        try:
            with Image.open(img_path) as img:
                w, h = img.size
                short_side = min(w, h)

                if short_side < min_size:
                    excluded.append({
                        'file': img_path.name,
                        'reason': f'Too small: {w}×{h}px (min {min_size}px on short side)',
                        'dimensions': (w, h)
                    })
                    continue

                # Convert to RGB (handles RGBA, palette, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Center-crop to square
                cropped = center_crop_square(img, min_size)

                # Save as JPEG
                out_name = img_path.stem + '.jpg'
                out_path = output_dir / out_name
                # Handle name collisions (e.g., photo.jpg and photo.png in same folder)
                if out_path.exists():
                    out_name = img_path.stem + '_' + img_path.suffix.lstrip('.') + '.jpg'
                    out_path = output_dir / out_name

                cropped.save(out_path, 'JPEG', quality=JPEG_QUALITY)

                included.append({
                    'file': img_path.name,
                    'output': out_name,
                    'original_dimensions': (w, h),
                    'output_dimensions': (min_size, min_size)
                })

        except Exception as e:
            errors.append({
                'file': img_path.name,
                'reason': f'Could not open/process: {e}'
            })

    return {'included': included, 'excluded': excluded, 'errors': errors}


def print_report(results: dict, output_dir: Path, min_size: int):
    """Print a human-readable summary of what was included/excluded."""
    included = results['included']
    excluded = results['excluded']
    errors = results['errors']
    total = len(included) + len(excluded) + len(errors)

    print()
    print("=" * 60)
    print("  DATASET PREPARATION REPORT")
    print("=" * 60)
    print(f"  Total images scanned:  {total}")
    print(f"  Included:           {len(included)}")
    print(f"  Excluded:           {len(excluded)}")
    if errors:
        print(f"  Errors:            {len(errors)}")
    print(f"  Output directory:      {output_dir}")
    print(f"  Output size:           {min_size}×{min_size}px JPEG (quality {JPEG_QUALITY})")
    print()

    if included:
        print(f"  INCLUDED ({len(included)} images):")
        for item in included:
            orig = '×'.join(map(str, item['original_dimensions']))
            print(f"    OK  {item['file']}  [{orig}] -> {item['output']}")

    if excluded:
        print()
        print(f"  EXCLUDED ({len(excluded)} images):")
        for item in excluded:
            print(f"    EXCLUDED  {item['file']}  -- {item['reason']}")

    if errors:
        print()
        print(f"  ERRORS ({len(errors)} files could not be read):")
        for item in errors:
            print(f"    ERROR   {item['file']}  -- {item['reason']}")

    print()
    print("=" * 60)

    if len(included) < 20:
        print(f"\n  WARNING: Only {len(included)} images included.")
        print("  LoRA training works best with 20+ images. Consider:")
        print("  - Adding more images from different angles/compositions")
        print("  - Accepting images with smaller dimensions (lower --min-size,")
        print("    though 512 is the practical minimum for quality results)")
    elif len(included) < 40:
        print(f"\n  {len(included)} images included -- this will work for a first run.")
        print("  40-60 images will give better generalization in a future iteration.")
    else:
        print(f"\n  {len(included)} images -- good dataset size for quality training.")

    print()

    if len(included) > 0:
        steps = max(1500, len(included) * 60)
        hours = (steps * 1.4) / 3600
        cost = hours * 4.49
        print(f"  TRAINING ESTIMATES (based on {len(included)} images):")
        print(f"    Recommended steps: ~{steps}")
        print(f"    Estimated time:    ~{hours:.1f} hours ({hours*60:.0f} minutes)")
        print(f"    Estimated cost:    ~${cost:.2f} (H100 @ $4.49/hr)")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Prepare images for LoRA training on RunComfy (ai-toolkit)'
    )
    parser.add_argument(
        'source_dir',
        type=Path,
        help='Directory containing your source images'
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=1024,
        help='Minimum dimension in pixels (default: 1024). Images smaller than this on either side will be excluded.'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for prepared images (default: <source_dir>/lora-ready-jpg/)'
    )

    args = parser.parse_args()

    source_dir = args.source_dir.expanduser().resolve()
    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        sys.exit(1)
    if not source_dir.is_dir():
        print(f"ERROR: Not a directory: {source_dir}")
        sys.exit(1)

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        output_dir = source_dir / 'lora-ready-jpg'

    print(f"Scanning: {source_dir}")
    print(f"Output:   {output_dir}")
    print(f"Min size: {args.min_size}×{args.min_size}px")
    print()

    results = audit_and_prepare(source_dir, output_dir, args.min_size)
    print_report(results, output_dir, args.min_size)

    if not results['included']:
        sys.exit(1)


if __name__ == '__main__':
    main()
