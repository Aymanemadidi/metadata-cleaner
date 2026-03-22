#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Strip metadata from video files")
    parser.add_argument("input", help="Path to the input video file")
    parser.add_argument("-o", "--output", help="Output file path (default: <name>_clean.<ext>)")
    parser.add_argument("--compress", action="store_true", help="Compress video using H.264 (re-encodes)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    if not args.output:
        basename = os.path.basename(args.input)
        name, ext = os.path.splitext(basename)
        args.output = os.path.join(os.path.expanduser("~/Downloads"), f"{name}_clean{ext}")

    cmd = ["ffmpeg", "-y", "-i", args.input, "-map_metadata", "-1",
           "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact"]

    if args.compress:
        cmd += ["-vcodec", "libx264", "-crf", "23", "-preset", "medium"]
    else:
        cmd += ["-c", "copy"]

    cmd.append(args.output)

    print(f"Processing: {args.input}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: ffmpeg failed\n{result.stderr}")
        sys.exit(1)

    input_size = os.path.getsize(args.input) / (1024 * 1024)
    output_size = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Done: {args.output}")
    print(f"Size: {input_size:.1f} MB -> {output_size:.1f} MB")


if __name__ == "__main__":
    main()
