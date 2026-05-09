"""
Example 5 — GDELT: download and parse one day of global news events

Source: data.gdeltproject.org (GDELT 1.0 events)
Goal: download one day's worth of global news events, filter for crude oil
      coverage, save to CSV.

Run with:
    uv run python examples/05_gdelt_one_day.py

Why this example?
"Scraping" doesn't always mean parsing HTML. Sometimes the cleanest
approach is to download a structured file the data provider already
prepared. GDELT is one of the best examples for researchers.

GDELT URL pattern:
    http://data.gdeltproject.org/events/YYYYMMDD.export.CSV.zip

Each file = ~10MB zipped, ~150,000 events for that day, headerless TSV.

If the date you pick returns 404, try a different recent weekday.
"""

import io
import zipfile
import requests
import pandas as pd


# GDELT 1.0 columns. The CSV files are headerless — you apply the schema.
GDELT_COLS = [
    "GlobalEventID", "Day", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode",
    "QuadClass", "GoldsteinScale", "NumMentions", "NumSources",
    "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_Lat", "ActionGeo_Long", "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]

OIL_KEYWORDS = ["crude", "opec", "brent", "wti", "petroleum", "oil-price", "barrel", "refinery"]


def fetch_gdelt_day(day: str) -> pd.DataFrame:
    """Download one day's GDELT zip and return as DataFrame with column names."""
    url = f"http://data.gdeltproject.org/events/{day}.export.CSV.zip"
    print(f"Downloading {url} ...")

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()  # crash loudly if 404 / 500
    print(f"  Status: {resp.status_code} | Size: {len(resp.content) // 1024} KB")

    # Open the zip IN MEMORY — never write to disk
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f, sep="\t", header=None, low_memory=False)

    df.columns = GDELT_COLS
    return df


def filter_oil_events(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows whose source URL mentions any oil-related keyword."""
    pattern = "|".join(OIL_KEYWORDS)
    mask = df["SOURCEURL"].str.lower().str.contains(pattern, na=False)
    return df[mask].copy()


def main():
    day = "20240301"  # 1 March 2024 — change if you get 404
    df = fetch_gdelt_day(day)
    print(f"\nTotal events on {day}: {len(df):,} | Columns: {df.shape[1]}")

    oil_df = filter_oil_events(df)
    print(f"Oil-related events:    {len(oil_df):,}")
    print(f"Filter ratio:          {len(oil_df) / len(df) * 100:.2f}%\n")

    output_path = f"data/raw/gdelt_oil_{day}.csv"
    oil_df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

    print("\nSample oil-related events:")
    print(oil_df[["Day", "Actor1Name", "AvgTone", "SOURCEURL"]].head(5))


if __name__ == "__main__":
    main()
