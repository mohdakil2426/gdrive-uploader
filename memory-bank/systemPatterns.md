# System Patterns: Universal Google Drive Uploader

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                           │
│                  (Google Colab Tab)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ Paste URL + Run
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               GOOGLE COLAB RUNTIME                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ URL Resolver│→ │  Streamer   │→ │  Drive API Upload   │ │
│  │  (yt-dlp)   │  │  (requests) │  │  (google-api-client)│ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼ Direct server-to-server transfer
┌─────────────────────────────────────────────────────────────┐
│                   GOOGLE DRIVE                              │
│                  (User's 2TB Storage)                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Streaming Pipeline
- Never download entire file to memory/disk
- Stream chunks directly: Source → RAM buffer → Drive API
- Chunk size: 8-50MB for optimal performance

### 2. URL Resolution Strategy
```
Input URL
    │
    ▼
┌─────────────────┐
│ Is Direct Link? │──Yes──→ Use requests.get(stream=True)
└────────┬────────┘
         │ No
         ▼
┌─────────────────┐
│  Try yt-dlp     │──Success──→ Extract direct stream URL
└────────┬────────┘
         │ Fail
         ▼
    Return Error
```

### 3. Authentication Flow
- Google Colab: Native `drive.mount()` - simplest
- VM/Script: OAuth2 with refresh token from token.json

## Component Relationships

### Colab Notebook (Primary)
```
colab_uploader.ipynb
├── Cell 1: Setup & Mount Drive
├── Cell 2: URL Input Form
├── Cell 3: Download Functions
│   ├── direct_download()
│   └── ytdlp_download()
└── Cell 4: Execute Upload
```

### VM Script (Secondary)
```
gdrive_uploader.py
├── Authentication (token.json)
├── File Upload (MediaFileUpload)
├── Folder Management
└── CLI Interface
```

## Critical Implementation Details

### Chunk Size Selection
- Colab to Drive: 8MB chunks (fast, stable)
- External URL: Match server's preferred chunk size
- Drive API: Must be multiple of 256KB

### Error Handling
- Network timeout: Retry with exponential backoff
- Auth expired: Auto-refresh token
- File too large: Use resumable upload

### Performance Optimizations
- Google-to-Google transfers: ~100MB/s possible
- Use `stream=True` in requests
- Avoid intermediate disk writes
