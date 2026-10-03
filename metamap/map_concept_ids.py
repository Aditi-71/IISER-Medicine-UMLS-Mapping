"""
Alternative to map_semantic_types.py: replace biomedical phrases with their
UMLS Concept Unique Identifier (CUI) instead of their semantic type.

Example:
    "Clarithromycin (500mg)"  ->  " C0055856  (500mg)"

Only concepts whose semantic type is in SEMANTIC_TYPES below are replaced.

Usage:
    python metamap/map_concept_ids.py --metamap-dir data/sample \
        --text-dir data/sample --out-dir outputs/sample
"""

import argparse
import os

from parse_metamap import SCORE_ANY, parse_metamap_output

SEMANTIC_TYPES = [
    "Amino Acid, Peptide, or Protein",
    "Biologically Active Substance",
    "Biologic Function",
    "Chemical",
    "Chemical Viewed Functionally",
    "Chemical Viewed Structurally",
    "Clinical Drug",
    "Drug Delivery Device",
    "Disease or Syndrome",
    "Health Care Activity",
    "Immunologic Factor",
    "Molecular Function",
    "Nucleic Acid, Nucleoside, or Nucleotide",
    "Organic Chemical",
    "Pharmacologic Substance",
    "Organic Chemical,Pharmacologic Substance",
    "Plant",
    "Vitamin",
]


def main():
    parser = argparse.ArgumentParser(description="Replace biomedical phrases with UMLS CUIs")
    parser.add_argument("--metamap-dir", required=True, help="folder with MetaMap .out files")
    parser.add_argument("--text-dir", required=True, help="folder with the original .txt files")
    parser.add_argument("--out-dir", required=True, help="where to write results")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    out_files = sorted(f for f in os.listdir(args.metamap_dir) if f.endswith(".out"))

    for name in out_files:
        base = name[: -len(".out")]
        print(f"Processing {name}")

        df = parse_metamap_output(
            os.path.join(args.metamap_dir, name),
            line_pattern=SCORE_ANY,
            semantic_types=SEMANTIC_TYPES,
            strip=False,
        )
        df = df[df["Phrase"].map(len) > 1].reset_index(drop=True)
        print(f"  {len(df)} phrase-concept mappings")

        with open(os.path.join(args.text_dir, base + ".txt"), "r", encoding="utf-8") as f:
            text = f.read()

        for phrase, cid in zip(df["Phrase"], df["CID"]):
            text = text.replace(phrase, " " + cid + " ")

        with open(os.path.join(args.out_dir, f"cui_output_{base}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  wrote cui_output_{base}.txt")


if __name__ == "__main__":
    main()
