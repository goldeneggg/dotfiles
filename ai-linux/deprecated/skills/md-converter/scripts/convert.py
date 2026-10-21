#!/usr/bin/env python3
"""Convert various text formats to Markdown using pandoc.

Supported input formats: html, rst, asciidoc (and any format pandoc supports)
Output format: GitHub Flavored Markdown (gfm)

Usage:
  python3 convert.py <input_file> [--from FORMAT] [--output OUTPUT_FILE]
  echo "content" | python3 convert.py - [--from FORMAT] [--output OUTPUT_FILE]
"""

import argparse
import subprocess
import sys


def detect_format(file_path: str) -> str | None:
    """Detect format from file extension."""
    ext_map = {
        ".html": "html",
        ".htm": "html",
        ".rst": "rst",
        ".adoc": "asciidoc",
        ".asciidoc": "asciidoc",
        ".asc": "asciidoc",
    }
    if file_path == "-":
        return None
    suffix = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ""
    return ext_map.get(suffix.lower())


def convert(input_path: str, from_format: str | None = None, output_path: str | None = None) -> str:
    """Convert a file to Markdown using pandoc.

    Args:
        input_path: Path to input file or "-" for stdin
        from_format: Input format (html/rst/asciidoc). Auto-detected if None.
        output_path: Path to save output. Returns string if None.

    Returns:
        Converted markdown content (if output_path is None)
    """
    cmd = ["pandoc", "--to=gfm"]

    if from_format:
        cmd.append(f"--from={from_format}")
    elif input_path != "-":
        detected = detect_format(input_path)
        if detected:
            cmd.append(f"--from={detected}")

    if output_path:
        cmd.extend(["--output", output_path])

    cmd.append(input_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)

    if not output_path:
        return result.stdout
    return ""


def main():
    parser = argparse.ArgumentParser(description="Convert text formats to Markdown")
    parser.add_argument("input", help="Input file path or '-' for stdin")
    parser.add_argument("--from", dest="from_format", help="Input format (html/rst/asciidoc/etc.)")
    parser.add_argument("--output", "-o", help="Output file path (prints to stdout if omitted)")
    args = parser.parse_args()

    result = convert(args.input, args.from_format, args.output)
    if result:
        print(result, end="")


if __name__ == "__main__":
    main()
