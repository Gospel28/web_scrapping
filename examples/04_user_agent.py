"""
Example 4 — User-Agent header (the 403 fix)

Site: en.wikipedia.org
Goal: extract the title and first paragraph of a Wikipedia article.

Run with:
    uv run python examples/04_user_agent.py

Why this example?
Many sites block requests that look like bots. The default User-Agent
that Python sends is literally "python-requests/2.x.x" — which screams
"I am a bot, please block me."

The fix is one header. Pretend to be a real browser. This single change
solves most 403 Forbidden errors you'll ever encounter.
"""

import requests
from bs4 import BeautifulSoup


# This is what a real Chrome browser sends. Copy-paste it into all your scrapers.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def main():
    url = "https://en.wikipedia.org/wiki/Web_scraping"

    # WITHOUT User-Agent — works on Wikipedia, but many sites would refuse
    r = requests.get(url, timeout=30)
    print(f"Without User-Agent: status {r.status_code}, length {len(r.text)}")

    # WITH User-Agent — the safer default for all scraping
    r = requests.get(url, headers=HEADERS, timeout=30)
    print(f"With User-Agent:    status {r.status_code}, length {len(r.text)}\n")

    soup = BeautifulSoup(r.text, "lxml")

    # Page title
    title = soup.find("h1").get_text(strip=True)
    print(f"Title: {title}\n")

    # First real paragraph (skipping empty placeholder paragraphs)
    first_para = soup.find("p", class_=lambda c: c != "mw-empty-elt").get_text(strip=True)
    print("First paragraph:")
    print(first_para[:400] + "...")


if __name__ == "__main__":
    main()
