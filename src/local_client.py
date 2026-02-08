#!/usr/bin/env python3
"""
Universal Uploader - Local Client
Send URLs to Google Colab server for processing.

Usage:
    python local_client.py "https://example.com/file.zip"
    python local_client.py "https://youtube.com/watch?v=xxx" --ytdlp
    python local_client.py --status
    python local_client.py --list

Author: Akila
Version: 2.0.0
"""

import io
import os
import sys
import json
import uuid
import argparse
from datetime import datetime

# pylint: disable=no-member
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


# ==================== CONFIGURATION ====================
class Config:
    """Configuration settings."""
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Go up one level from src/ to find credentials
    PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
    TOKEN_PATH = os.path.join(PROJECT_DIR, 'token.json')
    CREDENTIALS_PATH = os.path.join(PROJECT_DIR, 'credentials.json')

    # Queue settings
    QUEUE_FOLDER_NAME = "UploaderQueue"
    QUEUE_FILE_NAME = "queue.json"
    DEFAULT_OUTPUT_FOLDER = "Downloads"


# ==================== GOOGLE DRIVE SERVICE ====================
class DriveService:
    """Google Drive API wrapper."""

    _instance = None
    _service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_service(self):
        """Get authenticated Drive service."""
        if self._service is not None:
            return self._service

        creds = None

        if os.path.exists(Config.TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(
                Config.TOKEN_PATH, Config.SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing token...")
                creds.refresh(Request())
                with open(Config.TOKEN_PATH, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
            else:
                print("❌ No valid credentials found!")
                print(f"   Token path: {Config.TOKEN_PATH}")
                sys.exit(1)

        self._service = build('drive', 'v3', credentials=creds)
        return self._service

    def find_queue_folder(self):
        """Find or create the queue folder."""
        service = self.get_service()

        # Search for existing folder
        query = (f"name='{Config.QUEUE_FOLDER_NAME}' and "
                 f"mimeType='application/vnd.google-apps.folder' and "
                 f"trashed=false")

        results = service.files().list(
            q=query, fields="files(id, name)"
        ).execute()

        files = results.get('files', [])

        if files:
            return files[0]['id']

        # Create folder
        folder_metadata = {
            'name': Config.QUEUE_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        folder = service.files().create(
            body=folder_metadata, fields='id'
        ).execute()

        print(f"📁 Created queue folder: {Config.QUEUE_FOLDER_NAME}")
        return folder['id']

    def find_queue_file(self, folder_id):
        """Find the queue file."""
        service = self.get_service()

        query = (f"name='{Config.QUEUE_FILE_NAME}' and "
                 f"'{folder_id}' in parents and trashed=false")

        results = service.files().list(
            q=query, fields="files(id, name)"
        ).execute()

        files = results.get('files', [])
        return files[0]['id'] if files else None

    def read_queue(self):
        """Read the queue from Drive."""
        service = self.get_service()
        folder_id = self.find_queue_folder()
        file_id = self.find_queue_file(folder_id)

        if not file_id:
            return {'items': [], 'processed': []}

        try:
            request = service.files().get_media(fileId=file_id)
            content = io.BytesIO()
            downloader = MediaIoBaseDownload(content, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            content.seek(0)
            return json.loads(content.read().decode('utf-8'))
        except Exception:
            return {'items': [], 'processed': []}

    def write_queue(self, queue_data):
        """Write the queue to Drive."""
        service = self.get_service()
        folder_id = self.find_queue_folder()
        file_id = self.find_queue_file(folder_id)

        content = json.dumps(queue_data, indent=2).encode('utf-8')

        # Create a temporary file
        temp_path = os.path.join(Config.SCRIPT_DIR, '.temp_queue.json')
        with open(temp_path, 'wb') as f:
            f.write(content)

        try:
            media = MediaFileUpload(temp_path, mimetype='application/json')

            if file_id:
                # Update existing
                service.files().update(
                    fileId=file_id, media_body=media
                ).execute()
            else:
                # Create new
                file_metadata = {
                    'name': Config.QUEUE_FILE_NAME,
                    'parents': [folder_id]
                }
                service.files().create(
                    body=file_metadata, media_body=media
                ).execute()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def add_to_queue(self, url, filename=None, folder=None, method='auto',
                     video_format='best'):
        """Add a URL to the queue."""
        queue = self.read_queue()

        item = {
            'id': str(uuid.uuid4())[:8],
            'url': url,
            'filename': filename,
            'folder': folder or Config.DEFAULT_OUTPUT_FOLDER,
            'method': method,
            'format': video_format,
            'status': 'pending',
            'added_at': datetime.now().isoformat()
        }

        queue['items'].append(item)
        self.write_queue(queue)

        return item


# ==================== CLI INTERFACE ====================
def print_banner():
    """Print banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           UNIVERSAL UPLOADER - LOCAL CLIENT                  ║
╠══════════════════════════════════════════════════════════════╣
║  Send URLs to Colab server for processing                    ║
╚══════════════════════════════════════════════════════════════╝
""")


def cmd_add(args):
    """Add URL(s) to queue."""
    drive = DriveService()

    for url in args.urls:
        print(f"📤 Adding to queue: {url[:50]}...")

        item = drive.add_to_queue(
            url=url,
            filename=args.name,
            folder=args.folder,
            method='video' if args.ytdlp else 'auto',
            video_format=args.format
        )

        print(f"   ✅ Added! ID: {item['id']}")

    print("\n💡 Make sure Colab server is running to process the queue.")


def cmd_status(_args):
    """Show queue status."""
    drive = DriveService()
    queue = drive.read_queue()
    items = queue.get('items', [])

    print("📋 QUEUE STATUS")
    print("=" * 60)

    if not items:
        print("   Queue is empty.")
    else:
        # Show recent items
        for item in items[-10:]:
            status_icon = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(item.get('status'), '❓')

            url = item.get('url', '')[:45]
            print(f"   {status_icon} [{item.get('id')}] {url}...")

            result = item.get('result', {})
            if result.get('filename'):
                print(f"      → {result['filename']}")
            elif result.get('error'):
                print(f"      ✗ {result['error'][:50]}")

    print("=" * 60)

    pending = len([i for i in items if i.get('status') == 'pending'])
    processing = len([i for i in items if i.get('status') == 'processing'])
    completed = len([i for i in items if i.get('status') == 'completed'])
    failed = len([i for i in items if i.get('status') == 'failed'])

    print(f"   ⏳ Pending: {pending}")
    print(f"   🔄 Processing: {processing}")
    print(f"   ✅ Completed: {completed}")
    print(f"   ❌ Failed: {failed}")
    print("=" * 60)


def cmd_clear(args):
    """Clear the queue."""
    if not args.confirm:
        print("⚠️  Use --confirm to clear the queue")
        return

    drive = DriveService()
    drive.write_queue({'items': [], 'processed': []})
    print("✅ Queue cleared!")


def cmd_list(_args):
    """List completed downloads."""
    drive = DriveService()
    queue = drive.read_queue()
    items = queue.get('items', [])

    completed = [i for i in items if i.get('status') == 'completed']

    print("📂 COMPLETED DOWNLOADS")
    print("=" * 60)

    if not completed:
        print("   No completed downloads.")
    else:
        for item in completed[-20:]:
            result = item.get('result', {})
            filename = result.get('filename', 'Unknown')
            size = result.get('size', 0)

            # Format size
            if size:
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        size_str = f"{size:.1f} {unit}"
                        break
                    size /= 1024
                else:
                    size_str = f"{size:.1f} TB"
            else:
                size_str = "Unknown"

            print(f"   ✅ {filename} ({size_str})")

    print("=" * 60)
    print(f"   Total: {len(completed)} files")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Universal Uploader - Local Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Add URL to queue
  python local_client.py "https://example.com/file.zip"

  # Add YouTube video
  python local_client.py "https://youtube.com/watch?v=xxx" --ytdlp

  # Add multiple URLs
  python local_client.py "url1" "url2" "url3"

  # Add with custom settings
  python local_client.py "url" --folder "MyFolder" --name "custom.zip"

  # Check queue status
  python local_client.py --status

  # List completed downloads
  python local_client.py --list

  # Clear queue
  python local_client.py --clear --confirm
        """
    )

    parser.add_argument(
        'urls', nargs='*',
        help='URL(s) to add to queue'
    )
    parser.add_argument(
        '--folder', '-f',
        default=Config.DEFAULT_OUTPUT_FOLDER,
        help='Destination folder in Drive (default: Downloads)'
    )
    parser.add_argument(
        '--name', '-n',
        help='Custom filename'
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
        '--status', '-s', action='store_true',
        help='Show queue status'
    )
    parser.add_argument(
        '--list', '-l', action='store_true',
        help='List completed downloads'
    )
    parser.add_argument(
        '--clear', action='store_true',
        help='Clear the queue'
    )
    parser.add_argument(
        '--confirm', action='store_true',
        help='Confirm destructive operations'
    )

    args = parser.parse_args()

    print_banner()

    # Handle commands
    if args.status:
        cmd_status(args)
    elif args.list:
        cmd_list(args)
    elif args.clear:
        cmd_clear(args)
    elif args.urls:
        cmd_add(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
