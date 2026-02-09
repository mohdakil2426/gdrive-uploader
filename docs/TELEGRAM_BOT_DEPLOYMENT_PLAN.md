# Telegram Bot Deployment Plan: Universal Drive Uploader

## Executive Summary

This document outlines the plan to create a Telegram-based interface for the Universal Google Drive Uploader, making it accessible to users without technical knowledge. Users will simply send a URL to a Telegram bot, and the file will automatically appear in their Google Drive.

---

## Research Findings

### Telegram Bot Options

| Option | Description | Complexity | User Experience |
|--------|-------------|------------|-----------------|
| **Simple Bot** | Text-based commands, send URL, get status | Low | Good |
| **Mini App** | Full web UI inside Telegram | High | Excellent |
| **Inline Bot** | Use in any chat via @mention | Medium | Good |

### Hosting Platforms (Free Tier)

| Platform | Free Tier | Best For | Limitations |
|----------|-----------|----------|-------------|
| [Render](https://render.com) | Yes (with card) | Python bots | Zero-downtime deploy issues |
| [Fly.io](https://fly.io) | 3 VMs free | Global distribution | CLI setup required |
| [Railway](https://railway.app) | $5 credit/month | Easy deploy | Limited free hours |
| [Vercel](https://vercel.com) | Serverless | Webhook-based bots | No long-running processes |
| [PythonAnywhere](https://pythonanywhere.com) | Yes | Simple bots | Limited resources |
| **Google Colab** | Free | Current setup | 12h session limit, needs tab open |

### Key Insights

1. **Colab Limitation**: Sessions timeout after ~12 hours and require browser tab open ([Stack Overflow](https://stackoverflow.com/questions/tagged/google-colaboratory))
2. **Webhook vs Polling**: Webhooks are more efficient for production ([python-telegram-bot docs](https://github.com/python-telegram-bot/python-telegram-bot))
3. **Mini Apps**: Require HTTPS hosting and more development effort ([Telegram Mini Apps Guide](https://telegram-mini-apps.com))

---

## Recommended Approach

### Phase 1: Simple Telegram Bot (Recommended First)

**Why Start Here:**
- Fastest to implement (1-2 days)
- Works with existing codebase
- No frontend development needed
- Can upgrade to Mini App later

**Architecture:**
```
User                    Telegram Bot              Google Drive
  │                          │                          │
  │── Send URL ─────────────>│                          │
  │                          │── Download file ────────>│
  │                          │<─── Upload complete ─────│
  │<── Success message ──────│                          │
```

### Phase 2: Telegram Mini App (Future Enhancement)

**Why Consider Later:**
- Beautiful visual interface
- File browser, progress bars, history
- More complex to build and maintain
- Requires React/Vue frontend

---

## Implementation Plan

### Phase 1: Simple Telegram Bot

#### Step 1: Create Bot Structure

```
src/
├── telegram_bot/
│   ├── __init__.py
│   ├── bot.py              # Main bot logic
│   ├── handlers.py         # Command handlers
│   ├── downloader.py       # Download logic (reuse existing)
│   └── config.py           # Configuration
```

#### Step 2: Core Features

| Command | Description |
|---------|-------------|
| `/start` | Welcome message, instructions |
| `/help` | List all commands |
| `/upload <url>` | Download URL to Drive |
| `/status` | Check current download status |
| `/history` | Show recent downloads |
| `/folder <name>` | Set destination folder |
| `/quota` | Check Drive storage |

#### Step 3: Bot Code Structure

```python
# bot.py - Core structure
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

async def start(update: Update, context):
    """Welcome message."""
    await update.message.reply_text(
        "Welcome to Drive Uploader Bot!\n\n"
        "Send me any URL and I'll upload it to your Google Drive.\n\n"
        "Commands:\n"
        "/upload <url> - Upload a file\n"
        "/status - Check download status\n"
        "/history - Recent downloads\n"
        "/quota - Check storage"
    )

async def handle_url(update: Update, context):
    """Handle URL messages."""
    url = update.message.text
    # Validate URL
    # Start download
    # Send progress updates
    # Notify completion

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.run_polling()  # or app.run_webhook() for production
```

#### Step 4: Deployment Options

**Option A: Render (Recommended)**
```yaml
# render.yaml
services:
  - type: worker
    name: drive-uploader-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python src/telegram_bot/bot.py
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: GOOGLE_CREDENTIALS
        sync: false
```

**Option B: Fly.io**
```toml
# fly.toml
app = "drive-uploader-bot"
primary_region = "sjc"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"
```

**Option C: Railway**
- Connect GitHub repo
- Add environment variables
- Auto-deploy on push

#### Step 5: Authentication Flow

For multi-user support, each user needs their own Google Drive access:

```
1. User sends /start
2. Bot generates OAuth URL
3. User clicks link, authorizes
4. Callback saves token for user
5. All uploads go to user's Drive
```

**Single-User Mode (Simpler):**
- Use your existing token.json
- All uploads go to your Drive
- Share bot only with trusted users

---

### Phase 2: Telegram Mini App (Future)

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Mini App                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  URL Input  │  │  Progress   │  │  File Browser   │ │
│  │    Form     │  │    Bars     │  │    (Drive)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└───────────────────────────┬─────────────────────────────┘
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend Server                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  FastAPI    │  │  Download   │  │  Google Drive   │ │
│  │  Endpoints  │  │   Queue     │  │     API         │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + Vite + Telegram Web App SDK |
| Backend | FastAPI (Python) |
| Database | SQLite / PostgreSQL |
| Queue | Redis + Celery |
| Hosting | Vercel (frontend) + Render (backend) |

#### Mini App Features

1. **URL Input**
   - Paste or type URL
   - Auto-detect URL type (video, direct, etc.)
   - Custom filename option

2. **Progress Dashboard**
   - Real-time download progress
   - Speed and ETA
   - Cancel option

3. **File Browser**
   - Browse Drive folders
   - Select destination
   - Create new folders

4. **History**
   - Past downloads
   - Re-download option
   - Share links

5. **Settings**
   - Default folder
   - Video quality preferences
   - Notifications

---

## Cost Analysis

### Free Tier Limits

| Service | Free Limit | Monthly Cost if Exceeded |
|---------|------------|--------------------------|
| Render Worker | 750 hours | $7/month |
| Fly.io | 3 shared VMs | $1.94/VM |
| Railway | $5 credit | Pay as you go |
| Google Drive API | 1B calls/day | Free |
| Telegram Bot API | Unlimited | Free |

### Recommended Setup (Free)

1. **Render** - Bot hosting (750 free hours = always on)
2. **Telegram** - Bot API (free)
3. **Google Drive** - Storage (your 2TB plan)

**Total Cost: $0/month**

---

## Implementation Timeline

### Week 1: Simple Bot
- [ ] Day 1-2: Bot structure and basic commands
- [ ] Day 3-4: Download integration (reuse existing code)
- [ ] Day 5: Testing and error handling
- [ ] Day 6-7: Deployment to Render

### Week 2: Enhancements
- [ ] Add video site support (yt-dlp)
- [ ] Add progress notifications
- [ ] Add download history
- [ ] Add multiple folder support

### Month 2+ (Optional): Mini App
- [ ] Design UI/UX
- [ ] Build React frontend
- [ ] Build FastAPI backend
- [ ] Integrate with Telegram Web App SDK
- [ ] Deploy and test

---

## Security Considerations

1. **Bot Token**: Store in environment variables, never in code
2. **Google Credentials**: Encrypt or use environment variables
3. **User Validation**: Whitelist allowed Telegram user IDs
4. **Rate Limiting**: Prevent abuse with download limits
5. **URL Validation**: Sanitize and validate all URLs

---

## Quick Start Commands

### Create Telegram Bot

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Choose name: `Drive Uploader Bot`
4. Choose username: `your_drive_uploader_bot`
5. Save the token provided

### Install Dependencies

```bash
pip install python-telegram-bot google-auth google-api-python-client yt-dlp requests
```

### Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
export GOOGLE_TOKEN_PATH="/path/to/token.json"
export ALLOWED_USERS="123456789,987654321"  # Telegram user IDs
```

---

## Recommendation

**Start with Phase 1 (Simple Bot)** because:

1. **Fastest to deploy** - Can be done in 1-2 days
2. **Uses existing code** - Reuse download logic from uploader_pro.py
3. **Free hosting available** - Render/Fly.io free tier sufficient
4. **Easy to maintain** - Simple Python code
5. **Good user experience** - Just send URL, get file in Drive

**Upgrade to Mini App only if:**
- You need a visual interface
- You have many non-technical users
- You want to offer it as a public service

---

## Sources

- [Telegram Bot Development Best Practices](https://merge.rocks)
- [python-telegram-bot GitHub](https://github.com/python-telegram-bot/python-telegram-bot)
- [Telegram Mini Apps Documentation](https://telegram-mini-apps.com)
- [Render Deployment Guide](https://alexfranz.com)
- [Fly.io Platform](https://fly.io)
- [Colab Session Management](https://stackoverflow.com/questions/tagged/google-colaboratory)
