"""
Parse MetaMap's human-readable output (.out) into a table of
(UMLS Concept ID, matched phrase, semantic type).

A typical MetaMap line looks like:

    1000   C0055856:CLARITHROMYCIN (clarithromycin) [Antibiotic,Organic Chemical]
    score  CUI      matched text     preferred name   semantic type(s)
"""

import re

import pandas as pd

# Only keep mappings with a perfect MetaMap score of 1000
SCORE_1000 = r"(.+?)(\b1000\b)([ ]+)([C])([0-9]+)(:)(.+)"

# Keep any mapping line (the score part is optional in this pattern)
SCORE_ANY = r"(.+?)(\b[7-9][0-9][0-9]|\b)([ ]+)([C])([0-9]+)(:)(.+)"


def parse_metamap_output(path, line_pattern=SCORE_1000, semantic_types=None, strip=True):
    """
    Read a MetaMap .out file and return a DataFrame with columns CID, Phrase, Category.

    line_pattern   regex deciding which mapping lines to keep (see SCORE_1000 / SCORE_ANY)
    semantic_types optional list; if given, only these semantic types are kept
    strip          strip surrounding whitespace from phrase and category
    """
    rows = {"CID": [], "Phrase": [], "Category": []}

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip("\n")
        result = re.search(line_pattern, line)
        if not result:
            continue

        match = result.group(0)
        phrase = re.search(r"(\:)([a-zA-Z, a-zA-Z]+(?:-[a-zA-Z, a-zA-Z]+)?)", match)
        sem_type = re.search(r"(\[)([a-zA-Z, ]+)(\])", match)
        if not sem_type:
            continue
        if semantic_types is not None and sem_type.group(2) not in semantic_types:
            continue

        cid_match = re.search(r"([C])([0-9]+)(:)", match)
        if cid_match and phrase is not None:
            p, c = phrase.group(2), sem_type.group(2)
            rows["CID"].append(cid_match.group(1) + cid_match.group(2))
            rows["Phrase"].append(p.strip() if strip else p)
            rows["Category"].append(c.strip() if strip else c)

    return pd.DataFrame(rows)
