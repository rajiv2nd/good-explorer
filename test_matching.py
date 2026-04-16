"""Test the matching logic and API end-to-end."""
import asyncio
import sys

sys.path.insert(0, ".")

from app.scrapers.price_engine import _find_matching_products, search_all_platforms, search_list


def test_matching():
    """Verify strict matching returns correct results."""
    tests = {
        "paneer": ["paneer"],
        "papaya": ["papaya"],
        "apple": ["apple"],
        "milk": ["milk"],
        "toor dal": ["toor dal", "dal"],
        "banana": ["banana"],
        "rice": ["rice"],
        "butter": ["butter"],
        "eggs": ["egg"],
        "sugar": ["sugar"],
    }

    all_pass = True
    for query, expected_substrings in tests.items():
        results = _find_matching_products(query)
        names = [r["name"].lower() for r in results]

        # Must have results
        if not results:
            print(f"FAIL: '{query}' returned 0 results")
            all_pass = False
            continue

        # Every result must contain at least one expected substring
        for name in names:
            if not any(sub in name for sub in expected_substrings):
                print(f"FAIL: '{query}' returned unexpected product: {name}")
                all_pass = False

        print(f"OK: '{query}' -> {len(results)} results: {names}")

    # Negative test: nonsense query should return empty
    results = _find_matching_products("xyznonexistent")
    if results:
        print(f"FAIL: 'xyznonexistent' should return empty, got {len(results)} results")
        all_pass = False
    else:
        print("OK: 'xyznonexistent' -> 0 results (correct)")

    # Critical bug test: papaya must NOT return dal/sugar/biscuits
    papaya_results = _find_matching_products("papaya")
    papaya_names = [r["name"].lower() for r in papaya_results]
    for name in papaya_names:
        if any(bad in name for bad in ["dal", "sugar", "biscuit", "atta"]):
            print(f"FAIL: 'papaya' incorrectly matched: {name}")
            all_pass = False

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    return all_pass


def test_search_api():
    """Test the search_all_platforms function."""
    async def run():
        # Test single search
        result = await search_all_platforms("paneer")
        assert result["total_results"] > 0, "paneer should have results"
        assert result["cheapest"] is not None, "paneer should have a cheapest item"
        print(f"OK: search 'paneer' -> {result['total_results']} results, cheapest: ₹{result['cheapest']['price']}")

        # Test papaya
        result = await search_all_platforms("papaya")
        assert result["total_results"] > 0, "papaya should have results"
        for platform, items in result["platforms"].items():
            for item in items:
                assert "papaya" in item["name"].lower(), f"papaya search returned wrong item: {item['name']}"
        print(f"OK: search 'papaya' -> {result['total_results']} results, all contain 'papaya'")

        # Test empty
        result = await search_all_platforms("xyznonexistent")
        assert result["total_results"] == 0, "nonexistent should have 0 results"
        print(f"OK: search 'xyznonexistent' -> 0 results")

    asyncio.run(run())


def test_list_search():
    """Test the list search with summary."""
    async def run():
        items = [
            {"name": "paneer", "quantity": ""},
            {"name": "milk", "quantity": ""},
            {"name": "eggs", "quantity": ""},
            {"name": "rice", "quantity": ""},
            {"name": "butter", "quantity": ""},
            {"name": "sugar", "quantity": ""},
        ]
        results, summary = await search_list(items)
        assert len(results) == 6, f"Expected 6 results, got {len(results)}"
        assert summary["total_items"] > 0, "Summary should have items"
        assert summary["total_cheapest_cost"] > 0, "Summary should have a cost"
        assert summary["best_platform"], "Summary should have a best platform"
        assert len(summary["cheapest_cart"]) > 0, "Summary should have cheapest cart items"
        print(f"OK: list search -> {len(results)} results")
        print(f"    Summary: {summary['total_items']} items, cheapest cart ₹{summary['total_cheapest_cost']}")
        print(f"    Best platform: {summary['best_platform']}")
        print(f"    Savings: ₹{summary['savings_vs_most_expensive']}")
        print(f"    Cart items: {len(summary['cheapest_cart'])}")

    asyncio.run(run())


if __name__ == "__main__":
    print("=== Testing Matching Logic ===")
    test_matching()
    print("\n=== Testing Search API ===")
    test_search_api()
    print("\n=== Testing List Search ===")
    test_list_search()
    print("\n=== ALL TESTS COMPLETE ===")
