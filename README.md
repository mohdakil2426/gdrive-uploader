# Universal Drive Uploader

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/user/GdriveUploader/blob/main/notebooks/Web_Uploader_Server.ipynb)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

> Upload any URL directly to Google Drive. Zero local bandwidth.

## Quick Start

### Web UI (Recommended)
1. Open `notebooks/Web_Uploader_Server.ipynb` in Google Colab
2. Run all cells - copy the Pinggy URL shown
3. Open `web/index.html` in your browser
4. Paste the URL, click Connect, start uploading!

### CLI Mode
```bash
python src/uploader_pro.py "https://example.com/file.zip"
```

## Features
- **1500+ Sites** - YouTube, Twitter, Instagram, TikTok, and more
- **Direct Links** - Any file type from any URL
- **Real-time Progress** - Live speed, ETA, and progress bar
- **Zero Bandwidth** - Files transfer within Google's network
- **Dark Theme** - Beautiful modern interface

## Project Structure
```
GdriveUploader/
├── web/                    # Web UI (HTML/CSS/JS)
├── notebooks/              # Colab notebooks
│   └── Web_Uploader_Server.ipynb  # Main server
├── src/                    # Python scripts
└── docs/                   # Documentation
```

## Tech Stack
- **Frontend**: Tailwind CSS, Vanilla JS, SSE
- **Backend**: Flask, Pinggy.io, yt-dlp
- **Cloud**: Google Colab, Google Drive API

## Setup

1. **Google Cloud Console**: Enable Drive API, create OAuth credentials
2. **Download**: `credentials.json` to project root
3. **First Run**: Authorize when prompted, creates `token.json`

See `docs/SETUP_GUIDE.md` for detailed instructions.

## License
MIT
