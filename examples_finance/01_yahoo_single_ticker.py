"""
Example F1 — Yahoo Finance: download stock or commodity price history

Source: Yahoo Finance (via yfinance library — wraps Yahoo's hidden API)
Goal:   download daily OHLCV data for a ticker, save to CSV.

Run with:
    uv run python examples_finance/01_yahoo_single_ticker.py

Why this example?
This is the cleanest entry point to financial data. yfinance handles all
the scraping for you — no API key, no auth, no rate limiting headaches.
Works for stocks, ETFs, indices, FX, commodities, crypto.

Useful tickers for energy & finance research:
    Crude oil futures:   CL=F        (WTI)         BZ=F   (Brent)
    Natural gas:         NG=F
    Gold:                GC=F
    S&P 500:             ^GSPC
    Nifty 50:            ^NSEI
    Bank Nifty:          ^NSEBANK
    Reliance:            RELIANCE.NS
    ONGC:                ONGC.NS
    USD/INR:             INR=X
    Bitcoin:             BTC-USD

Install yfinance once:
    uv add yfinance
"""

import yfinance as yf


def main():
    ticker = "CL=F"          # WTI crude oil futures
    start = "2020-01-01"
    end = "2024-12-31"

    print(f"Downloading {ticker} from {start} to {end}...")
    df = yf.download(ticker, start=start, end=end, progress=False)

    print(f"\nRows: {len(df)} | Columns: {list(df.columns)}")
    print(f"Date range: {df.index.min().date()} → {df.index.max().date()}\n")

    output_path = f"data/raw/{ticker.replace('=', '_')}_prices.csv"
    df.to_csv(output_path)
    print(f"Saved to {output_path}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nLast 5 rows:")
    print(df.tail())


if __name__ == "__main__":
    main()
