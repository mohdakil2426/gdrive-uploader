#!/usr/bin/env python3
"""
Google Drive Upload Queue Manager
A simple CLI tool to manage download queues stored in Google Drive
"""

import argparse
import io
import json
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
except ImportError:
    print("Error: Google API libraries not found.")
    print("Install with: pip install google-auth google-auth-oauthlib "
          "google-auth-httplib2 google-api-python-client")
    sys.exit(1)

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    # Fallback to simple ANSI colors
    class Fore:  # pylint: disable=too-few-public-methods
        """ANSI color codes for terminal output."""
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        RESET = '\033[0m'

    class Style:  # pylint: disable=too-few-public-methods
        """ANSI style codes for terminal output."""
        BRIGHT = '\033[1m'
        RESET_ALL = '\033[0m'


# Google Drive API configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
UPLOADER_FOLDER = '.uploader'
QUEUE_FILE = 'queue.json'
STATUS_FILE = 'status.json'


class GoogleDriveManager:
    """Handles Google Drive API operations."""

    def __init__(self):
        self.service = None
        self.uploader_folder_id = None

    def authenticate(self) -> bool:
        """Authenticate with Google Drive API."""
        creds = None

        # Try to load token from Drive or local
        token_locations = [
            'token.json',
            Path.home() / 'token.json'
        ]

        for token_path in token_locations:
            if Path(token_path).exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
                break

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Look for credentials.json
                creds_locations = [
                    'credentials.json',
                    Path.home() / 'credentials.json'
                ]

                creds_file = None
                for creds_path in creds_locations:
                    if Path(creds_path).exists():
                        creds_file = str(creds_path)
                        break

                if not creds_file:
                    print(f"{Fore.RED}Error: credentials.json not found!{Style.RESET_ALL}")
                    print(f"\n{Fore.YELLOW}Setup Instructions:{Style.RESET_ALL}")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a new project or select existing")
                    print("3. Enable Google Drive API")
                    print("4. Create OAuth 2.0 credentials (Desktop app)")
                    print("5. Download credentials.json to this directory")
                    print(f"   or to {Path.home()}/credentials.json")
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as err:  # pylint: disable=broad-except
                    print(f"{Fore.RED}Authentication failed: {err}{Style.RESET_ALL}")
                    return False

            # Save the credentials
            with open('token.json', 'w', encoding='utf-8') as token:
                token.write(creds.to_json())

        try:
            self.service = build('drive', 'v3', credentials=creds)
            return True
        except Exception as err:  # pylint: disable=broad-except
            print(f"{Fore.RED}Failed to build Drive service: {err}{Style.RESET_ALL}")
            return False

    def _get_or_create_uploader_folder(self) -> Optional[str]:
        """Get or create .uploader folder in Drive."""
        if self.uploader_folder_id:
            return self.uploader_folder_id

        try:
            # Search for existing folder
            query = (
                f"name='{UPLOADER_FOLDER}' and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"trashed=false"
            )
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])

            if files:
                self.uploader_folder_id = files[0]['id']
            else:
                # Create folder
                file_metadata = {
                    'name': UPLOADER_FOLDER,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                self.uploader_folder_id = folder.get('id')

            return self.uploader_folder_id
        except HttpError as err:
            print(f"{Fore.RED}Error accessing Drive folder: {err}{Style.RESET_ALL}")
            return None

    def read_json_file(self, filename: str) -> Optional[dict]:
        """Read JSON file from Drive."""
        folder_id = self._get_or_create_uploader_folder()
        if not folder_id:
            return None

        try:
            # Search for file
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])

            if not files:
                return None

            file_id = files[0]['id']

            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            fh.seek(0)
            return json.loads(fh.read().decode('utf-8'))

        except HttpError as err:
            if err.resp.status == 404:
                return None
            print(f"{Fore.RED}Error reading file: {err}{Style.RESET_ALL}")
            return None
        except Exception as err:  # pylint: disable=broad-except
            print(f"{Fore.RED}Error parsing JSON: {err}{Style.RESET_ALL}")
            return None

    def write_json_file(self, filename: str, data: dict) -> bool:
        """Write JSON file to Drive."""
        folder_id = self._get_or_create_uploader_folder()
        if not folder_id:
            return False

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            ) as tmp:
                json.dump(data, tmp, indent=2)
                tmp_path = tmp.name

            # Search for existing file
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])

            media = MediaFileUpload(tmp_path, mimetype='application/json')

            if files:
                # Update existing file
                file_id = files[0]['id']
                self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
            else:
                # Create new file
                file_metadata = {
                    'name': filename,
                    'parents': [folder_id]
                }
                self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            # Clean up temp file
            Path(tmp_path).unlink()
            return True

        except HttpError as err:
            print(f"{Fore.RED}Error writing file: {err}{Style.RESET_ALL}")
            return False


class QueueManager:
    """Manages download queue operations."""

    def __init__(self, drive_manager: GoogleDriveManager):
        self.drive = drive_manager

    def _get_queue(self) -> dict:
        """Get current queue from Drive."""
        queue = self.drive.read_json_file(QUEUE_FILE)
        if queue is None:
            queue = {"downloads": []}
        return queue

    def _save_queue(self, queue: dict) -> bool:
        """Save queue to Drive."""
        return self.drive.write_json_file(QUEUE_FILE, queue)

    def add_download(self, url: str, folder: str = "Downloads") -> bool:
        """Add a new download to the queue."""
        queue = self._get_queue()

        download = {
            "id": str(uuid.uuid4()),
            "url": url,
            "folder": folder,
            "status": "pending",
            "added_at": datetime.now().isoformat()
        }

        queue["downloads"].append(download)

        if self._save_queue(queue):
            print(f"{Fore.GREEN}✓ Added to queue:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}ID:{Style.RESET_ALL} {download['id']}")
            print(f"  {Fore.CYAN}URL:{Style.RESET_ALL} {url}")
            print(f"  {Fore.CYAN}Folder:{Style.RESET_ALL} {folder}")
            return True

        print(f"{Fore.RED}✗ Failed to add download to queue{Style.RESET_ALL}")
        return False

    def show_status(self):
        """Display current queue status."""
        queue = self._get_queue()
        status = self.drive.read_json_file(STATUS_FILE) or {}

        downloads = queue.get("downloads", [])

        if not downloads:
            print(f"{Fore.YELLOW}Queue is empty{Style.RESET_ALL}")
            return

        print(f"\n{Style.BRIGHT}{Fore.BLUE}=== Download Queue ==={Style.RESET_ALL}\n")

        # Group by status
        pending = [d for d in downloads if d.get("status") == "pending"]
        in_progress = [d for d in downloads if d.get("status") == "in_progress"]
        completed = [d for d in downloads if d.get("status") == "completed"]
        failed = [d for d in downloads if d.get("status") == "failed"]

        def print_download(download: dict, index: int):
            status_icon = {
                "pending": f"{Fore.YELLOW}⏳",
                "in_progress": f"{Fore.BLUE}⬇",
                "completed": f"{Fore.GREEN}✓",
                "failed": f"{Fore.RED}✗"
            }.get(download.get("status", "pending"), "•")

            url_display = download['url']
            if len(url_display) > 60:
                url_display = url_display[:60] + '...'

            print(f"{status_icon} {Style.BRIGHT}[{index + 1}]{Style.RESET_ALL} {url_display}")
            print(f"    {Fore.CYAN}Folder:{Style.RESET_ALL} {download.get('folder', 'Downloads')}")
            print(f"    {Fore.CYAN}ID:{Style.RESET_ALL} {download['id']}")
            print(f"    {Fore.CYAN}Added:{Style.RESET_ALL} {download.get('added_at', 'Unknown')}")

            if download.get("status") == "in_progress":
                progress = status.get("current_download", {})
                if progress.get("id") == download["id"]:
                    pct = progress.get('progress', 0)
                    print(f"    {Fore.CYAN}Progress:{Style.RESET_ALL} {pct}%")

            print()

        if in_progress:
            print(f"{Style.BRIGHT}In Progress:{Style.RESET_ALL}")
            for i, download in enumerate(in_progress):
                print_download(download, i)

        if pending:
            print(f"{Style.BRIGHT}Pending ({len(pending)}):{Style.RESET_ALL}")
            for i, download in enumerate(pending):
                print_download(download, i)

        if completed:
            print(f"{Style.BRIGHT}Completed ({len(completed)}):{Style.RESET_ALL}")
            for i, download in enumerate(completed[:5]):  # Show last 5
                print_download(download, i)
            if len(completed) > 5:
                print(f"    ... and {len(completed) - 5} more")
                print()

        if failed:
            print(f"{Style.BRIGHT}Failed ({len(failed)}):{Style.RESET_ALL}")
            for i, download in enumerate(failed):
                print_download(download, i)

        print(f"{Style.BRIGHT}Total:{Style.RESET_ALL} {len(downloads)} downloads")

    def clear_completed(self) -> bool:
        """Remove completed downloads from queue."""
        queue = self._get_queue()
        downloads = queue.get("downloads", [])

        completed = [d for d in downloads if d.get("status") == "completed"]
        remaining = [d for d in downloads if d.get("status") != "completed"]

        if not completed:
            print(f"{Fore.YELLOW}No completed downloads to clear{Style.RESET_ALL}")
            return True

        queue["downloads"] = remaining

        if self._save_queue(queue):
            print(f"{Fore.GREEN}✓ Cleared {len(completed)} completed download(s){Style.RESET_ALL}")
            return True

        print(f"{Fore.RED}✗ Failed to clear completed downloads{Style.RESET_ALL}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Google Drive Upload Queue Manager',
        epilog='Examples:\n'
               '  python uploader.py "https://example.com/file.zip"\n'
               '  python uploader.py "https://youtube.com/watch?v=xxx" --folder "Videos"\n'
               '  python uploader.py --status\n'
               '  python uploader.py --clear',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='URL to add to download queue'
    )

    parser.add_argument(
        '--folder',
        default='Downloads',
        help='Target folder for download (default: Downloads)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current queue status'
    )

    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear completed downloads from queue'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.url and not args.status and not args.clear:
        parser.print_help()
        sys.exit(1)

    # Initialize Drive manager
    print(f"{Fore.CYAN}Connecting to Google Drive...{Style.RESET_ALL}")
    drive = GoogleDriveManager()

    if not drive.authenticate():
        sys.exit(1)

    print(f"{Fore.GREEN}✓ Connected to Google Drive{Style.RESET_ALL}\n")

    # Initialize queue manager
    queue_manager = QueueManager(drive)

    # Execute command
    if args.status:
        queue_manager.show_status()
    elif args.clear:
        queue_manager.clear_completed()
    elif args.url:
        queue_manager.add_download(args.url, args.folder)

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:  # pylint: disable=broad-except
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)
