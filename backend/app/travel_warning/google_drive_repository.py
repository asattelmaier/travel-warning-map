from datetime import datetime, timedelta
import json
import io
from typing import Dict, Optional
from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.travel_warning.repository import TravelWarningRepository

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

class GoogleDriveTravelWarningRepository(TravelWarningRepository):
    def __init__(self, drive_folder_id: str):
        self.drive_folder_id = drive_folder_id
        self.credentials = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self._verify_folder_access()

    def _get_credentials(self):
        creds, _ = default(scopes=SCOPES)
        if not creds.valid:
            creds.refresh(Request())
        return creds

    def _verify_folder_access(self) -> None:
        try:
            result = self.drive_service.files().get(
                fileId=self.drive_folder_id,
                fields='id, name, mimeType'
            ).execute()
            if result.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError(f"ID {self.drive_folder_id} is not a folder")
        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Folder with ID {self.drive_folder_id} not found")
            elif e.resp.status == 403:
                error_details = json.loads(e.content.decode())
                error_message = error_details.get('error', {}).get('message', 'Unknown error')
                raise PermissionError(
                    f"No access to folder with ID {self.drive_folder_id}. Error: {error_message}"
                )
            else:
                raise

    def _validate_folder_structure(self, folder_id: str, expected_name: str) -> None:
        try:
            result = self.drive_service.files().get(
                fileId=folder_id,
                fields='id, name, mimeType'
            ).execute()
            if result.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError(f"ID {folder_id} is not a folder")
            if result.get('name') != expected_name:
                raise ValueError(f"Folder name mismatch: expected {expected_name}, got {result.get('name')}")
        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Folder with ID {folder_id} not found")
            elif e.resp.status == 403:
                raise PermissionError(f"No access to folder with ID {folder_id}")
            raise

    def _get_today_folder_id(self) -> Optional[str]:
        today = datetime.now().strftime('%Y-%m-%d')
        origin_query = f"name = '{settings.DRIVE_ORIGIN_FOLDER}' and '{self.drive_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        try:
            origin_results = self.drive_service.files().list(
                q=origin_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            origin_folders = origin_results.get('files', [])
            if not origin_folders:
                return None
            origin_id = origin_folders[0]['id']
            self._validate_folder_structure(origin_id, settings.DRIVE_ORIGIN_FOLDER)
            date_query = f"name = '{today}' and '{origin_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
            date_results = self.drive_service.files().list(
                q=date_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            date_folders = date_results.get('files', [])
            if not date_folders:
                return None
            date_id = date_folders[0]['id']
            self._validate_folder_structure(date_id, today)
            return date_id
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to list contents of folder {self.drive_folder_id}")
            raise

    def _get_yesterday_folder_id(self) -> Optional[str]:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        origin_query = f"name = '{settings.DRIVE_ORIGIN_FOLDER}' and '{self.drive_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        try:
            origin_results = self.drive_service.files().list(
                q=origin_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            origin_folders = origin_results.get('files', [])
            if not origin_folders:
                return None
            origin_id = origin_folders[0]['id']
            self._validate_folder_structure(origin_id, settings.DRIVE_ORIGIN_FOLDER)
            date_query = f"name = '{yesterday}' and '{origin_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
            date_results = self.drive_service.files().list(
                q=date_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            date_folders = date_results.get('files', [])
            if not date_folders:
                return None
            date_id = date_folders[0]['id']
            self._validate_folder_structure(date_id, yesterday)
            return date_id
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to list contents of folder {self.drive_folder_id}")
            raise

    def _validate_warning_id(self, warning_id: str) -> None:
        if not warning_id.isdigit():
            raise ValueError("Invalid warning ID format: must be a number")
        if len(warning_id) > 6:
            raise ValueError("Warning ID must not be longer than 6 digits")

    def get_travel_warnings(self, language: str = "en") -> Dict:
        today_folder_id = self._get_today_folder_id()
        if not today_folder_id:
            today_folder_id = self._get_yesterday_folder_id()
            if not today_folder_id:
                return {"response": {}}
        query = f"name = '{settings.DRIVE_TRAVELWARNING_FILE}' and '{today_folder_id}' in parents"
        try:
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, size, mimeType)'
            ).execute()
            files = results.get('files', [])
            if not files:
                return {"response": {}}
            if files[0].get('mimeType') != 'application/json':
                raise ValueError(f"File {files[0]['name']} is not a JSON file")
            request = self.drive_service.files().get_media(fileId=files[0]['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            content = fh.read().decode()
            warning_data = json.loads(content)
            if 'response' in warning_data:
                return warning_data
            return {"response": {}}
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to travelwarning.json")
            raise
        except json.JSONDecodeError as e:
            raise
        except Exception as e:
            raise

    def get_travel_warning(self, warning_id: str, language: str = "en") -> Dict:
        self._validate_warning_id(warning_id)
        today_folder_id = self._get_today_folder_id()
        if not today_folder_id:
            today_folder_id = self._get_yesterday_folder_id()
            if not today_folder_id:
                return {"response": {}}
        travel_query = f"name = '{settings.DRIVE_TRAVELWARNING_FOLDER}' and '{today_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        try:
            travel_results = self.drive_service.files().list(
                q=travel_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            travel_folders = travel_results.get('files', [])
            if not travel_folders:
                return {"response": {}}
            travel_folder_id = travel_folders[0]['id']
            self._validate_folder_structure(travel_folder_id, settings.DRIVE_TRAVELWARNING_FOLDER)
            warning_query = f"name = '{warning_id}.json' and '{travel_folder_id}' in parents"
            warning_results = self.drive_service.files().list(
                q=warning_query,
                spaces='drive',
                fields='files(id, name, mimeType)'
            ).execute()
            warning_files = warning_results.get('files', [])
            if not warning_files:
                return {"response": {}}
            if warning_files[0].get('mimeType') != 'application/json':
                raise ValueError(f"File {warning_files[0]['name']} is not a JSON file")
            request = self.drive_service.files().get_media(fileId=warning_files[0]['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            content = fh.read().decode()
            warning_data = json.loads(content)
            return warning_data
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to warning file {warning_id}.json")
            raise
        except json.JSONDecodeError as e:
            raise
        except Exception as e:
            raise 