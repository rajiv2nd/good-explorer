"""Tests for the price comparator module."""

import pytest

from goodexplorer.comparator import compare_single_item, compare_items, build_optimized_cart
from goodexplorer.models import ComparisonResult, ProductResult, SearchItem


@pytest.mark.asyncio
async def test_compare_single_item_returns_results():
    """Searching for a known item should return results from all platforms."""
    item = SearchItem(name="Amul Butter", quantity="500g")
    result = await compare_single_item(item)

    assert isinstance(result, ComparisonResult)
    assert result.search_term == "Amul Butter"
    assert len(result.results) > 0
    assert result.cheapest is not None
    assert result.cheapest.price > 0


@pytest.mark.asyncio
async def test_compare_single_item_cheapest_is_minimum():
    """The cheapest result should have the lowest price."""
    item = SearchItem(name="Toor Dal", quantity="1kg")
    result = await compare_single_item(item)

    if result.cheapest and len(result.results) > 1:
        min_price = min(r.price for r in result.results)
        assert abs(result.cheapest.price - min_price) < 0.01


@pytest.mark.asyncio
async def test_compare_items_multiple():
    """Comparing multiple items should return one result per item."""
    items = [
        SearchItem(name="Rice", quantity="1kg"),
        SearchItem(name="Sugar", quantity="1kg"),
    ]
    results = await compare_items(items)

    assert len(results) == 2
    assert results[0].search_term == "Rice"
    assert results[1].search_term == "Sugar"


def test_build_optimized_cart():
    """Optimized cart should group cheapest items by platform."""
    comparisons = [
        ComparisonResult(
            search_term="Rice",
            requested_quantity="1kg",
            cheapest=ProductResult(
                platform="BigBasket",
                product_name="Rice 1kg",
                price=60.0,
                mrp=75.0,
                product_url="https://bigbasket.com/rice",
            ),
            results=[
                ProductResult(platform="BigBasket", product_name="Rice 1kg", price=60.0, mrp=75.0, product_url=""),
                ProductResult(platform="Amazon", product_name="Rice 1kg", price=68.0, mrp=75.0, product_url=""),
            ],
        ),
        ComparisonResult(
            search_term="Sugar",
            requested_quantity="1kg",
            cheapest=ProductResult(
                platform="JioMart",
                product_name="Sugar 1kg",
                price=42.0,
                mrp=52.0,
                product_url="https://jiomart.com/sugar",
            ),
            results=[
                ProductResult(platform="BigBasket", product_name="Sugar 1kg", price=45.0, mrp=52.0, product_url=""),
                ProductResult(platform="JioMart", product_name="Sugar 1kg", price=42.0, mrp=52.0, product_url=""),
            ],
        ),
    ]

    cart = build_optimized_cart(comparisons)

    assert cart["optimized_total"] == 102.0
    assert "BigBasket" in cart["optimized_cart"]
    assert "JioMart" in cart["optimized_cart"]
    assert len(cart["optimized_cart"]["BigBasket"]) == 1
    assert len(cart["optimized_cart"]["JioMart"]) == 1
    assert cart["savings"] >= 0
