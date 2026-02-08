# Product Context: Universal Google Drive Uploader

## Why This Project Exists

### Problem Statement
When you want to download a large file (video, software, backup) to Google Drive:
- Traditional method: Download to PC → Upload to Drive (uses 2x bandwidth + local storage)
- This wastes time, bandwidth, and requires local disk space

### Solution
Use Google's own infrastructure (Colab/VM) to transfer directly:
- URL → Google Servers → Google Drive
- Your PC only sends the URL command
- All heavy lifting happens in Google's data centers

## How It Should Work

### User Experience Flow
1. Open Google Colab notebook
2. Paste the file URL
3. Click "Run"
4. File appears in Google Drive

### Supported Sources
- Direct download links (any file type)
- Video platforms (YouTube, Twitter, Reddit, etc. via yt-dlp)
- File hosting services (where possible)
- Any HTTP/HTTPS accessible URL

## User Experience Goals

### Simplicity
- One notebook, minimal configuration
- Copy-paste URL workflow
- Clear progress feedback

### Reliability
- Handle network interruptions
- Resume failed uploads
- Validate file integrity

### Flexibility
- Any file format
- Custom destination folders
- Batch URL processing
