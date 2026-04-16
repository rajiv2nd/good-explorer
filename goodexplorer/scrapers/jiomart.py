"""JioMart scraper."""

from __future__ import annotations

from goodexplorer.models import ProductResult
from goodexplorer.scrapers.base import BaseScraper


class JioMartScraper(BaseScraper):
    """Scraper for JioMart — often cheapest, 1-2 day delivery."""

    name = "JioMart"
    platform_color = "#0078AD"
    platform_logo = "🏪"
    delivery_time = "1-2 days"
    base_url = "https://www.jiomart.com"
    price_variance = (-0.10, 0.03)

    async def _real_search(
        self, query: str, quantity: str, pincode: str
    ) -> list[ProductResult]:
        """Real scraping via jiomart.com/search — not implemented."""
        return []
