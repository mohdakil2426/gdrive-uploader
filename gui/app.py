#!/usr/bin/env python3
"""
Modern Download Manager GUI with Google Drive Integration
Uses CustomTkinter for modern dark-themed interface
"""

import io
import json
import os
import threading
import uuid
from datetime import datetime
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GoogleDriveManager:
    """Handle all Google Drive operations."""

    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json"
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.uploader_folder_id = None
        self._connect()

    def _connect(self):
        """Connect to Google Drive API."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise ConnectionError(
                    "No valid credentials found. Please run authentication first."
                )

        self.service = build('drive', 'v3', credentials=creds)
        self._ensure_uploader_folder()

    def _ensure_uploader_folder(self):
        """Ensure .uploader folder exists in MyDrive."""
        # Search for .uploader folder
        query = (
            "name='.uploader' and "
            "mimeType='application/vnd.google-apps.folder' and "
            "trashed=false"
        )
        results = self.service.files().list(
            q=query, spaces='drive', fields='files(id, name)'
        ).execute()
        files = results.get('files', [])

        if files:
            self.uploader_folder_id = files[0]['id']
        else:
            # Create .uploader folder
            folder_metadata = {
                'name': '.uploader',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=folder_metadata, fields='id'
            ).execute()
            self.uploader_folder_id = folder.get('id')

    def _get_file_id(self, filename: str) -> Optional[str]:
        """Get file ID by name in .uploader folder."""
        try:
            query = (
                f"name='{filename}' and "
                f"'{self.uploader_folder_id}' in parents and "
                f"trashed=false"
            )
            results = self.service.files().list(
                q=query, spaces='drive', fields='files(id)'
            ).execute()
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception:  # pylint: disable=broad-except
            return None

    def read_json(self, filename: str) -> dict:
        """Read JSON file from .uploader folder."""
        try:
            file_id = self._get_file_id(filename)
            if not file_id:
                return {} if filename == "queue.json" else {"downloads": {}}

            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            content = fh.getvalue().decode('utf-8')
            return json.loads(content)
        except Exception as err:  # pylint: disable=broad-except
            print(f"Error reading {filename}: {err}")
            return {} if filename == "queue.json" else {"downloads": {}}

    def write_json(self, filename: str, data: dict):
        """Write JSON file to .uploader folder."""
        file_id = self._get_file_id(filename)
        content = json.dumps(data, indent=2)
        fh = io.BytesIO(content.encode('utf-8'))

        media = MediaIoBaseUpload(fh, mimetype='application/json', resumable=True)

        if file_id:
            # Update existing file
            self.service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Create new file
            file_metadata = {
                'name': filename,
                'parents': [self.uploader_folder_id],
                'mimeType': 'application/json'
            }
            self.service.files().create(
                body=file_metadata, media_body=media, fields='id'
            ).execute()


class DownloadItem(ctk.CTkFrame):
    """Individual download item widget."""

    def __init__(
        self, parent, download_id: str, url: str, folder: str, status: str, **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.download_id = download_id
        self.url = url
        self.folder = folder
        self.current_status = status

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # URL Label (truncated)
        url_display = url if len(url) <= 60 else url[:57] + "..."
        self.url_label = ctk.CTkLabel(
            self,
            text=url_display,
            anchor="w",
            font=("Arial", 12)
        )
        self.url_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        # Info frame (folder + status)
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 0))

        self.folder_label = ctk.CTkLabel(
            self.info_frame,
            text=f"📁 {folder}",
            font=("Arial", 10),
            text_color="gray70"
        )
        self.folder_label.pack(side="left", padx=(0, 20))

        self.status_label = ctk.CTkLabel(
            self.info_frame,
            text=f"Status: {status}",
            font=("Arial", 10),
            text_color="gray70"
        )
        self.status_label.pack(side="left")

        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)

        # Details label (filename, speed)
        self.details_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 9),
            text_color="gray60"
        )

    def update_status(self, status_data: dict):
        """Update the download status."""
        status = status_data.get('status', 'pending')
        self.current_status = status

        # Update status label with color
        status_colors = {
            'pending': 'gray70',
            'downloading': '#3b8ed0',
            'completed': '#2fa572',
            'error': '#d92027',
            'queued': 'gray60'
        }

        self.status_label.configure(
            text=f"Status: {status.capitalize()}",
            text_color=status_colors.get(status, 'gray70')
        )

        # Handle progress bar
        if status == 'downloading':
            percent = status_data.get('percent', 0)
            speed = status_data.get('speed', '')
            filename = status_data.get('filename', '')

            # Show progress bar if not already visible
            if not self.progress_bar.winfo_ismapped():
                self.progress_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
                self.details_label.grid(row=3, column=0, sticky="w", padx=10, pady=(2, 10))

            self.progress_bar.set(percent / 100.0)

            details_text = f"{filename} • {percent}%"
            if speed:
                details_text += f" • {speed}"
            self.details_label.configure(text=details_text)

        elif status == 'completed':
            filename = status_data.get('filename', 'Download')
            if self.progress_bar.winfo_ismapped():
                self.progress_bar.set(1.0)
                self.details_label.configure(text=f"✓ {filename}")
            else:
                self.details_label.grid(row=3, column=0, sticky="w", padx=10, pady=(2, 10))
                self.details_label.configure(text="✓ Completed")

        else:
            # Hide progress bar for other statuses
            if self.progress_bar.winfo_ismapped():
                self.progress_bar.grid_forget()
                self.details_label.grid_forget()


class DownloadManagerApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Download Manager")
        self.geometry("800x600")
        self.minsize(600, 400)

        # Google Drive Manager
        self.drive_manager = None
        self.download_widgets: dict[str, DownloadItem] = {}
        self.completed_downloads = set()
        self.polling_active = False

        # Initialize Google Drive
        self.after(100, self._initialize_drive)

        # Setup UI
        self._setup_ui()

        # Protocol for window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _initialize_drive(self):
        """Initialize Google Drive connection in background."""
        def connect():
            try:
                self.drive_manager = GoogleDriveManager()
                self.after(0, lambda: self.status_bar.configure(
                    text="✓ Connected to Google Drive"
                ))
                self.after(0, self._load_queue)
                self.after(0, self._start_polling)
            except Exception as err:  # pylint: disable=broad-except
                error_msg = str(err)
                self.after(0, lambda msg=error_msg: self.status_bar.configure(
                    text=f"✗ Drive Error: {msg}",
                    text_color="#d92027"
                ))
                self.after(0, lambda msg=error_msg: messagebox.showerror(
                    "Connection Error",
                    f"Failed to connect to Google Drive:\n{msg}"
                ))

        threading.Thread(target=connect, daemon=True).start()

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="📥 Download Manager",
            font=("Arial", 24, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Input frame
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)

        # URL input
        url_label = ctk.CTkLabel(input_frame, text="URL:", font=("Arial", 12))
        url_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        self.url_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter download URL...",
            height=40,
            font=("Arial", 12)
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.url_entry.bind("<Return>", lambda e: self._add_download())

        # Folder and button frame
        control_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        control_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        control_frame.grid_columnconfigure(1, weight=1)

        folder_label = ctk.CTkLabel(control_frame, text="Folder:", font=("Arial", 12))
        folder_label.grid(row=0, column=0, padx=(0, 10))

        self.folder_dropdown = ctk.CTkComboBox(
            control_frame,
            values=["Downloads", "Videos", "Music", "Documents", "Pictures"],
            state="readonly",
            width=200,
            font=("Arial", 12)
        )
        self.folder_dropdown.set("Downloads")
        self.folder_dropdown.grid(row=0, column=1, sticky="w")

        self.add_button = ctk.CTkButton(
            control_frame,
            text="Add Download",
            command=self._add_download,
            height=40,
            font=("Arial", 12, "bold")
        )
        self.add_button.grid(row=0, column=2, padx=(20, 0))

        # Queue frame
        queue_label = ctk.CTkLabel(
            self, text="Download Queue", font=("Arial", 16, "bold")
        )
        queue_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 10))

        # Scrollable frame for downloads
        self.queue_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.queue_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.queue_frame.grid_columnconfigure(0, weight=1)

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self,
            text="⏳ Connecting to Google Drive...",
            font=("Arial", 10),
            anchor="w",
            fg_color="#2b2b2b",
            corner_radius=0,
            height=30,
            padx=20
        )
        self.status_bar.grid(row=4, column=0, sticky="ew")

    def _add_download(self):
        """Add a new download to the queue."""
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showwarning("Invalid Input", "Please enter a URL")
            return

        if not self.drive_manager:
            messagebox.showerror("Not Connected", "Google Drive is not connected yet")
            return

        folder = self.folder_dropdown.get()

        # Create download object
        download = {
            "id": str(uuid.uuid4()),
            "url": url,
            "folder": folder,
            "status": "pending",
            "added_at": datetime.now().isoformat()
        }

        try:
            # Read existing queue
            queue_data = self.drive_manager.read_json("queue.json")

            if "downloads" not in queue_data:
                queue_data["downloads"] = []

            # Add new download
            queue_data["downloads"].append(download)

            # Write back to Drive
            self.drive_manager.write_json("queue.json", queue_data)

            # Update UI
            self._add_download_widget(download)

            # Clear input
            self.url_entry.delete(0, 'end')

            # Update status
            self.status_bar.configure(text=f"✓ Download added: {url[:50]}...")

        except Exception as err:  # pylint: disable=broad-except
            messagebox.showerror("Error", f"Failed to add download:\n{err}")

    def _add_download_widget(self, download: dict):
        """Add a download widget to the queue."""
        download_id = download['id']

        if download_id in self.download_widgets:
            return

        widget = DownloadItem(
            self.queue_frame,
            download_id=download_id,
            url=download['url'],
            folder=download['folder'],
            status=download['status']
        )
        widget.grid(sticky="ew", pady=5)
        self.queue_frame.grid_columnconfigure(0, weight=1)

        self.download_widgets[download_id] = widget

    def _load_queue(self):
        """Load existing queue from Google Drive."""
        if not self.drive_manager:
            return

        try:
            queue_data = self.drive_manager.read_json("queue.json")
            downloads = queue_data.get("downloads", [])

            for download in downloads:
                self._add_download_widget(download)

            if downloads:
                self.status_bar.configure(text=f"✓ Loaded {len(downloads)} download(s)")

        except Exception as err:  # pylint: disable=broad-except
            print(f"Error loading queue: {err}")

    def _start_polling(self):
        """Start polling for status updates."""
        if self.polling_active:
            return

        self.polling_active = True
        self._poll_status()

    def _poll_status(self):
        """Poll status.json for updates."""
        if not self.polling_active or not self.drive_manager:
            return

        def poll():
            try:
                status_data = self.drive_manager.read_json("status.json")
                downloads_status = status_data.get("downloads", {})

                # Update widgets
                for download_id, status_info in downloads_status.items():
                    if download_id in self.download_widgets:
                        widget = self.download_widgets[download_id]
                        old_status = widget.current_status
                        widget.update_status(status_info)

                        # Show notification on completion
                        if (old_status != 'completed' and
                                status_info.get('status') == 'completed'):
                            if download_id not in self.completed_downloads:
                                self.completed_downloads.add(download_id)
                                filename = status_info.get('filename', 'Download')
                                self.after(
                                    0,
                                    lambda f=filename: self._show_completion_notification(f)
                                )

            except Exception as err:  # pylint: disable=broad-except
                print(f"Polling error: {err}")

            # Schedule next poll
            if self.polling_active:
                self.after(3000, self._poll_status)

        threading.Thread(target=poll, daemon=True).start()

    def _show_completion_notification(self, filename: str):
        """Show completion notification."""
        self.status_bar.configure(
            text=f"✓ Download completed: {filename}",
            text_color="#2fa572"
        )

        # Reset status bar color after 5 seconds
        self.after(5000, lambda: self.status_bar.configure(text_color="white"))

    def _on_closing(self):
        """Handle window closing."""
        self.polling_active = False
        self.destroy()


def main():
    """Main entry point."""
    try:
        app = DownloadManagerApp()
        app.mainloop()
    except Exception as err:
        messagebox.showerror("Fatal Error", f"Application failed to start:\n{err}")
        raise


if __name__ == "__main__":
    main()
