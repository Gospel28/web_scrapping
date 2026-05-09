# Web Scraping — Student Handout

> A 1-page reference to keep on your desk while learning. Everything we covered today, condensed.

---

## The 5+2 libraries you need (install once)

```bash
pip install requests beautifulsoup4 lxml pandas tqdm selenium webdriver-manager
```

| Library | Job |
|---|---|
| `requests` | Fetch the raw HTML from a URL |
| `beautifulsoup4` | Parse HTML, find tags |
| `lxml` | Fast parser (used by BeautifulSoup) |
| `pandas` | Store data in tables, save CSV |
| `tqdm` | Progress bars |
| `selenium` | Drive a real Chrome browser (when JS blocks you) |
| `webdriver-manager` | Auto-installs the matching ChromeDriver |

**Built-in (no install) but worth knowing:** `re` (regex), `time` (sleep, timing), `json`, `os` (paths), `io.BytesIO` + `zipfile` (in-memory zip), `urllib.parse` (URL parts), `datetime` (date math).

**Adjacent libraries you'll meet later:**

| Library | When |
|---|---|
| `playwright` | Modern alternative to Selenium |
| `httpx`, `aiohttp` | Async HTTP for parallel scraping |
| `scrapy` | 10,000+ URL crawls |
| `feedparser` | RSS / Atom feeds |
| `pdfplumber`, `pymupdf` | PDF text extraction |
| `pytesseract` | OCR for scanned documents |
| `cloudscraper` | Cloudflare bypass (use carefully) |

---

## The 4-step pattern (every scraper)

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. FETCH
r = requests.get("https://quotes.toscrape.com/")

# 2. PARSE
soup = BeautifulSoup(r.text, "lxml")

# 3. FIND
quotes = soup.find_all("div", class_="quote")

# 4. SAVE
data = [{"text": q.find("span", class_="text").get_text(strip=True),
         "author": q.find("small", class_="author").get_text(strip=True)}
        for q in quotes]

pd.DataFrame(data).to_csv("quotes.csv", index=False)
```

---

## Pagination pattern (most sites)

```python
import time
for page in range(1, 11):                 # 10 pages
    url = f"https://example.com/page/{page}/"
    r   = requests.get(url)
    # ... parse and store ...
    time.sleep(1)                         # ALWAYS — be polite
```

---

## Status code cheat sheet

| Code | Meaning | Fix |
|---|---|---|
| 200 | Success | — |
| 403 | Forbidden | Add User-Agent header |
| 404 | Not found | URL is wrong |
| 429 | Too many requests | Slow down, add delay |
| 5xx | Server error | Retry later, not your fault |

## User-Agent (the 403 fix)

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
r = requests.get(url, headers=headers)
```

---

## CSS selectors (cleaner than `find_all`)

```python
# These do the same thing:
soup.find_all("div", class_="quote")
soup.select("div.quote")          # CSS selector — shorter

# Useful patterns:
soup.select("#main")              # id="main"
soup.select("div.quote span.text")  # nested
soup.select("a[href*='author']")  # attribute contains
```

**Pro tip**: in Chrome, right-click element → Inspect → in dev tools, right-click → Copy → Copy selector.

---

## Working with bulk data files (GDELT pattern)

```python
import io, zipfile
import pandas as pd, requests

url = "http://data.gdeltproject.org/events/20240301.export.CSV.zip"
resp = requests.get(url, timeout=60)

# Open zip in MEMORY — don't write to disk first
with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
    with z.open(z.namelist()[0]) as f:
        df = pd.read_csv(f, sep="\t", header=None, low_memory=False)

# Apply schema yourself if file is headerless
df.columns = ['col1', 'col2', ...]

# Filter
mask = df['some_col'].str.contains('keyword', case=False, na=False)
filtered = df[mask]
```

---

## Calling a JSON API (Reddit / Arctic Shift pattern)

```python
import requests, pandas as pd

API = "https://arctic-shift.photon-reddit.com/api/posts/search"
params = {
    "subreddit": "oil",
    "title":     "crude oil",
    "after":     "2023-01-01",     # YYYY-MM-DD strings, not timestamps
    "before":    "2023-12-31",
    "limit":     100,
    "sort":      "asc",
}
headers = {"User-Agent": "MyResearch/1.0"}

resp = requests.get(API, params=params, headers=headers, timeout=30)
data = resp.json()                  # JSON → Python dict, automatic

posts = data.get("data", [])
df = pd.DataFrame(posts)
```

---

## Selenium pattern — when JavaScript blocks you

Use only when `requests` returns nothing because the page is JavaScript-rendered.

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Setup Chrome (headless = invisible window)
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver  = webdriver.Chrome(service=service, options=options)

# Visit page, let JS run, grab rendered HTML
driver.get("https://quotes.toscrape.com/js/")
time.sleep(2)                         # wait for JS to render
rendered_html = driver.page_source

# From here — same BeautifulSoup pattern
soup = BeautifulSoup(rendered_html, "lxml")
quotes = soup.find_all("div", class_="quote")

driver.quit()                         # ALWAYS close the browser
```

**Selenium can also interact** — click, fill forms, scroll:

```python
from selenium.webdriver.common.by import By

button = driver.find_element(By.CSS_SELECTOR, "li.next a")
button.click()
time.sleep(2)                         # wait for new page
```

**Speed cost**: 5-10× slower than `requests`. Use only when needed.

---

## Decision tree — before writing any scraper

```
1. Does the site have an API?
     YES → use it. Stop.
     NO  → continue.

2. Does the site offer bulk downloads?
     YES → download those.
     NO  → continue.

3. Is content visible in 'View Source' (Ctrl+U)?
     YES → requests + BeautifulSoup. Done.
     NO  → check Network tab in DevTools first.
            (Often there's a hidden API you can hit directly.)
            If still no luck → Selenium / Playwright.

4. Are you allowed? Check robots.txt and ToS.
```

---

## Errors you'll actually see — and what to do

| Error type | Means | First fix to try |
|---|---|---|
| `ConnectionError` | Cannot reach server | Check URL spelling, check internet |
| `Timeout` | Server too slow / hung | Increase `timeout=` parameter |
| `HTTPError 403` | Forbidden | Add User-Agent header |
| `HTTPError 404` | Page not found | Check URL — pattern might have changed |
| `HTTPError 429` | Too many requests | Add `time.sleep(1)` or longer between calls |
| `HTTPError 5xx` | Server-side broken | Wait, retry — not your fault |
| `AttributeError: 'NoneType' has no attribute ...` | `find()` returned None — tag not on page | Check class name spelling, inspect page |
| `JSONDecodeError` | Server didn't return JSON (often HTML error page) | `print(r.text[:300])` to see what came back |
| `KeyError: 'fieldname'` | Dictionary missing the field | Use `data.get('fieldname', '')` instead of `data['fieldname']` |
| `SSLError` | Certificate issue | Check date/time on machine. Last resort: `verify=False` |
| `ChromeDriver version mismatch` | Selenium driver / browser don't match | Re-run `ChromeDriverManager().install()` |

**Read the traceback bottom-up:**

```
Traceback (most recent call last):
  File "scraper.py", line 23, in <module>
    process_data(soup)
  File "scraper.py", line 15, in process_data
    title = item.find("h1").get_text()       ← THE ACTUAL PROBLEM IS HERE
AttributeError: 'NoneType' object has no attribute 'get_text'   ← AND HERE
```

The last two lines tell you (a) the error type and (b) exactly which line of YOUR code broke. Everything above is context.

---

## Prompt templates — for when you're not coding from scratch

### Building something new

```
I want to [GOAL].
Constraints:
  - Use only [LIBRARIES]
  - I have no [API key / login / paid access]
  - Output: [CSV / DataFrame] with columns [LIST]
Edge cases: [rate limits / pagination / missing fields]
Add comments explaining each block.
```

### Fixing an error

```
My code threw this error:
  [PASTE FULL TRACEBACK]

Here's the code:
  [PASTE THE CELL]

What I was trying to do:
  [ONE SENTENCE]

What I already tried:
  [LIST or "nothing yet"]

Explain what went wrong and give me the fix.
```

### Adapting code to a new site

```
Working scraper for [SOURCE A]:
  [PASTE CODE]

I want to adapt it for [SOURCE B]. Differences:
  - URL pattern: [NEW]
  - Field names: [OLD] → [NEW]

Modify minimally — keep the structure.
```

### Inspecting a new page

```
Here's the HTML structure of a page I want to scrape:
  [PASTE soup.prettify()[:2000]]

I want to extract: [FIELD 1], [FIELD 2], [FIELD 3]

Give me the BeautifulSoup selectors and a loop that builds a DataFrame.
```

### Cleaning scraped data

```
I scraped this and got:
  [PASTE df.head(5)]

Problems:
  - [e.g. dates inconsistent]
  - [e.g. prices have $ and commas]
  - [e.g. duplicates]

Write pandas code to clean these. Show before-and-after.
```

---

## What to PASTE vs what NOT to paste in your prompt

| Paste this | Not this |
|---|---|
| Full error message + traceback | "It gave me an error" |
| The exact code that broke | The whole 400-line file |
| Sample output (`df.head()`, first 500 chars of HTML) | Description in words |
| Small HTML snippet or URL | Screenshot of code |
| What you already tried | Nothing |
| Your goal in one sentence | "It's not working" |

**Biggest mistake non-coders make**: describing the problem instead of pasting evidence. LLMs need text patterns. Paste the weird output, get a fix in 30 seconds.

---

## How to write a good prompt to an LLM

> "I want to download Reddit posts mentioning 'crude oil' from r/investing
> between Jan 2020 and Dec 2023. I'd prefer the Arctic Shift API since I
> have no Reddit API key. Output should be a CSV with date, title, score,
> and permalink. Add rate-limit handling and resume support. Use Python
> with requests and pandas only."

**Five things every prompt needs**: goal, constraint, tools, output format, edge cases.

---

## Practice sites (safe to scrape)

- `quotes.toscrape.com` — quotes with authors and tags
- `books.toscrape.com` — books with prices, ratings
- `httpbin.org` — for testing requests, headers, etc.
- `webscraper.io/test-sites` — variety of practice scenarios

## Real research sources (no scraping needed — they give you APIs/dumps)

- **GDELT** (`data.gdeltproject.org`) — global news events, every 15 min
- **Arctic Shift** (`arctic-shift.photon-reddit.com`) — Reddit historical
- **Common Crawl** (`commoncrawl.org`) — petabytes of crawled web
- **OpenAlex** (`openalex.org`) — academic papers and citations
- **data.gov, data.gov.in, data.worldbank.org** — government open data

---

## Three rules to take home

1. **time.sleep(1)** between requests. Always. No exceptions.
2. **Set a User-Agent**. Looks like a browser, behaves like a researcher.
3. **Check for an API first**. Scraping is the fallback, not the default.

---

*If you get stuck, the error message is more useful than the code that produced it. Paste the error into your LLM with the question "why am I getting this?" — that single habit will save you weeks.*
