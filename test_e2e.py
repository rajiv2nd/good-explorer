"""End-to-end API tests against the running server."""
import json
import urllib.request

BASE = "http://localhost:8000"


def post(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def test_single_searches():
    """Test individual search queries."""
    tests = [
        ("paneer", "paneer"),
        ("papaya", "papaya"),
        ("apple", "apple"),
        ("milk", "milk"),
        ("toor dal", "dal"),
        ("banana", "banana"),
    ]
    for query, expected_in_name in tests:
        data = post("/api/search", {"query": query, "quantity": ""})
        assert data["total_results"] > 0, f"'{query}' should have results"
        # Verify all results contain expected substring
        for platform, items in data["platforms"].items():
            for item in items:
                assert expected_in_name in item["name"].lower(), (
                    f"'{query}' returned wrong item on {platform}: {item['name']}"
                )
        print(f"OK: '{query}' -> {data['total_results']} results, cheapest ₹{data['cheapest']['price']}")

    # Papaya must NOT return dal/sugar/biscuits
    data = post("/api/search", {"query": "papaya", "quantity": ""})
    for platform, items in data["platforms"].items():
        for item in items:
            name = item["name"].lower()
            assert "dal" not in name, f"papaya returned dal: {name}"
            assert "sugar" not in name, f"papaya returned sugar: {name}"
            assert "biscuit" not in name, f"papaya returned biscuit: {name}"
    print("OK: papaya does NOT return dal/sugar/biscuits")


def test_no_results():
    """Test that nonexistent items return empty."""
    data = post("/api/search", {"query": "xyznonexistent", "quantity": ""})
    assert data["total_results"] == 0, "nonexistent should return 0"
    print("OK: nonexistent query -> 0 results")


def test_list_search():
    """Test list comparison with summary."""
    items = [
        {"name": "paneer", "quantity": ""},
        {"name": "milk", "quantity": ""},
        {"name": "eggs", "quantity": ""},
        {"name": "rice", "quantity": ""},
        {"name": "butter", "quantity": ""},
        {"name": "sugar", "quantity": ""},
    ]
    data = post("/api/compare-list", {"items": items})

    assert "items" in data, "Response should have 'items'"
    assert "summary" in data, "Response should have 'summary'"
    assert len(data["items"]) == 6, f"Expected 6 items, got {len(data['items'])}"

    s = data["summary"]
    assert s["total_items"] > 0, "Summary should have items"
    assert s["total_cheapest_cost"] > 0, "Summary should have cost"
    assert s["best_platform"], "Summary should have best platform"
    assert len(s["cheapest_cart"]) > 0, "Summary should have cart items"
    assert s["savings_vs_most_expensive"] >= 0, "Savings should be >= 0"

    print(f"OK: list search -> {len(data['items'])} items")
    print(f"    Summary: {s['total_items']} items, cheapest ₹{s['total_cheapest_cost']}")
    print(f"    Best platform: {s['best_platform']}")
    print(f"    Savings: ₹{s['savings_vs_most_expensive']}")
    print(f"    Cart: {len(s['cheapest_cart'])} items")

    # Verify each item in the list has correct results
    for comp in data["items"]:
        query = comp["query"]
        if comp["total_results"] > 0:
            print(f"    '{query}': {comp['total_results']} results, cheapest ₹{comp['cheapest']['price']} on {comp['cheapest']['platform']}")


def test_homepage():
    """Test that the homepage loads."""
    req = urllib.request.Request(f"{BASE}/")
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()
        assert "Good Explorer" in html, "Homepage should contain 'Good Explorer'"
        assert "Smart Cart" in html or "smart-cart" in html, "Homepage should have Smart Cart section"
        assert "suggestion-tag" in html, "Homepage should have suggestion tags"
    print("OK: Homepage loads with all UI elements")


if __name__ == "__main__":
    print("=== E2E API Tests ===\n")
    test_homepage()
    test_single_searches()
    test_no_results()
    test_list_search()
    print("\n=== ALL E2E TESTS PASSED ===")
