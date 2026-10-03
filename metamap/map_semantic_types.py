"""
Replace biomedical phrases in the medicine text with their UMLS semantic types,
using MetaMap's output, so that similar concepts collapse into one label.

Example:
    "... include diarrhea, nausea, ..."  ->  "... include [[Sign or Symptom]] ..."

For every MetaMap output file <name>.out in --metamap-dir, the script reads the
matching original text <name>.txt from --text-dir and writes:

    <out-dir>/cid_output_<name>.txt      text with phrases replaced by semantic types
    <out-dir>/concept_table_<name>.csv   the phrase -> CUI -> semantic type table used

Only mappings with a MetaMap score of 1000 (exact matches) are used.

Usage:
    python metamap/map_semantic_types.py --metamap-dir data/sample \
        --text-dir data/sample --out-dir outputs/sample
"""

import argparse
import os
from itertools import permutations

from parse_metamap import SCORE_1000, parse_metamap_output

# A phrase is only replaced when it is surrounded by one of these characters,
# so that e.g. "nausea" is replaced but "nauseating" is not.
DELIMITERS = [" ", ".", ",", ";"]
DELIMITER_PAIRS = [(p[0], p[1]) for p in permutations(DELIMITERS)]


def build_concept_table(metamap_file):
    df = parse_metamap_output(metamap_file, line_pattern=SCORE_1000)
    df = df[df["Phrase"].map(len) > 1].copy()  # skip single-character matches

    df["lower_Phrase"] = df["Phrase"].str.lower()
    df = df.drop_duplicates().reset_index(drop=True)

    # A phrase can map to several concepts; collect all of its semantic types
    concept_dict = {}
    for _, row in df.iterrows():
        ph, cat = row["lower_Phrase"], row["Category"]
        if ph not in concept_dict:
            concept_dict[ph] = f"[{cat}]"
        else:
            concept_dict[ph] += f", [{cat}]"

    df["all_categories"] = df["lower_Phrase"].map(concept_dict)
    return df


def replace_phrases(text, concept_table):
    for i in range(len(concept_table)):
        phrase = concept_table["Phrase"][i]
        label = " [" + concept_table["all_categories"][i] + "] "
        for left, right in DELIMITER_PAIRS:
            text = text.replace(left + phrase + right, label)
    return text


def main():
    parser = argparse.ArgumentParser(description="Tag medicine text with UMLS semantic types")
    parser.add_argument("--metamap-dir", required=True, help="folder with MetaMap .out files")
    parser.add_argument("--text-dir", required=True, help="folder with the original .txt files")
    parser.add_argument("--out-dir", required=True, help="where to write results")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    out_files = sorted(f for f in os.listdir(args.metamap_dir) if f.endswith(".out"))

    for name in out_files:
        base = name[: -len(".out")]
        print(f"Processing {name}")

        table = build_concept_table(os.path.join(args.metamap_dir, name))
        table.to_csv(os.path.join(args.out_dir, f"concept_table_{base}.csv"))
        print(f"  {len(table)} phrase-concept mappings")

        with open(os.path.join(args.text_dir, base + ".txt"), "r", encoding="utf-8") as f:
            text = f.read()

        with open(os.path.join(args.out_dir, f"cid_output_{base}.txt"), "w", encoding="utf-8") as f:
            f.write(replace_phrases(text, table))
        print(f"  wrote cid_output_{base}.txt")


if __name__ == "__main__":
    main()
