# System Patterns: Universal Google Drive Uploader

## Architecture (v2.0 - Tunnel-Free)

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR PC                                  │
│   ┌─────────────────┐         ┌─────────────────┐               │
│   │   GUI App       │   OR    │   CLI Script    │               │
│   │   gui/app.py    │         │   uploader.py   │               │
│   └────────┬────────┘         └────────┬────────┘               │
│            └───────────┬───────────────┘                         │
│                        ▼                                         │
│              Google Drive API (writes queue.json)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE DRIVE                                  │
│   MyDrive/.uploader/                                            │
│   ├── queue.json    ← URLs to download                          │
│   └── status.json   ← Progress updates                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE COLAB                                  │
│   notebooks/Worker.ipynb                                        │
│   - Polls queue.json every 5 seconds                            │
│   - Downloads via yt-dlp (1500+ sites) or requests              │
│   - Saves directly to Google Drive                              │
│   - Updates status.json with progress                           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **User adds URL** via GUI or CLI
2. **Local app writes** to `queue.json` on Drive
3. **Colab Worker polls** `queue.json` every 5 seconds
4. **Worker downloads** file using yt-dlp or requests
5. **Worker saves** file directly to Google Drive
6. **Worker updates** `status.json` with progress
7. **Local app reads** `status.json` for UI updates

## File Formats

### queue.json
```json
{
  "downloads": [
    {
      "id": "uuid",
      "url": "https://...",
      "folder": "Downloads",
      "status": "pending",
      "added_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### status.json
```json
{
  "downloads": {
    "uuid": {
      "status": "downloading",
      "percent": 45,
      "speed": "5.2 MB/s",
      "filename": "video.mp4"
    }
  }
}
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Drive as queue | No tunnel needed, persistent, both sides can access |
| Polling (not push) | Simpler, Colab can't receive webhooks |
| CustomTkinter | Modern look, dark theme built-in, cross-platform |
| Single-file scripts | Easy to understand, no complex imports |
| yt-dlp for videos | Supports 1500+ sites, active development |

## Why Not Web UI?

| Issue | Impact |
|-------|--------|
| CORS | Browser blocks cross-origin requests |
| Tunnel expiry | Pinggy 60-min sessions |
| Complexity | Flask + tunnel + frontend code |
