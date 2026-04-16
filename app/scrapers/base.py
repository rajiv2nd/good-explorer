"""Base scraper interface for all platforms."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class ProductResult:
    """A single product result from a platform."""
    name: str
    price: float
    unit: str = ""
    quantity: str = ""
    image_url: str = ""
    product_url: str = ""
    platform: str = ""
    delivery_time: str = ""
    in_stock: bool = True
    rating: float = 0.0
    original_price: float = 0.0
    discount_pct: float = 0.0


class BaseScraper(ABC):
    """Abstract base for all platform scrapers."""

    platform_name: str = "Unknown"
    platform_icon: str = "🛒"
    base_url: str = ""

    @abstractmethod
    async def search(self, query: str, quantity: str = "") -> list[ProductResult]:
        """Search for a product and return results."""
        ...
