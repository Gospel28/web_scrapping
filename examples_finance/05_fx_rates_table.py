"""
Example F5 — RBI: scrape reference exchange rates from a public page

Source: investing.com or RBI public exchange rate page (HTML)
Goal:   demonstrate scraping a structured HTML table of FX rates and
        converting it to a clean DataFrame.

Run with:
    uv run python examples_finance/05_fx_rates_table.py

Why this example?
Many central banks and financial sites publish daily/weekly rates as
HTML tables, NOT APIs. pandas.read_html handles these directly.
We use a publicly accessible exchange rate listing here.

Note: site structures change. If this fails, the lesson is exactly what
we taught — scrapers are maintenance contracts. Open the page, inspect,
adjust the table index. That IS the skill.
"""

import requests
import pandas as pd
import io


# A public source of cross-currency rates that publishes data as HTML tables
# Using x-rates.com which has been stable for many years
URL = "https://www.x-rates.com/table/?from=USD&amount=1"


def main():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(f"Fetching FX rates from: {URL}")
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Status: {resp.status_code}")

    # Parse all HTML tables on the page
    tables = pd.read_html(io.StringIO(resp.text))
    print(f"Tables found: {len(tables)}")
    for i, t in enumerate(tables):
        print(f"  Table {i}: shape {t.shape}, columns {list(t.columns)}")

    # The cross-rate table is the largest one
    largest = max(range(len(tables)), key=lambda i: tables[i].shape[0])
    df = tables[largest]
    print(f"\nUsing table {largest}: {df.shape}")
    print(df.head(10))

    output_path = "data/raw/fx_rates_usd.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
