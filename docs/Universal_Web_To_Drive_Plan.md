# Universal Web-to-Drive Uploader: Research & Implementation Plan

## 1. Executive Summary

This document outlines the expansion of the "CloudROM Porter" concept into a **Universal Web-to-Drive Uploader**. The goal is to allow the user to transfer files from _any_ website (direct links, video sites, file hosts) directly to their Google Drive (2TB storage) without using local bandwidth or disk space.

**Key Infrastructure:**

- **Storage:** Google Drive (2TB via Google One AI Premium).
- **Compute:** Google Colab (Recommended for free, high-speed Google-to-Google transfer) or Google Cloud Platform (GCP) VM.
- **Core Technology:** RAM-buffered streaming pipeline (`URL` -> `RAM` -> `Google Drive`).

---

## 2. Analysis of Original PRD (CloudROM Porter)

**Strengths:**

- **Core Concept:** Solves the bandwidth/storage bottleneck effectively using streaming.
- **Tech Stack:** Python + `google-api-python-client` is the standard, robust choice.
- **Architecture:** Separation of Scraper, Streamer, and Uploader is good design.

**Limitations to Address for "Universal" Scope:**

- **Specific Scraper:** Originally designed only for XDA/OnePlus. Needs a general-purpose link extractor.
- **Download Logic:** Relying solely on `requests.get()` works for direct links but fails for:
  - Video sites (YouTube, Vimeo, etc.).
  - File hosts with countdowns/captchas (MediaFire, Mega, etc.).
  - JavaScript-protected links.

---

## 3. Universal Architecture (The "Any Website" Upgrade)

### 3.1. The "Smart" Extractor Engine

Instead of writing custom scrapers for every site, we will utilize a tiered extraction strategy:

1.  **Tier 1: Direct Link Validator**
    - Checks if the URL allows a direct `HEAD` request and returns headers (Content-Length, Content-Type).
    - _Best for:_ Open directories, direct GitHub releases, static files.
2.  **Tier 2: The `yt-dlp` Layer (Media & General Sites)**
    - Uses `yt-dlp` (fork of `youtube-dl`) capable of extracting **direct video/file URLs** from 1000+ websites.
    - Command: `yt-dlp -g <url>` returns the underlying direct stream URL.
    - _Best for:_ YouTube, Twitter, Reddit, Twitch, and many supported generic video/file sites.
3.  **Tier 3: CloudScraper / Browserless (Advanced)**
    - For sites with Cloudflare protection or complex JS.
    - _Tools:_ `cloudscraper` library (Python) or a headless browser (Playwright).
    - _Strategy:_ Solve the challenge, get the cookie/user-agent, pass distinct headers to the Streamer.

### 3.2. The Streaming Bridge

This is the core pipeline that connects the Source URL to Google Drive.

- **Mechanism:** `requests.get(stream=True)` linked to `googleapiclient.http.MediaIoBaseUpload`.
- **Buffer Management:** A custom `io.BytesIO` wrapper or generator that chunks data (e.g., 10MB chunks).
- **Resumability:**
  - Google Drive API supports chunked uploads.
  - We must handle network interruptions by keeping track of the uploaded byte offset.

### 3.3. Infrastructure Upgrade (Leveraging "Google AI Ultra")

The user mentioned having the "Google AI Ultra" plan (likely **Google One AI Premium**).

- **Clarification:** This plan gives 2TB storage + Gemini Advanced. It does **not** typically grant free/unlimited Compute Engine (VM) credits beyond the standard GCP free tier (e2-micro).
- **Recommendation: Google Colab (Pro/Free)**
  - **Why:** It effectively acts as a Google-hosted "VM" with massive bandwidth to Google Drive (since they rely on similar backbone infrastructure).
  - **Cost:** Free.
  - **Speed:** fast (often 100MB/s+).
  - **Integration:** Native Google Drive mounting (`drive.mount`) or API authentication.

---

## 4. Implementation Plan

### Phase 1: Core Streamer Development (Python)

**Objective:** Build the universal pipe.

- **Tasks:**
  1.  Create `GDriveUploader` class with OAuth2 authentication.
  2.  Implement `stream_upload(file_url, folder_id, filename)` function.
  3.  **Critical:** Ensure the stream wrapper supports `read()`, `tell()`, and `seek()` (simulated) as required by `MediaIoBaseUpload`.

### Phase 2: Universal Link Extractor

**Objective:** Get a "streamable" URL from any input.

- **Tasks:**
  1.  Integrate `yt-dlp` Python library.
  2.  Create a resolver function:
      ```python
      def resolve_url(input_url):
          # Try yt-dlp first
          try:
              info = ytdl.extract_info(input_url, download=False)
              return info.get('url'), info.get('title')
          # Fallback to direct request
          except:
              return input_url, get_filename_from_headers(input_url)
      ```

### Phase 3: Interface & Deployment

**Objective:** Easy user interaction.

- **Deployment Target:** **Google Colab Notebook** (Instant access, no server setup cost).
- **UI:** Simple forms in Colab or a minimalist Streamlit app if running on a local/GCP VM.

---

## 5. Detailed Research Plan (Next Steps)

To execute this, we need to validate specific technical behaviors:

1.  **Verify `yt-dlp` Streaming Capability:**
    - Confirm `yt-dlp -g` links work with standard `requests.get` (check for expiring tokens/IP binding).
    - _Risk:_ Some generated URLs are IP-bound to the generator. If Colab generates the link, Colab must download it. (Safe).
2.  **Google Drive API Resumable Upload Chunks:**
    - Required chunk size must be a multiple of 256KB.
    - Testing the "pass-through" stream without calculating file size beforehand (some servers don't return `Content-Length`). (Drive API allows `resumable=True` with unknown size, but it's trickier).
3.  **Mega.nz / Mediafire Specifics:**
    - Sites like Mega.nz use client-side decryption. `yt-dlp` supports Mega, but streaming from it might require decrypting chunks on the fly. We need to verify if `mega.py` library allows stream interface.

## 6. Proposed Project Structure

```
Universal-Drive-Uploader/
├── core/
│   ├── auth.py          # Google OAuth handling
│   ├── streamer.py      # The requests -> GDrive pipe
│   ├── extractors/
│       ├── generic.py   # yt-dlp wrapper
│       ├── direct.py    # Standard HTTP handling
│       └── mega.py      # Special handling for Mega (if needed)
├── interface/
│   └── colab.ipynb      # The primary user interface
├── requirements.txt
└── README.md
```
