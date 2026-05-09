"""
Example 3 — Different site, same pattern

Site: books.toscrape.com
Goal: extract book titles, prices, and ratings from the homepage.

Run with:
    uv run python examples/03_books.py

Why this example? To show the 4-step pattern is universal.
Once you've scraped one site, you've scraped most sites.
The HTML structure is different — the THINKING is identical.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd


def main():
    url = "https://books.toscrape.com/"
    r = requests.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "lxml")

    # Each book is wrapped in <article class="product_pod">
    book_blocks = soup.find_all("article", class_="product_pod")
    print(f"Found {len(book_blocks)} books on the homepage\n")

    books = []
    for book in book_blocks:
        # Title is in the title attribute of the <a> inside <h3>
        title = book.find("h3").find("a")["title"]
        price = book.find("p", class_="price_color").get_text(strip=True)

        # Rating is encoded as the second class on <p class="star-rating Three">
        rating = book.find("p", class_="star-rating")["class"][1]

        # Stock availability
        stock = book.find("p", class_="instock availability").get_text(strip=True)

        books.append({
            "title": title,
            "price": price,
            "rating": rating,
            "stock": stock,
        })

    df = pd.DataFrame(books)
    output_path = "data/raw/books.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} books to {output_path}")
    print("\nFirst 5 books:")
    print(df.head(5))


if __name__ == "__main__":
    main()
