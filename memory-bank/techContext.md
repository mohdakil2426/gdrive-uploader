# Tech Context: Universal Google Drive Uploader

## Technology Stack

### Primary Platform: Google Colab
- Python 3.10+
- Pre-installed: requests, google-auth
- Native Drive mounting via `google.colab.drive`

### Secondary Platform: Google Cloud VM (Ubuntu)
- Python 3.8+
- OAuth2 authentication via token.json

## Dependencies

### Colab (Pre-installed)
```
google-colab (native)
requests
google-auth
google-api-python-client
```

### VM/Local (requirements.txt)
```
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-api-python-client>=2.0.0
yt-dlp>=2024.0.0
requests>=2.28.0
```

## API & Authentication

### Google Drive API v3
- Scopes: `https://www.googleapis.com/auth/drive`
- Endpoints used:
  - `files.create` - Upload files
  - `files.list` - List folders
  - `about.get` - Check quota

### Authentication Methods
1. **Colab**: `drive.mount('/content/drive')` - Browser OAuth popup
2. **VM**: `Credentials.from_authorized_user_file('token.json')` - Pre-authorized

### Credential Files
- `credentials.json` - OAuth client config (from Google Cloud Console)
- `token.json` - User's access + refresh token (auto-generated)

## Development Setup

### Local Development
```bash
cd GdriveUploader
pip install -r requirements.txt
python gdrive_uploader.py --help
```

### Colab Development
1. Open `Universal_GDrive_Uploader.ipynb` in Colab
2. Run cells in order
3. Authenticate when prompted

## Technical Constraints

### Google Colab Limits
- Session timeout: ~12 hours (free), 24 hours (Pro)
- RAM: 12GB (free), 25GB (Pro)
- Disk: 100GB temporary

### Google Drive API Limits
- Upload: 750GB/day per user
- API calls: 1,000,000,000/day (effectively unlimited)
- File size: 5TB max

### yt-dlp Considerations
- Some sites have IP-bound URLs (must download from same IP that extracted)
- Rate limiting on some platforms
- Regular updates needed for site compatibility

## Tool Usage Patterns

### yt-dlp Integration
```python
import yt_dlp
ydl_opts = {'format': 'best', 'quiet': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    direct_url = info['url']
```

### Streaming Upload
```python
response = requests.get(url, stream=True)
for chunk in response.iter_content(chunk_size=8*1024*1024):
    file.write(chunk)
```
