"""
Combine all scraped page CSVs (page_a/page_1.csv ... page_z/page_N.csv) into one dataset.

Duplicate rows (e.g. from re-scraped pages) and rows without a "Product introduction" (description) are dropped, since that text
is what gets passed to MetaMap later.

Usage:
    python preprocessing/combine_pages.py --in-dir data/raw --out data/all_medicines.csv
"""

import argparse
import glob
import os
import string

import pandas as pd

# Columns kept in the final dataset (any that are missing are simply skipped)
COLUMNS = [
    "Name",
    "Marketer",
    "SALT COMPOSITION",
    "Storage",
    "Chemical Class",
    "Habit Forming",
    "Therapeutic Class",
    "Action Class",
    "Product introduction",
]


def main():
    parser = argparse.ArgumentParser(description="Combine scraped page CSVs into one file")
    parser.add_argument("--in-dir", default="data/raw", help="folder containing page_a ... page_z")
    parser.add_argument("--out", default="data/all_medicines.csv", help="output CSV path")
    args = parser.parse_args()

    frames = []
    for letter in string.ascii_lowercase:
        folder = os.path.join(args.in_dir, f"page_{letter}")
        for csv_file in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            frames.append(pd.read_csv(csv_file))

    if not frames:
        raise SystemExit(f"No CSV files found under {args.in_dir}")

    df = pd.concat(frames, ignore_index=True)
    df = df[[c for c in COLUMNS if c in df.columns]]
    print(f"Combined rows: {len(df)}")

    df = df.drop_duplicates()
    print(f"After removing duplicates: {len(df)}")

    df = df[df["Product introduction"].notna()]
    print(f"Rows with a description: {len(df)}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
