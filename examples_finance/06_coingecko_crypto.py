"""
Example F6 — CoinGecko: crypto prices via free JSON API (no key)

Source: CoinGecko public API
Goal:   download daily price history for any cryptocurrency, save as CSV.

Run with:
    uv run python examples_finance/06_coingecko_crypto.py

Why this example?
Crypto markets run 24/7 and CoinGecko's free tier returns clean JSON
without authentication. Useful for any market microstructure study, and
a great template for ANY similar JSON API (the pattern is identical).

Free tier limits:
    - ~10-30 calls/minute (no key)
    - Up to 365 days of daily history per call
    - For longer histories, paginate or use Pro key
"""

import time
import requests
import pandas as pd


API = "https://api.coingecko.com/api/v3"
HEADERS = {"User-Agent": "ResearchDemo/1.0"}


def fetch_coin_history(coin_id: str, days: int = 365) -> pd.DataFrame:
    """Fetch daily price history for a coin. Returns DataFrame with date, price, volume, market_cap."""
    url = f"{API}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}

    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    print(f"Status: {resp.status_code}")
    resp.raise_for_status()

    data = resp.json()
    # API returns 3 separate arrays of [timestamp_ms, value] pairs
    prices = pd.DataFrame(data["prices"], columns=["ts", "price"])
    vols = pd.DataFrame(data["total_volumes"], columns=["ts", "volume"])
    mcaps = pd.DataFrame(data["market_caps"], columns=["ts", "market_cap"])

    # Merge on timestamp
    df = prices.merge(vols, on="ts").merge(mcaps, on="ts")
    df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.date
    df = df[["date", "price", "volume", "market_cap"]]
    return df


def main():
    coins = ["bitcoin", "ethereum", "solana"]

    for coin in coins:
        print(f"\n--- {coin} ---")
        df = fetch_coin_history(coin, days=365)
        print(f"Rows: {len(df)} | Date range: {df['date'].min()} → {df['date'].max()}")

        output_path = f"data/raw/crypto_{coin}_daily.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")
        print(df.head(3))

        time.sleep(2)  # be polite to free-tier API


if __name__ == "__main__":
    main()
