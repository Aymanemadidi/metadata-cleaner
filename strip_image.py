#!/usr/bin/env python3
import argparse
import os
import sys
from PIL import Image


SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp"}


def strip_image(input_path, output_path, compress=False):
    img = Image.open(input_path)

    # Convert to RGB if needed (e.g. RGBA PNG saved as JPEG would fail)
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg") and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Create a clean copy with no metadata by rebuilding the image
    clean = Image.frombytes(img.mode, img.size, img.tobytes())

    save_kwargs = {}
    if ext in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 70 if compress else 95
        save_kwargs["optimize"] = True
    elif ext == ".png":
        save_kwargs["compress_level"] = 9 if compress else 6
    elif ext == ".webp":
        save_kwargs["quality"] = 70 if compress else 90

    clean.save(output_path, **save_kwargs)


def main():
    parser = argparse.ArgumentParser(description="Strip metadata from image files")
    parser.add_argument("input", help="Path to the input image file")
    parser.add_argument("-o", "--output", help="Output file path (default: <name>_clean.<ext>)")
    parser.add_argument("--compress", action="store_true", help="Compress image (lower quality/higher PNG compression)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()
    if ext not in SUPPORTED:
        print(f"Error: unsupported format '{ext}'. Supported: {', '.join(SUPPORTED)}")
        sys.exit(1)

    if not args.output:
        basename = os.path.basename(args.input)
        name, ext = os.path.splitext(basename)
        args.output = os.path.join(os.path.expanduser("~/Downloads"), f"{name}_clean{ext}")

    print(f"Processing: {args.input}")
    strip_image(args.input, args.output, compress=args.compress)

    input_size = os.path.getsize(args.input) / (1024 * 1024)
    output_size = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Done: {args.output}")
    print(f"Size: {input_size:.1f} MB -> {output_size:.1f} MB")


if __name__ == "__main__":
    main()
