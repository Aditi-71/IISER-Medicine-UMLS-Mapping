"""
Split a large text file into smaller chunks (default 500 lines each) so MetaMap
can process them one at a time, and combine chunks back into one file afterwards.

Usage:
    python preprocessing/split_file.py split   data/all_medicines.txt chunks/
    python preprocessing/split_file.py combine chunks/ combined.txt
"""

import argparse
import os


def split_file(input_file, output_dir, lines_per_file=500):
    os.makedirs(output_dir, exist_ok=True)
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    file_index = 0
    for i in range(0, len(lines), lines_per_file):
        out_path = os.path.join(output_dir, f"file_{file_index}.txt")
        with open(out_path, "w", encoding="utf-8") as out:
            out.writelines(lines[i:i + lines_per_file])
        file_index += 1
    print(f"Wrote {file_index} files to {output_dir}")


def combine_files(input_dir, output_file):
    # sort numerically so file_10 comes after file_9
    files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    files.sort(key=lambda name: int("".join(ch for ch in name if ch.isdigit()) or 0))

    with open(output_file, "w", encoding="utf-8") as out:
        for name in files:
            with open(os.path.join(input_dir, name), "r", encoding="utf-8") as f:
                out.write(f.read())
    print(f"Combined {len(files)} files into {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Split or combine text files")
    sub = parser.add_subparsers(dest="command", required=True)

    p_split = sub.add_parser("split", help="split one file into chunks")
    p_split.add_argument("input_file")
    p_split.add_argument("output_dir")
    p_split.add_argument("--lines", type=int, default=500, help="lines per chunk (default 500)")

    p_combine = sub.add_parser("combine", help="combine chunks into one file")
    p_combine.add_argument("input_dir")
    p_combine.add_argument("output_file")

    args = parser.parse_args()
    if args.command == "split":
        split_file(args.input_file, args.output_dir, args.lines)
    else:
        combine_files(args.input_dir, args.output_file)


if __name__ == "__main__":
    main()
