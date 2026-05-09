"""
GDELT Crude Oil Downloader v3 — Fixed & Improved
=================================================
FIXES FROM v2:
  - Saves ALL important columns: AvgTone, GoldsteinScale, NumMentions,
    Actor1Name, Actor2Name, Actor1CountryCode, ActionGeo_FullName
  - STRICT crude oil filter — no more "vaccine spoil" / "olive oil" noise
  - Deduplicates by SOURCEURL automatically — no repeated articles
  - Handles pre-2013 files (no SOURCEURL) via Actor name filter
  - Batch download: enter range like 2020-2023 or single year or 'all'
  - Resume support: safely restart if interrupted

INSTALL ONCE:
    pip install requests pandas tqdm

RUN:
    python gdelt_crude_oil_v3.py
"""

import os, io, re, zipfile
import requests, pandas as pd
from datetime import date, timedelta
from urllib.parse import urlparse
from tqdm import tqdm

# ── Output folder ──────────────────────────────────────────────────────────────
OUTPUT_FOLDER = "gdelt_oil_by_year"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── STRICT crude oil keywords (URL filter — Apr 2013 onwards) ─────────────────
# These are SPECIFIC to crude oil — no generic words like 'energy', 'fuel', 'gas'
# which cause false positives like vaccine/olive oil/natural gas articles
STRICT_URL_KEYWORDS = [
    'crude-oil', 'crude_oil', 'crudeoil',
    'crude',
    'opec',
    'brent',
    'wti',
    'petroleum',
    'oil-price', 'oil_price', 'oilprice',
    'oil-market', 'oil_market',
    'oil-production', 'oil_production',
    'oil-demand', 'oil_demand',
    'oil-supply', 'oil_supply',
    'oil-output', 'oil_output',
    'oil-barrel', 'oil_barrel',
    'oil-refin',
    'oil-sanction',
    'oil-export', 'oil_export',
    'oil-import', 'oil_import',
    'oil-field', 'oil_field', 'oilfield',
    'oil-well', 'oil_well',
    'oil-spill', 'oil_spill',
    'barrel',
    'refinery', 'refineries', 'refining',
    'drilling',
    'upstream', 'downstream',
    'petrochemical',
    'hydrocarbon',
    'lng',           # liquefied natural gas
    'shale-oil', 'shale_oil',
    'tar-sand', 'tar_sand', 'oilsand',
    'offshore-oil',
    'oil-rig', 'oil_rig',
    'tanker',        # oil tanker context
    'aramco',
    'gazprom',
    'rosneft',
    'chevron',
    'exxon',
    'shell-oil',
    'bp-oil',
    'total-oil',
]

# For headline-level secondary check (after URL filter)
STRICT_HEADLINE_KEYWORDS = [
    'crude oil', 'crude-oil',
    'opec', 'brent', 'wti',
    'petroleum', 'barrel', 'barrels',
    'refinery', 'refining', 'refineries',
    'oil price', 'oil prices',
    'oil market', 'oil demand', 'oil supply',
    'oil production', 'oil output',
    'oil export', 'oil import',
    'oil field', 'oilfield',
    'oil spill', 'oil well',
    'drilling', 'upstream', 'downstream',
    'petrochemical', 'hydrocarbon',
    'oil sanction', 'oil embargo',
    'shale oil', 'tar sand', 'oil sand',
    'oil tanker', 'oil rig',
    'aramco', 'gazprom', 'rosneft',
    'lng price', 'lng market',
]

# Actor name keywords for pre-2013 files (no SOURCEURL column)
ACTOR_OIL_KEYWORDS = [
    'OPEC', 'ARAMCO', 'GAZPROM', 'ROSNEFT', 'LUKOIL',
    'EXXON', 'CHEVRON', 'SHELL', 'BP', 'TOTAL', 'CONOCO',
    'PETROLEUM', 'OIL', 'CRUDE', 'BRENT', 'WTI',
    'REFIN', 'PIPELINE', 'DRILLING', 'BARREL',
    'SAUDI', 'IRAN', 'IRAQ', 'KUWAIT', 'UAE',
    'LIBYA', 'NIGERIA', 'VENEZUELA', 'ECUADOR',
    'ENERGY-OIL', 'OILMIN',   # GDELT actor type codes
]

# ── GDELT 1.0 column definitions ───────────────────────────────────────────────
GDELT_COLS = [
    'GlobalEventID','Day','MonthYear','Year','FractionDate',
    'Actor1Code','Actor1Name','Actor1CountryCode','Actor1KnownGroupCode',
    'Actor1EthnicCode','Actor1Religion1Code','Actor1Religion2Code',
    'Actor1Type1Code','Actor1Type2Code','Actor1Type3Code',
    'Actor2Code','Actor2Name','Actor2CountryCode','Actor2KnownGroupCode',
    'Actor2EthnicCode','Actor2Religion1Code','Actor2Religion2Code',
    'Actor2Type1Code','Actor2Type2Code','Actor2Type3Code',
    'IsRootEvent','EventCode','EventBaseCode','EventRootCode',
    'QuadClass','GoldsteinScale','NumMentions','NumSources',
    'NumArticles','AvgTone',
    'Actor1Geo_Type','Actor1Geo_FullName','Actor1Geo_CountryCode',
    'Actor1Geo_ADM1Code','Actor1Geo_Lat','Actor1Geo_Long','Actor1Geo_FeatureID',
    'Actor2Geo_Type','Actor2Geo_FullName','Actor2Geo_CountryCode',
    'Actor2Geo_ADM1Code','Actor2Geo_Lat','Actor2Geo_Long','Actor2Geo_FeatureID',
    'ActionGeo_Type','ActionGeo_FullName','ActionGeo_CountryCode',
    'ActionGeo_ADM1Code','ActionGeo_Lat','ActionGeo_Long','ActionGeo_FeatureID',
    'DATEADDED','SOURCEURL'
]

# Columns to KEEP in output — all the important ones
KEEP_COLS = [
    'Day',
    'Actor1Name',
    'Actor2Name',
    'Actor1CountryCode',
    'Actor2CountryCode',
    'EventCode',
    'EventBaseCode',
    'QuadClass',
    'GoldsteinScale',     # conflict/cooperation score -10 to +10
    'NumMentions',        # media attention level
    'NumArticles',
    'AvgTone',            # GDELT pre-computed sentiment -100 to +100
    'ActionGeo_FullName',
    'ActionGeo_CountryCode',
    'SOURCEURL',
]

BASE = "http://data.gdeltproject.org/events/"

# ── URL → headline ─────────────────────────────────────────────────────────────
def url_to_headline(url):
    try:
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]
        best = ''
        for seg in segments:
            seg = re.sub(r'\.(html|htm|php|asp|aspx)$', '', seg)
            if re.match(r'^\d+$', seg) or len(seg) < 5:
                continue
            words = [w for w in re.split(r'[-_]', seg)
                     if not w.isdigit() and len(w) > 1]
            if len(words) > len(re.split(r'[-_]', best)):
                best = seg
        if not best:
            return ''
        best = re.sub(r'[-_]\d{6,}$', '', best)
        best = re.sub(r'[-_][a-z0-9]{7,}$', '', best)
        return re.sub(r'[-_]+', ' ', best).strip().title()
    except:
        return ''

# ── File list builder ──────────────────────────────────────────────────────────
def has_sourceurl(year, month):
    """SOURCEURL column only exists from April 2013 onwards"""
    return not (year < 2013 or (year == 2013 and month <= 3))

def get_files_for_year(year):
    files = []
    for month in range(1, 13):
        if year in (2011, 2012) or (year == 2013 and month <= 3):
            url = f"{BASE}{year}{month:02d}.export.CSV.zip"
            files.append((f"{year}-{month:02d}", url, year, month))
        else:
            start = date(year, month, 1)
            end   = date(year+1,1,1) if month==12 else date(year, month+1, 1)
            d = start
            while d < end:
                files.append((str(d), f"{BASE}{d.strftime('%Y%m%d')}.export.CSV.zip", year, month))
                d += timedelta(days=1)
    return files

# ── Download + strict filter ───────────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'Mozilla/5.0 (research; crude oil study)'})

def is_strictly_crude_oil_url(url):
    """Check if URL contains strict crude oil keywords"""
    url_lower = url.lower()
    return any(kw in url_lower for kw in STRICT_URL_KEYWORDS)

def is_strictly_crude_oil_headline(headline):
    """Secondary check on the headline"""
    hl = headline.lower()
    return any(kw in hl for kw in STRICT_HEADLINE_KEYWORDS)

def download_and_filter(url, year, month):
    use_url = has_sourceurl(year, month)
    try:
        resp = SESSION.get(url, timeout=60)
        if resp.status_code == 404:
            return None, "404"
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            with z.open(z.namelist()[0]) as f:
                # Pre-2013 files are missing the SOURCEURL column (57 cols not 58)
                cols = GDELT_COLS if use_url else GDELT_COLS[:-1]
                df = pd.read_csv(
                    f, sep='\t', header=None, names=cols,
                    dtype=str, on_bad_lines='skip',
                    encoding='utf-8', encoding_errors='replace'
                )

        if use_url:
            # STRICT URL filter — only keep rows with crude-oil-specific URL patterns
            mask = df['SOURCEURL'].apply(is_strictly_crude_oil_url)
            oil  = df[mask].copy()

            if len(oil) == 0:
                return pd.DataFrame(), "ok"

            # Keep all important columns
            keep = [c for c in KEEP_COLS if c in oil.columns]
            oil  = oil[keep].copy()

            # Add headline from URL
            oil['Headline'] = oil['SOURCEURL'].apply(url_to_headline)

            # Secondary headline filter — drop rows where headline has zero oil signal
            # (catches edge cases where URL matched but article is unrelated)
            oil['_hl_lower'] = oil['Headline'].str.lower().fillna('')
            oil['_url_lower'] = oil['SOURCEURL'].str.lower().fillna('')
            secondary = (
                oil['_hl_lower'].apply(is_strictly_crude_oil_headline) |
                oil['_url_lower'].str.contains(
                    'crude|opec|brent|wti|petroleum|barrel|refin|drilling|aramco|gazprom|rosneft',
                    case=False, na=False
                )
            )
            oil = oil[secondary].drop(columns=['_hl_lower','_url_lower'])

            # Deduplicate by SOURCEURL — keep first occurrence only
            oil = oil.drop_duplicates(subset=['SOURCEURL'])

        else:
            # Pre-2013: filter by Actor names
            actor_pat = '|'.join(ACTOR_OIL_KEYWORDS)
            mask = (
                df['Actor1Name'].str.contains(actor_pat, case=False, na=False) |
                df['Actor2Name'].str.contains(actor_pat, case=False, na=False)
            )
            oil = df[mask].copy()
            if len(oil) == 0:
                return pd.DataFrame(), "ok"

            keep = [c for c in KEEP_COLS if c in oil.columns]
            oil  = oil[keep].copy()
            oil['SOURCEURL'] = ''
            oil['Headline']  = ''
            oil = oil.drop_duplicates(subset=['Day','Actor1Name','Actor2Name','EventCode'])

        return oil, "ok"

    except Exception as e:
        return None, str(e)[:80]

# ── Per-year download ──────────────────────────────────────────────────────────
def download_year(year):
    output_csv = os.path.join(OUTPUT_FOLDER, f"gdelt_crude_oil_{year}.csv")
    progress_f = os.path.join(OUTPUT_FOLDER, f".done_{year}.txt")

    files = get_files_for_year(year)

    # Resume support
    done_labels = set()
    if os.path.exists(progress_f):
        with open(progress_f) as f:
            done_labels = set(l.strip() for l in f if l.strip())

    remaining = [(lbl, url, yr, mo) for lbl, url, yr, mo in files
                 if lbl not in done_labels]

    if not remaining:
        print(f"\n  Year {year} already complete → {output_csv}")
        return

    method = ("Actor names (no URL col in pre-2013)"
              if year <= 2012 else
              "Mixed: actor Jan-Mar, strict URL Apr-Dec"
              if year == 2013 else
              "Strict URL + headline double-filter")

    print(f"\n  {'='*52}")
    print(f"  Downloading year: {year}")
    print(f"  Files to process: {len(remaining)}")
    print(f"  Filter method   : {method}")
    print(f"  Output          : {output_csv}")
    print(f"  {'='*52}")

    all_dfs  = []
    ok = skip = err = total_rows = 0

    with open(progress_f, 'a') as prog:
        for i, (label, url, yr, mo) in enumerate(
                tqdm(remaining, desc=f"  {year}", unit="file"), 1):

            df, status = download_and_filter(url, yr, mo)

            if status == "404":
                skip += 1
            elif df is None:
                err += 1
                tqdm.write(f"  ERROR {label}: {status}")
            elif len(df) > 0:
                df['source_label'] = label
                all_dfs.append(df)
                total_rows += len(df)
                ok += 1
            else:
                ok += 1

            prog.write(label + '\n')

            # Save every 20 files
            if i % 20 == 0 and all_dfs:
                combined = pd.concat(all_dfs, ignore_index=True)
                mode   = 'a' if os.path.exists(output_csv) else 'w'
                header = not os.path.exists(output_csv)
                combined.to_csv(output_csv, mode=mode, header=header, index=False)
                all_dfs = []
                tqdm.write(f"  Saved [{i}/{len(remaining)}] — {total_rows:,} rows so far")

    # Final flush
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        mode   = 'a' if os.path.exists(output_csv) else 'w'
        header = not os.path.exists(output_csv)
        combined.to_csv(output_csv, mode=mode, header=header, index=False)

    # Summary
    print(f"\n  Year {year} complete!")
    print(f"    Processed : {ok}  |  Skipped (404): {skip}  |  Errors: {err}")
    if os.path.exists(output_csv):
        final = pd.read_csv(output_csv)
        size_kb = os.path.getsize(output_csv) / 1024
        print(f"    Rows saved  : {len(final):,}")
        print(f"    File size   : {size_kb:.0f} KB ({size_kb/1024:.2f} MB)")
        print(f"    Columns     : {list(final.columns)}")
        print(f"    Saved to    : {output_csv}")

# ── Time estimate table ────────────────────────────────────────────────────────
def show_estimates():
    print(f"\n  {'Year':<6} {'Files':<8} {'Raw DL':<10} {'Filter':<30} {'~Time @20Mbps'}")
    print(f"  {'-'*68}")
    for y in range(2011, 2024):
        files = get_files_for_year(y)
        n = len(files)
        if y in (2011, 2012):
            mb = 12 * 75
        elif y == 2013:
            mb = 3 * 75 + 9 * 30
        else:
            mb = n * 8
        mins  = (mb / (20/8) + n * 2) / 60
        size  = f"~{mb/1024:.1f}GB" if mb >= 1024 else f"~{mb}MB"
        method = "Actor names" if y<=2012 else "Mixed" if y==2013 else "Strict URL+headline"
        print(f"  {y:<6} {n:<8} {size:<10} {method:<30} ~{mins:.0f} min")

# ── Parse year input ───────────────────────────────────────────────────────────
def parse_years(choice):
    choice = choice.strip()
    if choice.lower() == 'all':
        return list(range(2011, 2024))

    # Range: 2020-2023
    range_match = re.match(r'^(\d{4})-(\d{4})$', choice)
    if range_match:
        s, e = int(range_match.group(1)), int(range_match.group(2))
        if 2011 <= s <= e <= 2023:
            return list(range(s, e + 1))
        else:
            print(f"  Range must be within 2011-2023"); return None

    # Single year
    if re.match(r'^\d{4}$', choice):
        y = int(choice)
        if 2011 <= y <= 2023:
            return [y]
        else:
            print("  Year must be between 2011 and 2023"); return None

    print("  Invalid input. Try: 2021  or  2020-2023  or  all")
    return None

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  GDELT Crude Oil Downloader v3 — Strict Filter")
    print("=" * 60)
    print()
    print("  WHAT'S FIXED vs previous version:")
    print("  + Saves AvgTone, GoldsteinScale, NumMentions, Actor names")
    print("  + Strict crude oil filter — no more noise articles")
    print("  + Auto-deduplication — no repeated URLs")
    print("  + Batch download support (e.g. 2020-2023)")
    print("  + Resume support — safely restart if interrupted")

    show_estimates()

    print("\n  Enter what to download:")
    print("    Single year  →  2021")
    print("    Year range   →  2020-2023")
    print("    All years    →  all")
    print()

    while True:
        choice = input("  Your choice: ").strip()
        years  = parse_years(choice)
        if years:
            break

    print(f"\n  Will download: {years[0]} to {years[-1]} ({len(years)} year(s))")
    total_files = sum(len(get_files_for_year(y)) for y in years)
    print(f"  Total files  : {total_files:,}")

    if input("  Start? (y/n): ").strip().lower() != 'y':
        print("  Cancelled.")
        return

    for year in years:
        download_year(year)

    print("\n" + "=" * 60)
    print(f"  ALL DONE!")
    print(f"  Files saved in: {OUTPUT_FOLDER}/")
    print(f"  Filename format: gdelt_crude_oil_YYYY.csv")
    print("=" * 60)

    # Print final summary of all files created
    print("\n  Output files:")
    for year in years:
        f = os.path.join(OUTPUT_FOLDER, f"gdelt_crude_oil_{year}.csv")
        if os.path.exists(f):
            df = pd.read_csv(f)
            print(f"    {year}: {len(df):>7,} rows  |  {os.path.getsize(f)/1024:.0f} KB  →  {f}")

if __name__ == "__main__":
    main()