"""Test the API with multiple queries."""

import asyncio
from app.scrapers.price_engine import search_all_platforms

TESTS = [
    ("toor dal", "1kg"),
    ("rice", "5kg"),
    ("amul butter", ""),
    ("sugar", "1kg"),
    ("maggi", ""),
    ("eggs", ""),
    ("shampoo", ""),
]


async def main():
    for query, qty in TESTS:
        result = await search_all_platforms(query, qty)
        total = result["total_results"]
        cheapest = result.get("cheapest")
        print(f"\n{'='*60}")
        print(f"Query: {query} {qty}")
        print(f"Total results: {total}")
        if cheapest:
            print(f"Cheapest: {cheapest['name']} @ Rs.{cheapest['price']} on {cheapest['platform']}")
        for platform, items in result["platforms"].items():
            if items:
                prices = [f"Rs.{i['price']}" for i in items]
                print(f"  {platform}: {len(items)} items - {', '.join(prices)}")
        if total == 0:
            print("  FAILED: No results!")

    print(f"\n{'='*60}")
    print("ALL TESTS COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
