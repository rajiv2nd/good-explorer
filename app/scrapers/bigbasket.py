"""BigBasket price scraper."""

from __future__ import annotations

import logging
import re

import httpx

from .base import BaseScraper, ProductResult

log = logging.getLogger(__name__)


class BigBasketScraper(BaseScraper):
    platform_name = "BigBasket"
    platform_icon = "🧺"
    base_url = "https://www.bigbasket.com"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9",
    }

    async def search(self, query: str, quantity: str = "") -> list[ProductResult]:
        search_query = f"{query} {quantity}".strip()
        url = f"{self.base_url}/ps/"
        params = {"q": search_query}

        results: list[ProductResult] = []
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True,
            ) as client:
                resp = await client.get(
                    url, params=params, headers=self.HEADERS,
                )
                if resp.status_code != 200:
                    log.warning("BigBasket returned %d", resp.status_code)
                    return results

                # BigBasket uses JSON API internally
                # Try to extract product data from page
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                items = soup.select('[qa="product"], .PaginateItems___StyledDiv-sc-1yrbjdr-0 > div, .SKUDeck___StyledDiv-sc-1e5d9gk-0')
                for item in items[:8]:
                    try:
                        result = self._parse_item(item)
                        if result:
                            results.append(result)
                    except Exception:
                        continue

        except Exception as exc:
            log.error("BigBasket search failed: %s", exc)

        return results

    def _parse_item(self, item) -> ProductResult | None:
        title_el = item.select_one('[qa="product-name"], .BrandName___StyledLabel2-sc-hssfrl-1, h3')
        if not title_el:
            return None
        name = title_el.get_text(strip=True)
        if not name or len(name) < 3:
            return None

        price_el = item.select_one('[qa="product-price"], .Pricing___StyledLabel-sc-pldi2d-1, .discnt-price')
        if not price_el:
            return None
        price = self._parse_price(price_el.get_text(strip=True))
        if price <= 0:
            return None

        link_el = item.select_one("a[href]")
        product_url = ""
        if link_el and link_el.get("href"):
            href = link_el["href"]
            product_url = f"{self.base_url}{href}" if href.startswith("/") else href

        img_el = item.select_one("img")
        image_url = img_el.get("src", "") if img_el else ""

        return ProductResult(
            name=name,
            price=price,
            platform="BigBasket",
            product_url=product_url,
            image_url=image_url,
            delivery_time="2-4 hours",
            in_stock=True,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
