"""Test script to verify scrapers return real data."""

import asyncio
import re
from playwright.async_api import async_playwright


async def extract_amazon(page):
    """Extract products from Amazon search results."""
    print("=== AMAZON ===")
    await page.goto(
        "https://www.amazon.in/s?k=toor+dal+1kg",
        wait_until="domcontentloaded", timeout=30000,
    )
    await page.wait_for_timeout(3000)

    results = []
    items = await page.query_selector_all('[data-component-type="s-search-result"]')
    for item in items[:5]:
        title_el = await item.query_selector("h2 a span")
        price_el = await item.query_selector(".a-price .a-offscreen")
        img_el = await item.query_selector("img.s-image")
        link_el = await item.query_selector("h2 a")

        if not title_el or not price_el:
            continue

        title = await title_el.inner_text()
        price_text = await price_el.inner_text()
        img = (await img_el.get_attribute("src")) if img_el else ""
        href = (await link_el.get_attribute("href")) if link_el else ""

        price_clean = re.sub(r"[^\d.]", "", price_text.replace(",", ""))
        price = float(price_clean) if price_clean else 0

        results.append({
            "name": title, "price": price,
            "image_url": img, "product_url": f"https://www.amazon.in{href}" if href else "",
        })
        print(f"  {title[:60]} - Rs.{price}")

    print(f"  Total: {len(results)} products")
    return results


async def extract_flipkart(page):
    """Extract products from Flipkart search results."""
    print("\n=== FLIPKART ===")
    await page.goto(
        "https://www.flipkart.com/search?q=toor+dal+1kg",
        wait_until="domcontentloaded", timeout=30000,
    )
    await page.wait_for_timeout(3000)

    # Close login popup
    try:
        close = await page.query_selector("button._2KpZ6l._2doB4z")
        if close:
            await close.click()
            await page.wait_for_timeout(500)
    except Exception:
        pass

    results = await page.evaluate("""() => {
        const products = [];
        // Flipkart grocery items use specific card structure
        const cards = document.querySelectorAll('[data-id], .slAVV4, .tUxRFH, ._1sdMkc, .CGtC98');
        for (const card of cards) {
            const titleEl = card.querySelector('a[title], .WKTcLC, .IRpwTa, ._4rR01T, .s1Q9rs');
            const priceEl = card.querySelector('.Nx9bqj, ._30jeq3, ._1_WHN1');
            const imgEl = card.querySelector('img');
            const linkEl = card.querySelector('a[href]');

            if (!titleEl || !priceEl) continue;

            const title = titleEl.title || titleEl.textContent || '';
            const priceText = priceEl.textContent || '';
            const priceMatch = priceText.replace(/[^0-9.]/g, '');
            const price = parseFloat(priceMatch) || 0;

            if (title.length < 3 || price <= 0) continue;

            products.push({
                name: title.trim(),
                price: price,
                image_url: imgEl ? (imgEl.src || '') : '',
                product_url: linkEl ? linkEl.href : '',
            });
        }
        return products.slice(0, 8);
    }""")

    for p in results[:5]:
        print(f"  {p['name'][:60]} - Rs.{p['price']}")
    print(f"  Total: {len(results)} products")
    return results


async def extract_blinkit(page):
    """Extract products from Blinkit search results."""
    print("\n=== BLINKIT ===")
    await page.goto(
        "https://blinkit.com/s/?q=toor+dal",
        wait_until="domcontentloaded", timeout=30000,
    )
    await page.wait_for_timeout(5000)

    results = await page.evaluate("""() => {
        const products = [];
        // Blinkit renders products in a specific structure
        // Try to find product containers by looking at the DOM
        const allLinks = document.querySelectorAll('a[href*="/prn/"]');
        for (const link of allLinks) {
            const container = link.closest('div') || link;
            const text = container.textContent || '';

            // Extract product name - usually the longest text segment
            const spans = container.querySelectorAll('div, span');
            let name = '';
            let price = 0;
            let imgSrc = '';

            for (const span of spans) {
                const t = span.textContent.trim();
                // Price pattern
                const priceMatch = t.match(/^₹(\\d+)$/);
                if (priceMatch && !price) {
                    price = parseInt(priceMatch[1]);
                    continue;
                }
                // Name: longer text without special chars
                if (t.length > 5 && t.length < 80 && !t.includes('₹') && t.length > name.length) {
                    // Skip if it contains too many child elements' text
                    if (span.children.length <= 2) {
                        name = t;
                    }
                }
            }

            const img = container.querySelector('img');
            if (img) imgSrc = img.src || '';

            if (name && price > 0) {
                products.push({
                    name: name,
                    price: price,
                    image_url: imgSrc,
                    product_url: link.href,
                });
            }
        }

        // Deduplicate by name
        const seen = new Set();
        return products.filter(p => {
            if (seen.has(p.name)) return false;
            seen.add(p.name);
            return true;
        }).slice(0, 8);
    }""")

    for p in results[:5]:
        print(f"  {p['name'][:60]} - Rs.{p['price']}")
    print(f"  Total: {len(results)} products")
    return results


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            channel="chromium",
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
            viewport={"width": 1280, "height": 720},
        )
        await context.add_init_script(
            'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        )
        page = await context.new_page()

        amazon = await extract_amazon(page)
        flipkart = await extract_flipkart(page)
        blinkit = await extract_blinkit(page)

        print("\n=== SUMMARY ===")
        print(f"Amazon: {len(amazon)} products")
        print(f"Flipkart: {len(flipkart)} products")
        print(f"Blinkit: {len(blinkit)} products")

        total = len(amazon) + len(flipkart) + len(blinkit)
        if total > 0:
            print(f"\nSUCCESS: {total} total products found!")
        else:
            print("\nFAILED: No products found")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
