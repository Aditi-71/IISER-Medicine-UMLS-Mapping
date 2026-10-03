"""
Scrape medicine information from Tata 1mg (https://www.1mg.com/drugs-all-medicines).

For each starting letter, the script walks through every listing page, opens each
medicine's page with a headless Chrome browser (Selenium), parses it with
BeautifulSoup, and saves one CSV per listing page:

    <out-dir>/page_<letter>/page_<n>.csv

Fields collected include: Name, Marketer, Salt composition, Storage,
Chemical Class, Habit Forming, Therapeutic Class, Action Class and the
Product introduction (description).

Usage examples
--------------
    # scrape every letter A-Z
    python scraping/scrape_1mg.py

    # scrape only letter 'f', resuming from listing page 19
    python scraping/scrape_1mg.py --letters f --start-page 19

Note: the CSS class names below match the 1mg website as of mid-2024.
Websites change their markup often, so these selectors may need updating.
"""

import argparse
import multiprocessing as mp
import os
import string
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

BASE_URL = "https://www.1mg.com"
LISTING_URL = BASE_URL + "/drugs-all-medicines?page={page}&label={letter}"
MAX_ATTEMPTS = 10

# One browser per process, created lazily so each worker process gets its own.
_browser = None


def get_browser():
    global _browser
    if _browser is None:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        _browser = webdriver.Chrome(options=chrome_options)
    return _browser


def get_html_content(url):
    """Load a page in the headless browser and return its HTML (retries on failure)."""
    browser = get_browser()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            browser.get(url)
            return browser.page_source
        except Exception as e:  # network hiccups, timeouts, etc.
            print(f"Attempt {attempt} failed for {url}: {e}")
            time.sleep(2)
    return None


def get_medicine_names_and_links(listing_url):
    """Return a list of (name, link) tuples from one listing page."""
    html_content = get_html_content(listing_url)
    if html_content is None:
        return []

    soup = BeautifulSoup(html_content, "lxml")
    product_containers = soup.find_all(
        "div",
        class_="style__product-card___1gbex style__card___3eL67 style__raised___3MFEA "
        "style__white-bg___10nDR style__overflow-hidden___2maTX",
    )

    medicines = []
    for container in product_containers:
        name_tag = container.find("a")
        if name_tag:
            medicines.append((name_tag.text, BASE_URL + name_tag["href"]))
    return medicines


def get_medicine_details(medicine_url):
    """Parse a single medicine page into a {field: [value]} dict."""
    html_content = get_html_content(medicine_url)
    if html_content is None:
        return None

    soup = BeautifulSoup(html_content, "lxml")

    # Header box: Marketer, Salt composition
    top_box_keys = soup.find_all("div", class_="DrugHeader__meta-title___22zXC")
    top_val = [soup.find("div", class_="DrugHeader__meta-value___vqYM0")]
    top_box_vals = soup.find_all("div", class_="saltInfo DrugHeader__meta-value___vqYM0")

    # Fact box: Storage, Chemical Class, Habit Forming, Therapeutic Class, Action Class
    bottom_box_keys = soup.find_all(
        "div", class_="DrugFactBox__col-left___znwNB DrugFactBox__black___5cVbb"
    )
    bottom_box_vals = soup.find_all(
        "div",
        class_="DrugFactBox__col-right___36e1P DrugFactBox__black___5cVbb DrugFactBox__bold___1fqoO",
    )

    # Product introduction (description)
    product_intro_key = [soup.find("h2", class_="DrugOverview__title___1OwgG")]
    product_intro_val = [soup.find("div", class_="DrugOverview__content___22ZBX")]

    keys = top_box_keys + bottom_box_keys + product_intro_key
    values = top_val + top_box_vals + bottom_box_vals + product_intro_val

    details = {}
    for key, value in zip(keys, values):
        if key is not None and value is not None:
            details[key.text] = [value.text]
    return details


def get_max_page_idx(letter):
    """Find how many listing pages exist for a letter."""
    html_content = get_html_content(LISTING_URL.format(page=1, letter=letter))
    soup = BeautifulSoup(html_content, "lxml")
    page_links = soup.find_all("a", class_="button-text link-page")
    return int(page_links[-1].text.strip())


def process_medicine(medicine):
    name, link = medicine
    name = name.split("MRP")[0]  # the card text also contains the price
    details = get_medicine_details(link)
    if details is None:
        return None
    details["Name"] = [name]
    return pd.DataFrame.from_dict(details)


def get_df_per_page(listing_url, num_workers):
    medicines = [m for m in get_medicine_names_and_links(listing_url) if m is not None]
    print(f"Page has {len(medicines)} medicines")

    start = time.time()
    with mp.Pool(processes=num_workers) as pool:
        results = list(
            tqdm(pool.imap_unordered(process_medicine, medicines), total=len(medicines))
        )
    print(f"took {time.time() - start:.1f} sec")

    results = [r for r in results if r is not None]
    if not results:
        return None
    df = pd.concat(results, ignore_index=True)
    df.insert(0, "Name", df.pop("Name"))
    return df


def main():
    parser = argparse.ArgumentParser(description="Scrape medicine data from Tata 1mg")
    parser.add_argument("--letters", default=string.ascii_lowercase,
                        help="letters to scrape, e.g. 'abc' (default: a-z)")
    parser.add_argument("--start-page", type=int, default=1,
                        help="listing page to start from (useful for resuming)")
    parser.add_argument("--out-dir", default="data/raw",
                        help="where to save page CSVs (default: data/raw)")
    parser.add_argument("--workers", type=int, default=1,
                        help="number of parallel browser processes (default: 1)")
    args = parser.parse_args()

    for letter in args.letters.lower():
        print(f"Extracting letter: {letter}")
        max_page = get_max_page_idx(letter)
        print(f"'{letter}' has {max_page} pages")

        letter_dir = os.path.join(args.out_dir, f"page_{letter}")
        os.makedirs(letter_dir, exist_ok=True)

        for page in range(args.start_page, max_page + 1):
            print(f"Extracting page {page}")
            df = get_df_per_page(LISTING_URL.format(page=page, letter=letter), args.workers)
            if df is not None:
                df.to_csv(os.path.join(letter_dir, f"page_{page}.csv"), index=False)


if __name__ == "__main__":
    main()
