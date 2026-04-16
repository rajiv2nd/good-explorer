"""Amazon India price scraper."""

from __future__ import annotations

import logging
import re

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ProductResult

log = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    platform_name = "Amazon"
    platform_icon = "📦"
    base_url = "https://www.amazon.in"

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
        url = f"{self.base_url}/s"
        params = {"k": search_query, "ref": "nb_sb_noss"}

        results: list[ProductResult] = []
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True
            ) as client:
                resp = await client.get(
                    url, params=params, headers=self.HEADERS,
                )
                if resp.status_code != 200:
                    log.warning("Amazon returned %d", resp.status_code)
                    return results

                soup = BeautifulSoup(resp.text, "lxml")
                items = soup.select('[data-component-type="s-search-result"]')
                for item in items[:8]:
                    try:
                        result = self._parse_item(item)
                        if result:
                            results.append(result)
                    except Exception:
                        continue

        except Exception as exc:
            log.error("Amazon search failed: %s", exc)

        return results

    def _parse_item(self, item) -> ProductResult | None:
        title_el = item.select_one("h2 a span")
        if not title_el:
            return None
        name = title_el.get_text(strip=True)

        price_el = item.select_one(".a-price .a-offscreen")
        if not price_el:
            return None
        price_text = price_el.get_text(strip=True)
        price = self._parse_price(price_text)
        if price <= 0:
            return None

        link_el = item.select_one("h2 a")
        product_url = ""
        if link_el and link_el.get("href"):
            href = link_el["href"]
            product_url = f"{self.base_url}{href}" if href.startswith("/") else href

        img_el = item.select_one("img.s-image")
        image_url = img_el["src"] if img_el and img_el.get("src") else ""

        original_el = item.select_one(".a-price.a-text-price .a-offscreen")
        original_price = self._parse_price(original_el.get_text(strip=True)) if original_el else price

        rating_el = item.select_one(".a-icon-alt")
        rating = 0.0
        if rating_el:
            match = re.search(r"([\d.]+)", rating_el.get_text())
            if match:
                rating = float(match.group(1))

        discount_pct = round((1 - price / original_price) * 100, 1) if original_price > price else 0.0

        return ProductResult(
            name=name,
            price=price,
            platform="Amazon",
            product_url=product_url,
            image_url=image_url,
            delivery_time="1-3 days",
            rating=rating,
            original_price=original_price,
            discount_pct=discount_pct,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
