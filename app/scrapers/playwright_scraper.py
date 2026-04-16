"""Playwright-based scraper for JS-rendered platforms (Blinkit, Zepto, BigBasket)."""

from __future__ import annotations

import asyncio
import logging
import re
from contextlib import asynccontextmanager

from .base import BaseScraper, ProductResult

log = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    log.warning("Playwright not installed. JS-rendered sites won't work.")


PLATFORM_CONFIGS = {
    "Blinkit": {
        "icon": "⚡",
        "base_url": "https://blinkit.com",
        "search_url": "https://blinkit.com/s/?q={query}",
        "delivery": "10-15 min",
        "product_sel": '[data-testid="plp-product"], .Product__UpdatedPlp-sc-11dk8zd-0, [class*="Product__"]',
        "name_sel": '[data-testid="product-name"], [class*="Product__UpdatedTitle"], h3, div[class*="name"]',
        "price_sel": '[data-testid="product-price"], [class*="Product__UpdatedPrice"], div[class*="price"]',
    },
    "Zepto": {
        "icon": "🚀",
        "base_url": "https://www.zeptonow.com",
        "search_url": "https://www.zeptonow.com/search?query={query}",
        "delivery": "10-15 min",
        "product_sel": '[data-testid="product-card"], [class*="ProductCard"], [class*="product-card"]',
        "name_sel": '[data-testid="product-name"], h5, [class*="product-name"], [class*="ProductName"]',
        "price_sel": '[data-testid="product-price"], [class*="product-price"], [class*="Price"]',
    },
    "BigBasket": {
        "icon": "🧺",
        "base_url": "https://www.bigbasket.com",
        "search_url": "https://www.bigbasket.com/ps/?q={query}",
        "delivery": "2-4 hours",
        "product_sel": '[qa="product"], [class*="SKUDeck"], [class*="ProductCard"], li[class*="PaginateItems"]',
        "name_sel": '[qa="product-name"], [class*="BrandName"], h3, [class*="product-name"]',
        "price_sel": '[qa="product-price"], [class*="Pricing"], [class*="discnt-price"], [class*="price"]',
    },
}


class PlaywrightScraper(BaseScraper):
    """Scraper using headless Chromium for JS-rendered platforms."""

    def __init__(self, platform: str) -> None:
        config = PLATFORM_CONFIGS.get(platform, {})
        self.platform_name = platform
        self.platform_icon = config.get("icon", "🛒")
        self.base_url = config.get("base_url", "")
        self._search_url_tpl = config.get("search_url", "")
        self._delivery = config.get("delivery", "N/A")
        self._product_sel = config.get("product_sel", "")
        self._name_sel = config.get("name_sel", "")
        self._price_sel = config.get("price_sel", "")

    async def search(self, query: str, quantity: str = "") -> list[ProductResult]:
        if not HAS_PLAYWRIGHT:
            return []

        search_query = f"{query} {quantity}".strip()
        url = self._search_url_tpl.format(query=search_query.replace(" ", "+"))
        results: list[ProductResult] = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
                    ),
                    locale="en-IN",
                )
                page = await context.new_page()

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    # Wait for products to render
                    try:
                        await page.wait_for_selector(
                            self._product_sel, timeout=10000,
                        )
                    except Exception:
                        log.debug("%s: no products found with selector", self.platform_name)

                    # Extract product data
                    items = await page.query_selector_all(self._product_sel)
                    for item in items[:8]:
                        try:
                            result = await self._parse_item(item, page)
                            if result:
                                results.append(result)
                        except Exception:
                            continue
                finally:
                    await browser.close()

        except Exception as exc:
            log.error("%s Playwright search failed: %s", self.platform_name, exc)

        return results

    async def _parse_item(self, item, page) -> ProductResult | None:
        name_el = await item.query_selector(self._name_sel)
        if not name_el:
            return None
        name = (await name_el.inner_text()).strip()
        if not name or len(name) < 3:
            return None

        price_el = await item.query_selector(self._price_sel)
        if not price_el:
            return None
        price_text = (await price_el.inner_text()).strip()
        price = self._parse_price(price_text)
        if price <= 0:
            return None

        # Try to get link
        link_el = await item.query_selector("a[href]")
        product_url = ""
        if link_el:
            href = await link_el.get_attribute("href")
            if href:
                product_url = f"{self.base_url}{href}" if href.startswith("/") else href

        # Try to get image
        img_el = await item.query_selector("img")
        image_url = ""
        if img_el:
            image_url = await img_el.get_attribute("src") or ""

        return ProductResult(
            name=name,
            price=price,
            platform=self.platform_name,
            product_url=product_url,
            image_url=image_url,
            delivery_time=self._delivery,
            in_stock=True,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
