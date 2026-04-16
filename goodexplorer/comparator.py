"""Price comparison logic — finds cheapest options across platforms."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from goodexplorer.models import ComparisonResult, ProductResult, SearchItem
from goodexplorer.scrapers import ALL_SCRAPERS

logger = logging.getLogger(__name__)


async def compare_single_item(
    item: SearchItem, pincode: str = "110001"
) -> ComparisonResult:
    """Compare a single item across all platforms concurrently."""
    scrapers = [cls() for cls in ALL_SCRAPERS]

    try:
        tasks = [
            scraper.search(item.name, item.quantity, pincode)
            for scraper in scrapers
        ]
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: list[ProductResult] = []
        for result in platform_results:
            if isinstance(result, Exception):
                logger.warning("Scraper error: %s", result)
                continue
            all_results.extend(r for r in result if r.in_stock)

        # Find cheapest
        cheapest = min(all_results, key=lambda r: r.price) if all_results else None

        return ComparisonResult(
            search_term=item.name,
            requested_quantity=item.quantity,
            cheapest=cheapest,
            results=sorted(all_results, key=lambda r: r.price),
        )
    finally:
        for scraper in scrapers:
            await scraper.close()


async def compare_items(
    items: list[SearchItem], pincode: str = "110001"
) -> list[ComparisonResult]:
    """Compare multiple items across all platforms."""
    tasks = [compare_single_item(item, pincode) for item in items]
    return await asyncio.gather(*tasks)


def build_optimized_cart(
    comparisons: list[ComparisonResult],
) -> dict:
    """Find the optimal platform split to minimize total cost.

    Returns a dict with:
      - optimized_cart: {platform: [{item, quantity, price}]}
      - optimized_total: total cost of optimized cart
      - single_platform_totals: {platform: total}
      - best_single_platform: cheapest single-platform option
      - savings: how much the optimized cart saves vs best single platform
    """
    platform_totals: dict[str, float] = defaultdict(float)
    optimized_cart: dict[str, list[dict]] = defaultdict(list)
    optimized_total = 0.0

    for comp in comparisons:
        if not comp.cheapest:
            continue

        platform = comp.cheapest.platform
        optimized_cart[platform].append({
            "item": comp.search_term,
            "quantity": comp.requested_quantity,
            "price": comp.cheapest.price,
            "product_url": comp.cheapest.product_url,
        })
        optimized_total += comp.cheapest.price

        for result in comp.results:
            platform_totals[result.platform] += result.price

    best_single_platform = ""
    best_single_total = float("inf")
    for platform, total in platform_totals.items():
        if total < best_single_total:
            best_single_total = total
            best_single_platform = platform

    savings = round(best_single_total - optimized_total, 2) if best_single_total < float("inf") else 0.0

    return {
        "optimized_cart": dict(optimized_cart),
        "optimized_total": round(optimized_total, 2),
        "single_platform_totals": {k: round(v, 2) for k, v in platform_totals.items()},
        "best_single_platform": best_single_platform,
        "best_single_total": round(best_single_total, 2) if best_single_total < float("inf") else 0.0,
        "savings": max(savings, 0.0),
    }
