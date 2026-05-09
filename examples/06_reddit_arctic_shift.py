"""
Example 6 — Reddit via Arctic Shift API

Source: https://arctic-shift.photon-reddit.com (community Reddit archive)
Goal: download Reddit posts mentioning "crude oil" from a given subreddit
      within a date range, save to CSV.

Run with:
    uv run python examples/06_reddit_arctic_shift.py

Why this example?
GDELT gives you bulk files. Reddit gives you an API. Different shape, same
skill. With an API you don't parse HTML — you ask the server with parameters
and it returns JSON. JSON is just a Python dictionary in disguise.

Why Arctic Shift instead of Reddit's official API?
    - No account, no OAuth, no API key
    - Historical data goes back further
    - Free for researchers

Two bugs that wasted me half a day on this API (so you don't repeat them):
    1. Date format must be YYYY-MM-DD strings, NOT Unix timestamps
    2. Search parameter is `title=` (or `body=`), NOT `q=` like most APIs
"""

import requests
import pandas as pd


API = "https://arctic-shift.photon-reddit.com/api/posts/search"
HEADERS = {"User-Agent": "LectureDemo/1.0 (academic research)"}


def search_reddit_posts(
    subreddit: str,
    title_query: str,
    after: str,   # YYYY-MM-DD format
    before: str,  # YYYY-MM-DD format
    limit: int = 50,
) -> list[dict]:
    """Call Arctic Shift API and return raw post dicts."""
    params = {
        "subreddit": subreddit,
        "title": title_query,
        "after": after,
        "before": before,
        "limit": limit,
        "sort": "asc",
    }

    resp = requests.get(API, params=params, headers=HEADERS, timeout=30)
    print(f"Status: {resp.status_code}")
    resp.raise_for_status()

    data = resp.json()
    posts = data.get("data", [])
    print(f"Posts returned: {len(posts)}")
    return posts


def normalize_posts(posts: list[dict]) -> pd.DataFrame:
    """Pull out just the fields we care about and turn into a DataFrame."""
    rows = []
    for p in posts:
        rows.append({
            "date": pd.to_datetime(p.get("created_utc", 0), unit="s").strftime("%Y-%m-%d"),
            "subreddit": p.get("subreddit"),
            "title": p.get("title"),
            "score": p.get("score"),
            "num_comments": p.get("num_comments"),
            "url": "https://reddit.com" + p.get("permalink", ""),
        })
    return pd.DataFrame(rows)


def main():
    posts = search_reddit_posts(
        subreddit="oil",
        title_query="crude oil",
        after="2023-01-01",
        before="2023-01-31",
        limit=50,
    )

    df = normalize_posts(posts)
    output_path = "data/raw/reddit_crude_oil_jan2023.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} posts to {output_path}")
    print("\nFirst 10 posts:")
    print(df.head(10))


if __name__ == "__main__":
    main()
