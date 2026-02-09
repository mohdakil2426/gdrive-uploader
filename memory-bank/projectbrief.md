# Project Brief: Universal Google Drive Uploader

## Project Overview
A universal file uploader that transfers files from any URL directly to Google Drive without using local bandwidth or storage. Uses Google Drive as a message queue between local Python app and Google Colab worker.

## Core Requirements

### Primary Goal
- Upload any file from any URL directly to Google Drive
- Zero local network/storage usage (all transfers happen on Google's servers)
- No tunnels or CORS issues

### Architecture (v2.1)
```
Local (GUI/CLI) → Google Drive Queue → Colab Worker → Google Drive Storage
```

### Key Features
- **Smart URL Detection**: Auto-detects video platforms vs direct files
- **1500+ video sites** via yt-dlp (YouTube, Twitter, TikTok, etc.)
- **Any file type** (.zip, .pdf, .exe, .iso, etc.) via direct download
- **Original filename preservation** from Content-Disposition headers
- **Retry logic** with exponential backoff (3 retries)
- **Progress tracking** via status.json
- **Folder organization** in Drive

## User Profile
- Owner: Akila (mohdakil2426)
- GitHub: https://github.com/mohdakil2426/gdrive-uploader
- Google One AI Premium subscriber (2TB storage)
- Use case: Transfer large files without consuming local bandwidth

## Success Criteria
1. Add URL via GUI or CLI → File appears in Google Drive
2. No local download required
3. No tunnel or CORS issues
4. Works with direct links AND video sites
5. Preserves original filenames
6. Shows download progress

## Version
Current: 2.1.0
