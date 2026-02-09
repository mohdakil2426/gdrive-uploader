# System Patterns: Universal Google Drive Uploader

## Architecture (v2.1 - Smart Download)

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
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Smart Download Logic:                                    │   │
│   │ URL → Check extension →                                  │   │
│   │   ├─ .zip/.pdf/.exe → Direct download (requests)        │   │
│   │   ├─ youtube.com    → Video download (yt-dlp)           │   │
│   │   └─ Unknown        → Try yt-dlp, fallback to direct    │   │
│   └─────────────────────────────────────────────────────────┘   │
│   - Polls queue.json every 5 seconds                            │
│   - Preserves original filenames                                │
│   - Retries with exponential backoff                            │
│   - Saves directly to Google Drive                              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **User adds URL** via GUI or CLI
2. **Local app writes** to `queue.json` on Drive
3. **Colab Worker polls** `queue.json` every 5 seconds
4. **Worker detects URL type** (video platform or direct file)
5. **Worker downloads** using appropriate method (yt-dlp or requests)
6. **Worker saves** file with original filename to Google Drive
7. **Worker updates** `status.json` with progress
8. **Local app reads** `status.json` for UI updates

## Smart URL Detection

| Check | Method | Example |
|-------|--------|---------|
| File extension in URL | Direct download | `example.com/file.zip` |
| Known video platform | yt-dlp | `youtube.com/watch?v=xxx` |
| Content-Type header | Direct download | Non-HTML responses |
| Unknown | Try yt-dlp first | Falls back to direct |

## Supported Extensions (Direct Download)

```python
DIRECT_DOWNLOAD_EXTENSIONS = {
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.iso',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Images
    '.jpg', '.png', '.gif', '.svg', '.webp',
    # Executables
    '.exe', '.msi', '.dmg', '.apk', '.deb',
    # Media
    '.mp3', '.mp4', '.mkv', '.flac', '.wav',
    # And more...
}
```

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
      "filename": "original_file.zip",
      "eta": "30s"
    }
  }
}
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Drive as queue | No tunnel needed, persistent, both sides can access |
| Smart URL detection | Don't treat .zip files as videos |
| Original filename preservation | User expects same filename as source |
| Retry with backoff | Networks are unreliable, 3 attempts reasonable |
| CustomTkinter | Modern look, dark theme built-in, cross-platform |
| Single-file scripts | Easy to understand, no complex imports |
