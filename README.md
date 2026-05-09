# Web Scraping for Researchers

A 1-hour lecture pack covering web scraping from beginner to intermediate, built around two real research scrapers (GDELT and Reddit) and a Selenium demo for JavaScript-rendered pages.

## What's in here

```
.
├── pyproject.toml              # uv dependencies
├── README.md                   # this file
│
├── notebook/
│   └── web_scraping_demo.ipynb # the live demo notebook
│
├── examples/                   # standalone runnable scripts
│   ├── 01_quotes_basic.py
│   ├── 02_pagination.py
│   ├── 03_books.py
│   ├── 04_user_agent.py
│   ├── 05_gdelt_one_day.py
│   ├── 06_reddit_arctic_shift.py
│   └── 07_selenium_js_page.py
│
├── scripts/                    # full production scrapers
│   ├── test.py                 # GDELT crude oil scraper (multi-year)
│   └── testreddit.py           # Reddit Arctic Shift scraper
│
├── docs/
│   ├── Lecturer_Pack.docx           # teaching script + Q&A defense
│   ├── Student_Handout.md           # 1-page reference
│   └── AI_Scraping_Playbook.docx    # error taxonomy + prompt patterns
│
└── data/
    └── raw/                    # scraped CSVs land here (gitignored)
```

## Setup (with uv)

If you don't have uv yet, install it once:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then in this folder:

```bash
# 1. uv reads pyproject.toml, creates a .venv, installs everything
uv sync

# 2. (optional) register the venv as a Jupyter kernel so the notebook can find it
uv run python -m ipykernel install --user --name=scraping-lecture --display-name "Scraping Lecture"
```

That's it. No `pip install`, no manual venv activation, no version juggling.

## Running things

**Run any standalone example:**

```bash
uv run python examples/01_quotes_basic.py
uv run python examples/05_gdelt_one_day.py
uv run python examples/07_selenium_js_page.py
```

**Open the notebook:**

```bash
uv run jupyter lab notebook/
```

When the notebook opens, pick the **Scraping Lecture** kernel from the kernel selector (top-right).

**Run the full GDELT or Reddit scrapers:**

```bash
uv run python scripts/test.py
uv run python scripts/testreddit.py
```

These are long-running. Read them, don't run them in a hurry.

## What you need installed (uv handles all of this)

| Library | What it does |
|---|---|
| `requests` | Fetches HTML and JSON over HTTP |
| `beautifulsoup4` | Parses HTML, finds elements |
| `lxml` | Fast parser used by BeautifulSoup |
| `pandas` | Stores data, saves to CSV |
| `tqdm` | Progress bars |
| `selenium` | Drives a real Chrome browser (for JS pages) |
| `webdriver-manager` | Auto-installs the right ChromeDriver |
| `jupyterlab` | The notebook environment |
| `ipykernel` | Lets the venv work as a Jupyter kernel |

## Selenium prerequisite

Selenium needs Google Chrome installed on your machine. Download it from [google.com/chrome](https://www.google.com/chrome/) if you don't have it.

`webdriver-manager` will download the matching ChromeDriver on first run automatically — no manual driver setup required.

## Quick troubleshooting

| Problem | Most likely fix |
|---|---|
| `ModuleNotFoundError` | Did you run `uv sync`? Are you in the project folder? |
| Notebook can't find libraries | Wrong kernel selected. Pick "Scraping Lecture" from the kernel picker |
| GDELT URL returns 404 | Try a different recent weekday in `examples/05_gdelt_one_day.py` |
| Selenium fails to start | Install Google Chrome. First run takes ~20 seconds to download driver |
| `403 Forbidden` on a site | Check the example with User-Agent header |
| `429 Too Many Requests` | You're going too fast. Add `time.sleep(2)` between requests |

For deeper troubleshooting, see `docs/AI_Scraping_Playbook.docx` — Part 3 has a full error taxonomy.

## Practice sites used in this lecture

- `quotes.toscrape.com` — quotes with authors and tags
- `quotes.toscrape.com/js/` — JavaScript-rendered version (for Selenium)
- `books.toscrape.com` — books with prices, ratings
- `en.wikipedia.org` — for the User-Agent example

All are scraping-friendly by design.

## Real research data sources (no scraping needed)

- **GDELT** — `data.gdeltproject.org` — global news events, every 15 min
- **Arctic Shift** — `arctic-shift.photon-reddit.com` — Reddit historical archive
- **Common Crawl** — `commoncrawl.org` — petabytes of crawled web
- **OpenAlex** — `openalex.org` — academic papers and citations
- **Government open data** — `data.gov`, `data.gov.in`, `data.worldbank.org`

If your research question can be answered with one of these, use it. Custom scraping is the fallback, not the default.

## License & ethics

The example scrapers in this repo only target sites explicitly designed for scraping practice. When applying these patterns to real sites, always:

1. Check the site's `robots.txt`
2. Read the terms of service
3. Add `time.sleep()` between requests
4. Identify yourself with a real `User-Agent`
5. If in doubt, email the site owner — many will say yes

Public data ≠ permission to scrape at any rate.
