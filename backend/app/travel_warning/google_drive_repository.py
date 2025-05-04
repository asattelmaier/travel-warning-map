import logging
logger = logging.getLogger(__name__)
logger.info("GoogleDriveTravelWarningRepository module loaded.")

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
        logger.info("Instantiating GoogleDriveTravelWarningRepository...")
        self.drive_folder_id = drive_folder_id
        self.credentials = self._get_credentials()
        self._verify_folder_access()

    def _get_credentials(self):
        creds, _ = default(scopes=SCOPES)
        if not creds.valid:
            creds.refresh(Request())
        return creds

    def _get_drive_service(self):
        return build('drive', 'v3', credentials=self.credentials)

    def _verify_folder_access(self) -> None:
        drive_service = self._get_drive_service()
        try:
            result = drive_service.files().get(
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

    def _get_folder_id_for_date(self, date: str) -> Optional[str]:
        drive_service = self._get_drive_service()
        origin_query = f"name = '{settings.DRIVE_ORIGIN_FOLDER}' and '{self.drive_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        origin_results = drive_service.files().list(
            q=origin_query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        origin_folders = origin_results.get('files', [])
        if not origin_folders:
            return None
        origin_id = origin_folders[0]['id']
        self._validate_folder_structure(origin_id, settings.DRIVE_ORIGIN_FOLDER)
        date_query = f"name = '{date}' and '{origin_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        date_results = drive_service.files().list(
            q=date_query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        date_folders = date_results.get('files', [])
        if not date_folders:
            return None
        date_id = date_folders[0]['id']
        self._validate_folder_structure(date_id, date)
        return date_id

    def _validate_folder_structure(self, folder_id: str, expected_name: str) -> None:
        drive_service = self._get_drive_service()
        try:
            result = drive_service.files().get(
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

    def _validate_warning_id(self, warning_id: str) -> None:
        if not warning_id.isdigit():
            raise ValueError("Invalid warning ID format: must be a number")
        if len(warning_id) > 6:
            raise ValueError("Warning ID must not be longer than 6 digits")

    def get_travel_warnings(self, date: str, language: str = "en") -> Dict:
        drive_service = self._get_drive_service()
        folder_id = self._get_folder_id_for_date(date)
        if not folder_id:
            return {"response": {}}
        query = f"name = '{settings.DRIVE_TRAVELWARNING_FILE}' and '{folder_id}' in parents"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, size, mimeType)'
        ).execute()
        files = results.get('files', [])
        if not files or files[0].get('mimeType') != 'application/json':
            return {"response": {}}
        file_id = files[0]['id']
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        content = fh.read().decode()
        try:
            return json.loads(content)
        except Exception:
            return {"response": {}}

    def get_travel_warning(self, warning_id: str, date: str, language: str = "en") -> Dict:
        drive_service = self._get_drive_service()
        self._validate_warning_id(warning_id)
        folder_id = self._get_folder_id_for_date(date)
        if not folder_id:
            return {"response": {}}
        travel_query = f"name = '{settings.DRIVE_TRAVELWARNING_FOLDER}' and '{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        travel_results = drive_service.files().list(
            q=travel_query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        travel_folders = travel_results.get('files', [])
        if not travel_folders:
            return {"response": {}}
        travel_folder_id = travel_folders[0]['id']
        file_query = f"name = '{warning_id}.json' and '{travel_folder_id}' in parents"
        file_results = drive_service.files().list(
            q=file_query,
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute()
        files = file_results.get('files', [])
        if not files:
            return {"response": {}}
        file = files[0]
        request = drive_service.files().get_media(fileId=file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        content = fh.read().decode()
        try:
            return json.loads(content)
        except Exception:
            return {"response": {}} 