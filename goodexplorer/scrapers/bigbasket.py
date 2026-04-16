"""BigBasket scraper."""

from __future__ import annotations

from goodexplorer.models import ProductResult
from goodexplorer.scrapers.base import BaseScraper


class BigBasketScraper(BaseScraper):
    """Scraper for BigBasket — grocery specialist, 2-4 hour delivery, often cheapest."""

    name = "BigBasket"
    platform_color = "#84C225"
    platform_logo = "🧺"
    delivery_time = "2-4 hours"
    base_url = "https://www.bigbasket.com"
    price_variance = (-0.08, 0.05)

    async def _real_search(
        self, query: str, quantity: str, pincode: str
    ) -> list[ProductResult]:
        """Real scraping via bigbasket.com — not implemented."""
        return []
