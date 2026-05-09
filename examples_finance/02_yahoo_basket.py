"""
Example F2 — Yahoo Finance: compare multiple energy tickers

Source: Yahoo Finance
Goal:   download closing prices for multiple energy assets, align on
        date, save one tidy CSV for analysis.

Run with:
    uv run python examples_finance/02_yahoo_basket.py

Why this example?
Real research rarely uses one ticker. You usually want a basket — WTI,
Brent, natural gas, energy stocks — to study spreads, correlations, and
co-movement. yfinance can fetch them in one call.
"""

import yfinance as yf
import pandas as pd


# Energy basket — feel free to add/remove tickers
TICKERS = {
    "WTI":     "CL=F",
    "Brent":   "BZ=F",
    "NatGas":  "NG=F",
    "ONGC":    "ONGC.NS",
    "Reliance": "RELIANCE.NS",
    "ExxonMobil": "XOM",
    "Chevron":  "CVX",
}


def main():
    start = "2022-01-01"
    end = "2024-12-31"

    print(f"Fetching {len(TICKERS)} tickers from {start} to {end}...")

    # yfinance accepts a space-separated string of tickers
    symbols = " ".join(TICKERS.values())
    raw = yf.download(symbols, start=start, end=end, progress=False)

    # Keep only adjusted close — that's what you typically want for analysis
    closes = raw["Close"]

    # Rename columns from tickers to friendly names
    name_map = {v: k for k, v in TICKERS.items()}
    closes = closes.rename(columns=name_map)

    print(f"\nShape: {closes.shape}")
    print(f"Date range: {closes.index.min().date()} → {closes.index.max().date()}")
    print(f"\nMissing values per column:\n{closes.isna().sum()}")

    output_path = "data/raw/energy_basket_closes.csv"
    closes.to_csv(output_path)
    print(f"\nSaved to {output_path}")

    # Quick correlation matrix — useful sanity check for energy research
    print("\nDaily return correlations:")
    returns = closes.pct_change().dropna()
    print(returns.corr().round(2))


if __name__ == "__main__":
    main()
