# Product Context: Universal Google Drive Uploader

## Why This Project Exists

### Problem Statement
When you want to download a large file to Google Drive:
- Traditional: Download to PC → Upload to Drive (uses 2x bandwidth + local storage)
- Web UI approach: CORS issues, tunnel session expiry, complexity

### Solution (v2.0)
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

### Supported Sources
- Direct download links (any file type)
- Video platforms (YouTube, Twitter, Reddit, etc. via yt-dlp)
- 1500+ sites supported by yt-dlp
- Any HTTP/HTTPS accessible URL

## User Experience Goals

### Simplicity
- GUI: Paste URL, click button
- CLI: `python uploader.py "url"`
- No tunnel URLs to copy/paste

### Reliability
- Queue persists in Google Drive
- Colab can restart without losing queue
- No 60-minute session limits

### No Dependencies
- No browser required (unlike Web UI)
- No tunnel services
- Just Python + Google API
