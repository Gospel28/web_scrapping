"""
Example F3 — EIA: scrape weekly US crude oil inventory

Source: U.S. Energy Information Administration (EIA) public data
Goal:   download weekly crude oil ending stocks (excl. SPR) directly from
        EIA's published CSV, save to local file.

Run with:
    uv run python examples_finance/03_eia_crude_inventory.py

Why this example?
EIA publishes hundreds of energy series as CSV/Excel files at fixed URLs.
No API key needed if you go straight to the data file. This is a hidden
goldmine — most researchers reach for the EIA API and miss the bulk files.

What we're downloading:
    Weekly U.S. Ending Stocks of Crude Oil (excl. SPR), thousand barrels
    Series: WCESTUS1
    URL: a static CSV that EIA refreshes every Wednesday

This series correlates with WTI prices and is a key input for any
oil supply/demand model.
"""

import io
import requests
import pandas as pd


# EIA publishes series as CSV at predictable URLs
# Format: https://www.eia.gov/dnav/pet/hist_xls/<SERIES>w.htm — but for
# direct CSV you can use their API endpoint without a key for many series.
# Here we use the public CSV download for weekly crude stocks.
URL = "https://www.eia.gov/dnav/pet/hist_xls/WCESTUS1w.htm"


def main():
    # EIA serves both HTML pages and direct CSV/Excel. The pattern below
    # uses pandas.read_html, which handles their HTML tables natively.
    print(f"Fetching crude oil inventory from EIA: {URL}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"Status: {resp.status_code} | Length: {len(resp.text)} chars")

    # pandas.read_html parses ALL tables on the page into a list of DataFrames
    tables = pd.read_html(io.StringIO(resp.text))
    print(f"Tables found on page: {len(tables)}")

    # The data table is usually the largest one
    sizes = [(i, t.shape) for i, t in enumerate(tables)]
    print(f"Table sizes: {sizes}")

    # Take the largest table by row count
    largest_idx = max(range(len(tables)), key=lambda i: tables[i].shape[0])
    df = tables[largest_idx]
    print(f"\nUsing table {largest_idx} with shape {df.shape}")
    print("\nFirst 5 rows:")
    print(df.head())

    output_path = "data/raw/eia_crude_inventory_weekly.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
