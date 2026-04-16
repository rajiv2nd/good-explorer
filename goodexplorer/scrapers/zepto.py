"""Zepto scraper."""

from __future__ import annotations

from goodexplorer.models import ProductResult
from goodexplorer.scrapers.base import BaseScraper


class ZeptoScraper(BaseScraper):
    """Scraper for Zepto — quick commerce, 10 min delivery, slight premium."""

    name = "Zepto"
    platform_color = "#7B2D8E"
    platform_logo = "🚀"
    delivery_time = "10 min"
    base_url = "https://www.zeptonow.com"
    price_variance = (0.02, 0.15)

    async def _real_search(
        self, query: str, quantity: str, pincode: str
    ) -> list[ProductResult]:
        """Real scraping via zeptonow.com — not implemented."""
        return []
