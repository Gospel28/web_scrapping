"""
Example 7 — Selenium: scrape a JavaScript-rendered page

Site: quotes.toscrape.com/js/  (the JavaScript version of the same site
      we used in Example 1)
Goal: show that requests fails on this page, then succeed with Selenium.

Run with:
    uv run python examples/07_selenium_js_page.py

Why this example?
Modern websites build themselves with JavaScript AFTER the page loads.
The server sends a skeleton, the browser runs JavaScript, and only then
does the content appear. requests can't run JavaScript — it just downloads
what the server sent. So for these pages, we need something that actually
runs JavaScript: Selenium (or its modern cousin, Playwright).

Selenium is 5-10x slower than requests. Use it ONLY when needed.
The decision rule:
    - Press Ctrl+U on the page in your browser (View Source)
    - If your data is in the source → use requests
    - If your data is NOT in the source → use Selenium
"""

import time
import requests
from bs4 import BeautifulSoup
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


URL = "https://quotes.toscrape.com/js/"


def show_requests_fails():
    """Demonstrate that plain requests can't see the data on a JS-rendered page."""
    print("=" * 60)
    print("Step 1: Try with plain requests (the WRONG tool for this page)")
    print("=" * 60)
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "lxml")
    quotes = soup.find_all("div", class_="quote")
    print(f"Status: {r.status_code}")
    print(f"Quotes found with requests: {len(quotes)}")
    print("(Server only sent the skeleton — JavaScript builds the rest.)\n")


def build_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    """Create a Chrome driver with sensible defaults.
    
    Set headless=False if you want to SEE Chrome open during the demo
    (useful for teaching, slower in practice).
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # webdriver-manager auto-downloads the matching ChromeDriver — saves you
    # the version-mismatch headache that used to plague Selenium setups.
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def scrape_with_selenium() -> pd.DataFrame:
    """Use Selenium to render the page, then BeautifulSoup to parse it."""
    print("=" * 60)
    print("Step 2: Now with Selenium (the RIGHT tool for this page)")
    print("=" * 60)

    driver = build_chrome_driver(headless=True)
    try:
        driver.get(URL)
        time.sleep(2)  # let JavaScript finish rendering

        rendered_html = driver.page_source
        print(f"Rendered HTML length: {len(rendered_html)} characters")

        # From here, it's the SAME BeautifulSoup pattern as Example 1
        soup = BeautifulSoup(rendered_html, "lxml")
        quote_blocks = soup.find_all("div", class_="quote")
        print(f"Quotes found with Selenium: {len(quote_blocks)}\n")

        rows = []
        for q in quote_blocks:
            rows.append({
                "text": q.find("span", class_="text").get_text(strip=True),
                "author": q.find("small", class_="author").get_text(strip=True),
            })

        # Bonus: demonstrate interaction — click "Next" to go to page 2
        print("Bonus: clicking 'Next' to scrape page 2 too...")
        next_button = driver.find_element(By.CSS_SELECTOR, "li.next a")
        next_button.click()
        time.sleep(2)

        soup2 = BeautifulSoup(driver.page_source, "lxml")
        for q in soup2.find_all("div", class_="quote"):
            rows.append({
                "text": q.find("span", class_="text").get_text(strip=True),
                "author": q.find("small", class_="author").get_text(strip=True),
            })

        return pd.DataFrame(rows)

    finally:
        # ALWAYS close the browser — otherwise Chrome processes leak
        driver.quit()
        print("Browser closed cleanly.")


def main():
    show_requests_fails()
    df = scrape_with_selenium()

    output_path = "data/raw/quotes_js_selenium.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} quotes (across 2 pages) to {output_path}")
    print("\nFirst 5 quotes:")
    print(df.head(5))


if __name__ == "__main__":
    main()
