"""
Example 1 — Beginner: scrape a single page

Site: quotes.toscrape.com
Goal: extract quotes, authors, and tags from page 1 and save to CSV.

Run with:
    uv run python examples/01_quotes_basic.py

This is the 4-step pattern every scraper follows:
    1. FETCH — download the HTML
    2. PARSE — turn HTML into a searchable tree
    3. FIND  — pick out the bits you want
    4. SAVE  — write to CSV
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd


def main():
    # 1. FETCH
    url = "https://quotes.toscrape.com/"
    response = requests.get(url, timeout=30)
    print(f"Status: {response.status_code}")  # 200 = OK

    # 2. PARSE
    soup = BeautifulSoup(response.text, "lxml")

    # 3. FIND — each quote sits inside <div class="quote">
    quote_blocks = soup.find_all("div", class_="quote")
    print(f"Found {len(quote_blocks)} quotes on this page\n")

    results = []
    for q in quote_blocks:
        text = q.find("span", class_="text").get_text(strip=True)
        author = q.find("small", class_="author").get_text(strip=True)
        tags = [t.get_text(strip=True) for t in q.find_all("a", class_="tag")]
        results.append({
            "text": text,
            "author": author,
            "tags": ", ".join(tags),
        })

    # 4. SAVE
    df = pd.DataFrame(results)
    output_path = "data/raw/quotes_page1.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")
    print("\nFirst 3 rows:")
    print(df.head(3))


if __name__ == "__main__":
    main()
