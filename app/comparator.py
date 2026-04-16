"""Price comparison engine — runs scrapers in parallel."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict

from app.scrapers.amazon import AmazonScraper
from app.scrapers.base import BaseScraper, ProductResult
from app.scrapers.flipkart import FlipkartScraper
from app.scrapers.google_shopping import GoogleShoppingScraper
from app.scrapers.playwright_scraper import PlaywrightScraper

log = logging.getLogger(__name__)

ALL_SCRAPERS: list[BaseScraper] = [
    AmazonScraper(),
    FlipkartScraper(),
    GoogleShoppingScraper(),
    PlaywrightScraper("Blinkit"),
    PlaywrightScraper("BigBasket"),
    PlaywrightScraper("Zepto"),
]


async def compare_prices(
    query: str,
    quantity: str = "",
    platforms: list[str] | None = None,
) -> dict:
    """Search all platforms in parallel and return comparison."""
    scrapers = ALL_SCRAPERS
    if platforms:
        lower = [p.lower() for p in platforms]
        scrapers = [s for s in ALL_SCRAPERS if s.platform_name.lower() in lower]

    tasks = [s.search(query, quantity) for s in scrapers]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    platform_results: dict[str, list[dict]] = {}
    cheapest: dict | None = None
    cheapest_price = float("inf")

    for scraper, result in zip(scrapers, all_results):
        name = scraper.platform_name
        if isinstance(result, Exception):
            log.error("%s failed: %s", name, result)
            platform_results[name] = []
            continue

        items = [asdict(r) for r in result]
        platform_results[name] = items

        for item in items:
            if item["price"] > 0 and item["price"] < cheapest_price:
                cheapest_price = item["price"]
                cheapest = item

    return {
        "query": query,
        "quantity": quantity,
        "platforms": platform_results,
        "cheapest": cheapest,
        "platform_count": len(scrapers),
        "total_results": sum(len(v) for v in platform_results.values()),
    }


async def compare_list(items: list[dict]) -> list[dict]:
    """Compare prices for a list of items."""
    results = []
    for item in items:
        query = item.get("name", "")
        qty = item.get("quantity", "")
        if query:
            comparison = await compare_prices(query, qty)
            results.append(comparison)
    return results
