# Universal Drive Uploader

[![Open Worker in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohdakil2426/gdrive-uploader/blob/main/notebooks/Worker.ipynb)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

> Upload any URL directly to Google Drive. Zero local bandwidth.

## Quick Start

### 1. Start the Colab Worker
Click the badge above or open `notebooks/Worker.ipynb` in Google Colab and run all cells.

### 2. Use GUI or CLI

**GUI (Recommended)**
```bash
pip install customtkinter google-api-python-client google-auth-oauthlib
python gui/app.py
```

**CLI**
```bash
python uploader.py "https://youtube.com/watch?v=xxx"
python uploader.py "https://example.com/file.zip" --folder "Archives"
python uploader.py --status
```

## How It Works

```
Your PC (GUI/CLI) → Google Drive Queue → Colab Worker → Google Drive Storage
```

- No tunnels, no CORS issues, no session limits
- Queue persists in Google Drive
- Works offline (queue syncs when online)

## Features
- **1500+ Sites** - YouTube, Twitter, Instagram, TikTok, and more (via yt-dlp)
- **Direct Links** - Any file type from any URL
- **Real-time Progress** - Live speed and progress tracking
- **Zero Bandwidth** - Files transfer within Google's network
- **Modern GUI** - Dark-themed CustomTkinter interface

## Project Structure
```
GdriveUploader/
├── gui/
│   └── app.py              # Modern GUI (CustomTkinter)
├── notebooks/
│   └── Worker.ipynb        # Colab worker (click badge to open)
├── uploader.py             # CLI script
├── pyproject.toml          # Linting config (ruff, pylint, pyrefly)
└── memory-bank/            # Project documentation
```

## Setup

1. **Google Cloud Console**: Enable Drive API, create OAuth credentials (Desktop app)
2. **Download**: `credentials.json` to project root
3. **First Run**: Authorize when prompted, creates `token.json`

## License
MIT
