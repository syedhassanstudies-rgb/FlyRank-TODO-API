## Reviewer Note

This is Assignment A9 — The Polite Scraper.
Built inside the same repo as the FlyRank TODO API (A1-A4).
The scraper lives in the scraper/ folder and is completely independent of the API code.

# Polite Scraper — Books to Scrape

## Target Classification

- **Site:** Books to Scrape (https://books.toscrape.com)
- **Type:** Public sandbox — built specifically for scraping practice
- **Scope:** First 3 catalogue pages only (60 books)
- **Data collected:** Title, price, availability, rating, description, URL
- **robots.txt:** Checked at https://books.toscrape.com/robots.txt — no restrictions found
- **Why appropriate:** This site exists for this exact purpose

I will not reuse this code on another site without checking its rules and terms first.

## How to Run

From the repo root:

    uv run python scraper/src/main.py

First run fetches all pages and caches them. Every run after reads from cache.
Output is saved to scraper/output/

## Installation

    uv add requests beautifulsoup4 pydantic

## Record Schema

Each validated book record contains:

| Field | Type | Description |
|-------|------|-------------|
| title | string | Book title |
| product_url | string | Absolute URL to book page |
| price_text | string | Raw price e.g. £51.77 |
| price_gbp | float | Cleaned numeric price e.g. 51.77 |
| availability_text | string | Raw availability text |
| rating_text | string | Raw rating e.g. Three |
| rating | int | Numeric rating 1-5 |
| description | string or null | Book description (null if missing) |
| source_page | string | Catalogue page URL this book was found on |
| fetched_at | string | ISO 8601 UTC timestamp of when it was fetched |

## Politeness Rules

- **User-Agent:** FlyRankInternshipA9/1.0 (+https://github.com/syedhassanstudies-rgb/FlyRank-TODO-API)
- **Delay:** 500ms minimum between every real request
- **Timeout:** 10 seconds — requests never hang forever
- **Cache:** HTML is saved locally after first fetch — development never hits the site twice
- **Status check:** Only 200 responses are parsed — anything else is logged as a failure

## Output Files

- books.json — 60 validated, unique book records
- errors.json — any records that failed schema validation
- run-report.json — summary of every run

## Sample Run Report

    {
      "start_time": "2026-08-31T13:01:38.729797+00:00",
      "duration_seconds": 6.99,
      "catalogue_pages": 3,
      "valid_records": 60,
      "invalid_records": 0,
      "failed_pages": 1,
      "failed_urls": [
        {
          "url": "https://books.toscrape.com/catalogue/fake-book-does-not-exist/index.html",
          "reason": "Failed to fetch — status 404"
        }
      ]
    }

## Why No Browser Was Needed

The data is already present in the HTML the server sends. A browser would only add
memory overhead and complexity. A plain HTTP request is faster, cheaper, and sufficient
when the content is server-rendered.

## Error Handling

- Each page is handled separately — one broken page never crashes the run
- 404 errors are logged and skipped — retrying a missing page wastes requests
- All failed URLs are recorded in run-report.json with their reason

## Ethics Note

Use an official API when one exists — scraping is a last resort, not a first choice.
Never bypass logins, paywalls, or blocks — if a site says no, respect it.
Collect only what you need — this scraper takes 3 pages, not the whole site.
Identify yourself honestly in the user-agent so site owners know who you are.

## Limitation

Data is only as fresh as the last run. The cache never expires automatically — delete
the cache/ folder and rerun to get updated prices or availability.

## Tech Stack

- Python 3.11
- requests
- BeautifulSoup4
- Pydantic v2
- uv