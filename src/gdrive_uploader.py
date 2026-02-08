#!/usr/bin/env python3
"""
Universal Google Drive Uploader
Upload any file type directly to Google Drive from Ubuntu VM
Author: Akila
"""

import os
import sys
import mimetypes
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
# pylint: disable=no-member
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# ============== CONFIGURATION ==============
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')

# Optional: Set a default folder ID to upload to (leave None for root)
DEFAULT_FOLDER_ID = None


def get_drive_service():
    """Authenticate and return Google Drive service."""
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Validate and refresh if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
            # Save the refreshed token
            with open(TOKEN_PATH, 'w', encoding='utf-8') as token:
                token.write(creds.to_json())
            print("✓ Token refreshed successfully")
        else:
            print("❌ Error: No valid credentials found!")
            print("   Make sure token.json exists in the script directory.")
            print(f"   Expected path: {TOKEN_PATH}")
            sys.exit(1)

    return build('drive', 'v3', credentials=creds)


def get_mime_type(file_path):
    """Detect MIME type of file."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'


def format_size(size_bytes):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def upload_file(file_path, folder_id=None, custom_name=None):
    """
    Upload any file to Google Drive with progress tracking.

    Args:
        file_path: Path to the file to upload
        folder_id: Google Drive folder ID (optional, uses root if None)
        custom_name: Custom name for the file in Drive (optional)

    Returns:
        dict: File metadata from Google Drive
    """
    service = get_drive_service()

    # Validate file exists
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)

    if not file_path.is_file():
        print(f"❌ Error: Not a file: {file_path}")
        sys.exit(1)

    # File details
    file_name = custom_name or file_path.name
    file_size = file_path.stat().st_size
    mime_type = get_mime_type(file_path)

    print(f"\n{'='*50}")
    print(f"📁 File: {file_name}")
    print(f"📊 Size: {format_size(file_size)}")
    print(f"📄 Type: {mime_type}")
    print(f"{'='*50}\n")

    # Prepare metadata
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    elif DEFAULT_FOLDER_ID:
        file_metadata['parents'] = [DEFAULT_FOLDER_ID]

    # Create resumable upload (handles large files)
    media = MediaFileUpload(
        str(file_path),
        mimetype=mime_type,
        resumable=True,
        chunksize=50 * 1024 * 1024  # 50MB chunks for fast upload
    )

    try:
        # Start upload
        request = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size, webViewLink, mimeType'
        )

        response = None
        print("⬆️  Uploading...")

        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                uploaded = format_size(status.resumable_progress)
                print(f"   Progress: {progress}% ({uploaded})")

        # Success
        print(f"\n{'='*50}")
        print("✅ UPLOAD SUCCESSFUL!")
        print(f"{'='*50}")
        print(f"📄 Name: {response.get('name')}")
        print(f"🆔 ID: {response.get('id')}")
        print(f"📊 Size: {format_size(int(response.get('size', 0)))}")
        print(f"🔗 Link: {response.get('webViewLink')}")
        print(f"{'='*50}\n")

        return response

    except HttpError as error:
        print(f"❌ Upload failed: {error}")
        sys.exit(1)


def list_folders(parent_id=None):
    """List folders in Drive."""
    service = get_drive_service()

    if parent_id:
        query = (f"mimeType='application/vnd.google-apps.folder' "
                 f"and '{parent_id}' in parents and trashed=false")
    else:
        query = ("mimeType='application/vnd.google-apps.folder' "
                 "and 'root' in parents and trashed=false")

    try:
        results = service.files().list(
            q=query,
            pageSize=50,
            fields="files(id, name)",
            orderBy="name"
        ).execute()

        folders = results.get('files', [])

        print(f"\n{'='*50}")
        print("📂 YOUR GOOGLE DRIVE FOLDERS")
        print(f"{'='*50}")

        if not folders:
            print("   No folders found.")
        else:
            for folder in folders:
                print(f"   📁 {folder['name']}")
                print(f"      ID: {folder['id']}")
                print()

        print(f"{'='*50}")
        print("💡 Use folder ID with: python3 gdrive_uploader.py <file> <folder_id>")
        print(f"{'='*50}\n")

        return folders

    except HttpError as error:
        print(f"❌ Error listing folders: {error}")
        sys.exit(1)


def create_folder(folder_name, parent_id=None):
    """Create a new folder in Drive."""
    service = get_drive_service()

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
        print(f"   Name: {folder.get('name')}")
        print(f"   ID: {folder.get('id')}")
        print(f"   Link: {folder.get('webViewLink')}\n")

        return folder

    except HttpError as error:
        print(f"❌ Error creating folder: {error}")
        sys.exit(1)


def check_quota():
    """Check Google Drive storage quota."""
    service = get_drive_service()

    try:
        about = service.about().get(fields="storageQuota, user").execute()
        quota = about.get('storageQuota', {})
        user = about.get('user', {})

        used = int(quota.get('usage', 0))
        total = int(quota.get('limit', 0))

        print(f"\n{'='*50}")
        print(f"👤 Account: {user.get('emailAddress', 'Unknown')}")
        print(f"{'='*50}")
        print(f"📊 Storage Used: {format_size(used)}")
        if total > 0:
            print(f"📊 Storage Total: {format_size(total)}")
            print(f"📊 Available: {format_size(total - used)}")
            print(f"📊 Usage: {(used/total)*100:.1f}%")
        print(f"{'='*50}\n")

    except HttpError as error:
        print(f"❌ Error checking quota: {error}")


def print_usage():
    """Print usage instructions."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           UNIVERSAL GOOGLE DRIVE UPLOADER                    ║
╠══════════════════════════════════════════════════════════════╣
║  Upload any file to Google Drive from command line           ║
╚══════════════════════════════════════════════════════════════╝

USAGE:
    python3 gdrive_uploader.py <file_path> [folder_id]
    python3 gdrive_uploader.py <command>

COMMANDS:
    --list-folders          List all folders in Drive root
    --list-folders <id>     List subfolders of a folder
    --create-folder <name>  Create new folder in root
    --quota                 Check storage quota
    --help                  Show this help message

EXAMPLES:
    # Upload file to Drive root
    python3 gdrive_uploader.py video.mp4

    # Upload file to specific folder
    python3 gdrive_uploader.py document.pdf 1ABC123xyz

    # Upload any file type
    python3 gdrive_uploader.py backup.tar.gz
    python3 gdrive_uploader.py database.sql
    python3 gdrive_uploader.py image.png

    # List folders to find folder ID
    python3 gdrive_uploader.py --list-folders

    # Check storage
    python3 gdrive_uploader.py --quota
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1]

    # Handle commands
    if command in ('--help', '-h'):
        print_usage()

    elif command == '--list-folders':
        parent_id = sys.argv[2] if len(sys.argv) > 2 else None
        list_folders(parent_id)

    elif command == '--create-folder':
        if len(sys.argv) < 3:
            print("❌ Error: Folder name required")
            print("   Usage: python3 gdrive_uploader.py --create-folder <name>")
            sys.exit(1)
        folder_name = sys.argv[2]
        parent_id = sys.argv[3] if len(sys.argv) > 3 else None
        create_folder(folder_name, parent_id)

    elif command == '--quota':
        check_quota()

    elif command.startswith('--'):
        print(f"❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)

    else:
        # It's a file path - upload it
        file_path = command
        folder_id = sys.argv[2] if len(sys.argv) > 2 else None
        upload_file(file_path, folder_id)


if __name__ == '__main__':
    main()
