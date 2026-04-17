"""Tests for bot formatter functions and WhatsApp message parser."""

from __future__ import annotations

import pytest

from app.bots.formatter import (
    format_list_summary,
    format_slack_blocks,
    format_slack_list_blocks,
    format_telegram_html,
    format_telegram_list_html,
    format_text_results,
)
from app.bots.whatsapp_bot import parse_whatsapp_message


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


# ── format_text_results ────────────────────────────────────────────────

class TestFormatTextResults:
    def test_with_results(self):
        text = format_text_results("toor dal", SAMPLE_RESULTS)
        assert "Good Explorer Results" in text
        assert "toor dal" in text
        assert "₹145" in text
        assert "BigBasket" in text
        assert "🏆" in text

    def test_empty_results(self):
        text = format_text_results("nonexistent", EMPTY_RESULTS)
        assert "No results found" in text
        assert "nonexistent" in text

    def test_contains_platform_icons(self):
        text = format_text_results("toor dal", SAMPLE_RESULTS)
        assert "📦" in text  # Amazon
        assert "🧺" in text  # BigBasket
        assert "⚡" in text  # Blinkit

    def test_contains_buy_link(self):
        text = format_text_results("toor dal", SAMPLE_RESULTS)
        assert "Buy cheapest:" in text
        assert "bigbasket.com" in text


# ── format_telegram_html ───────────────────────────────────────────────

class TestFormatTelegramHtml:
    def test_with_results(self):
        html = format_telegram_html("toor dal", SAMPLE_RESULTS)
        assert "<b>" in html
        assert "toor dal" in html
        assert "₹145" in html
        assert "🏆" in html

    def test_empty_results(self):
        html = format_telegram_html("nonexistent", EMPTY_RESULTS)
        assert "No results found" in html
        assert "<code>" in html

    def test_html_escaping(self):
        results = {**SAMPLE_RESULTS, "query": "test <script>"}
        html = format_telegram_html("test <script>", results)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_buy_links(self):
        html = format_telegram_html("toor dal", SAMPLE_RESULTS)
        assert 'href="' in html
        assert "Buy" in html


class TestFormatTelegramListHtml:
    def test_list_format(self):
        comparisons = [SAMPLE_RESULTS, SAMPLE_RESULTS]
        html = format_telegram_list_html(comparisons, SAMPLE_SUMMARY)
        assert "Shopping List Comparison" in html
        assert "₹290" in html
        assert "BigBasket" in html
        assert "₹68" in html


# ── format_slack_blocks ────────────────────────────────────────────────

class TestFormatSlackBlocks:
    def test_with_results(self):
        blocks = format_slack_blocks("toor dal", SAMPLE_RESULTS)
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        assert blocks[0]["type"] == "header"
        assert "toor dal" in blocks[0]["text"]["text"]

    def test_empty_results(self):
        blocks = format_slack_blocks("nonexistent", EMPTY_RESULTS)
        assert isinstance(blocks, list)
        assert any("No results found" in str(b) for b in blocks)

    def test_has_buy_button(self):
        blocks = format_slack_blocks("toor dal", SAMPLE_RESULTS)
        has_button = any(
            b.get("accessory", {}).get("type") == "button"
            for b in blocks
            if isinstance(b, dict)
        )
        assert has_button

    def test_has_divider(self):
        blocks = format_slack_blocks("toor dal", SAMPLE_RESULTS)
        assert any(b.get("type") == "divider" for b in blocks)


class TestFormatSlackListBlocks:
    def test_list_blocks(self):
        comparisons = [SAMPLE_RESULTS]
        blocks = format_slack_list_blocks(comparisons, SAMPLE_SUMMARY)
        assert isinstance(blocks, list)
        assert blocks[0]["type"] == "header"
        assert any("divider" in str(b) for b in blocks)


# ── format_list_summary ────────────────────────────────────────────────

class TestFormatListSummary:
    def test_summary(self):
        text = format_list_summary([SAMPLE_RESULTS], SAMPLE_SUMMARY)
        assert "Shopping List Comparison" in text
        assert "₹290" in text
        assert "BigBasket" in text

    def test_savings(self):
        text = format_list_summary([SAMPLE_RESULTS], SAMPLE_SUMMARY)
        assert "₹68" in text
        assert "save" in text.lower()


# ── parse_whatsapp_message ──────────────────────────────────────────────

class TestParseWhatsAppMessage:
    def test_search_command(self):
        result = parse_whatsapp_message("search toor dal 1kg")
        assert result["command"] == "search"
        assert result["query"] == "toor dal 1kg"

    def test_compare_command(self):
        result = parse_whatsapp_message("compare milk, eggs, rice")
        assert result["command"] == "compare"
        assert len(result["items"]) == 3
        assert "milk" in result["items"]
        assert "eggs" in result["items"]

    def test_help_command(self):
        result = parse_whatsapp_message("help")
        assert result["command"] == "help"

    def test_list_command(self):
        result = parse_whatsapp_message("list milk, eggs")
        assert result["command"] == "compare"
        assert len(result["items"]) == 2

    def test_plain_text(self):
        result = parse_whatsapp_message("paneer 200g")
        assert result["command"] == "search"
        assert result["query"] == "paneer 200g"

    def test_case_insensitive(self):
        result = parse_whatsapp_message("SEARCH butter")
        assert result["command"] == "search"
        assert result["query"] == "butter"

    def test_empty_message(self):
        result = parse_whatsapp_message("")
        assert result["command"] == "search"
        assert result["query"] == ""
