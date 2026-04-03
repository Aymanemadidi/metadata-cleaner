#!/usr/bin/env python3
import argparse
import os
import sys
import pikepdf


def strip_pdf(input_path, output_path):
    with pikepdf.open(input_path) as pdf:
        if '/Info' in pdf.trailer:
            del pdf.trailer['/Info']

        try:
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                for key in list(meta.keys()):
                    del meta[key]
        except Exception:
            pass

        if '/Metadata' in pdf.Root:
            del pdf.Root['/Metadata']

        pdf.save(output_path, fix_metadata_version=False)


def main():
    parser = argparse.ArgumentParser(description="Strip metadata from PDF files")
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument("-o", "--output", help="Output file path (default: <name>_clean.pdf)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    if not args.input.lower().endswith(".pdf"):
        print("Error: input file must be a PDF")
        sys.exit(1)

    if not args.output:
        basename = os.path.basename(args.input)
        name, _ = os.path.splitext(basename)
        args.output = os.path.join(os.path.expanduser("~/Downloads"), f"{name}_clean.pdf")

    print(f"Processing: {args.input}")
    strip_pdf(args.input, args.output)

    input_size = os.path.getsize(args.input) / (1024 * 1024)
    output_size = os.path.getsize(args.output) / (1024 * 1024)
    print(f"Done: {args.output}")
    print(f"Size: {input_size:.1f} MB -> {output_size:.1f} MB")


if __name__ == "__main__":
    main()
