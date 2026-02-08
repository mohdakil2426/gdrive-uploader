#!/usr/bin/env python3
"""
Universal Google Drive Uploader - Local Client
Send URLs to Google Colab or upload directly from local machine.

Author: Akila
Version: 2.0.0
"""

import os
import sys
import re
import time
import hashlib
import mimetypes
import argparse
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse, unquote

import requests

# pylint: disable=no-member
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


# ==================== CONFIGURATION ====================
class Config:
    """Global configuration."""
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TOKEN_PATH = os.path.join(SCRIPT_DIR, 'token.json')
    CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, 'credentials.json')
    CHUNK_SIZE = 50 * 1024 * 1024  # 50MB chunks
    MAX_RETRIES = 5
    RETRY_DELAY = 3
    TIMEOUT = 60
    USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36")
    DEFAULT_FOLDER_ID = None  # Set to folder ID for default upload location


# ==================== UTILITY FUNCTIONS ====================
def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    if size_bytes is None or size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_time(seconds):
    """Convert seconds to human-readable format."""
    if seconds is None or seconds < 0:
        return "--:--"
    return str(timedelta(seconds=int(seconds)))


def format_speed(bytes_per_sec):
    """Convert bytes/sec to human-readable format."""
    if bytes_per_sec is None or bytes_per_sec == 0:
        return "0 B/s"
    return format_size(bytes_per_sec) + "/s"


def sanitize_filename(filename):
    """Remove invalid characters from filename."""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip(' .')
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename or "downloaded_file"


def get_filename_from_url(url, response=None):
    """Extract filename from URL or response headers."""
    if response and 'Content-Disposition' in response.headers:
        cd = response.headers['Content-Disposition']
        matches = re.findall(
            r'filename[*]?=["\']?(?:UTF-8\'\')?([^"\';\\n]*)',
            cd, re.IGNORECASE
        )
        if matches:
            return sanitize_filename(unquote(matches[0]))

    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)

    if filename and '.' in filename:
        return sanitize_filename(filename)

    return None


def get_file_hash(filepath, algorithm='md5'):
    """Calculate file hash for integrity verification."""
    hash_func = getattr(hashlib, algorithm)()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def detect_url_type(url):
    """Detect the type of URL for appropriate handling."""
    url_lower = url.lower()

    if url_lower.startswith('magnet:'):
        return 'torrent'
    if url_lower.endswith('.torrent'):
        return 'torrent'
    if 'mega.nz' in url_lower or 'mega.co.nz' in url_lower:
        return 'mega'
    if 'drive.google.com' in url_lower:
        return 'gdrive'

    video_domains = [
        'youtube.com', 'youtu.be', 'twitter.com', 'x.com', 'instagram.com',
        'tiktok.com', 'reddit.com', 'twitch.tv', 'vimeo.com', 'dailymotion.com',
        'facebook.com', 'fb.watch', 'soundcloud.com', 'bandcamp.com',
        'bilibili.com', 'nicovideo.jp'
    ]
    for domain in video_domains:
        if domain in url_lower:
            return 'video'

    return 'direct'


def print_banner():
    """Print application banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           UNIVERSAL GOOGLE DRIVE UPLOADER PRO v2.0               ║
╠══════════════════════════════════════════════════════════════════╣
║  Upload ANY file to Google Drive - Local & URL Support           ║
╚══════════════════════════════════════════════════════════════════╝
""")


# ==================== GOOGLE DRIVE SERVICE ====================
class DriveService:
    """Google Drive API service wrapper."""

    _instance = None
    _service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_service(self):
        """Get or create Drive service."""
        if self._service is not None:
            return self._service

        creds = None

        if os.path.exists(Config.TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(
                Config.TOKEN_PATH, Config.SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                creds.refresh(Request())
                with open(Config.TOKEN_PATH, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
                print("✓ Token refreshed successfully")
            else:
                print("❌ Error: No valid credentials found!")
                print(f"   Expected token at: {Config.TOKEN_PATH}")
                print("   Run the initial auth setup first.")
                sys.exit(1)

        self._service = build('drive', 'v3', credentials=creds)
        return self._service

    def upload_file(self, filepath, folder_id=None, custom_name=None,
                    show_progress=True):
        """
        Upload a local file to Google Drive.

        Args:
            filepath: Path to the file
            folder_id: Destination folder ID (optional)
            custom_name: Custom filename (optional)
            show_progress: Show upload progress

        Returns:
            dict: File metadata from Drive API
        """
        service = self.get_service()
        filepath = Path(filepath).resolve()

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        filename = custom_name or filepath.name
        file_size = filepath.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(filepath))
        mime_type = mime_type or 'application/octet-stream'

        print(f"\n{'='*60}")
        print("⬆️  UPLOADING TO GOOGLE DRIVE")
        print(f"{'='*60}")
        print(f"   📄 File: {filename}")
        print(f"   📊 Size: {format_size(file_size)}")
        print(f"   📁 Type: {mime_type}")
        print(f"{'='*60}\n")

        file_metadata = {'name': filename}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        elif Config.DEFAULT_FOLDER_ID:
            file_metadata['parents'] = [Config.DEFAULT_FOLDER_ID]

        media = MediaFileUpload(
            str(filepath),
            mimetype=mime_type,
            resumable=True,
            chunksize=Config.CHUNK_SIZE
        )

        try:
            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, webViewLink, mimeType'
            )

            response = None
            start_time = time.time()
            last_progress = 0

            while response is None:
                status, response = request.next_chunk()
                if status and show_progress:
                    progress = int(status.progress() * 100)
                    if progress != last_progress:
                        uploaded = status.resumable_progress
                        elapsed = time.time() - start_time
                        speed = uploaded / elapsed if elapsed > 0 else 0
                        print(f"   ⬆️  Progress: {progress}% | "
                              f"{format_size(uploaded)} | "
                              f"{format_speed(speed)}")
                        last_progress = progress

            duration = time.time() - start_time
            avg_speed = file_size / duration if duration > 0 else 0

            print(f"\n{'='*60}")
            print("✅ UPLOAD SUCCESSFUL!")
            print(f"{'='*60}")
            print(f"   📄 Name: {response.get('name')}")
            print(f"   🆔 ID: {response.get('id')}")
            print(f"   📊 Size: {format_size(int(response.get('size', 0)))}")
            print(f"   ⏱️  Time: {format_time(duration)}")
            print(f"   🚀 Speed: {format_speed(avg_speed)}")
            print(f"   🔗 Link: {response.get('webViewLink')}")
            print(f"{'='*60}\n")

            return response

        except HttpError as error:
            print(f"❌ Upload failed: {error}")
            raise

    def download_and_upload(self, url, folder_id=None, filename=None,
                            use_ytdlp=False, video_format='best'):
        """
        Download from URL and upload to Google Drive.

        Args:
            url: Source URL
            folder_id: Destination folder ID
            filename: Custom filename
            use_ytdlp: Use yt-dlp for video sites
            video_format: yt-dlp format string

        Returns:
            dict: File metadata from Drive API
        """
        url_type = detect_url_type(url)

        print(f"\n{'='*60}")
        print("📥 DOWNLOADING FROM URL")
        print(f"{'='*60}")
        print(f"   🔗 URL: {url[:60]}{'...' if len(url) > 60 else ''}")
        print(f"   📋 Type: {url_type.upper()}")
        print(f"{'='*60}\n")

        # Create temp directory
        temp_dir = os.path.join(Config.SCRIPT_DIR, '.temp_downloads')
        os.makedirs(temp_dir, exist_ok=True)

        try:
            if use_ytdlp or url_type == 'video':
                filepath = self._download_ytdlp(url, temp_dir, video_format)
            else:
                filepath = self._download_direct(url, temp_dir, filename)

            if filepath and os.path.exists(filepath):
                result = self.upload_file(
                    filepath,
                    folder_id=folder_id,
                    custom_name=filename
                )

                # Cleanup temp file
                os.remove(filepath)
                return result
            else:
                print("❌ Download failed: No file created")
                return None

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)

    def _download_direct(self, url, save_dir, filename=None):
        """Download file using requests."""
        headers = {'User-Agent': Config.USER_AGENT}

        for attempt in range(Config.MAX_RETRIES):
            try:
                response = requests.get(
                    url, headers=headers, stream=True,
                    allow_redirects=True, timeout=Config.TIMEOUT
                )
                response.raise_for_status()

                if not filename:
                    filename = get_filename_from_url(url, response)
                if not filename:
                    content_type = response.headers.get(
                        'Content-Type', 'application/octet-stream'
                    )
                    ext = mimetypes.guess_extension(
                        content_type.split(';')[0]
                    ) or '.bin'
                    filename = f"download_{int(time.time())}{ext}"

                filename = sanitize_filename(filename)
                filepath = os.path.join(save_dir, filename)

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                start_time = time.time()

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(
                        chunk_size=Config.CHUNK_SIZE
                    ):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                elapsed = time.time() - start_time
                                speed = downloaded / elapsed if elapsed > 0 else 0
                                progress = (downloaded / total_size) * 100
                                print(
                                    f"\r   📥 Downloading: {progress:.1f}% | "
                                    f"{format_size(downloaded)} / "
                                    f"{format_size(total_size)} | "
                                    f"{format_speed(speed)}",
                                    end=""
                                )

                print()  # New line after progress
                return filepath

            except Exception as e:
                if attempt < Config.MAX_RETRIES - 1:
                    print(f"   ⚠️ Attempt {attempt+1} failed. Retrying...")
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))
                else:
                    raise

    def _download_ytdlp(self, url, save_dir, format_spec='best'):
        """Download using yt-dlp."""
        try:
            import yt_dlp
        except ImportError:
            print("❌ yt-dlp not installed. Install with: pip install yt-dlp")
            raise

        outtmpl = os.path.join(save_dir, '%(title)s.%(ext)s')

        ydl_opts = {
            'format': format_spec,
            'outtmpl': outtmpl,
            'quiet': False,
            'no_warnings': True,
            'retries': Config.MAX_RETRIES,
            'fragment_retries': Config.MAX_RETRIES,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                if 'requested_downloads' in info:
                    return info['requested_downloads'][0]['filepath']
                return ydl.prepare_filename(info)

        return None

    def list_folders(self, parent_id=None):
        """List folders in Drive."""
        service = self.get_service()

        if parent_id:
            query = (f"mimeType='application/vnd.google-apps.folder' "
                     f"and '{parent_id}' in parents and trashed=false")
        else:
            query = ("mimeType='application/vnd.google-apps.folder' "
                     "and 'root' in parents and trashed=false")

        try:
            results = service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name)",
                orderBy="name"
            ).execute()

            folders = results.get('files', [])

            print(f"\n{'='*60}")
            print("📂 GOOGLE DRIVE FOLDERS")
            print(f"{'='*60}")

            if not folders:
                print("   No folders found.")
            else:
                for folder in folders:
                    print(f"   📁 {folder['name']}")
                    print(f"      ID: {folder['id']}")
                    print()

            print(f"{'='*60}")
            print("💡 Use folder ID with: --folder <ID>")
            print(f"{'='*60}\n")

            return folders

        except HttpError as error:
            print(f"❌ Error: {error}")
            raise

    def create_folder(self, folder_name, parent_id=None):
        """Create a new folder."""
        service = self.get_service()

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        try:
            folder = service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()

            print("\n✅ Folder created!")
            print(f"   📁 Name: {folder.get('name')}")
            print(f"   🆔 ID: {folder.get('id')}")
            print(f"   🔗 Link: {folder.get('webViewLink')}\n")

            return folder

        except HttpError as error:
            print(f"❌ Error: {error}")
            raise

    def check_quota(self):
        """Check Drive storage quota."""
        service = self.get_service()

        try:
            about = service.about().get(
                fields="storageQuota, user"
            ).execute()

            quota = about.get('storageQuota', {})
            user = about.get('user', {})

            used = int(quota.get('usage', 0))
            total = int(quota.get('limit', 0))

            print(f"\n{'='*60}")
            print(f"👤 Account: {user.get('emailAddress', 'Unknown')}")
            print(f"{'='*60}")
            print(f"   📊 Used: {format_size(used)}")
            if total > 0:
                print(f"   📊 Total: {format_size(total)}")
                print(f"   📊 Free: {format_size(total - used)}")
                print(f"   📊 Usage: {(used/total)*100:.1f}%")
            print(f"{'='*60}\n")

            return about

        except HttpError as error:
            print(f"❌ Error: {error}")
            raise

    def batch_upload(self, items, folder_id=None):
        """
        Upload multiple files/URLs.

        Args:
            items: List of file paths or URLs
            folder_id: Destination folder ID

        Returns:
            list: Results for each item
        """
        results = []

        print(f"\n{'='*60}")
        print(f"📦 BATCH UPLOAD: {len(items)} items")
        print(f"{'='*60}\n")

        for i, item in enumerate(items, 1):
            print(f"\n[{i}/{len(items)}] Processing: {item[:50]}...")

            try:
                if os.path.exists(item):
                    # It's a local file
                    result = self.upload_file(item, folder_id=folder_id)
                else:
                    # It's a URL
                    result = self.download_and_upload(item, folder_id=folder_id)

                results.append({'item': item, 'success': True, 'result': result})

            except Exception as e:
                print(f"❌ Failed: {e}")
                results.append({'item': item, 'success': False, 'error': str(e)})

        # Summary
        success = sum(1 for r in results if r['success'])
        print(f"\n{'='*60}")
        print("📊 BATCH UPLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"   ✅ Successful: {success}/{len(items)}")
        print(f"   ❌ Failed: {len(items) - success}/{len(items)}")
        print(f"{'='*60}\n")

        return results


# ==================== CLI INTERFACE ====================
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Universal Google Drive Uploader Pro',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Upload a local file
  python uploader_pro.py /path/to/file.zip

  # Upload from URL
  python uploader_pro.py "https://example.com/file.zip"

  # Upload YouTube video
  python uploader_pro.py "https://youtube.com/watch?v=xxx" --ytdlp

  # Upload to specific folder
  python uploader_pro.py file.zip --folder FOLDER_ID

  # Batch upload
  python uploader_pro.py file1.zip file2.pdf "https://example.com/file3.zip"

  # List folders
  python uploader_pro.py --list-folders

  # Check quota
  python uploader_pro.py --quota
        """
    )

    parser.add_argument(
        'items', nargs='*',
        help='Files or URLs to upload'
    )
    parser.add_argument(
        '--folder', '-f',
        help='Destination folder ID'
    )
    parser.add_argument(
        '--name', '-n',
        help='Custom filename for single file upload'
    )
    parser.add_argument(
        '--ytdlp', '-y', action='store_true',
        help='Use yt-dlp for video downloads'
    )
    parser.add_argument(
        '--format',
        default='best',
        help='Video format for yt-dlp (default: best)'
    )
    parser.add_argument(
        '--list-folders', '-l', action='store_true',
        help='List Drive folders'
    )
    parser.add_argument(
        '--create-folder', '-c',
        help='Create a new folder'
    )
    parser.add_argument(
        '--quota', '-q', action='store_true',
        help='Check storage quota'
    )
    parser.add_argument(
        '--hash',
        help='Verify file hash after upload (provide expected hash)'
    )
    parser.add_argument(
        '--hash-type',
        default='md5',
        choices=['md5', 'sha1', 'sha256'],
        help='Hash algorithm (default: md5)'
    )

    args = parser.parse_args()

    # Show banner
    print_banner()

    # Create service
    drive = DriveService()

    # Handle commands
    if args.list_folders:
        drive.list_folders(args.folder)
        return

    if args.create_folder:
        drive.create_folder(args.create_folder, args.folder)
        return

    if args.quota:
        drive.check_quota()
        return

    if not args.items:
        parser.print_help()
        return

    # Process items
    if len(args.items) == 1:
        item = args.items[0]

        if os.path.exists(item):
            # Local file
            result = drive.upload_file(
                item,
                folder_id=args.folder,
                custom_name=args.name
            )
        else:
            # URL
            result = drive.download_and_upload(
                item,
                folder_id=args.folder,
                filename=args.name,
                use_ytdlp=args.ytdlp,
                video_format=args.format
            )

        # Verify hash if requested
        if args.hash and result and os.path.exists(item):
            print(f"🔍 Verifying {args.hash_type.upper()} hash...")
            file_hash = get_file_hash(item, args.hash_type)
            if file_hash.lower() == args.hash.lower():
                print("   ✅ Hash matches! File integrity verified.")
            else:
                print("   ❌ Hash mismatch!")
                print(f"   Expected: {args.hash}")
                print(f"   Got: {file_hash}")

    else:
        # Batch upload
        drive.batch_upload(args.items, folder_id=args.folder)


if __name__ == '__main__':
    main()
