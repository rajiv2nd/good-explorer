"""Good Explorer — FastAPI backend for price comparison."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

from app.scrapers.price_engine import search_all_platforms, search_list

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("good-explorer")

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Good Explorer", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Request models ──────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    quantity: str = ""
    platforms: list[str] | None = None


class ListSearchRequest(BaseModel):
    items: list[dict]


class SlackSearchRequest(BaseModel):
    webhook_url: str
    query: str
    quantity: str = ""


# ── Core API endpoints ──────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/search")
async def search(req: SearchRequest):
    """Search for a single item across all platforms."""
    return await search_all_platforms(req.query, req.quantity)


@app.post("/api/compare-list")
async def compare_list_endpoint(req: ListSearchRequest):
    """Compare prices for a list of items with consolidated summary."""
    results, summary = await search_list(req.items)
    return {"items": results, "summary": summary}


# ── Telegram webhook ───────────────────────────────────────────────────

@app.post("/api/telegram/webhook")
async def telegram_webhook_post(request: Request):
    """Handle Telegram webhook updates (POST)."""
    try:
        from app.channels.telegram_bot import build_application
    except ImportError:
        return JSONResponse({"error": "Telegram integration not available"}, status_code=501)

    try:
        from telegram import Update

        data = await request.json()
        application = build_application()
        async with application:
            update = Update.de_json(data, application.bot)
            await application.process_update(update)
        return JSONResponse({"ok": True})
    except Exception:
        log.exception("Telegram webhook processing failed")
        return JSONResponse({"ok": False}, status_code=500)


@app.get("/api/telegram/webhook")
async def telegram_webhook_get():
    """Health check for Telegram webhook endpoint."""
    return {"status": "ok", "endpoint": "telegram_webhook"}


# ── Slack endpoints ─────────────────────────────────────────────────────

@app.post("/api/slack/command")
async def slack_command(request: Request):
    """Handle Slack slash commands (/compare)."""
    try:
        from app.channels.slack_bot import handle_slash_command
    except ImportError:
        return JSONResponse({"text": "Slack integration not available"}, status_code=501)

    form = await request.form()
    form_dict = dict(form)
    result = await handle_slash_command(form_dict)
    return JSONResponse(result)


@app.post("/api/slack/search")
async def slack_search(req: SlackSearchRequest):
    """Send search results to a Slack webhook.

    Accepts {webhook_url, query, quantity} and posts formatted results.
    """
    try:
        from app.channels.slack_bot import send_search_results
    except ImportError:
        return JSONResponse(
            {"success": False, "error": "Slack integration not available"},
            status_code=501,
        )

    try:
        results = await search_all_platforms(req.query, req.quantity)
        ok = await send_search_results(req.webhook_url, req.query, results)
        return {"success": ok, "message": "Sent to Slack" if ok else "Failed to send"}
    except Exception:
        log.exception("Slack search endpoint failed")
        return JSONResponse(
            {"success": False, "error": "Internal error"},
            status_code=500,
        )


@app.post("/api/notify/slack")
async def notify_slack(request: Request):
    """Send comparison results to Slack webhook via unified notifier."""
    try:
        from app.channels.notifier import send_to_slack
    except ImportError:
        return JSONResponse(
            {"success": False, "error": "Slack integration not available"},
            status_code=501,
        )

    try:
        body = await request.json()
        webhook_url = body.get("webhook_url", os.environ.get("SLACK_WEBHOOK_URL", ""))
        query = body.get("query", "")
        quantity = body.get("quantity", "")

        if not webhook_url:
            return JSONResponse(
                {"success": False, "error": "No webhook URL provided"},
                status_code=400,
            )

        results = await search_all_platforms(query, quantity)
        ok = await send_to_slack(webhook_url, results)
        return {"success": ok, "message": "Sent to Slack" if ok else "Failed to send"}
    except Exception:
        log.exception("Notify Slack endpoint failed")
        return JSONResponse(
            {"success": False, "error": "Internal error"},
            status_code=500,
        )


# ── WhatsApp webhook ───────────────────────────────────────────────────

@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages via Twilio webhook."""
    try:
        from app.channels.whatsapp_bot import build_twiml_response, handle_incoming_message
    except ImportError:
        return Response(content="WhatsApp integration not available", status_code=501)

    form = await request.form()
    form_dict = dict(form)
    reply = await handle_incoming_message(form_dict)
    twiml = build_twiml_response(reply)
    return Response(content=twiml, media_type="application/xml")


# ── Bot status API ──────────────────────────────────────────────────────

@app.get("/api/bots/status")
async def bots_status():
    """Check which bots are configured."""
    return {
        "telegram": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "slack": bool(os.environ.get("SLACK_WEBHOOK_URL")),
        "whatsapp": bool(os.environ.get("TWILIO_ACCOUNT_SID")),
    }


@app.get("/api/channels/status")
async def channels_status():
    """Return configuration status of each channel integration."""
    telegram_configured = bool(os.environ.get("TELEGRAM_BOT_TOKEN"))
    slack_configured = bool(os.environ.get("SLACK_WEBHOOK_URL"))
    whatsapp_configured = bool(
        os.environ.get("TWILIO_ACCOUNT_SID")
        and os.environ.get("TWILIO_AUTH_TOKEN")
        and os.environ.get("TWILIO_WHATSAPP_FROM")
    )

    return {
        "telegram": {"configured": telegram_configured, "has_library": _check_import("telegram")},
        "slack": {"configured": slack_configured, "has_library": _check_import("slack_sdk")},
        "whatsapp": {"configured": whatsapp_configured, "has_library": _check_import("twilio")},
    }


@app.post("/api/channels/test")
async def test_channel(request: Request):
    """Test a channel integration with a sample query."""
    body = await request.json()
    channel = body.get("channel", "")
    query = body.get("query", "toor dal")

    if channel == "telegram":
        return {"message": "Telegram bot runs in polling mode. Use the CLI: good-explorer telegram-bot"}

    if channel == "slack":
        try:
            from app.channels.slack_bot import send_comparison_to_slack
            ok = await send_comparison_to_slack(query)
            return {"success": ok, "message": "Sent to Slack" if ok else "Failed to send"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    if channel == "whatsapp":
        return {
            "message": "WhatsApp works via Twilio webhook. "
            "Configure your Twilio number to POST to /api/whatsapp/webhook"
        }

    return {"error": f"Unknown channel: {channel}"}


def _check_import(module: str) -> bool:
    """Check if a Python module is importable."""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


# ── CLI entry point ─────────────────────────────────────────────────────

def cli():
    """CLI entry point for good-explorer commands."""
    args = sys.argv[1:]

    if not args or args[0] in ("serve", "server"):
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
        return

    if args[0] == "telegram-bot":
        try:
            from app.channels.telegram_bot import run_polling
            run_polling()
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    if args[0] == "slack-test":
        webhook_url = None
        query = "toor dal"
        i = 1
        while i < len(args):
            if args[i] == "--webhook-url" and i + 1 < len(args):
                webhook_url = args[i + 1]
                i += 2
            elif args[i] == "--query" and i + 1 < len(args):
                query = args[i + 1]
                i += 2
            else:
                i += 1

        if webhook_url:
            os.environ["SLACK_WEBHOOK_URL"] = webhook_url

        from app.channels.slack_bot import send_comparison_to_slack
        ok = asyncio.run(send_comparison_to_slack(query))
        if ok:
            print(f"Sent comparison for '{query}' to Slack.")
        else:
            print("Failed to send to Slack. Check webhook URL and logs.")
            sys.exit(1)
        return

    print("Usage: good-explorer <command>")
    print("Commands:")
    print("  serve           Start the web server (default)")
    print("  telegram-bot    Start Telegram bot in polling mode")
    print("  slack-test      Test Slack integration")
    print("    --webhook-url URL   Slack webhook URL")
    print("    --query TEXT        Search query (default: toor dal)")
