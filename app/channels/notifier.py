"""Unified notification system for Good Explorer.

Provides a single interface to send price comparison results
to any configured channel: Telegram, Slack, or WhatsApp.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


# ── Plain text formatter (shared across all channels) ───────────────────

PLATFORM_ICONS = {
    "Amazon": "📦", "Flipkart": "🛍️", "BigBasket": "🧺",
    "Blinkit": "⚡", "Zepto": "🚀", "JioMart": "🏪",
}


def format_text_results(comparison_data: dict) -> str:
    """Format comparison results as plain text suitable for any channel.

    Args:
        comparison_data: Result dict from search_all_platforms().

    Returns:
        Plain text string with emoji formatting.
    """
    query = comparison_data.get("query", "")
    platforms = comparison_data.get("platforms", {})
    total = comparison_data.get("total_results", 0)

    if total == 0:
        return (
            f"🛒 Good Explorer — {query}\n\n"
            "❌ No results found.\n"
            "Try: milk, rice, dal, butter, eggs, paneer"
        )

    cheapest = comparison_data.get("cheapest")
    lines = ["🛒 Good Explorer — Price Comparison", "", f"Search: {query}", ""]

    if cheapest:
        delivery = cheapest.get("delivery_time", "N/A")
        lines.append(
            f'🏆 Best: ₹{cheapest["price"]:.0f} on {cheapest["platform"]} ({delivery})'
        )
        lines.append(f'   {cheapest["name"]}')
        lines.append("")

    for platform in ["Amazon", "Flipkart", "BigBasket", "Blinkit", "Zepto"]:
        items = platforms.get(platform, [])
        if not items:
            continue
        icon = PLATFORM_ICONS.get(platform, "🛒")
        best = min(items, key=lambda x: x["price"])
        lines.append(f"{icon} {platform}: ₹{best['price']:.0f}")

    if cheapest and cheapest.get("product_url"):
        lines.append("")
        lines.append(f"Buy: {cheapest['product_url']}")

    return "\n".join(lines)


# ── Channel senders ─────────────────────────────────────────────────────

async def send_to_telegram(chat_id: str, results: dict) -> bool:
    """Send comparison results to a Telegram chat.

    Args:
        chat_id: Telegram chat ID.
        results: Result dict from search_all_platforms().

    Returns:
        True on success, False on failure.
    """
    try:
        from telegram import Bot
    except ImportError:
        log.error("python-telegram-bot not installed")
        return False

    import os
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        log.error("TELEGRAM_BOT_TOKEN not set")
        return False

    try:
        from app.channels.telegram_bot import _format_single_result

        query = results.get("query", "")
        message = _format_single_result(query, results)
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        return True
    except Exception:
        log.exception("Failed to send to Telegram chat %s", chat_id)
        return False


async def send_to_slack(webhook_url: str, results: dict) -> bool:
    """Send comparison results to a Slack channel via webhook.

    Args:
        webhook_url: Slack incoming webhook URL.
        results: Result dict from search_all_platforms().

    Returns:
        True on success, False on failure.
    """
    try:
        from app.channels.slack_bot import format_slack_blocks, send_webhook

        query = results.get("query", "")
        blocks = format_slack_blocks(query, results)
        return send_webhook(blocks, text=f"🛒 Price Comparison: {query}", webhook_url=webhook_url)
    except ImportError:
        log.error("Slack bot module not available")
        return False
    except Exception:
        log.exception("Failed to send to Slack")
        return False


async def send_to_whatsapp(phone_number: str, results: dict) -> bool:
    """Send comparison results via WhatsApp (Twilio).

    Args:
        phone_number: Recipient in format 'whatsapp:+1234567890'.
        results: Result dict from search_all_platforms().

    Returns:
        True on success, False on failure.
    """
    try:
        from app.channels.whatsapp_bot import format_text_results as fmt, _send_message

        query = results.get("query", "")
        body = fmt(query, results)
        return _send_message(phone_number, body)
    except ImportError:
        log.error("WhatsApp bot module not available")
        return False
    except Exception:
        log.exception("Failed to send to WhatsApp %s", phone_number)
        return False
