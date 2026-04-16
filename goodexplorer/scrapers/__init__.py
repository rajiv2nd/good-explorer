"""Platform scrapers for Good Explorer."""

from goodexplorer.scrapers.amazon import AmazonScraper
from goodexplorer.scrapers.flipkart import FlipkartScraper
from goodexplorer.scrapers.bigbasket import BigBasketScraper
from goodexplorer.scrapers.blinkit import BlinkitScraper
from goodexplorer.scrapers.jiomart import JioMartScraper
from goodexplorer.scrapers.zepto import ZeptoScraper

ALL_SCRAPERS = [
    AmazonScraper,
    FlipkartScraper,
    BigBasketScraper,
    BlinkitScraper,
    JioMartScraper,
    ZeptoScraper,
]

__all__ = [
    "AmazonScraper",
    "FlipkartScraper",
    "BigBasketScraper",
    "BlinkitScraper",
    "JioMartScraper",
    "ZeptoScraper",
    "ALL_SCRAPERS",
]
