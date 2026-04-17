"""Shared message formatter for bot integrations.

Converts price engine results into formatted messages for
plain text (WhatsApp/SMS), Telegram HTML, and Slack Block Kit.
"""

from __future__ import annotations


# ── Plain text (WhatsApp / SMS) ─────────────────────────────────────────

def format_text_results(query: str, results: dict) -> str:
    """Format search results as plain text for WhatsApp/SMS.

    Args:
        query: The original search query.
        results: Result dict from search_all_platforms().

    Returns:
        Plain text string with emoji formatting.
    """
    platforms = results.get("platforms", {})
    total = results.get("total_results", 0)

    if total == 0:
        return (
            f'🛒 Good Explorer Results\n\n'
            f'Search: {query}\n\n'
            f'❌ No results found.\n'
            f'Try: milk, rice, dal, butter, eggs, paneer'
        )

    cheapest = results.get("cheapest")
    lines = [
        "🛒 Good Explorer Results",
        "",
        f"Search: {query}",
        "",
    ]

    if cheapest:
        delivery = cheapest.get("delivery_time", "N/A")
        lines.append(
            f'🏆 Best Price: ₹{cheapest["price"]:.0f} on {cheapest["platform"]} ({delivery})'
        )
        lines.append("")

    platform_icons = {
        "Amazon": "📦", "Flipkart": "🛍️", "BigBasket": "🧺",
        "Blinkit": "⚡", "Zepto": "🚀", "JioMart": "🏪",
    }

    for platform in ["Amazon", "Flipkart", "BigBasket", "Blinkit", "Zepto"]:
        items = platforms.get(platform, [])
        if not items:
            continue
        icon = platform_icons.get(platform, "🛒")
        best = min(items, key=lambda x: x["price"])
        lines.append(f'{icon} {platform}: ₹{best["price"]:.0f}')

    if cheapest and cheapest.get("product_url"):
        lines.append("")
        lines.append(f'Buy cheapest: {cheapest["product_url"]}')

    return "\n".join(lines)


def format_list_summary(items_results: list[dict], summary: dict) -> str:
    """Format list comparison summary as plain text.

    Args:
        items_results: List of result dicts from search_all_platforms().
        summary: Summary dict from search_list().

    Returns:
        Plain text summary string.
    """
    lines = ["🛒 Shopping List Comparison", ""]

    for comp in items_results:
        cheapest = comp.get("cheapest")
        if cheapest:
            lines.append(
                f'✅ {comp["query"]}: ₹{cheapest["price"]:.0f} on {cheapest["platform"]}'
            )
        else:
            lines.append(f'❌ {comp["query"]}: Not found')

    lines.append("")
    lines.append(f'💰 Total (cheapest cart): ₹{summary.get("total_cheapest_cost", 0):.0f}')
    lines.append(f'🏪 Best single platform: {summary.get("best_platform", "N/A")}')
    savings = summary.get("savings_vs_most_expensive", 0)
    if savings > 0:
        lines.append(f'💸 You save up to: ₹{savings:.0f}')

    return "\n".join(lines)


# ── Telegram HTML ───────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Escape HTML special characters for Telegram HTML mode."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_telegram_html(query: str, results: dict) -> str:
    """Format search results as Telegram HTML.

    Args:
        query: The original search query.
        results: Result dict from search_all_platforms().

    Returns:
        HTML-formatted string for Telegram's HTML parse mode.
    """
    platforms = results.get("platforms", {})
    total = results.get("total_results", 0)

    if total == 0:
        return (
            f'🔍 No results found for <b>{_esc(query)}</b>\n\n'
            'Try: <code>milk</code>, <code>rice</code>, <code>dal</code>, '
            '<code>butter</code>, <code>eggs</code>, <code>paneer</code>'
        )

    lines = [f"🛒 <b>Price Comparison: {_esc(query)}</b>", f"<i>{total} results found</i>", ""]

    cheapest = results.get("cheapest")
    if cheapest:
        lines.append(
            f'🏆 <b>Best Price:</b> {_esc(cheapest["name"])}\n'
            f'💰 <b>₹{cheapest["price"]:.0f}</b> on <b>{_esc(cheapest["platform"])}</b>'
        )
        if cheapest.get("product_url"):
            lines.append(f'<a href="{cheapest["product_url"]}">Buy Now →</a>')
        lines.append("")

    for platform, items in sorted(platforms.items()):
        lines.append(f"<b>{_esc(platform)}:</b>")
        for item in items:
            is_cheapest = (
                cheapest
                and item["name"] == cheapest["name"]
                and item["platform"] == cheapest["platform"]
            )
            marker = " ✅" if is_cheapest else ""
            price_str = f"<b>₹{item['price']:.0f}</b>"
            line = f"  • {_esc(item['name'])} — {price_str}{marker}"
            if item.get("product_url"):
                line += f'  <a href="{item["product_url"]}">Buy</a>'
            lines.append(line)
        lines.append("")

    return "\n".join(lines).strip()


def format_telegram_list_html(comparisons: list[dict], summary: dict) -> str:
    """Format multi-item comparison as Telegram HTML.

    Args:
        comparisons: List of result dicts.
        summary: Summary dict.

    Returns:
        HTML-formatted string for Telegram.
    """
    lines = ["🛒 <b>Shopping List Comparison</b>", ""]

    for comp in comparisons:
        cheapest = comp.get("cheapest")
        if cheapest:
            lines.append(
                f'✅ <b>{_esc(comp["query"])}</b>: '
                f'₹{cheapest["price"]:.0f} on {_esc(cheapest["platform"])}'
            )
        else:
            lines.append(f'❌ <b>{_esc(comp["query"])}</b>: Not found')

    lines.append("")
    lines.append(
        f'💰 <b>Total (cheapest cart):</b> ₹{summary.get("total_cheapest_cost", 0):.0f}'
    )
    lines.append(
        f'🏪 <b>Best single platform:</b> {_esc(summary.get("best_platform", "N/A"))}'
    )
    savings = summary.get("savings_vs_most_expensive", 0)
    if savings > 0:
        lines.append(f"💸 <b>You save up to:</b> ₹{savings:.0f}")

    return "\n".join(lines).strip()


# ── Slack Block Kit ─────────────────────────────────────────────────────

def _section(text: str) -> dict:
    """Create a Slack mrkdwn section block."""
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def format_slack_blocks(query: str, results: dict) -> list[dict]:
    """Format search results as Slack Block Kit blocks.

    Args:
        query: The original search query.
        results: Result dict from search_all_platforms().

    Returns:
        List of Slack Block Kit block dicts.
    """
    platforms = results.get("platforms", {})
    total = results.get("total_results", 0)

    if total == 0:
        return [
            _section(f":mag: No results found for *{query}*"),
            _section("Try: `milk`, `rice`, `dal`, `butter`, `eggs`, `paneer`"),
        ]

    blocks: list[dict] = [
        {"type": "header", "text": {"type": "plain_text", "text": f"🛒 Price Comparison: {query}"}},
    ]

    cheapest = results.get("cheapest")
    if cheapest:
        text = (
            f':trophy: *Best Price:* {cheapest["name"]}\n'
            f':moneybag: *₹{cheapest["price"]:.0f}* on *{cheapest["platform"]}*'
        )
        block: dict = {"type": "section", "text": {"type": "mrkdwn", "text": text}}
        if cheapest.get("product_url"):
            block["accessory"] = {
                "type": "button",
                "text": {"type": "plain_text", "text": "Buy Now"},
                "url": cheapest["product_url"],
                "action_id": "buy_cheapest",
            }
        blocks.append(block)
        blocks.append({"type": "divider"})

    for platform, items in sorted(platforms.items()):
        item_lines = []
        for item in items:
            is_best = (
                cheapest
                and item["name"] == cheapest["name"]
                and item["platform"] == cheapest["platform"]
            )
            marker = " :white_check_mark:" if is_best else ""
            item_lines.append(f"• {item['name']} — ₹{item['price']:.0f}{marker}")

        section: dict = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{platform}:*\n" + "\n".join(item_lines)},
        }

        if items:
            best_on_platform = min(items, key=lambda x: x["price"])
            if best_on_platform.get("product_url"):
                section["accessory"] = {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"Buy on {platform}"},
                    "url": best_on_platform["product_url"],
                    "action_id": f"buy_{platform.lower().replace(' ', '_')}",
                }
        blocks.append(section)

    return blocks


def format_slack_list_blocks(comparisons: list[dict], summary: dict) -> list[dict]:
    """Format multi-item comparison as Slack Block Kit blocks.

    Args:
        comparisons: List of result dicts.
        summary: Summary dict.

    Returns:
        List of Slack Block Kit block dicts.
    """
    blocks: list[dict] = [
        {"type": "header", "text": {"type": "plain_text", "text": "🛒 Shopping List Comparison"}},
    ]

    for comp in comparisons:
        cheapest = comp.get("cheapest")
        if cheapest:
            blocks.append(
                _section(
                    f':white_check_mark: *{comp["query"]}*: '
                    f'₹{cheapest["price"]:.0f} on {cheapest["platform"]}'
                )
            )
        else:
            blocks.append(_section(f':x: *{comp["query"]}*: Not found'))

    blocks.append({"type": "divider"})

    summary_text = (
        f':moneybag: *Total (cheapest cart):* ₹{summary.get("total_cheapest_cost", 0):.0f}'
        f'\n:department_store: *Best single platform:* {summary.get("best_platform", "N/A")}'
    )
    savings = summary.get("savings_vs_most_expensive", 0)
    if savings > 0:
        summary_text += f"\n:money_with_wings: *You save up to:* ₹{savings:.0f}"

    blocks.append(_section(summary_text))
    return blocks
