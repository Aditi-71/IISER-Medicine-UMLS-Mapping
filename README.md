# Medicine Data Scraping and UMLS Concept Mapping

Summer research internship project at **IISER Bhopal**, under the supervision of **Dr. Tanmay Basu** (May–July 2024).

The project builds a structured dataset of medicines from the [Tata 1mg](https://www.1mg.com/drugs-all-medicines) website and normalizes the biomedical text in it using **MetaMap** and the **UMLS Metathesaurus**, so that different words for the same concept (for example *"Macrolides"* and *"macrolide antibiotic"*) map to a single standard identifier.

## Pipeline

```
 1mg website ──► scraping ──► page CSVs ──► combine ──► split into chunks ──► MetaMap ──► concept mapping
               (Selenium +                 (one big    (500 lines each)       (UMLS)     (semantic types
               BeautifulSoup)               dataset)                                     or CUIs)
```

1. **Web scraping** (`scraping/scrape_1mg.py`): goes through the alphabetical medicine listings on 1mg and opens each medicine's page in a headless Chrome browser (Selenium). It parses the page with BeautifulSoup and records the name, marketer, salt composition, storage, chemical class, therapeutic class, action class, habit-forming status, and product description.
2. **Combining** (`preprocessing/combine_pages.py`): merges all page CSVs into one dataset and removes duplicate rows and medicines with no description.
3. **Splitting** (`preprocessing/split_file.py`): breaks the dataset into 500-line text files so MetaMap can process them in manageable pieces.
4. **MetaMap**: each text file is run through [MetaMap](https://lhncbc.nlm.nih.gov/ii/tools/MetaMap.html), which identifies biomedical phrases and maps them to UMLS concepts (CUI + semantic type + confidence score).
5. **Concept mapping** (`metamap/`): parses the MetaMap output and rewrites the original text so that each recognized phrase is replaced by its UMLS semantic type (`map_semantic_types.py`) or its Concept Unique Identifier (`map_concept_ids.py`).

## Dataset

The scraped dataset contains **125,692 unique medicines** with descriptions, covering all letters A–Z. Each record has these fields:

| Field | Example |
|---|---|
| Name | Avastin 100mg Injection |
| Marketer | Roche Products India Pvt Ltd |
| SALT COMPOSITION | Bevacizumab (100mg) |
| Storage | Store in a refrigerator (2 - 8°C). Do not freeze. |
| Chemical Class | Monoclonal antibody (mAb) |
| Habit Forming | No |
| Therapeutic Class | ANTI NEOPLASTICS |
| Action Class | Vascular endothelial growth factor (VEGF) inhibitor |
| Product introduction | Avastin 100mg Injection is an anticancer medication... |

The full dataset is not included in this repository (see [Data availability](#data-availability)). Small samples are in `data/sample/`.

## Example output

MetaMap maps phrases to UMLS concepts. A few rows from the concept table:

| Phrase | CUI | Semantic type |
|---|---|---|
| CLARITHROMYCIN | C0055856 | Antibiotic, Organic Chemical |
| Macrolides | C0003240 | Antibiotic, Organic Chemical |
| Anti-Infectives | C0003204 | Pharmacologic Substance |

The text is then rewritten with those labels:

```
Before: ...side effects with this medicine include diarrhea, nausea, abnormal taste, indigestion...
After:  ...side effects with this medicine include diarrhea, nausea, [[Sign or Symptom]]  indigestion...
```

## Repository structure

```
├── scraping/
│   └── scrape_1mg.py              # Selenium + BeautifulSoup scraper
├── preprocessing/
│   ├── combine_pages.py           # merge page CSVs into one dataset
│   └── split_file.py              # split/combine text files for MetaMap
├── metamap/
│   ├── parse_metamap.py           # parser for MetaMap output files
│   ├── map_semantic_types.py      # replace phrases with UMLS semantic types
│   └── map_concept_ids.py         # replace phrases with UMLS CUIs
├── data/sample/                   # small samples of scraped data and MetaMap output
├── outputs/sample/                # results of running the mapping scripts on the samples
└── requirements.txt
```

## Setup

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
pip install -r requirements.txt
```

The scraper also needs Google Chrome installed (Selenium 4 downloads a matching driver automatically).

MetaMap must be installed separately. It requires a free [UMLS license](https://uts.nlm.nih.gov/uts/signup-login) from the U.S. National Library of Medicine.

## Usage

```bash
# 1. Scrape (all letters, or pick some with --letters)
python scraping/scrape_1mg.py --letters abc --out-dir data/raw

# 2. Combine page CSVs into one dataset
python preprocessing/combine_pages.py --in-dir data/raw --out data/all_medicines.csv

# 3. Split into 500-line chunks for MetaMap
python preprocessing/split_file.py split data/all_medicines.csv data/chunks/

# 4. Run MetaMap on each chunk (example; adjust options to your MetaMap install)
metamap -I data/chunks/file_0.txt data/metamap_out/file_0.out

# 5. Map phrases to UMLS semantic types (or use map_concept_ids.py for CUIs)
python metamap/map_semantic_types.py --metamap-dir data/metamap_out \
    --text-dir data/chunks --out-dir outputs/
```

To try step 5 right away on the included sample:

```bash
python metamap/map_semantic_types.py --metamap-dir data/sample --text-dir data/sample --out-dir outputs/sample
```

## Known limitations

- The scraper relies on 1mg's CSS class names as of mid-2024. If the website's layout changes, the selectors in `scrape_1mg.py` need updating.
- Phrase replacement uses plain string matching on the MetaMap phrases, so a common word that happens to match a UMLS concept can be replaced too. Filtering by semantic type (as `map_concept_ids.py` does) reduces this.

## Data availability

The full scraped dataset and MetaMap outputs are not published here. The medicine descriptions belong to Tata 1mg, and MetaMap output contains UMLS Metathesaurus content, which is covered by the UMLS license. Only small samples are included for demonstration.

## Acknowledgements

I thank Dr. Tanmay Basu, IISER Bhopal, for his guidance during this internship.

**Author:** Aditi Biswas, KIIT
