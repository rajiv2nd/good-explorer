"""Base scraper with shared mock price database for Indian grocery items."""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from typing import ClassVar

import httpx

from goodexplorer.models import ProductResult

logger = logging.getLogger(__name__)

# Realistic base prices in INR for common Indian grocery/household items.
# Each platform scraper applies its own variance to these base prices.
MOCK_PRICE_DB: dict[str, dict] = {
    # Staples
    "rice 1kg": {"base": 65, "mrp": 75, "img": "🍚"},
    "rice 5kg": {"base": 310, "mrp": 350, "img": "🍚"},
    "basmati rice 1kg": {"base": 145, "mrp": 170, "img": "🍚"},
    "basmati rice 5kg": {"base": 680, "mrp": 780, "img": "🍚"},
    "wheat flour 1kg": {"base": 42, "mrp": 50, "img": "🌾"},
    "wheat flour 5kg": {"base": 195, "mrp": 230, "img": "🌾"},
    "atta 1kg": {"base": 42, "mrp": 50, "img": "🌾"},
    "atta 5kg": {"base": 195, "mrp": 230, "img": "🌾"},
    "aashirvaad atta 5kg": {"base": 245, "mrp": 280, "img": "🌾"},
    "sugar 1kg": {"base": 44, "mrp": 52, "img": "🍬"},
    "sugar 5kg": {"base": 210, "mrp": 250, "img": "🍬"},
    "salt 1kg": {"base": 22, "mrp": 25, "img": "🧂"},
    "tata salt 1kg": {"base": 24, "mrp": 28, "img": "🧂"},
    "jaggery 1kg": {"base": 85, "mrp": 100, "img": "🍯"},
    # Dairy
    "milk 1l": {"base": 60, "mrp": 64, "img": "🥛"},
    "amul milk 1l": {"base": 62, "mrp": 66, "img": "🥛"},
    "curd 400g": {"base": 35, "mrp": 40, "img": "🥛"},
    "paneer 200g": {"base": 80, "mrp": 90, "img": "🧀"},
    "paneer 500g": {"base": 180, "mrp": 210, "img": "🧀"},
    "amul butter 500g": {"base": 270, "mrp": 295, "img": "🧈"},
    "butter 500g": {"base": 270, "mrp": 295, "img": "🧈"},
    "amul butter 100g": {"base": 56, "mrp": 62, "img": "🧈"},
    "cheese 200g": {"base": 99, "mrp": 115, "img": "🧀"},
    "amul cheese 200g": {"base": 99, "mrp": 115, "img": "🧀"},
    "ghee 1l": {"base": 540, "mrp": 610, "img": "🫕"},
    "amul ghee 1l": {"base": 560, "mrp": 625, "img": "🫕"},
    # Bread & Eggs
    "bread": {"base": 40, "mrp": 45, "img": "🍞"},
    "brown bread": {"base": 50, "mrp": 55, "img": "🍞"},
    "eggs 12": {"base": 72, "mrp": 84, "img": "🥚"},
    "eggs 6": {"base": 39, "mrp": 45, "img": "🥚"},
    "eggs 30": {"base": 175, "mrp": 210, "img": "🥚"},
    # Cooking Oils
    "cooking oil 1l": {"base": 155, "mrp": 180, "img": "🫒"},
    "mustard oil 1l": {"base": 170, "mrp": 195, "img": "🫒"},
    "sunflower oil 1l": {"base": 145, "mrp": 170, "img": "🫒"},
    "fortune sunflower oil 1l": {"base": 150, "mrp": 175, "img": "🫒"},
    "olive oil 500ml": {"base": 420, "mrp": 499, "img": "🫒"},
    "refined oil 1l": {"base": 140, "mrp": 165, "img": "🫒"},
    # Beverages
    "tea 250g": {"base": 110, "mrp": 130, "img": "🍵"},
    "tata tea 250g": {"base": 115, "mrp": 135, "img": "🍵"},
    "green tea 25 bags": {"base": 145, "mrp": 175, "img": "🍵"},
    "coffee 200g": {"base": 310, "mrp": 370, "img": "☕"},
    "nescafe 200g": {"base": 340, "mrp": 395, "img": "☕"},
    "bru coffee 200g": {"base": 295, "mrp": 350, "img": "☕"},
    # Pulses & Lentils
    "toor dal 1kg": {"base": 145, "mrp": 170, "img": "🫘"},
    "moong dal 1kg": {"base": 130, "mrp": 155, "img": "🫘"},
    "chana dal 1kg": {"base": 95, "mrp": 115, "img": "🫘"},
    "masoor dal 1kg": {"base": 105, "mrp": 125, "img": "🫘"},
    "urad dal 1kg": {"base": 135, "mrp": 160, "img": "🫘"},
    "rajma 1kg": {"base": 155, "mrp": 185, "img": "🫘"},
    "chole 1kg": {"base": 110, "mrp": 130, "img": "🫘"},
    # Vegetables
    "onion 1kg": {"base": 35, "mrp": 45, "img": "🧅"},
    "potato 1kg": {"base": 30, "mrp": 40, "img": "🥔"},
    "tomato 1kg": {"base": 40, "mrp": 50, "img": "🍅"},
    "ginger 250g": {"base": 30, "mrp": 40, "img": "🫚"},
    "garlic 250g": {"base": 35, "mrp": 45, "img": "🧄"},
    "green chilli 100g": {"base": 12, "mrp": 18, "img": "🌶️"},
    "capsicum 250g": {"base": 30, "mrp": 40, "img": "🫑"},
    "carrot 500g": {"base": 30, "mrp": 38, "img": "🥕"},
    "cucumber 500g": {"base": 25, "mrp": 32, "img": "🥒"},
    # Fruits
    "banana 1 dozen": {"base": 45, "mrp": 55, "img": "🍌"},
    "apple 1kg": {"base": 160, "mrp": 200, "img": "🍎"},
    "mango 1kg": {"base": 120, "mrp": 150, "img": "🥭"},
    "orange 1kg": {"base": 80, "mrp": 100, "img": "🍊"},
    # Spices
    "turmeric powder 100g": {"base": 35, "mrp": 42, "img": "🌿"},
    "red chilli powder 100g": {"base": 40, "mrp": 48, "img": "🌶️"},
    "coriander powder 100g": {"base": 32, "mrp": 38, "img": "🌿"},
    "cumin seeds 100g": {"base": 55, "mrp": 65, "img": "🌿"},
    "garam masala 100g": {"base": 65, "mrp": 78, "img": "🌿"},
    "mdh chana masala 100g": {"base": 58, "mrp": 70, "img": "🌿"},
    # Personal Care & Household
    "soap": {"base": 38, "mrp": 45, "img": "🧼"},
    "shampoo 200ml": {"base": 145, "mrp": 175, "img": "🧴"},
    "toothpaste 200g": {"base": 95, "mrp": 110, "img": "🪥"},
    "colgate 200g": {"base": 105, "mrp": 120, "img": "🪥"},
    "detergent 1kg": {"base": 110, "mrp": 135, "img": "🧹"},
    "surf excel 1kg": {"base": 125, "mrp": 145, "img": "🧹"},
    "vim bar": {"base": 22, "mrp": 28, "img": "🧽"},
    "harpic 500ml": {"base": 95, "mrp": 115, "img": "🧹"},
    "tissue paper": {"base": 45, "mrp": 55, "img": "🧻"},
    # Snacks & Instant
    "maggi 4 pack": {"base": 52, "mrp": 60, "img": "🍜"},
    "maggi 12 pack": {"base": 144, "mrp": 168, "img": "🍜"},
    "biscuits": {"base": 30, "mrp": 35, "img": "🍪"},
    "parle g": {"base": 10, "mrp": 10, "img": "🍪"},
    "chips": {"base": 20, "mrp": 25, "img": "🥔"},
    "lays chips": {"base": 20, "mrp": 20, "img": "🥔"},
    "namkeen 200g": {"base": 55, "mrp": 65, "img": "🥜"},
    "haldiram namkeen 200g": {"base": 60, "mrp": 70, "img": "🥜"},
    "poha 500g": {"base": 38, "mrp": 45, "img": "🍚"},
    "oats 500g": {"base": 110, "mrp": 135, "img": "🥣"},
    "cornflakes 500g": {"base": 175, "mrp": 210, "img": "🥣"},
}


def _fuzzy_match(query: str) -> str | None:
    """Find the best matching item key for a search query."""
    query_lower = query.lower().strip()

    # Exact match
    if query_lower in MOCK_PRICE_DB:
        return query_lower

    # Substring match — find keys that contain the query or vice versa
    candidates: list[str] = []
    for key in MOCK_PRICE_DB:
        if query_lower in key or key in query_lower:
            candidates.append(key)

    # Word-overlap match as fallback
    if not candidates:
        scored: list[tuple[int, str]] = []
        query_words = set(query_lower.split())
        for key in MOCK_PRICE_DB:
            key_words = set(key.split())
            overlap = len(query_words & key_words)
            if overlap:
                scored.append((overlap, key))
        if scored:
            scored.sort(reverse=True)
            return scored[0][1]

    if candidates:
        # Prefer shorter keys (more specific matches)
        candidates.sort(key=len)
        return candidates[0]

    return None


class BaseScraper(ABC):
    """Abstract base class for platform scrapers.

    Each platform scraper extends this class and provides:
    - Platform metadata (name, color, logo, delivery time, base URL)
    - A price_variance range that simulates platform-specific pricing
    - An optional _real_search() for actual HTTP scraping
    """

    name: ClassVar[str] = ""
    platform_color: ClassVar[str] = ""
    platform_logo: ClassVar[str] = ""
    delivery_time: ClassVar[str] = ""
    base_url: ClassVar[str] = ""
    # Price variance range as (low_pct, high_pct) relative to base price
    price_variance: ClassVar[tuple[float, float]] = (-0.05, 0.10)

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            },
            follow_redirects=True,
        )

    async def search(
        self, query: str, quantity: str = "", pincode: str = "110001"
    ) -> list[ProductResult]:
        """Search for products. Tries real scraping, falls back to demo data."""
        try:
            results = await self._real_search(query, quantity, pincode)
            if results:
                return results
        except Exception as exc:
            logger.debug("Real search failed for %s on %s: %s", query, self.name, exc)

        return self._mock_search(query, quantity)

    @abstractmethod
    async def _real_search(
        self, query: str, quantity: str, pincode: str
    ) -> list[ProductResult]:
        """Attempt real HTTP scraping. Override in subclasses."""
        ...

    def _mock_search(self, query: str, quantity: str) -> list[ProductResult]:
        """Generate realistic mock results based on the price database."""
        search_key = f"{query} {quantity}".lower().strip()
        matched_key = _fuzzy_match(search_key) or _fuzzy_match(query)

        if not matched_key:
            base_price = random.uniform(30, 300)
            mrp = round(base_price * 1.15, 2)
            emoji = "🛒"
        else:
            item_data = MOCK_PRICE_DB[matched_key]
            base_price = item_data["base"]
            mrp = item_data["mrp"]
            emoji = item_data.get("img", "🛒")

        # Apply platform-specific variance
        low, high = self.price_variance
        variance = random.uniform(low, high)
        price = round(base_price * (1 + variance), 2)

        # Occasionally mark items as out of stock (5% chance)
        in_stock = random.random() > 0.05

        product_name = f"{query.title()} {quantity}".strip()
        discount_pct = round((1 - price / mrp) * 100, 1) if mrp and price < mrp else 0.0

        return [
            ProductResult(
                platform=self.name,
                platform_logo=self.platform_logo,
                product_name=product_name,
                price=price,
                mrp=mrp,
                discount_pct=max(discount_pct, 0.0),
                quantity=quantity,
                delivery_time=self.delivery_time,
                in_stock=in_stock,
                product_url=f"{self.base_url}/search?q={query.replace(' ', '+')}",
                image_url=emoji,
            )
        ]

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
