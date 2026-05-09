"""
Example F4 — Wikipedia: scrape index constituents (S&P 500, Nifty 50)

Source: Wikipedia
Goal:   get the current list of stocks in major indices for analysis.

Run with:
    uv run python examples_finance/04_wikipedia_index_constituents.py

Why this example?
Wikipedia maintains constantly-updated tables of index constituents.
For Nifty 50, S&P 500, FTSE 100, DAX — all kept current, all free, no
API. pandas.read_html turns these into DataFrames in two lines.

This is the easiest way to get a starting universe of tickers for any
quantitative study. Pair this with Example F2 to download price history
for all of them.
"""

import pandas as pd


SOURCES = {
    "SP500":   "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    "Nifty50": "https://en.wikipedia.org/wiki/NIFTY_50",
    "DowJones": "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average",
}


def fetch_index(name: str, url: str) -> pd.DataFrame:
    """Read all tables from a Wikipedia page; return the most likely constituents table."""
    print(f"\n--- {name} ---")
    print(f"URL: {url}")

    # pandas.read_html parses every table on the page
    tables = pd.read_html(url)
    print(f"Tables found: {len(tables)}")

    # Heuristic: the constituents table is usually one of the larger tables
    # with a 'Symbol' or 'Ticker' or 'Company' column
    for i, t in enumerate(tables):
        cols_lower = [str(c).lower() for c in t.columns]
        if any(k in " ".join(cols_lower) for k in ["symbol", "ticker", "company"]):
            if t.shape[0] >= 10:  # avoid tiny header tables
                print(f"Picked table {i}: shape {t.shape}, columns {list(t.columns)[:5]}")
                return t

    # Fallback: largest table
    largest = max(range(len(tables)), key=lambda i: tables[i].shape[0])
    print(f"Fallback to largest table {largest}: shape {tables[largest].shape}")
    return tables[largest]


def main():
    for name, url in SOURCES.items():
        try:
            df = fetch_index(name, url)
            output_path = f"data/raw/index_{name.lower()}_constituents.csv"
            df.to_csv(output_path, index=False)
            print(f"Saved {len(df)} rows to {output_path}")
            print(df.head(3))
        except Exception as e:
            print(f"Failed for {name}: {e}")


if __name__ == "__main__":
    main()
