"""WhatsApp bot integration for Good Explorer via Twilio API.

Functions:
  send_whatsapp_results(to_number, query, results) — send formatted message
  parse_whatsapp_message(message) — parse incoming message to extract query
  handle_incoming_message(form) — process Twilio webhook POST

Supported commands (case-insensitive):
  search <item>              — single item price comparison
  compare <item1>, <item2>   — multi-item comparison
  help                       — show usage instructions
  (plain text)               — treated as a search query

Requires: twilio>=9.0.0
Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM env vars.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "")

try:
    from twilio.rest import Client as TwilioClient

    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False

from app.bots.formatter import format_list_summary, format_text_results
from app.scrapers.price_engine import search_all_platforms, search_list


HELP_TEXT = (
    "🛒 Good Explorer — WhatsApp Bot\n\n"
    "Commands:\n"
    "• search <item> — compare prices for one item\n"
    "• compare item1, item2, item3 — compare multiple items\n"
    "• help — show this message\n\n"
    "Or just send any item name to search!\n"
    "Examples: toor dal, amul butter, paneer"
)


# ── Twilio client ──────────────────────────────────────────────────────

def _get_twilio_client() -> "TwilioClient":
    """Create and return a Twilio client."""
    if not HAS_TWILIO:
        raise RuntimeError(
            "twilio is not installed. Install with: pip install 'good-explorer[bots]'"
        )
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise RuntimeError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set.")
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# ── Public API functions ────────────────────────────────────────────────

def send_whatsapp_results(to_number: str, query: str, results: dict) -> bool:
    """Send formatted search results via WhatsApp.

    Args:
        to_number: Recipient in format 'whatsapp:+1234567890'.
        query: The search query.
        results: Result dict from search_all_platforms().

    Returns:
        True on success.
    """
    body = format_text_results(query, results)
    return _send_message(to_number, body)


def parse_whatsapp_message(message: str) -> dict:
    """Parse an incoming WhatsApp message to extract search intent.

    Args:
        message: Raw message text from user.

    Returns:
        Dict with keys: command ('search'|'compare'|'help'), query (str),
        items (list[str] for compare).
    """
    text = message.strip()
    lower = text.lower()

    if lower == "help":
        return {"command": "help", "query": "", "items": []}

    if lower.startswith("search "):
        return {"command": "search", "query": text[7:].strip(), "items": []}

    if lower.startswith("compare "):
        items_text = text[8:].strip()
        items = [i.strip() for i in items_text.split(",") if i.strip()]
        return {"command": "compare", "query": items_text, "items": items}

    if lower.startswith("list ") or lower.startswith("list:"):
        items_text = text.split(":", 1)[-1] if ":" in text else text[5:]
        items = [i.strip() for i in items_text.split(",") if i.strip()]
        if items:
            return {"command": "compare", "query": items_text.strip(), "items": items}

    # Default: treat as search query
    return {"command": "search", "query": text, "items": []}


def _send_message(to: str, body: str) -> bool:
    """Send a WhatsApp message via Twilio.

    Args:
        to: Recipient in format 'whatsapp:+1234567890'.
        body: Message text.

    Returns:
        True on success.
    """
    try:
        client = _get_twilio_client()
        client.messages.create(from_=TWILIO_WHATSAPP_FROM, to=to, body=body)
        return True
    except Exception:
        log.exception("Failed to send WhatsApp message to %s", to)
        return False


# ── Incoming message handler ───────────────────────────────────────────

async def handle_incoming_message(form: dict) -> str:
    """Process an incoming WhatsApp message and return reply text.

    Args:
        form: Parsed form data from Twilio webhook POST.

    Returns:
        Reply message string.
    """
    body = form.get("Body", "").strip()

    if not body:
        return "Send me a grocery item name to compare prices!"

    parsed = parse_whatsapp_message(body)

    if parsed["command"] == "help":
        return HELP_TEXT

    if parsed["command"] == "compare" and parsed["items"]:
        items = [{"name": i, "quantity": ""} for i in parsed["items"]]
        try:
            results, summary = await search_list(items)
            return format_list_summary(results, summary)
        except Exception:
            log.exception("WhatsApp compare failed")
            return "Something went wrong. Please try again."

    # Single search
    query = parsed["query"]
    if not query:
        return "Send me a grocery item name to compare prices!"

    try:
        results = await search_all_platforms(query)
        return format_text_results(query, results)
    except Exception:
        log.exception("WhatsApp search failed for: %s", query)
        return "Something went wrong. Please try again."


# ── TwiML response builder ─────────────────────────────────────────────

def build_twiml_response(message: str) -> str:
    """Build a TwiML XML response string for Twilio webhook."""
    escaped = (
        message.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Message>{escaped}</Message>"
        "</Response>"
    )
