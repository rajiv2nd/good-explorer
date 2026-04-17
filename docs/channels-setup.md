# Channel Integrations Setup Guide

Good Explorer supports sharing price comparison results via Telegram, Slack, and WhatsApp.
All channel dependencies are optional — the main web app works without any of them.

## Quick Install

```bash
# Install all channel dependencies
pip install 'good-explorer[channels]'

# Or install individually
pip install 'good-explorer[telegram]'
pip install 'good-explorer[slack]'
pip install 'good-explorer[whatsapp]'
```

---

## 1. Telegram Bot

### Create a Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Choose a name (e.g., "Good Explorer Bot") and username (e.g., `GoodExplorerBot`)
4. BotFather will give you a token like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### Configure

```bash
export TELEGRAM_BOT_TOKEN="your-bot-token-here"
```

### Run

**Polling mode** (simplest, good for development):
```bash
good-explorer telegram-bot
```

**Webhook mode** (for production):
- Deploy the app and set the webhook URL to `https://your-domain.com/api/telegram/webhook`
- Use the Telegram Bot API to register the webhook:
```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://your-domain.com/api/telegram/webhook"
```

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with instructions |
| `/search toor dal 1kg` | Search a single item |
| `/compare milk, eggs, rice` | Compare multiple items |
| `/help` | Show available commands |
| *(plain text)* | Treated as a search query |

---

## 2. Slack Integration

### Set Up Incoming Webhooks

1. Go to [Slack API Apps](https://api.slack.com/apps) and create a new app
2. Under "Incoming Webhooks", toggle it on
3. Click "Add New Webhook to Workspace" and select a channel
4. Copy the webhook URL

### Configure

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Set Up Slash Commands (Optional)

1. In your Slack app settings, go to "Slash Commands"
2. Create a new command: `/compare`
3. Set the Request URL to `https://your-domain.com/api/slack/command`
4. Add a description: "Compare grocery prices"

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/slack/command` | POST | Handles Slack slash commands |
| `/api/slack/search` | POST | Send results to a webhook URL |
| `/api/notify/slack` | POST | Send results via unified notifier |

### Test

```bash
good-explorer slack-test --webhook-url "https://hooks.slack.com/services/..." --query "toor dal"
```

---

## 3. WhatsApp (Twilio)

### Set Up Twilio WhatsApp Sandbox

1. Sign up at [Twilio](https://www.twilio.com/) (free trial available)
2. Go to **Messaging > Try it out > Send a WhatsApp message**
3. Follow the sandbox setup instructions (send a join code from your phone)
4. Note your Account SID, Auth Token, and sandbox number

### Configure

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"  # Twilio sandbox number
```

### Set Up Webhook

In the Twilio Console, set the webhook URL for incoming messages:
```
https://your-domain.com/api/whatsapp/webhook
```

Method: POST

### Supported Messages

| Message | Action |
|---------|--------|
| `search toor dal` | Single item comparison |
| `compare milk, eggs, rice` | Multi-item comparison |
| `help` | Show usage instructions |
| *(any text)* | Treated as a search query |

---

## 4. Environment Variables Summary

| Variable | Required For | Description |
|----------|-------------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram | Bot token from @BotFather |
| `SLACK_WEBHOOK_URL` | Slack | Incoming webhook URL |
| `TWILIO_ACCOUNT_SID` | WhatsApp | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | WhatsApp | Twilio Auth Token |
| `TWILIO_WHATSAPP_FROM` | WhatsApp | Sender number (e.g., `whatsapp:+14155238886`) |

### Example `.env` file

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

---

## 5. UI Share Buttons

The web UI includes share buttons after search results:

- **Share to Telegram** — Opens Telegram with a pre-filled message
- **Share to WhatsApp** — Opens WhatsApp Web with a pre-filled message
- **Send to Slack** — Sends results to your configured Slack webhook
- **Copy as Text** — Copies a plain-text summary to clipboard

---

## 6. Unified Notifier API

The `app.channels.notifier` module provides a unified interface:

```python
from app.channels.notifier import send_to_telegram, send_to_slack, send_to_whatsapp, format_text_results

# Format results as plain text
text = format_text_results(comparison_data)

# Send to any channel
await send_to_telegram(chat_id, results)
await send_to_slack(webhook_url, results)
await send_to_whatsapp("whatsapp:+1234567890", results)
```
