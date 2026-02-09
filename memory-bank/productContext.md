# Product Context: Universal Google Drive Uploader

## Why This Project Exists

### Problem Statement
When you want to download a large file to Google Drive:
- Traditional: Download to PC → Upload to Drive (uses 2x bandwidth + local storage)
- Web UI approach: CORS issues, tunnel session expiry, complexity

### Solution (v2.1)
Use Google Drive as a message queue:
- Local app writes URL to Drive queue
- Colab worker polls queue, downloads, saves to Drive
- No tunnels, no CORS, no session limits

## How It Works

### User Experience Flow
1. Run Python GUI or CLI
2. Paste URL, select folder
3. URL added to queue.json on Drive
4. Colab worker picks up and downloads
5. File appears in Google Drive

### Smart URL Detection
The Colab Worker automatically detects URL type:
- **Video platforms** (YouTube, Twitter, etc.) → Uses yt-dlp
- **Direct files** (.zip, .pdf, .exe, etc.) → Uses requests
- **Unknown URLs** → Tries yt-dlp first, falls back to direct download

### Supported Sources
- **50+ file extensions**: .zip, .rar, .pdf, .exe, .iso, .mp3, .mp4, etc.
- **1500+ video sites**: YouTube, Twitter, TikTok, Instagram, Reddit, etc.
- **Any HTTP/HTTPS URL**: Direct download with original filename preservation

## User Experience Goals

### Simplicity
- GUI: Paste URL, click button
- CLI: `python uploader.py "url"`
- Colab: Click badge in README → Run cells
- No tunnel URLs to copy/paste

### Reliability
- Queue persists in Google Drive
- Colab can restart without losing queue
- Retry logic with exponential backoff (3 attempts)
- No 60-minute session limits

### Original Filenames
- Extracts from Content-Disposition header
- Falls back to URL path
- Generates timestamp-based name if needed
- Sanitizes for filesystem compatibility

### No Dependencies
- No browser required (unlike Web UI)
- No tunnel services
- Just Python + Google API
