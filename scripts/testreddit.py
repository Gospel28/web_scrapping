"""
Reddit Crude Oil Scraper — Arctic Shift API (v3 Fixed)
=======================================================
FIXED: HTTP 400 error caused by:
  - Wrong date format (was Unix timestamps, must be YYYY-MM-DD strings)
  - Wrong parameter name (was q=, must be title= for posts, body= for comments)

INSTALL ONCE:
    pip install requests pandas tqdm

RUN:
    python reddit_crude_oil.py

OUTPUT per year:
    reddit_oil_data/
        reddit_posts_YYYY.csv
        reddit_comments_YYYY.csv
        reddit_combined_YYYY.csv
"""

import os, re, time
import requests, pandas as pd
from datetime import date, timedelta
from tqdm import tqdm

OUTPUT_FOLDER = "reddit_oil_data"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

API_BASE = "https://arctic-shift.photon-reddit.com/api"

# Subreddits ordered by crude oil relevance
SUBREDDITS = [
    "crudeoil",
    "oil",
    "energy",
    "investing",
    "stocks",
    "geopolitics",
    "wallstreetbets",
    "worldnews",
]

# Title search queries for posts (one API call per query)
# Arctic Shift title= does simple keyword match
POST_TITLE_QUERIES = [
    "crude oil",
    "opec",
    "brent oil",
    "wti crude",
    "oil price",
    "oil prices",
    "oil production",
    "oil market",
    "petroleum",
    "oil barrel",
    "oil refinery",
    "aramco",
    "oil sanctions",
    "shale oil",
    "oil demand",
    "oil supply",
    "oil futures",
    "peak oil",
    "oil pipeline",
    "oil drilling",
]

# Comment body search queries
# Arctic Shift body= does simple keyword match
COMMENT_BODY_QUERIES = [
    "crude oil",
    "opec",
    "brent",
    "wti",
    "oil price",
    "petroleum",
    "aramco",
    "oil barrel",
    "oil production",
    "oil market",
]

# Strict post-fetch filter — ensures no noise
OIL_STRICT = re.compile(
    r'crude\s*oil|opec|brent|wti|petroleum|oil\s*price|oil\s*market|'
    r'oil\s*production|oil\s*demand|oil\s*supply|oil\s*barrel|'
    r'oil\s*refin|aramco|gazprom|rosneft|shale\s*oil|oil\s*sanction|'
    r'oil\s*embargo|petrodollar|oil\s*futures|oil\s*well|oilfield|'
    r'oil\s*tanker|oil\s*spill|oil\s*drill|oil\s*pipeline|peak\s*oil',
    re.IGNORECASE
)

def is_oil_related(text):
    return bool(OIL_STRICT.search(str(text or '')))

def date_str(year, month=1, day=1):
    """Return YYYY-MM-DD string — correct format for Arctic Shift API"""
    return f"{year}-{month:02d}-{day:02d}"

def year_end_str(year):
    return f"{year}-12-31"

def ts_to_date(ts):
    try:
        return pd.to_datetime(int(ts), unit='s', utc=True).strftime('%Y-%m-%d')
    except:
        return ''

# ── API ────────────────────────────────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'CrudeOilResearch/3.0 (academic research)'})

def api_get(endpoint, params, retries=3):
    url = f"{API_BASE}/{endpoint}"
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, params=params, timeout=30)
            # Rate limit handling
            remaining = int(resp.headers.get('X-RateLimit-Remaining', 10))
            if remaining < 3:
                reset = int(resp.headers.get('X-RateLimit-Reset', 10))
                time.sleep(max(reset, 3))
            if resp.status_code == 429:
                wait = 15 * (attempt + 1)
                tqdm.write(f"    Rate limited — waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 400:
                tqdm.write(f"    400 Bad Request: {url} params={params}")
                return None
            if resp.status_code == 200:
                return resp.json()
            time.sleep(2)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
    return None

# ── Posts fetcher ──────────────────────────────────────────────────────────────
def fetch_posts(subreddit, year, title_query):
    """
    Fetch posts matching title_query from a subreddit for a year.
    CORRECT params: after=YYYY-MM-DD, before=YYYY-MM-DD, title=keyword
    Paginate by advancing 'after' to the date of the last post + 1 day.
    """
    posts   = []
    after   = date_str(year, 1, 1)
    before  = date_str(year, 12, 31)
    seen_ids = set()

    while True:
        params = {
            'subreddit': subreddit,
            'after':     after,          # YYYY-MM-DD  ← correct format
            'before':    before,         # YYYY-MM-DD  ← correct format
            'title':     title_query,    # title=      ← correct param name
            'limit':     100,
            'sort':      'asc',
        }
        data = api_get('posts/search', params)

        if not data or not data.get('data'):
            break

        batch = data['data']
        new_posts = 0

        for p in batch:
            pid = p.get('id', '')
            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            title = p.get('title', '')
            body  = p.get('selftext', '')
            if is_oil_related(title) or is_oil_related(body):
                posts.append({
                    'type':         'post',
                    'id':           pid,
                    'subreddit':    p.get('subreddit', subreddit),
                    'date':         ts_to_date(p.get('created_utc', 0)),
                    'created_utc':  p.get('created_utc', ''),
                    'title':        title,
                    'text':         body[:2000],
                    'author':       p.get('author', ''),
                    'score':        p.get('score', 0),
                    'upvote_ratio': p.get('upvote_ratio', ''),
                    'num_comments': p.get('num_comments', 0),
                    'url':          p.get('url', ''),
                    'permalink':    'https://reddit.com' + p.get('permalink', ''),
                    'post_id':      pid,
                    'parent_id':    '',
                })
                new_posts += 1

        if len(batch) < 100:
            break

        # Advance after date to the last post's date to paginate
        last_created = batch[-1].get('created_utc', 0)
        last_date = pd.to_datetime(int(last_created), unit='s', utc=True)
        after = last_date.strftime('%Y-%m-%d')

        # Safety: if we've reached year end stop
        if after >= before:
            break

        time.sleep(0.5)

    return posts

# ── Comments fetcher ───────────────────────────────────────────────────────────
def fetch_comments(subreddit, year, body_query):
    """
    Fetch comments matching body_query from a subreddit for a year.
    CORRECT params: after=YYYY-MM-DD, before=YYYY-MM-DD, body=keyword
    """
    comments = []
    after    = date_str(year, 1, 1)
    before   = date_str(year, 12, 31)
    seen_ids = set()

    while True:
        params = {
            'subreddit': subreddit,
            'after':     after,       # YYYY-MM-DD ← correct
            'before':    before,      # YYYY-MM-DD ← correct
            'body':      body_query,  # body=      ← correct param name
            'limit':     100,
            'sort':      'asc',
        }
        data = api_get('comments/search', params)

        if not data or not data.get('data'):
            break

        batch = data['data']

        for c in batch:
            cid  = c.get('id', '')
            if cid in seen_ids:
                continue
            seen_ids.add(cid)

            body = c.get('body', '')
            if not body or body in ('[deleted]', '[removed]'):
                continue
            if is_oil_related(body):
                comments.append({
                    'type':         'comment',
                    'id':           cid,
                    'subreddit':    c.get('subreddit', subreddit),
                    'date':         ts_to_date(c.get('created_utc', 0)),
                    'created_utc':  c.get('created_utc', ''),
                    'title':        '',
                    'text':         body[:2000],
                    'author':       c.get('author', ''),
                    'score':        c.get('score', 0),
                    'upvote_ratio': '',
                    'num_comments': '',
                    'url':          '',
                    'permalink':    'https://reddit.com' + c.get('permalink', ''),
                    'post_id':      c.get('link_id', '').replace('t3_', ''),
                    'parent_id':    c.get('parent_id', ''),
                })

        if len(batch) < 100:
            break

        last_created = batch[-1].get('created_utc', 0)
        last_date = pd.to_datetime(int(last_created), unit='s', utc=True)
        after = last_date.strftime('%Y-%m-%d')
        if after >= before:
            break
        time.sleep(0.5)

    return comments

# ── Year downloader ────────────────────────────────────────────────────────────
def download_year(year, subreddits=None):
    if subreddits is None:
        subreddits = SUBREDDITS

    posts_csv    = os.path.join(OUTPUT_FOLDER, f"reddit_posts_{year}.csv")
    comments_csv = os.path.join(OUTPUT_FOLDER, f"reddit_comments_{year}.csv")
    combined_csv = os.path.join(OUTPUT_FOLDER, f"reddit_combined_{year}.csv")
    progress_f   = os.path.join(OUTPUT_FOLDER, f".done_reddit_{year}.txt")

    done_keys = set()
    if os.path.exists(progress_f):
        with open(progress_f) as f:
            done_keys = set(l.strip() for l in f if l.strip())

    print(f"\n  {'='*55}")
    print(f"  Reddit Crude Oil — Year {year}")
    print(f"  Subreddits: {len(subreddits)}")
    print(f"  {'='*55}")

    total_posts = total_comments = 0

    for sub in tqdm(subreddits, desc=f"  {year}"):

        # Posts — one query per title keyword
        sub_posts = []
        for q in POST_TITLE_QUERIES:
            key = f"{sub}_post_{q.replace(' ','_')}"
            if key in done_keys:
                continue
            results = fetch_posts(sub, year, q)
            sub_posts.extend(results)
            with open(progress_f, 'a') as pf:
                pf.write(key + '\n')
            time.sleep(0.3)

        if sub_posts:
            df_p = pd.DataFrame(sub_posts).drop_duplicates(subset=['id'])
            df_p.to_csv(posts_csv, mode='a',
                        header=not os.path.exists(posts_csv), index=False)
            total_posts += len(df_p)
            tqdm.write(f"    r/{sub}: {len(df_p):,} posts")

        # Comments — one query per body keyword
        sub_comments = []
        for q in COMMENT_BODY_QUERIES:
            key = f"{sub}_comment_{q.replace(' ','_')}"
            if key in done_keys:
                continue
            results = fetch_comments(sub, year, q)
            sub_comments.extend(results)
            with open(progress_f, 'a') as pf:
                pf.write(key + '\n')
            time.sleep(0.3)

        if sub_comments:
            df_c = pd.DataFrame(sub_comments).drop_duplicates(subset=['id'])
            df_c.to_csv(comments_csv, mode='a',
                        header=not os.path.exists(comments_csv), index=False)
            total_comments += len(df_c)
            tqdm.write(f"    r/{sub}: {len(df_c):,} comments")

        time.sleep(1)

    # Build combined file
    dfs = []
    for f in [posts_csv, comments_csv]:
        if os.path.exists(f):
            dfs.append(pd.read_csv(f))

    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        combined = combined.drop_duplicates(subset=['id'])
        combined = combined.sort_values('created_utc')
        combined.to_csv(combined_csv, index=False)
        size_kb = os.path.getsize(combined_csv) / 1024
        print(f"\n  Year {year} complete!")
        print(f"    Posts          : {total_posts:,}")
        print(f"    Comments       : {total_comments:,}")
        print(f"    Combined rows  : {len(combined):,}")
        print(f"    File size      : {size_kb:.0f} KB ({size_kb/1024:.2f} MB)")
        print(f"    Saved to       : {combined_csv}")
    else:
        print(f"\n  Year {year}: No data found.")

# ── Input parser ───────────────────────────────────────────────────────────────
def parse_years(choice):
    choice = choice.strip()
    if choice.lower() == 'all':
        return list(range(2011, 2024))
    m = re.match(r'^(\d{4})-(\d{4})$', choice)
    if m:
        s, e = int(m.group(1)), int(m.group(2))
        if 2011 <= s <= e <= 2023:
            return list(range(s, e + 1))
        print("  Range must be within 2011-2023"); return None
    if re.match(r'^\d{4}$', choice):
        y = int(choice)
        if 2011 <= y <= 2023:
            return [y]
        print("  Year must be 2011-2023"); return None
    print("  Invalid. Examples: 2021  or  2019-2022  or  all")
    return None

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Reddit Crude Oil Scraper v3 — Arctic Shift API")
    print("=" * 60)
    print()
    print("  No Reddit account or API key needed")
    print("  Date format fix: now uses YYYY-MM-DD (was Unix timestamp)")
    print("  Param fix: title= for posts, body= for comments")
    print()
    print(f"  Subreddits: {', '.join('r/'+s for s in SUBREDDITS)}")
    print()
    print("  Enter what to download:")
    print("    Single year  →  2021")
    print("    Year range   →  2019-2022")
    print("    All years    →  all")
    print()

    while True:
        choice = input("  Your choice: ").strip()
        years = parse_years(choice)
        if years:
            break

    print(f"\n  Will download: {years[0]} to {years[-1]} ({len(years)} year(s))")
    if input("  Start? (y/n): ").strip().lower() != 'y':
        print("  Cancelled."); return

    for year in years:
        download_year(year)

    print("\n" + "=" * 60)
    print("  ALL DONE!")
    print(f"  Files saved in: {OUTPUT_FOLDER}/")
    for year in years:
        f = os.path.join(OUTPUT_FOLDER, f"reddit_combined_{year}.csv")
        if os.path.exists(f):
            df = pd.read_csv(f)
            p = (df['type'] == 'post').sum()
            c = (df['type'] == 'comment').sum()
            kb = os.path.getsize(f) / 1024
            print(f"    {year}: {p:>6,} posts + {c:>7,} comments | {kb:.0f} KB")
    print("=" * 60)

if __name__ == "__main__":
    main()