# Universal Google Drive Uploader

**Upload any file from any URL directly to Google Drive - Zero local bandwidth required.**

## Features

- **Any File Type** - Documents, videos, archives, images, executables, anything
- **1500+ Video Sites** - YouTube, Twitter, Instagram, TikTok, Reddit, and more
- **Zero Local Transfer** - All downloads happen on Google's servers (Colab)
- **Multiple Methods** - Direct, Aria2 (accelerated), yt-dlp, Mega.nz, torrents
- **Batch Processing** - Upload multiple files/URLs at once
- **Progress Tracking** - Real-time speed, ETA, percentage
- **Auto-Retry** - Resilient downloads with exponential backoff
- **Hash Verification** - MD5, SHA1, SHA256 integrity checks

## Quick Start

### Option 1: Google Colab (Recommended - Zero Local Resources)

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Upload `notebooks/Universal_Uploader_Pro.ipynb`
3. Run **Cell 1** (Setup) and **Cell 2** (Initialize)
4. Paste your URL and run!

### Option 2: Local/VM Script

```bash
# Install dependencies
pip install -r requirements.txt

# Upload local file
python src/uploader_pro.py /path/to/file.zip

# Upload from URL
python src/uploader_pro.py "https://example.com/file.zip"

# Upload YouTube video
python src/uploader_pro.py "https://youtube.com/watch?v=xxx" --ytdlp

# Batch upload
python src/uploader_pro.py file1.zip file2.pdf "https://example.com/file3.zip"

# List folders
python src/uploader_pro.py --list-folders

# Check storage
python src/uploader_pro.py --quota
```

## Project Structure

```
GdriveUploader/
├── src/                          # Source code
│   ├── uploader_pro.py           # Advanced CLI uploader
│   └── gdrive_uploader.py        # Basic CLI uploader
├── notebooks/                    # Jupyter/Colab notebooks
│   ├── Universal_Uploader_Pro.ipynb   # Full-featured Colab notebook
│   └── Universal_GDrive_Uploader.ipynb # Basic Colab notebook
├── docs/                         # Documentation
│   ├── SETUP_GUIDE.md            # Initial auth setup
│   └── Universal_Web_To_Drive_Plan.md # Project planning
├── memory-bank/                  # Project memory (for AI assistants)
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   ├── activeContext.md
│   └── progress.md
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── credentials.json              # OAuth config (DO NOT COMMIT)
└── token.json                    # Auth token (DO NOT COMMIT)
```

## Supported URL Types

| Type | Examples | Auto-Detected |
|------|----------|---------------|
| Direct Links | `.zip`, `.pdf`, `.exe`, any file | ✅ |
| YouTube | `youtube.com`, `youtu.be` | ✅ |
| Twitter/X | `twitter.com`, `x.com` | ✅ |
| Instagram | `instagram.com` | ✅ |
| TikTok | `tiktok.com` | ✅ |
| Reddit | `reddit.com` | ✅ |
| Twitch | `twitch.tv` | ✅ |
| Vimeo | `vimeo.com` | ✅ |
| Facebook | `facebook.com`, `fb.watch` | ✅ |
| SoundCloud | `soundcloud.com` | ✅ |
| Mega.nz | `mega.nz` | ✅ |
| Google Drive | `drive.google.com` | ✅ |
| Torrent | `.torrent`, `magnet:` | ✅ |
| 1500+ more | See [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) | ✅ |

## Initial Setup

If you don't have `credentials.json` and `token.json`, follow the setup guide:

1. Create a Google Cloud Project
2. Enable Google Drive API
3. Create OAuth credentials
4. Generate your token

See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed instructions.

## CLI Reference

```
usage: uploader_pro.py [-h] [--folder FOLDER] [--name NAME] [--ytdlp]
                       [--format FORMAT] [--list-folders] [--create-folder NAME]
                       [--quota] [--hash HASH] [--hash-type {md5,sha1,sha256}]
                       [items ...]

Universal Google Drive Uploader Pro

positional arguments:
  items                 Files or URLs to upload

options:
  -h, --help            show this help message and exit
  --folder, -f FOLDER   Destination folder ID
  --name, -n NAME       Custom filename
  --ytdlp, -y           Use yt-dlp for video downloads
  --format FORMAT       Video format for yt-dlp (default: best)
  --list-folders, -l    List Drive folders
  --create-folder, -c   Create a new folder
  --quota, -q           Check storage quota
  --hash HASH           Verify file hash after upload
  --hash-type TYPE      Hash algorithm: md5, sha1, sha256
```

## Requirements

- Python 3.8+
- Google account with Drive access
- For video sites: yt-dlp

## License

MIT License - Use freely for personal and commercial projects.

## Security Notice

**Never commit `credentials.json` or `token.json` to version control!**

These files contain sensitive OAuth tokens that grant access to your Google Drive.
