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

### Google Colab
| Component | Technology |
|-----------|------------|
| Runtime | Python 3.10+ |
| Video Downloads | yt-dlp |
| Direct Downloads | requests |
| Storage | Google Drive (mounted) |

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

### Colab (pre-installed or pip)
```
yt-dlp
requests
google-api-python-client
```

## Development Tools

| Tool | Purpose | Status |
|------|---------|--------|
| Pylint | Python linting | 10.00/10 |
| Ruff | Fast Python linting | 0 errors |
| Pyrefly | Type checking | False positives (ignore) |

Configuration in `pyproject.toml`.

## API Configuration

### Google Cloud Console
- Project: (user's project)
- APIs enabled: Google Drive API
- OAuth: Desktop application credentials

### Credential Files
| File | Location | Purpose |
|------|----------|---------|
| credentials.json | Project root | OAuth client config |
| token.json | Project root | User access token |

### Drive Folder Structure
```
MyDrive/
├── .uploader/           # Hidden folder for queue
│   ├── queue.json       # Download requests
│   └── status.json      # Progress updates
├── Downloads/           # Default download folder
├── Videos/
├── Music/
└── ...
```

## Platform Support

| Platform | GUI | CLI |
|----------|-----|-----|
| Windows | ✅ | ✅ |
| macOS | ✅ | ✅ |
| Linux | ✅ | ✅ |

## Known Limitations

1. **Pyrefly false positives**: Google API uses dynamic attributes
2. **Colab timeout**: Free tier may disconnect after ~12 hours
3. **Drive quota**: 15GB free, 2TB with Google One
