"""Blinkit scraper."""

from __future__ import annotations

from goodexplorer.models import ProductResult
from goodexplorer.scrapers.base import BaseScraper


class BlinkitScraper(BaseScraper):
    """Scraper for Blinkit — quick commerce, 10-15 min delivery, slight premium."""

    name = "Blinkit"
    platform_color = "#F8CB46"
    platform_logo = "⚡"
    delivery_time = "10-15 min"
    base_url = "https://blinkit.com"
    price_variance = (0.0, 0.15)

    async def _real_search(
        self, query: str, quantity: str, pincode: str
    ) -> list[ProductResult]:
        """Real scraping via blinkit.com/v6/search — not implemented."""
        return []
