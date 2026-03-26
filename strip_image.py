#!/usr/bin/env python3
import argparse
import os
import struct
import sys
from PIL import Image


SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp"}

# JPEG APP segments that carry metadata — strip all of these
# Keep: APP0 (JFIF header, needed for compatibility)
JPEG_META_MARKERS = {
    b'\xff\xe1',  # APP1  — EXIF / XMP
    b'\xff\xe2',  # APP2  — ICC profile / Flashpix
    b'\xff\xe3',  # APP3
    b'\xff\xe4',  # APP4
    b'\xff\xe5',  # APP5
    b'\xff\xe6',  # APP6
    b'\xff\xe7',  # APP7
    b'\xff\xe8',  # APP8
    b'\xff\xe9',  # APP9
    b'\xff\xea',  # APP10
    b'\xff\xeb',  # APP11
    b'\xff\xec',  # APP12 — Ducky / Photoshop
    b'\xff\xed',  # APP13 — IPTC / Photoshop IRB
    b'\xff\xee',  # APP14 — Adobe color transform
    b'\xff\xef',  # APP15
    b'\xff\xfe',  # COM   — JPEG comment
}


def strip_jpeg_lossless(input_path, output_path):
    """
    Strip metadata from JPEG by removing marker segments at the binary level.
    The compressed image data (DCT) is never decoded or re-encoded — zero quality loss.
    """
    with open(input_path, 'rb') as f:
        data = f.read()

    if data[:2] != b'\xff\xd8':
        raise ValueError("Not a valid JPEG file")

    out = bytearray()
    i = 0

    while i < len(data) - 1:
        marker = data[i:i+2]

        # SOI — start of image, always keep
        if marker == b'\xff\xd8':
            out += marker
            i += 2
            continue

        # SOS — start of scan: everything from here is raw image data, copy to end
        if marker == b'\xff\xda':
            out += data[i:]
            break

        # Markers without a length field
        if marker in (b'\xff\xd9', b'\xff\xd0', b'\xff\xd1',
                      b'\xff\xd2', b'\xff\xd3', b'\xff\xd4',
                      b'\xff\xd5', b'\xff\xd6', b'\xff\xd7'):
            out += marker
            i += 2
            continue

        # All other markers have a 2-byte length field
        if i + 3 >= len(data):
            break
        length = struct.unpack('>H', data[i+2:i+4])[0]
        segment_end = i + 2 + length

        if marker in JPEG_META_MARKERS:
            # Skip this segment entirely
            i = segment_end
        else:
            # Keep this segment (SOF, DHT, DQT, DRI, etc.)
            out += data[i:segment_end]
            i = segment_end

    with open(output_path, 'wb') as f:
        f.write(out)


def strip_image(input_path, output_path, compress=False):
    ext = os.path.splitext(output_path)[1].lower()

    if ext in (".jpg", ".jpeg") and not compress:
        # Lossless path: strip metadata segments at binary level, never re-encode
        strip_jpeg_lossless(input_path, output_path)
        return

    # For compress mode or non-JPEG formats: rebuild from pixels
    img = Image.open(input_path)

    if ext in (".jpg", ".jpeg") and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    clean = Image.frombytes(img.mode, img.size, img.tobytes())

    save_kwargs = {}
    if ext in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 70
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
    parser.add_argument("--compress", action="store_true", help="Compress image (re-encodes, reduces file size)")
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
