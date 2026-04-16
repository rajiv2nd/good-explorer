"""Amazon India scraper."""

from __future__ import annotations

from goodexplorer.models import ProductResult
from goodexplorer.scrapers.base import BaseScraper


class AmazonScraper(BaseScraper):
    """Scraper for Amazon.in — mid-range prices, next-day delivery."""

    name = "Amazon"
    platform_color = "#FF9900"
    platform_logo = "🅰️"
    delivery_time = "Tomorrow"
    base_url = "https://www.amazon.in"
    price_variance = (-0.03, 0.08)

    async def _real_search(
        self, query: str, quantity: str, pincode: str
    ) -> list[ProductResult]:
        """Real scraping via amazon.in/s?k={query} — not implemented, falls back to mock."""
        return []
