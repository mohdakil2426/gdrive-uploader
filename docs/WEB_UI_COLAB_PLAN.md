# Web UI + Colab Backend Plan: Universal Drive Uploader

## Executive Summary

A beautiful, modern web interface that runs locally in your browser, connected to a Google Colab backend via Pinggy.io tunnel. You provide URLs through the UI, Colab downloads and uploads to Google Drive - **zero local bandwidth used for file transfers**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR LOCAL MACHINE                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Beautiful Web UI (Browser)                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  │  URL Input  │  │   Folder    │  │     Download Queue      │   │  │
│  │  │  (Paste/    │  │   Picker    │  │  ┌─────┐ ┌─────┐ ┌───┐ │   │  │
│  │  │   Drag)     │  │   (Tree)    │  │  │ 45% │ │ 78% │ │...│ │   │  │
│  │  └─────────────┘  └─────────────┘  │  └─────┘ └─────┘ └───┘ │   │  │
│  │                                     └─────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    │ HTTP Requests (tiny JSON only)      │
│                                    │ SSE Events (progress updates)       │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
                            Pinggy.io tunnel
                                     │
┌────────────────────────────────────┼─────────────────────────────────────┐
│                           GOOGLE COLAB                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Flask API Server                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │  │
│  │  │  /download  │  │  /folders   │  │      /progress (SSE)    │   │  │
│  │  │   endpoint  │  │   endpoint  │  │   real-time updates     │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘   │  │
│  │         │                │                                        │  │
│  │         ▼                ▼                                        │  │
│  │  ┌─────────────────────────────────────────────────────────┐     │  │
│  │  │              Download Engine (yt-dlp + requests)         │     │  │
│  │  │                    ~100 MB/s speeds                      │     │  │
│  │  └──────────────────────────┬──────────────────────────────┘     │  │
│  │                             │                                     │  │
│  │                             ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────┐     │  │
│  │  │              Google Drive API (direct upload)            │     │  │
│  │  │               to your 2TB Google One storage             │     │  │
│  │  └─────────────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Approach?

| Benefit | Description |
|---------|-------------|
| **Zero Local Bandwidth** | Files never touch your machine - Colab downloads directly to Drive |
| **Beautiful UI** | Modern, responsive interface you can customize |
| **Real-time Progress** | SSE provides live download/upload progress |
| **No Installation** | Just open HTML file in browser |
| **Free Infrastructure** | Colab is free, Pinggy.io is free (no account needed) |
| **Fast Transfers** | Google-to-Google speeds (~100 MB/s) |

---

## Critical Requirements (Research Findings 2024-2025)

### Pinggy.io Tunnel (PRIMARY - Recommended)

> **Why Pinggy**: No account required, no installation, unlimited bandwidth, works instantly with a single SSH command.

**Free Tier Features:**
- No account or registration needed
- Unlimited bandwidth
- TCP/TLS tunnel support
- 60-minute session timeout (auto-reconnect handles this)
- Dynamic URLs (changes on restart)

**Setup in Colab (One Line!):**
```python
# Expose Flask server on port 5000
!ssh -p 443 -R0:localhost:5000 -o StrictHostKeyChecking=no a.pinggy.io
```

**With Auto-Reconnect:**
```python
import subprocess
import threading
import time

def start_pinggy_tunnel(port=5000):
    """Start Pinggy tunnel with auto-reconnect."""
    while True:
        try:
            process = subprocess.Popen(
                ["ssh", "-p", "443", f"-R0:localhost:{port}",
                 "-o", "StrictHostKeyChecking=no",
                 "-o", "ServerAliveInterval=30",
                 "a.pinggy.io"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            # Read and print the tunnel URL
            for line in process.stdout:
                line = line.decode().strip()
                if "http" in line.lower():
                    print(f"Tunnel URL: {line}")
                print(line)
            process.wait()
        except Exception as e:
            print(f"Tunnel error: {e}")
        print("Reconnecting in 5 seconds...")
        time.sleep(5)

# Run in background thread
tunnel_thread = threading.Thread(target=start_pinggy_tunnel, daemon=True)
tunnel_thread.start()
```

**Paid Option ($3/month):** Persistent URL that never changes.

Source: [pinggy.io](https://pinggy.io)

### Alternative: ngrok (Fallback)

If Pinggy has issues, ngrok is a reliable fallback:
- Requires free account registration
- 1 GB/month bandwidth limit
- More stable long-term

```python
from pyngrok import ngrok
ngrok.set_auth_token("YOUR_TOKEN")
public_url = ngrok.connect(5000)
```

Source: [ngrok.com](https://ngrok.com)

### Colab Session Keep-Alive

Colab has two timeouts:
- **Idle timeout**: ~90 minutes without interaction
- **Max session**: 12 hours (free) / 24 hours (Pro)

**Keep-Alive JavaScript** (paste in browser console):
```javascript
function KeepColabAlive() {
    setInterval(() => {
        console.log("Keeping Colab alive...");
        const btn = document.querySelector("colab-connect-button");
        if (btn?.shadowRoot?.querySelector("#connect")) {
            btn.shadowRoot.querySelector("#connect").click();
        }
    }, 60000);
}
KeepColabAlive();
```

Source: [Stack Overflow](https://stackoverflow.com/questions/tagged/google-colaboratory), [Medium](https://medium.com)

### Tunneling Alternatives

| Service | Pros | Cons | Best For |
|---------|------|------|----------|
| **ngrok** | Easy setup, reliable | Requires account | Default choice |
| **Cloudflare Tunnel** | Free SSL, DDoS protection, stable | More setup | Security-focused |
| **Serveo** | No installation, SSH-based | Less reliable | Quick testing |
| **Pinggy.io** | No install, generous free tier | Newer | Simple use |
| **LocalTunnel** | Open source, no account | Connection drops | Node.js users |

Source: [Medium](https://medium.com), [LocalTunnel](https://localtunnel.me)

---

## Tech Stack

### Frontend (Local Browser)

| Component | Technology | Why |
|-----------|------------|-----|
| **Styling** | Tailwind CSS (CDN) | Modern, utility-first, no build step |
| **Icons** | Heroicons or Lucide | Clean, professional SVG icons |
| **JavaScript** | Vanilla ES6+ | No framework needed, simple & fast |
| **Progress** | EventSource API | Native SSE support in browsers |
| **Storage** | localStorage | Remember settings, history |

### Backend (Google Colab)

| Component | Technology | Why |
|-----------|------------|-----|
| **Web Server** | Flask | Simple, Pythonic, well-documented |
| **Tunnel** | pyngrok | Expose Colab to internet |
| **Downloads** | yt-dlp + requests | Universal file/video downloads |
| **Drive API** | google-api-python-client | Official Google library |
| **Progress** | Flask SSE | Real-time event streaming |
| **Queue** | Python queue + threading | Handle multiple downloads |

---

## UI Design

### Color Palette

```css
:root {
    --bg-primary: #0f172a;      /* Dark slate */
    --bg-secondary: #1e293b;    /* Lighter slate */
    --accent-blue: #3b82f6;     /* Vibrant blue */
    --accent-green: #10b981;    /* Success green */
    --accent-red: #ef4444;      /* Error red */
    --accent-yellow: #f59e0b;   /* Warning yellow */
    --text-primary: #f1f5f9;    /* Light text */
    --text-secondary: #94a3b8;  /* Muted text */
}
```

### Layout Sections

```
┌──────────────────────────────────────────────────────────────┐
│  HEADER                                                       │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ [Logo] Universal Drive Uploader    [Settings] [Theme]    ││
│  └──────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────┤
│  CONNECTION STATUS                                            │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ [●] Connected to Colab   |   Server: xyz.ngrok.io        ││
│  └──────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────┤
│  URL INPUT                                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  ┌────────────────────────────────────────────────────┐  ││
│  │  │  Paste URL or drag & drop link here...             │  ││
│  │  │                                                     │  ││
│  │  │     [Supports 1500+ video sites, direct links,     │  ││
│  │  │      cloud storage, and more]                      │  ││
│  │  └────────────────────────────────────────────────────┘  ││
│  │                                                           ││
│  │  Destination: [Downloads ▼]  Format: [Best ▼]  [ADD]     ││
│  └──────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────┤
│  ACTIVE DOWNLOADS                                             │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  ┌────────────────────────────────────────────────────┐  ││
│  │  │ [▶] video_title.mp4                                │  ││
│  │  │ ████████████████████░░░░░░░░░░░░░░░░░░░░  67%     │  ││
│  │  │ 1.2 GB / 1.8 GB  •  45 MB/s  •  ETA: 13s  [Cancel]│  ││
│  │  └────────────────────────────────────────────────────┘  ││
│  │  ┌────────────────────────────────────────────────────┐  ││
│  │  │ [⏳] file.zip                                      │  ││
│  │  │ Queued • Position: 2                               │  ││
│  │  └────────────────────────────────────────────────────┘  ││
│  └──────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────┤
│  COMPLETED (Collapsible)                                      │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  [✓] movie.mkv      2.3 GB    /Movies     2 min ago     ││
│  │  [✓] document.pdf   15 MB     /Documents  5 min ago     ││
│  └──────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────┤
│  FOOTER                                                       │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  Drive Usage: 245 GB / 2 TB  [████░░░░░░] 12%           ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## Features

### Core Features (Phase 1)

| Feature | Description |
|---------|-------------|
| **URL Input** | Paste single URL or multiple URLs (one per line) |
| **Folder Selection** | Dropdown of existing Drive folders |
| **Progress Tracking** | Real-time progress bar with speed & ETA |
| **Download Queue** | Queue multiple URLs, process sequentially |
| **Connection Status** | Show if Colab server is connected |
| **History** | Recent downloads with status |
| **Dark/Light Theme** | Toggle between themes |

### Advanced Features (Phase 2)

| Feature | Description |
|---------|-------------|
| **Drag & Drop** | Drag URLs/links onto the page |
| **Folder Browser** | Full tree view of Drive folders |
| **Create Folder** | Create new folders from UI |
| **Video Quality** | Select quality for video sites |
| **Batch Import** | Import URLs from text file |
| **Notifications** | Browser notifications on complete |
| **Download History** | Persistent history with search |
| **Retry Failed** | One-click retry for failed downloads |

### Power Features (Phase 3)

| Feature | Description |
|---------|-------------|
| **Playlist Support** | Download entire playlists |
| **Schedule Downloads** | Queue for later execution |
| **Bandwidth Stats** | Show transfer statistics |
| **Multi-Server** | Connect to multiple Colab instances |
| **Export/Import Settings** | Backup configuration |

---

## API Endpoints

### Colab Flask Server

```python
# POST /api/download
# Start a new download
{
    "url": "https://example.com/file.zip",
    "folder": "Downloads",
    "filename": null,  # Optional custom filename
    "format": "best"   # For video sites
}
# Returns: { "id": "abc123", "status": "queued" }

# GET /api/progress/<id>
# SSE endpoint for real-time progress
# Streams: { "percent": 67, "speed": "45 MB/s", "eta": "13s", "downloaded": "1.2 GB", "total": "1.8 GB" }

# GET /api/status/<id>
# Get download status
# Returns: { "id": "abc123", "status": "downloading|completed|failed", "filename": "...", "error": null }

# GET /api/queue
# Get all queued/active downloads
# Returns: [ { "id": "...", "url": "...", "status": "..." }, ... ]

# DELETE /api/download/<id>
# Cancel a download
# Returns: { "success": true }

# GET /api/folders
# List Drive folders
# Returns: [ { "id": "...", "name": "Downloads", "path": "/Downloads" }, ... ]

# POST /api/folders
# Create new folder
{
    "name": "NewFolder",
    "parent": "root"  # or folder ID
}
# Returns: { "id": "...", "name": "NewFolder" }

# GET /api/quota
# Get Drive storage quota
# Returns: { "used": "245 GB", "total": "2 TB", "percent": 12 }

# GET /api/health
# Check server status
# Returns: { "status": "ok", "uptime": "2h 34m" }
```

---

## Implementation Plan

### Phase 1: Core System (Days 1-3)

#### Day 1: Colab Backend
- [ ] Flask server setup with CORS
- [ ] ngrok integration with stable URL
- [ ] Basic `/download` endpoint
- [ ] Direct URL download with progress
- [ ] Drive upload functionality
- [ ] `/health` endpoint

#### Day 2: Frontend Foundation
- [ ] HTML structure with Tailwind
- [ ] URL input component
- [ ] Server connection handling
- [ ] Basic download trigger
- [ ] Progress display (polling initially)

#### Day 3: Real-time & Polish
- [ ] SSE implementation for progress
- [ ] Download queue in UI
- [ ] Error handling & display
- [ ] Folder dropdown
- [ ] Basic styling & responsive design

### Phase 2: Enhanced Features (Days 4-6)

#### Day 4: Video Support & Queue
- [ ] yt-dlp integration
- [ ] Video format selection
- [ ] Download queue management
- [ ] Cancel functionality

#### Day 5: UI Enhancements
- [ ] Drag & drop support
- [ ] Dark/light theme toggle
- [ ] History panel
- [ ] Browser notifications
- [ ] localStorage for settings

#### Day 6: Drive Integration
- [ ] Folder browser/tree view
- [ ] Create folder functionality
- [ ] Storage quota display
- [ ] Multiple URL input

### Phase 3: Advanced Features (Days 7-10)

#### Day 7-8: Power Features
- [ ] Playlist support
- [ ] Batch URL import
- [ ] Retry failed downloads
- [ ] Download statistics

#### Day 9-10: Polish & Documentation
- [ ] Final UI polish
- [ ] Error edge cases
- [ ] README update
- [ ] Usage documentation

---

## File Structure

```
GdriveUploader/
├── web/
│   ├── index.html           # Main UI
│   ├── css/
│   │   └── styles.css       # Custom styles (minimal with Tailwind)
│   ├── js/
│   │   ├── app.js           # Main application logic
│   │   ├── api.js           # API communication
│   │   ├── ui.js            # UI updates & components
│   │   ├── storage.js       # localStorage helpers
│   │   └── utils.js         # Utility functions
│   └── assets/
│       └── logo.svg         # Logo/icons
├── notebooks/
│   └── Web_Uploader_Server.ipynb  # New Colab server
├── src/
│   └── (existing files)
└── docs/
    └── WEB_UI_COLAB_PLAN.md  # This document
```

---

## Colab Notebook Structure

### Cell 1: Setup & Dependencies
```python
# Install dependencies
!pip install -q flask flask-cors pyngrok yt-dlp google-auth google-api-python-client

# Mount Drive
from google.colab import drive
drive.mount('/content/drive')
```

### Cell 2: Configuration
```python
# Configuration
NGROK_AUTH_TOKEN = ""  # Optional: for stable URLs
DRIVE_BASE = "/content/drive/MyDrive"
DEFAULT_FOLDER = "Downloads"
```

### Cell 3: Flask Server
```python
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import threading
import queue
# ... full server implementation
```

### Cell 4: Start Server
```python
# Start the server
# Displays ngrok URL to use in web UI
run_server()
```

---

## Security Considerations

| Concern | Solution |
|---------|----------|
| **ngrok URL exposure** | Use auth token for stable URLs, don't share publicly |
| **CORS** | Restrict to localhost origins in production |
| **Input validation** | Sanitize all URLs before processing |
| **Rate limiting** | Implement request throttling |
| **Token security** | Keep OAuth tokens in Colab only, never expose to frontend |

---

## Known Limitations

| Limitation | Workaround |
|------------|------------|
| **Colab timeout** | Keep browser tab open, 12h max session |
| **ngrok URL changes** | Use ngrok auth for stable subdomain |
| **No authentication** | Run locally, don't expose to internet |
| **Single user** | Designed for personal use |

---

## Quick Start (After Implementation)

### 1. Start Colab Server
```
1. Open Web_Uploader_Server.ipynb in Colab
2. Run all cells
3. Copy the ngrok URL displayed
```

### 2. Open Web UI
```
1. Open web/index.html in browser
2. Paste ngrok URL in settings
3. Click "Connect"
4. Start adding URLs!
```

---

## UI Mockup (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│  ☁️ Universal Drive Uploader                    ⚙️ Settings     │
├─────────────────────────────────────────────────────────────────┤
│  ● Connected                     https://abc123.ngrok.io        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │                                                          │  │
│    │        📎 Paste URL or drop link here                   │  │
│    │                                                          │  │
│    │    Supports YouTube, Twitter, Instagram, direct links   │  │
│    │                    and 1500+ more sites                  │  │
│    │                                                          │  │
│    └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│    📁 Save to: [ Downloads          ▼]   🎬 [ Best Quality ▼]  │
│                                                                  │
│                        [ ➕ Add to Queue ]                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  DOWNLOADS                                                       │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  🎬 Rick Astley - Never Gonna Give You Up.mp4                   │
│  ████████████████████████░░░░░░░░░░░░░░░░  62%                  │
│  42.5 MB / 68.3 MB  •  12.4 MB/s  •  ETA: 2s           [Cancel] │
│                                                                  │
│  📄 project_files.zip                                            │
│  ⏳ Queued • Position #2                               [Remove] │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  ✅ COMPLETED                                            [Clear]│
│  ────────────────────────────────────────────────────────────── │
│  ✓ document.pdf          15.2 MB    /Documents     2 min ago   │
│  ✓ photo_album.zip       234 MB     /Photos        5 min ago   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  💾 Storage: 245 GB / 2 TB used  ████░░░░░░░░░░░░░░░░░░  12%   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

This plan creates a **beautiful, modern web UI** that:

1. **Runs locally** - Just open `index.html` in your browser
2. **Connects to Colab** - Via ngrok tunnel for API communication
3. **Uses zero local bandwidth** - All file transfers happen in Google's cloud
4. **Provides real-time feedback** - SSE for live progress updates
5. **Supports everything** - Direct links, video sites, cloud storage
6. **Is completely free** - Colab free tier + ngrok free tier

**Next Step**: Start implementation with Phase 1, beginning with the Colab Flask server notebook.

---

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [ngrok Python SDK](https://github.com/ngrok/ngrok-python)
- [Tailwind CSS](https://tailwindcss.com/)
- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Google Drive API](https://developers.google.com/drive/api/v3/reference)
