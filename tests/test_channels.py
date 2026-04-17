"""Tests for channel integrations — formatters, parsers, and notifier."""

from __future__ import annotations

import pytest

from app.channels.telegram_bot import _format_single_result, _format_list_result, _esc
from app.channels.slack_bot import format_slack_blocks, format_slack_list_blocks
from app.channels.whatsapp_bot import (
    format_text_results,
    format_list_summary,
    parse_whatsapp_message,
)
from app.channels.notifier import format_text_results as notifier_format


# ── Sample data ─────────────────────────────────────────────────────────

SAMPLE_RESULTS = {
    "query": "toor dal",
    "quantity": "1kg",
    "platforms": {
        "Amazon": [
            {
                "name": "Tata Sampann Toor Dal 1kg",
                "price": 179,
                "platform": "Amazon",
                "product_url": "https://www.amazon.in/s?k=toor+dal",
                "delivery_time": "1-3 days",
                "in_stock": True,
                "rating": 4.2,
                "original_price": 196.9,
                "discount_pct": 10.0,
            },
        ],
        "BigBasket": [
            {
                "name": "BB Royal Toor Dal 1kg",
                "price": 145,
                "platform": "BigBasket",
                "product_url": "https://www.bigbasket.com/ps/?q=toor+dal",
                "delivery_time": "2-4 hours",
                "in_stock": True,
                "rating": 4.2,
                "original_price": 159.5,
                "discount_pct": 10.0,
            },
        ],
        "Blinkit": [
            {
                "name": "BB Royal Toor Dal 1kg",
                "price": 150,
                "platform": "Blinkit",
                "product_url": "https://blinkit.com/s/?q=toor+dal",
                "delivery_time": "10-15 min",
                "in_stock": True,
                "rating": 4.2,
                "original_price": 165.0,
                "discount_pct": 10.0,
            },
        ],
    },
    "cheapest": {
        "name": "BB Royal Toor Dal 1kg",
        "price": 145,
        "platform": "BigBasket",
        "product_url": "https://www.bigbasket.com/ps/?q=toor+dal",
        "delivery_time": "2-4 hours",
        "in_stock": True,
        "rating": 4.2,
        "original_price": 159.5,
        "discount_pct": 10.0,
    },
    "platform_count": 3,
    "total_results": 3,
}

EMPTY_RESULTS = {
    "query": "nonexistent item",
    "quantity": "",
    "platforms": {},
    "cheapest": None,
    "platform_count": 0,
    "total_results": 0,
}

SAMPLE_SUMMARY = {
    "total_items": 2,
    "total_cheapest_cost": 290.0,
    "savings_vs_most_expensive": 68.0,
    "best_platform": "BigBasket",
    "cheapest_cart": [
        {"item": "BB Royal Toor Dal 1kg", "platform": "BigBasket", "price": 145},
        {"item": "BB Royal Moong Dal 1kg", "platform": "BigBasket", "price": 145},
    ],
}


# ── Telegram formatter tests ───────────────────────────────────────────

class TestTelegramFormatter:
    def test_single_result_with_data(self):
        html = _format_single_result("toor dal", SAMPLE_RESULTS)
        assert "<b>" in html
        assert "toor dal" in html
        assert "₹145" in html
        assert "BigBasket" in html
        assert "🏆" in html

    def test_single_result_empty(self):
        html = _format_single_result("nonexistent", EMPTY_RESULTS)
        assert "No results found" in html

    def test_html_escaping(self):
        assert _esc("<script>") == "&lt;script&gt;"
        assert _esc("a & b") == "a &amp; b"

    def test_list_result(self):
        html = _format_list_result([SAMPLE_RESULTS], SAMPLE_SUMMARY)
        assert "Shopping List Comparison" in html
        assert "₹290" in html
        assert "BigBasket" in html
        assert "₹68" in html

    def test_buy_link_present(self):
        html = _format_single_result("toor dal", SAMPLE_RESULTS)
        assert "Buy Now" in html
        assert "bigbasket.com" in html


# ── Slack formatter tests ──────────────────────────────────────────────

class TestSlackFormatter:
    def test_blocks_with_results(self):
        blocks = format_slack_blocks("toor dal", SAMPLE_RESULTS)
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        assert blocks[0]["type"] == "header"

    def test_blocks_empty_results(self):
        blocks = format_slack_blocks("nonexistent", EMPTY_RESULTS)
        assert any("No results found" in str(b) for b in blocks)

    def test_has_buy_button(self):
        blocks = format_slack_blocks("toor dal", SAMPLE_RESULTS)
        has_button = any(
            b.get("accessory", {}).get("type") == "button"
            for b in blocks if isinstance(b, dict)
        )
        assert has_button

    def test_list_blocks(self):
        blocks = format_slack_list_blocks([SAMPLE_RESULTS], SAMPLE_SUMMARY)
        assert isinstance(blocks, list)
        assert blocks[0]["type"] == "header"
        assert any(b.get("type") == "divider" for b in blocks)


# ── WhatsApp formatter tests ───────────────────────────────────────────

class TestWhatsAppFormatter:
    def test_text_results(self):
        text = format_text_results("toor dal", SAMPLE_RESULTS)
        assert "Good Explorer" in text
        assert "₹145" in text
        assert "BigBasket" in text

    def test_text_empty(self):
        text = format_text_results("nonexistent", EMPTY_RESULTS)
        assert "No results found" in text

    def test_list_summary(self):
        text = format_list_summary([SAMPLE_RESULTS], SAMPLE_SUMMARY)
        assert "Shopping List" in text
        assert "₹290" in text

    def test_platform_icons(self):
        text = format_text_results("toor dal", SAMPLE_RESULTS)
        assert "📦" in text  # Amazon
        assert "🧺" in text  # BigBasket


# ── WhatsApp parser tests ──────────────────────────────────────────────

class TestWhatsAppParser:
    def test_search_command(self):
        result = parse_whatsapp_message("search toor dal 1kg")
        assert result["command"] == "search"
        assert result["query"] == "toor dal 1kg"

    def test_compare_command(self):
        result = parse_whatsapp_message("compare milk, eggs, rice")
        assert result["command"] == "compare"
        assert len(result["items"]) == 3

    def test_help_command(self):
        result = parse_whatsapp_message("help")
        assert result["command"] == "help"

    def test_plain_text(self):
        result = parse_whatsapp_message("paneer 200g")
        assert result["command"] == "search"
        assert result["query"] == "paneer 200g"

    def test_case_insensitive(self):
        result = parse_whatsapp_message("SEARCH butter")
        assert result["command"] == "search"


# ── Notifier format_text_results tests ──────────────────────────────────

class TestNotifierFormatter:
    def test_format_with_results(self):
        text = notifier_format(SAMPLE_RESULTS)
        assert "Good Explorer" in text
        assert "toor dal" in text
        assert "₹145" in text

    def test_format_empty(self):
        text = notifier_format(EMPTY_RESULTS)
        assert "No results found" in text

    def test_contains_buy_link(self):
        text = notifier_format(SAMPLE_RESULTS)
        assert "Buy:" in text
        assert "bigbasket.com" in text
