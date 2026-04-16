"""Debug: save actual HTML from each platform to inspect selectors."""

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
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

        # Amazon
        print("Fetching Amazon...")
        await page.goto("https://www.amazon.in/s?k=toor+dal+1kg", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open("/tmp/amazon_debug.html", "w") as f:
            f.write(html)
        print(f"  Saved {len(html)} chars. Has 'a-price': {'a-price' in html}")
        print(f"  Has 's-search-result': {'s-search-result' in html}")
        print(f"  Has 'captcha': {'captcha' in html.lower()}")
        print(f"  Has 'robot': {'robot' in html.lower()}")

        # Flipkart
        print("Fetching Flipkart...")
        await page.goto("https://www.flipkart.com/search?q=toor+dal+1kg", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open("/tmp/flipkart_debug.html", "w") as f:
            f.write(html)
        print(f"  Saved {len(html)} chars. Has 'Nx9bqj': {'Nx9bqj' in html}")
        print(f"  Has 'data-id': {'data-id' in html}")

        # Blinkit
        print("Fetching Blinkit...")
        await page.goto("https://blinkit.com/s/?q=toor+dal", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(5000)
        html = await page.content()
        with open("/tmp/blinkit_debug.html", "w") as f:
            f.write(html)
        print(f"  Saved {len(html)} chars. Has 'prn': {'/prn/' in html}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
