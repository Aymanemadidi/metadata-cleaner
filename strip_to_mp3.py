#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys


def get_duration(input_path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", input_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="Strip metadata from video, extract audio as split MP3s")
    parser.add_argument("input", help="Path to the input video file")
    parser.add_argument("--chunk", type=int, default=600, help="Chunk duration in seconds (default: 600 = 10 min)")
    parser.add_argument("--bitrate", default="128k", help="MP3 bitrate (default: 128k)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    basename = os.path.basename(args.input)
    name, _ = os.path.splitext(basename)
    output_dir = os.path.expanduser("~/Downloads")

    duration = get_duration(args.input)
    total_chunks = int(duration / args.chunk) + (1 if duration % args.chunk else 0)

    print(f"Input:    {args.input}")
    print(f"Duration: {int(duration // 60)}m {int(duration % 60)}s")
    print(f"Chunks:   {total_chunks} x {args.chunk // 60} min")
    print()

    for i in range(total_chunks):
        start = i * args.chunk
        output_path = os.path.join(output_dir, f"{name}_part{i+1:02d}.mp3")

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", args.input,
            "-t", str(args.chunk),
            "-map_metadata", "-1",
            "-fflags", "+bitexact",
            "-flags:a", "+bitexact",
            "-vn",                        # drop video
            "-acodec", "libmp3lame",
            "-b:a", args.bitrate,
            "-metadata:s:a", "handler_name=",
            "-metadata:s:a", "vendor_id=",
            output_path
        ]

        print(f"[{i+1}/{total_chunks}] {os.path.basename(output_path)} (start {int(start//60)}m{int(start%60):02d}s)")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  Error: {result.stderr[-300:]}")
            sys.exit(1)

        size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  Done — {size:.1f} MB -> {output_path}")

    print(f"\nAll {total_chunks} parts saved to {output_dir}")


if __name__ == "__main__":
    main()
