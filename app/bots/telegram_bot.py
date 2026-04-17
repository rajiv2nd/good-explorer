"""Telegram bot for Good Explorer price comparison.

Commands:
  /start              — Welcome message with usage instructions
  /search <item> [qty] — Single item price comparison
  /compare item1, item2, item3 — Multi-item comparison
  /help               — Show available commands
  Plain text           — Treated as a search query

Requires: python-telegram-bot>=21.0
Set TELEGRAM_BOT_TOKEN environment variable.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
    )

    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False

from app.bots.formatter import format_telegram_html, format_telegram_list_html
from app.scrapers.price_engine import search_all_platforms, search_list


# ── Inline buy buttons ─────────────────────────────────────────────────

def _buy_buttons(results: dict) -> "InlineKeyboardMarkup | None":
    """Build inline keyboard with buy links for each platform."""
    if not HAS_TELEGRAM:
        return None
    platforms = results.get("platforms", {})
    buttons = []
    for platform in ["Amazon", "Flipkart", "BigBasket", "Blinkit", "Zepto"]:
        items = platforms.get(platform, [])
        if items:
            best = min(items, key=lambda x: x["price"])
            if best.get("product_url"):
                buttons.append(
                    InlineKeyboardButton(
                        f"🛒 {platform} ₹{best['price']:.0f}",
                        url=best["product_url"],
                    )
                )
    if not buttons:
        return None
    # Arrange 2 per row
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


# ── Command handlers ────────────────────────────────────────────────────

async def cmd_start(update: "Update", context) -> None:
    """/start — welcome message."""
    await update.message.reply_text(
        "🛒 <b>Good Explorer Bot</b>\n\n"
        "Send me any grocery item name and I'll compare prices "
        "across Amazon, Flipkart, BigBasket, Blinkit &amp; Zepto!\n\n"
        "<b>Commands:</b>\n"
        "• <code>/search paneer 200g</code> — single item\n"
        "• <code>/compare milk, eggs, rice</code> — compare multiple\n"
        "• <code>/help</code> — show this message\n\n"
        "Or just type an item name directly!",
        parse_mode="HTML",
    )


async def cmd_help(update: "Update", context) -> None:
    """/help — show available commands."""
    await update.message.reply_text(
        "<b>Available Commands:</b>\n\n"
        "/search &lt;item&gt; [quantity] — Search a single item\n"
        "/compare item1, item2, item3 — Compare multiple items\n"
        "/start — Welcome message\n"
        "/help — This help message\n\n"
        "You can also just type any item name to search.",
        parse_mode="HTML",
    )


async def cmd_search(update: "Update", context) -> None:
    """/search <item> [quantity] — single item comparison."""
    if context.args:
        query = " ".join(context.args)
    else:
        query = update.message.text.strip()

    if not query or query.startswith("/"):
        await update.message.reply_text(
            "Usage: <code>/search toor dal 1kg</code>", parse_mode="HTML"
        )
        return

    await update.message.reply_text(f"🔍 Searching for <b>{query}</b>...", parse_mode="HTML")

    try:
        results = await search_all_platforms(query)
        message = format_telegram_html(query, results)
        reply_markup = _buy_buttons(results)
        await update.message.reply_text(
            message, parse_mode="HTML", reply_markup=reply_markup
        )
    except Exception:
        log.exception("Telegram search failed for: %s", query)
        await update.message.reply_text("Something went wrong. Please try again.")


async def cmd_compare(update: "Update", context) -> None:
    """/compare item1, item2, item3 — multi-item comparison."""
    items_text = " ".join(context.args) if context.args else ""
    if not items_text:
        await update.message.reply_text(
            "Usage: <code>/compare milk, eggs, rice, sugar</code>",
            parse_mode="HTML",
        )
        return

    items = [{"name": i.strip(), "quantity": ""} for i in items_text.split(",") if i.strip()]
    if not items:
        await update.message.reply_text("No items found. Separate items with commas.")
        return

    names = ", ".join(i["name"] for i in items)
    await update.message.reply_text(
        f"🔍 Comparing {len(items)} items: <b>{names}</b>...",
        parse_mode="HTML",
    )

    try:
        results, summary = await search_list(items)
        message = format_telegram_list_html(results, summary)
        await update.message.reply_text(message, parse_mode="HTML")
    except Exception:
        log.exception("Telegram compare failed")
        await update.message.reply_text("Something went wrong. Please try again.")


async def plain_text_handler(update: "Update", context) -> None:
    """Handle plain text messages as search queries."""
    query = update.message.text.strip()
    if not query:
        return
    # Reuse search logic
    context.args = query.split()
    await cmd_search(update, context)


# ── Application builder ────────────────────────────────────────────────

def build_application() -> "Application":
    """Build and return the Telegram bot Application (not started)."""
    if not HAS_TELEGRAM:
        raise RuntimeError(
            "python-telegram-bot is not installed. "
            "Install with: pip install 'good-explorer[bots]'"
        )
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("search", cmd_search))
    application.add_handler(CommandHandler("compare", cmd_compare))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, plain_text_handler)
    )
    return application


def run_polling() -> None:
    """Start the Telegram bot in polling mode (blocking)."""
    application = build_application()
    log.info("Starting Telegram bot in polling mode...")
    application.run_polling()
