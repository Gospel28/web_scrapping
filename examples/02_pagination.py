"""
Example 2 — Pagination: scrape multiple pages

Site: quotes.toscrape.com (pages 1-5)
Goal: loop through pages, scrape each, combine into one CSV.

Run with:
    uv run python examples/02_pagination.py

The pattern: most sites encode page numbers in the URL.
    page 1 → /          (or /page/1/)
    page 2 → /page/2/
    page 3 → /page/3/
    ...

So the loop is: change the URL, scrape, sleep, repeat.

CRITICAL: time.sleep(1) between requests. Without it, you get banned.
"""

import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm


def scrape_page(page_number: int) -> list[dict]:
    """Scrape one page and return a list of quote dicts."""
    url = f"https://quotes.toscrape.com/page/{page_number}/"
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "lxml")

    rows = []
    for q in soup.find_all("div", class_="quote"):
        rows.append({
            "page": page_number,
            "text": q.find("span", class_="text").get_text(strip=True),
            "author": q.find("small", class_="author").get_text(strip=True),
        })
    return rows


def main():
    all_quotes = []

    for page in tqdm(range(1, 6), desc="Scraping pages"):
        page_rows = scrape_page(page)
        all_quotes.extend(page_rows)
        time.sleep(1)  # BE POLITE — 1 second between requests

    df = pd.DataFrame(all_quotes)
    output_path = "data/raw/quotes_all_pages.csv"
    df.to_csv(output_path, index=False)
    print(f"\nTotal quotes scraped: {len(df)}")
    print(f"Saved to {output_path}")
    print("\nQuotes per page:")
    print(df["page"].value_counts().sort_index())


if __name__ == "__main__":
    main()
