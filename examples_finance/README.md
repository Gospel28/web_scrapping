# Energy & Financial Market Examples

Six short, runnable examples for scraping market data — every one runs without an API key.

| # | File | Source | What you get |
|---|---|---|---|
| F1 | `01_yahoo_single_ticker.py` | Yahoo Finance | OHLCV history for any stock/commodity (WTI, Brent, Nifty, etc.) |
| F2 | `02_yahoo_basket.py` | Yahoo Finance | Multi-ticker basket with correlation matrix |
| F3 | `03_eia_crude_inventory.py` | EIA | Weekly US crude oil inventory (HTML table) |
| F4 | `04_wikipedia_index_constituents.py` | Wikipedia | Current S&P 500 / Nifty 50 / Dow constituents |
| F5 | `05_fx_rates_table.py` | x-rates.com | Cross-currency exchange rates (HTML table) |
| F6 | `06_coingecko_crypto.py` | CoinGecko | Daily crypto prices, volumes, market caps (JSON API) |

## One-time install

The Yahoo Finance examples need `yfinance` (everything else uses libraries already in `pyproject.toml`):

```bash
uv add yfinance
```

## Running them

```bash
uv run python examples_finance/01_yahoo_single_ticker.py
uv run python examples_finance/02_yahoo_basket.py
# ...etc
```

All output CSVs land in `data/raw/`.

## Three patterns these examples teach

1. **Library wrappers around hidden APIs** (F1, F2, F6) — fastest path, no scraping headache.
2. **`pandas.read_html` for HTML tables** (F3, F4, F5) — two lines, parses every table on the page.
3. **JSON APIs without keys** (F6) — call URL with params, parse `.json()`, done.

## Why no Bloomberg / Refinitiv / Alpha Vantage?

Bloomberg and Refinitiv require paid terminals — out of reach for most PhD work. Alpha Vantage and FRED need API keys, which would slow down the lecture. Everything in this folder runs on a fresh laptop in 30 seconds.

## Common breakages

| Symptom | Likely cause | Fix |
|---|---|---|
| Yahoo returns empty | Yahoo throttling | Wait 60s, retry. Use `progress=False` to reduce log noise |
| EIA page returns 403 | User-Agent blocked | Already handled in the script |
| Wikipedia table index wrong | Page restructured | Open the URL, inspect tables, adjust the index |
| CoinGecko 429 | Free tier rate limit | Add longer `time.sleep()` or get a free Demo key |

For deeper troubleshooting, see `docs/AI_Scraping_Playbook.docx` — Part 3 has the full error taxonomy.

## Adapting these to your research

Each script is ~50-60 lines. To use one for your own data:

1. Copy the file, rename it
2. Change the ticker / URL / parameters at the top
3. Adjust the column extraction in the parsing step
4. Run it

Don't try to rewrite from scratch. Copy + tweak is the right approach.
