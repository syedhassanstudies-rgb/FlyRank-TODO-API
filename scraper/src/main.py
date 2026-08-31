import requests
import os
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pydantic import BaseModel, field_validator
from typing import Optional
import time

# ── Config ────────────────────────────────────────────────
BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "../cache")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../output")
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/syedhassanstudies-rgb/FlyRank-TODO-API)"
}
DELAY = 0.5
TIMEOUT = 10

# ── Pydantic Schema ───────────────────────────────────────
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    rating: int
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator("product_url")
    def must_be_absolute(cls, v):
        assert v.startswith("https://"), "URL must be absolute"
        return v

    @field_validator("price_gbp")
    def must_be_positive(cls, v):
        assert v > 0, "Price must be positive"
        return v

# ── Helpers ───────────────────────────────────────────────
def fetch(url: str, cache_name: str) -> str:
    cache_path = os.path.join(CACHE_DIR, cache_name)
    if os.path.exists(cache_path):
        print(f"CACHE HIT: {cache_name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    print(f"FETCH: {url}")
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url} — status {response.status_code}")
    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved {len(html)} bytes to {cache_name}")
    time.sleep(DELAY)
    return html

def parse_price(price_text: str) -> float:
    # Remove any non-numeric characters except . and digits
    cleaned = ''.join(c for c in price_text if c.isdigit() or c == '.')
    return float(cleaned)

# ── Stage 2: Discover all book URLs ──────────────────────
def discover_books() -> list[str]:
    book_urls = []
    page_url = "https://books.toscrape.com/catalogue/page-1.html"
    pages_fetched = 0

    while page_url and pages_fetched < 3:
        cache_name = f"catalogue-page-{pages_fetched + 1}.html"
        html = fetch(page_url, cache_name)
        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod"):
            href = article.select_one("a")["href"]
            absolute = urljoin(page_url, href)
            book_urls.append(absolute)

        next_btn = soup.select_one("li.next a")
        page_url = urljoin(page_url, next_btn["href"]) if next_btn else None
        pages_fetched += 1

    unique = list(dict.fromkeys(book_urls))
    print(f"\ncatalogue_pages={pages_fetched}, discovered={len(book_urls)}, unique_urls={len(unique)}")
    return unique

# ── Stage 3: Extract raw record ───────────────────────────
def extract_book(url: str, source_page: str) -> dict:
    cache_name = url.split("/")[-2] + ".html"
    html = fetch(url, cache_name)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").text.strip()
    price_text = soup.select_one("p.price_color").text.strip()
    availability_text = soup.select_one("p.availability").text.strip()
    rating_text = soup.select_one("p.star-rating")["class"][1]
    desc_tag = soup.select_one("#product_description ~ p")
    description = desc_tag.text.strip() if desc_tag else None

    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

# ── Stage 4: Validate and store ───────────────────────────
def validate_and_store(raw: dict) -> Optional[Book]:
    try:
        book = Book(
            **raw,
            price_gbp=parse_price(raw["price_text"]),
            rating=RATING_MAP.get(raw["rating_text"], 0)
        )
        return book
    except Exception as e:
        print(f"VALIDATION ERROR: {e}")  # add this line
        return None

# ── Stage 5: Run with error handling ─────────────────────
def run():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    start = datetime.now(timezone.utc)
    cache_hits_before = 0
    valid_records = []
    invalid_records = []
    failed_pages = []

    book_urls = discover_books()

    # Add one fake URL to test failure handling
    test_urls = book_urls + ["https://books.toscrape.com/catalogue/fake-book-does-not-exist/index.html"]

    for url in test_urls:
        try:
            raw = extract_book(url, source_page="https://books.toscrape.com/catalogue/page-1.html")
            print(f"RAW: {raw}")
            book = validate_and_store(raw)
            if book:
                valid_records.append(book.model_dump())
            else:
                invalid_records.append({"url": url, "reason": "Validation failed"})
        except Exception as e:
            print(f"FAILED: {url} — {e}")
            failed_pages.append({"url": url, "reason": str(e)})

    # Deduplicate by product_url
    seen = set()
    unique_records = []
    for r in valid_records:
        if r["product_url"] not in seen:
            seen.add(r["product_url"])
            unique_records.append(r)

    # Write outputs
    with open(os.path.join(OUTPUT_DIR, "books.json"), "w", encoding="utf-8") as f:
        json.dump(unique_records, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "errors.json"), "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2)

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    report = {
        "start_time": start.isoformat(),
        "duration_seconds": round(duration, 2),
        "catalogue_pages": 3,
        "valid_records": len(unique_records),
        "invalid_records": len(invalid_records),
        "failed_pages": len(failed_pages),
        "failed_urls": failed_pages
    }

    with open(os.path.join(OUTPUT_DIR, "run-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Done — {len(unique_records)} books, {len(failed_pages)} failed, {round(duration, 2)}s")
    print(f"Report: {report}")

if __name__ == "__main__":
    run()