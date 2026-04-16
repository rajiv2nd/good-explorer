"""FastAPI application entry point for Good Explorer."""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from goodexplorer.comparator import build_optimized_cart, compare_items, compare_single_item
from goodexplorer.models import ComparisonResult, SearchItem, SearchRequest
from goodexplorer.scrapers import ALL_SCRAPERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Good Explorer",
    description="Compare grocery & household prices across Indian e-commerce platforms",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend() -> HTMLResponse:
    """Serve the single-page frontend."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


@app.post("/api/search")
async def search_items(request: SearchRequest) -> dict:
    """Search items across all platforms and return comparisons."""
    comparisons = await compare_items(request.items, request.pincode)
    return _build_response(comparisons)


@app.post("/api/search-single")
async def search_single(item: SearchItem, pincode: str = "110001") -> dict:
    """Search a single item across all platforms."""
    comparison = await compare_single_item(item, pincode)
    return comparison.model_dump()


@app.get("/api/platforms")
async def list_platforms() -> list[dict]:
    """List all supported platforms with metadata."""
    platforms = []
    for scraper_cls in ALL_SCRAPERS:
        scraper = scraper_cls()
        platforms.append({
            "name": scraper.name,
            "color": scraper.platform_color,
            "logo": scraper.platform_logo,
            "delivery_time": scraper.delivery_time,
            "url": scraper.base_url,
        })
        await scraper.close()
    return platforms


@app.post("/api/cart/optimize")
async def optimize_cart_endpoint(request: SearchRequest) -> dict:
    """Find the cheapest combination of platforms for a list of items."""
    comparisons = await compare_items(request.items, request.pincode)
    return build_optimized_cart(comparisons)


def _build_response(comparisons: list[ComparisonResult]) -> dict:
    """Build a search response dict from comparison results."""
    total_cheapest = sum(c.cheapest.price for c in comparisons if c.cheapest)

    all_prices = [r.price for c in comparisons for r in c.results]
    platform_count = len(ALL_SCRAPERS)
    total_average = sum(all_prices) / platform_count if platform_count and all_prices else 0.0
    total_savings = round(total_average - total_cheapest, 2) if total_average else 0.0

    platform_wins = Counter(
        c.cheapest.platform for c in comparisons if c.cheapest
    )
    best_platform = platform_wins.most_common(1)[0][0] if platform_wins else ""

    return {
        "comparisons": [c.model_dump() for c in comparisons],
        "total_cheapest": round(total_cheapest, 2),
        "total_average": round(total_average, 2),
        "total_savings": max(total_savings, 0.0),
        "best_platform": best_platform,
    }


def main() -> None:
    """Entry point for the CLI command."""
    import uvicorn
    uvicorn.run("goodexplorer.app:app", host="0.0.0.0", port=8000, reload=True)
