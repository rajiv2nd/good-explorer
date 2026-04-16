"""Flipkart scraper."""

from __future__ import annotations

from goodexplorer.models import ProductResult
from goodexplorer.scrapers.base import BaseScraper


class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart — competitive prices, 2-3 day delivery."""

    name = "Flipkart"
    platform_color = "#2874F0"
    platform_logo = "🛍️"
    delivery_time = "2-3 days"
    base_url = "https://www.flipkart.com"
    price_variance = (-0.05, 0.07)

    async def _real_search(
        self, query: str, quantity: str, pincode: str
    ) -> list[ProductResult]:
        """Real scraping via flipkart.com/search — not implemented."""
        return []
