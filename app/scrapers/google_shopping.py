"""Google Shopping scraper — most reliable aggregator for price comparison."""

from __future__ import annotations

import logging
import re

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ProductResult

log = logging.getLogger(__name__)


class GoogleShoppingScraper(BaseScraper):
    platform_name = "Google Shopping"
    platform_icon = "🔍"
    base_url = "https://www.google.co.in"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept": "text/html,application/xhtml+xml",
    }

    async def search(self, query: str, quantity: str = "") -> list[ProductResult]:
        search_query = f"{query} {quantity}".strip()
        url = f"{self.base_url}/search"
        params = {"q": search_query, "tbm": "shop", "hl": "en", "gl": "in"}

        results: list[ProductResult] = []
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True,
            ) as client:
                resp = await client.get(url, params=params, headers=self.HEADERS)
                if resp.status_code != 200:
                    log.warning("Google Shopping returned %d", resp.status_code)
                    return results

                soup = BeautifulSoup(resp.text, "lxml")
                # Google Shopping results are in div.sh-dgr__content or similar
                items = soup.select(".sh-dgr__content, .sh-dlr__list-result, [data-docid]")
                if not items:
                    # Fallback: try broader selectors
                    items = soup.select(".g, .commercial-unit-desktop-rhs .pla-unit")
                
                for item in items[:10]:
                    try:
                        result = self._parse_item(item)
                        if result:
                            results.append(result)
                    except Exception:
                        continue

        except Exception as exc:
            log.error("Google Shopping search failed: %s", exc)

        return results

    def _parse_item(self, item) -> ProductResult | None:
        # Try multiple selectors for product name
        title_el = (
            item.select_one("h3") or
            item.select_one("h4") or
            item.select_one("[aria-label]") or
            item.select_one("a[href*='shopping']")
        )
        if not title_el:
            return None
        name = title_el.get("aria-label") or title_el.get_text(strip=True)
        if not name or len(name) < 3:
            return None

        # Price
        price_el = (
            item.select_one("span.a8Pemb") or
            item.select_one("[data-price]") or
            item.select_one("span.HRLxBb") or
            item.select_one("span:has(> span)")
        )
        if not price_el:
            # Try finding any element with ₹ symbol
            for el in item.find_all("span"):
                text = el.get_text(strip=True)
                if "₹" in text or "Rs" in text:
                    price_el = el
                    break
        if not price_el:
            return None

        price = self._parse_price(price_el.get_text(strip=True))
        if price <= 0:
            return None

        # Source/platform
        source_el = item.select_one(".aULzUe, .E5ocAb, .IuHnof")
        source = source_el.get_text(strip=True) if source_el else "Google Shopping"

        # Link
        link_el = item.select_one("a[href]")
        product_url = ""
        if link_el and link_el.get("href"):
            href = link_el["href"]
            if href.startswith("/"):
                product_url = f"{self.base_url}{href}"
            else:
                product_url = href

        # Image
        img_el = item.select_one("img")
        image_url = ""
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src") or ""

        return ProductResult(
            name=name,
            price=price,
            platform=source,
            product_url=product_url,
            image_url=image_url,
            delivery_time="Varies",
            in_stock=True,
        )

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
