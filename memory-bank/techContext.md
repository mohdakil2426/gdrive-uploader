# Tech Context: Universal Google Drive Uploader

## Technology Stack

### Local Machine
| Component | Technology |
|-----------|------------|
| GUI | CustomTkinter (Python) |
| CLI | argparse (Python stdlib) |
| API Client | google-api-python-client |
| Auth | google-auth, google-auth-oauthlib |
| Colors | colorama |

### Google Colab (Worker)
| Component | Technology |
|-----------|------------|
| Runtime | Python 3.10+ |
| Video Downloads | yt-dlp (1500+ sites) |
| Direct Downloads | requests |
| Storage | Google Drive (mounted) |
| Progress | Real-time status.json updates |

### Communication
| Component | Technology |
|-----------|------------|
| Message Queue | Google Drive (.uploader/ folder) |
| Protocol | Google Drive API v3 |
| Format | JSON files |

## Dependencies

### Local (pip install)
```
customtkinter>=5.0.0
google-api-python-client>=2.0.0
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
colorama>=0.4.0
```

### Colab (pip install in notebook)
```
yt-dlp
requests
```

## Development Tools

| Tool | Purpose | Status |
|------|---------|--------|
| Ruff | Fast Python linting | 0 errors ✅ |
| Pylint | Python linting | 10.00/10 ✅ |
| Pyrefly | Type checking | False positives (documented) |

Configuration in `pyproject.toml`.

### Linting Commands
```bash
python -m ruff check .
python -m pylint uploader.py gui/app.py
python -m pyrefly check .  # Ignore errors - false positives
```

## API Configuration

### Google Cloud Console
- Project: (user's project)
- APIs enabled: Google Drive API
- OAuth: Desktop application credentials

### Credential Files
| File | Location | Purpose |
|------|----------|---------|
| credentials.json | Project root | OAuth client config |
| token.json | Project root | User access token (auto-generated) |

### Drive Folder Structure
```
MyDrive/
├── .uploader/           # Hidden folder for queue
│   ├── queue.json       # Download requests
│   └── status.json      # Progress updates
├── Downloads/           # Default download folder
├── Videos/
├── Music/
├── Documents/
├── Pictures/
└── ...
```

## Worker Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| POLL_INTERVAL | 5 seconds | Queue check frequency |
| MAX_RETRIES | 3 | Retry attempts per download |
| RETRY_DELAY | 5 seconds | Initial delay (exponential backoff) |
| CHUNK_SIZE | 1 MB | Download chunk size |
| REQUEST_TIMEOUT | 30 seconds | HTTP request timeout |

## Platform Support

| Platform | GUI | CLI | Colab |
|----------|-----|-----|-------|
| Windows | ✅ | ✅ | ✅ |
| macOS | ✅ | ✅ | ✅ |
| Linux | ✅ | ✅ | ✅ |

## Known Limitations

1. **Pyrefly false positives**: Google API uses dynamic attributes (`Resource.files()`)
2. **google.colab import**: Only available in Colab environment
3. **Colab timeout**: Free tier may disconnect after ~12 hours
4. **Drive quota**: 15GB free, 2TB with Google One
5. **yt-dlp updates**: May need periodic updates for site changes
