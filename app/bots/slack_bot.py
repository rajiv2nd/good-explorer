"""Slack bot integration for Good Explorer price comparison.

Supports:
  - Incoming webhooks: send formatted Block Kit messages to a channel
  - Slash commands: /compare <item> or /compare item1, item2
  - API endpoint: POST /api/slack/search for sending results to a webhook

Requires: SLACK_WEBHOOK_URL environment variable for webhook posting.
Optional: slack-sdk>=3.0 for enhanced webhook support.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")

try:
    from slack_sdk.webhook import WebhookClient

    HAS_SLACK_SDK = True
except ImportError:
    HAS_SLACK_SDK = False

from app.bots.formatter import format_slack_blocks, format_slack_list_blocks
from app.scrapers.price_engine import search_all_platforms, search_list


# ── Webhook sender ──────────────────────────────────────────────────────

def send_webhook(blocks: list[dict], text: str = "Price Comparison",
                 webhook_url: str | None = None) -> bool:
    """Send a message to Slack via incoming webhook.

    Uses slack_sdk if available, falls back to urllib.

    Args:
        blocks: Slack Block Kit blocks.
        text: Fallback text.
        webhook_url: Override webhook URL (uses SLACK_WEBHOOK_URL env if None).

    Returns:
        True on success.
    """
    url = webhook_url or SLACK_WEBHOOK
    if not url:
        log.error("SLACK_WEBHOOK_URL is not set and no webhook_url provided")
        return False

    payload = {"text": text, "blocks": blocks}

    if HAS_SLACK_SDK:
        try:
            client = WebhookClient(url)
            resp = client.send(text=text, blocks=blocks)
            return resp.status_code == 200
        except Exception:
            log.exception("Slack SDK webhook send failed")
            return False

    # Fallback: plain urllib
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return resp.status == 200
    except Exception:
        log.exception("Slack webhook send failed (urllib)")
        return False


# ── Public API functions ────────────────────────────────────────────────

async def send_search_results(webhook_url: str, query: str, results: dict) -> bool:
    """Send formatted search results to a Slack webhook.

    Args:
        webhook_url: Slack incoming webhook URL.
        query: The search query.
        results: Result dict from search_all_platforms().

    Returns:
        True on success.
    """
    blocks = format_slack_blocks(query, results)
    return send_webhook(blocks, text=f"🛒 Price Comparison: {query}", webhook_url=webhook_url)


async def send_list_comparison(webhook_url: str, items: list[dict],
                               summary: dict) -> bool:
    """Send list comparison with summary to a Slack webhook.

    Args:
        webhook_url: Slack incoming webhook URL.
        items: List of comparison result dicts.
        summary: Summary dict from search_list().

    Returns:
        True on success.
    """
    blocks = format_slack_list_blocks(items, summary)
    return send_webhook(blocks, text="🛒 Shopping List Comparison", webhook_url=webhook_url)


# ── Slash command handler ───────────────────────────────────────────────

async def handle_slash_command(form: dict) -> dict:
    """Handle a Slack slash command (/compare).

    Args:
        form: Parsed form data from Slack's POST request.

    Returns:
        Slack response dict with Block Kit blocks.
    """
    text = form.get("text", "").strip()

    if "," in text:
        return await _handle_list(text)
    return await _handle_single(text)


async def _handle_single(query: str) -> dict:
    """Search a single item and return Slack Block Kit response."""
    if not query:
        return {
            "response_type": "ephemeral",
            "text": "Usage: `/compare toor dal`",
        }

    try:
        results = await search_all_platforms(query)
        blocks = format_slack_blocks(query, results)
        return {"response_type": "in_channel", "blocks": blocks}
    except Exception:
        log.exception("Slack search failed for: %s", query)
        return {"response_type": "ephemeral", "text": "Something went wrong. Try again."}


async def _handle_list(text: str) -> dict:
    """Search a list of comma-separated items and return Slack response."""
    items = [{"name": i.strip(), "quantity": ""} for i in text.split(",") if i.strip()]
    if not items:
        return {
            "response_type": "ephemeral",
            "text": "Usage: `/compare milk, eggs, rice`",
        }

    try:
        results, summary = await search_list(items)
        blocks = format_slack_list_blocks(results, summary)
        return {"response_type": "in_channel", "blocks": blocks}
    except Exception:
        log.exception("Slack list search failed")
        return {"response_type": "ephemeral", "text": "Something went wrong. Try again."}


# ── Convenience function ────────────────────────────────────────────────

async def send_comparison_to_slack(query: str, webhook_url: str | None = None) -> bool:
    """Search for an item and post results to Slack webhook."""
    try:
        results = await search_all_platforms(query)
        blocks = format_slack_blocks(query, results)
        return send_webhook(blocks, text=f"Price Comparison: {query}", webhook_url=webhook_url)
    except Exception:
        log.exception("send_comparison_to_slack failed for: %s", query)
        return False
